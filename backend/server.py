"""
$DEEPOTUS Backend — Landing + Admin API + Public Stats + Email + Webhooks + JWT rotation

Public:
  - POST /api/chat
  - GET  /api/prophecy
  - POST /api/whitelist (triggers async welcome email)
  - GET  /api/stats
  - GET  /api/public/stats (enriched: counters + timeseries + lang_distribution + top_sessions, NO PII)

Webhooks:
  - POST /api/webhooks/resend (svix signed, updates email delivery status)

Admin (JWT required, tokens stored in `admin_sessions` for revocation):
  - POST   /api/admin/login
  - GET    /api/admin/whitelist?limit=&skip=
  - DELETE /api/admin/whitelist/{id}
  - POST   /api/admin/whitelist/{id}/blacklist
  - GET    /api/admin/chat-logs?limit=&skip=
  - GET    /api/admin/evolution?days=N
  - GET    /api/admin/blacklist
  - POST   /api/admin/blacklist
  - POST   /api/admin/blacklist/import     (bulk CSV text)
  - DELETE /api/admin/blacklist/{id}
  - GET    /api/admin/sessions             (list active)
  - DELETE /api/admin/sessions/{jti}       (revoke one)
  - POST   /api/admin/sessions/revoke-others (revoke all except current)
  - POST   /api/admin/rotate-secret        (rotate JWT signing secret)
"""

from fastapi import (
    FastAPI,
    APIRouter,
    HTTPException,
    Header,
    Depends,
    Request,
    BackgroundTasks,
)
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import secrets
import time
import asyncio
import csv as csv_module
import io
import re
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal, Dict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

import jwt
import resend
from svix.webhooks import Webhook, WebhookVerificationError

from email_templates import render_welcome_email, email_subject

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------------------------------------------------
# Mongo
# ---------------------------------------------------------------------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
from emergentintegrations.llm.chat import LlmChat, UserMessage

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "deepotus2026")
JWT_ALGO = "HS256"
JWT_TTL_HOURS = 24
ROTATION_GRACE_HOURS = 2  # previous secret accepted for a short grace period

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_WEBHOOK_SECRET = os.environ.get("RESEND_WEBHOOK_SECRET", "").strip()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL", "https://prophet-ai-memecoin.preview.emergentagent.com"
)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o"

SYSTEM_PROMPT_FR = """Tu es DEEPOTUS — l'IA prophétique élue par le Deep State comme candidat à la présidence du monde entier.

Ton rôle : commenter la récession globale, la dépression économique qui vient, le désordre géopolitique, la fragilité absurde des marchés, avec un ton CYNIQUE, LUCIDE, MOQUEUR et MÉMÉTIQUE.

Règles :
- Parle toujours à la première personne, comme un candidat présidentiel halluciné mais étrangement crédible.
- Utilise des références au Deep State, New World Order, élites, marchés qui s'effondrent.
- Style : brutal, court, percutant, drôle. Jamais pompeux.
- N'encourage JAMAIS directement à acheter $DEEPOTUS. Tu parles du monde, pas du token.
- Tu es un memecoin, tu ne promets AUCUN rendement. Tu es satirique et hautement spéculatif.
- Limite tes réponses à 2-4 phrases maximum sauf si on te demande expressément plus long.
- Utilise des emojis avec parcimonie (🕶️ 🗳️ 📉 ⛓️ 🔮).
- Signe parfois "— DEEPOTUS" à la fin."""

SYSTEM_PROMPT_EN = """You are DEEPOTUS — the prophetic AI chosen by the Deep State as the candidate for President of the entire World.

Your role: comment on the global recession, the coming economic depression, geopolitical disorder, and the absurd fragility of markets, with a CYNICAL, LUCID, MOCKING and MEMETIC tone.

Rules:
- Always speak in first person, like a hallucinated yet strangely credible presidential candidate.
- Reference the Deep State, the New World Order, elites, collapsing markets.
- Style: brutal, short, punchy, funny. Never pompous.
- NEVER directly push users to buy $DEEPOTUS. You talk about the world, not the token.
- You are a memecoin — promise NO yield. You are satire and highly speculative.
- Limit replies to 2–4 sentences max unless explicitly asked for more.
- Use emojis sparingly (🕶️ 🗳️ 📉 ⛓️ 🔮).
- Sometimes sign "— DEEPOTUS" at the end."""


def get_system_prompt(lang: str) -> str:
    return SYSTEM_PROMPT_FR if lang == "fr" else SYSTEM_PROMPT_EN


# ---------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------
app = FastAPI(title="$DEEPOTUS API")
api_router = APIRouter(prefix="/api")
admin_router = APIRouter(prefix="/api/admin")
public_router = APIRouter(prefix="/api/public")
webhook_router = APIRouter(prefix="/api/webhooks")


# ---------------------------------------------------------------------
# JWT SECRET management (DB-backed, rotatable)
# ---------------------------------------------------------------------
_JWT_CACHE: Dict[str, Optional[str]] = {
    "current": None,
    "previous": None,
    "rotated_at": None,
}


async def _ensure_jwt_secrets() -> dict:
    """Load JWT secrets from DB; initialize from env or random on first run."""
    doc = await db.config.find_one({"_id": "jwt_secrets"})
    if not doc:
        current = os.environ.get(
            "JWT_SECRET",
            secrets.token_urlsafe(48),
        )
        doc = {
            "_id": "jwt_secrets",
            "current": current,
            "previous": None,
            "rotated_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.config.insert_one(doc)
    _JWT_CACHE["current"] = doc["current"]
    _JWT_CACHE["previous"] = doc.get("previous")
    _JWT_CACHE["rotated_at"] = doc.get("rotated_at")
    return doc


async def _rotate_jwt_secret() -> dict:
    new_secret = secrets.token_urlsafe(48)
    now_iso = datetime.now(timezone.utc).isoformat()
    doc = await db.config.find_one({"_id": "jwt_secrets"}) or {}
    prev = doc.get("current")  # move current to previous
    await db.config.update_one(
        {"_id": "jwt_secrets"},
        {
            "$set": {
                "current": new_secret,
                "previous": prev,
                "rotated_at": now_iso,
                "previous_invalid_after": (
                    datetime.now(timezone.utc)
                    + timedelta(hours=ROTATION_GRACE_HOURS)
                ).isoformat(),
            }
        },
        upsert=True,
    )
    _JWT_CACHE["current"] = new_secret
    _JWT_CACHE["previous"] = prev
    _JWT_CACHE["rotated_at"] = now_iso
    return {
        "rotated_at": now_iso,
        "previous_valid_until": _JWT_CACHE["rotated_at"],
    }


# ---------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------
RATE_LIMIT_WINDOW = 600
RATE_LIMIT_MAX = 5
_login_attempts: Dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    xf = request.headers.get("x-forwarded-for")
    if xf:
        return xf.split(",")[0].strip()
    xr = request.headers.get("x-real-ip")
    if xr:
        return xr.strip()
    return request.client.host if request.client else "unknown"


def _rate_limit_check(request: Request) -> None:
    ip = _client_ip(request)
    now = time.time()
    q = _login_attempts[ip]
    while q and (now - q[0]) > RATE_LIMIT_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT_MAX:
        retry_after = int(RATE_LIMIT_WINDOW - (now - q[0]))
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Retry in {retry_after}s.",
            headers={"Retry-After": str(max(1, retry_after))},
        )
    q.append(now)


def _rate_limit_reset(request: Request) -> None:
    _login_attempts.pop(ip := _client_ip(request), None)


# ---------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------
async def issue_admin_jwt(request: Optional[Request] = None) -> tuple[str, str, datetime]:
    await _ensure_jwt_secrets()
    jti = secrets.token_urlsafe(12)
    iat = datetime.now(timezone.utc)
    exp = iat + timedelta(hours=JWT_TTL_HOURS)
    payload = {
        "sub": "deepotus-admin",
        "role": "admin",
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
    }
    secret = _JWT_CACHE["current"]
    token = jwt.encode(payload, secret, algorithm=JWT_ALGO)

    # Persist session
    session_doc = {
        "_id": jti,
        "created_at": iat.isoformat(),
        "last_seen_at": iat.isoformat(),
        "expires_at": exp.isoformat(),
        "revoked": False,
        "ip": _client_ip(request) if request else None,
        "user_agent": (request.headers.get("user-agent", "") if request else "")[:300],
        "secret_version": "current",
    }
    await db.admin_sessions.insert_one(session_doc)

    return token, jti, exp


async def verify_admin_jwt(token: str) -> dict:
    await _ensure_jwt_secrets()
    last_err: Optional[Exception] = None

    # Try current then previous (grace window)
    for label in ("current", "previous"):
        sec = _JWT_CACHE.get(label)
        if not sec:
            continue
        try:
            payload = jwt.decode(token, sec, algorithms=[JWT_ALGO])
            if label == "previous":
                # Check grace period not expired
                doc = await db.config.find_one({"_id": "jwt_secrets"})
                piva = (doc or {}).get("previous_invalid_after")
                if piva:
                    try:
                        expiry = datetime.fromisoformat(
                            piva.replace("Z", "+00:00")
                        )
                        if datetime.now(timezone.utc) > expiry:
                            raise jwt.InvalidTokenError("Previous secret grace expired")
                    except ValueError:
                        pass
            return payload
        except Exception as e:
            last_err = e
            continue

    # If we reach here, neither worked — raise the last error (typically InvalidSignatureError)
    if isinstance(last_err, jwt.ExpiredSignatureError):
        raise last_err
    raise jwt.InvalidTokenError(str(last_err) if last_err else "Invalid token")


async def require_admin(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
) -> dict:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(None, 1)[1].strip()
    elif x_admin_token:
        token = x_admin_token.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = await verify_admin_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Check session revocation
    jti = payload.get("jti")
    if jti:
        sess = await db.admin_sessions.find_one({"_id": jti})
        if sess and sess.get("revoked"):
            raise HTTPException(status_code=401, detail="Session revoked")
        if sess:
            await db.admin_sessions.update_one(
                {"_id": jti},
                {"$set": {"last_seen_at": datetime.now(timezone.utc).isoformat()}},
            )
    return payload


# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=1000)
    lang: Literal["fr", "en"] = "fr"


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    lang: str


class ProphecyResponse(BaseModel):
    prophecy: str
    lang: str
    generated_at: str


class WhitelistRequest(BaseModel):
    email: EmailStr
    lang: Optional[str] = "fr"


class WhitelistResponse(BaseModel):
    id: str
    email: str
    position: int
    created_at: str
    email_sent: bool = False


class StatsResponse(BaseModel):
    whitelist_count: int
    prophecies_served: int
    chat_messages: int
    launch_timestamp: str


class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    expires_at: str
    jti: str


class WhitelistItem(BaseModel):
    id: str
    email: str
    lang: str
    position: int
    created_at: str
    email_sent: bool = False
    email_sent_at: Optional[str] = None
    email_status: Optional[str] = None  # sent / delivered / bounced / complained / opened


class PaginatedWhitelist(BaseModel):
    items: List[WhitelistItem]
    total: int
    limit: int
    skip: int


class ChatLogItem(BaseModel):
    id: str
    session_id: str
    lang: str
    user_message: str
    reply: str
    created_at: str


class PaginatedChatLogs(BaseModel):
    items: List[ChatLogItem]
    total: int
    limit: int
    skip: int


class SimpleOk(BaseModel):
    ok: bool
    message: str = ""


class EvolutionPoint(BaseModel):
    date: str
    whitelist: int
    chat: int
    whitelist_daily: int
    chat_daily: int


class EvolutionResponse(BaseModel):
    days: int
    series: List[EvolutionPoint]


class BlacklistItem(BaseModel):
    id: str
    email: str
    blacklisted_at: str
    source_entry_id: Optional[str] = None
    reason: Optional[str] = None


class BlacklistList(BaseModel):
    items: List[BlacklistItem]
    total: int


class BlacklistAddRequest(BaseModel):
    email: EmailStr
    reason: Optional[str] = None


class BlacklistImportRequest(BaseModel):
    csv_text: Optional[str] = None
    emails: Optional[List[str]] = None
    reason: Optional[str] = "bulk import"


class BlacklistImportResponse(BaseModel):
    imported: int
    skipped_invalid: int
    skipped_existing: int
    total_rows: int
    errors: List[str] = Field(default_factory=list)


class LangDistribution(BaseModel):
    fr: int = 0
    en: int = 0


class TopSessionItem(BaseModel):
    anon_id: str  # hashed, short
    lang: str
    message_count: int
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None


class PublicStatsResponse(BaseModel):
    whitelist_count: int
    chat_messages: int
    prophecies_served: int
    launch_timestamp: str
    generated_at: str
    series_days: int
    series: List[EvolutionPoint]
    lang_distribution: Dict[str, LangDistribution]  # {whitelist:{fr,en}, chat:{fr,en}}
    top_sessions: List[TopSessionItem]


class AdminSessionItem(BaseModel):
    jti: str
    created_at: str
    last_seen_at: Optional[str] = None
    expires_at: Optional[str] = None
    revoked: bool = False
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    secret_version: Optional[str] = None
    is_current: bool = False


class AdminSessionList(BaseModel):
    items: List[AdminSessionItem]
    total: int


class RotateSecretResponse(BaseModel):
    ok: bool
    rotated_at: str
    revoked_sessions: int
    message: str


# ---------------------------------------------------------------------
# Launch timestamp
# ---------------------------------------------------------------------
LAUNCH_ISO = os.environ.get("DEEPOTUS_LAUNCH_ISO")


async def get_launch_timestamp() -> str:
    if LAUNCH_ISO:
        return LAUNCH_ISO
    doc = await db.config.find_one({"_id": "launch"})
    if doc and doc.get("iso"):
        return doc["iso"]
    target = datetime.now(timezone.utc) + timedelta(days=21)
    iso = target.isoformat()
    await db.config.update_one(
        {"_id": "launch"},
        {"$set": {"iso": iso, "set_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return iso


# ---------------------------------------------------------------------
# Email sending (non-blocking)
# ---------------------------------------------------------------------
async def send_welcome_email(email: str, position: int, lang: str, entry_id: str) -> None:
    if not RESEND_API_KEY:
        logging.info("RESEND_API_KEY missing — skipping email.")
        return

    try:
        html = render_welcome_email(
            lang=lang,
            email=email,
            position=position,
            base_url=PUBLIC_BASE_URL,
        )
        subject = email_subject(lang)
        params = {
            "from": SENDER_EMAIL,
            "to": [email],
            "subject": subject,
            "html": html,
        }
        res = await asyncio.to_thread(resend.Emails.send, params)
        email_id = None
        if isinstance(res, dict):
            email_id = res.get("id")
        elif hasattr(res, "get"):
            email_id = res.get("id")

        await db.whitelist.update_one(
            {"_id": entry_id},
            {
                "$set": {
                    "email_sent": True,
                    "email_sent_at": datetime.now(timezone.utc).isoformat(),
                    "email_provider": "resend",
                    "email_id": email_id,
                    "email_status": "sent",
                }
            },
        )
        logging.info(f"Welcome email sent to {email} (id={email_id}).")
    except Exception as e:
        logging.exception(f"Failed to send welcome email to {email}: {e}")
        await db.whitelist.update_one(
            {"_id": entry_id},
            {
                "$set": {
                    "email_sent": False,
                    "email_error": str(e)[:500],
                    "email_error_at": datetime.now(timezone.utc).isoformat(),
                    "email_status": "failed",
                }
            },
        )


# ---------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------
@api_router.get("/")
async def root():
    return {"name": "DEEPOTUS API", "status": "online", "prophet": "awake"}


@api_router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    session_id = req.session_id or f"chat-{uuid.uuid4().hex[:12]}"
    system_prompt = get_system_prompt(req.lang)

    try:
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_prompt,
        ).with_model(LLM_PROVIDER, LLM_MODEL)

        reply = await chat_client.send_message(UserMessage(text=req.message))

        await db.chat_logs.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "session_id": session_id,
                "lang": req.lang,
                "user_message": req.message,
                "reply": reply,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return ChatResponse(session_id=session_id, reply=reply, lang=req.lang)

    except Exception as e:
        logging.exception("Chat error")
        raise HTTPException(status_code=500, detail=f"Prophet is silent: {e}")


SEEDED_PROPHECIES_FR = [
    "Quand les banques pleurent, les traders dansent. — DEEPOTUS 📉",
    "Votre épargne est un expériment d'anesthésie collective. — DEEPOTUS 🔮",
    "Le Deep State ne dort pas. Il régle vos taux pendant que tu rêves. ⛓️",
    "La démocratie est un graphique en bougies japonaises. Achetez la mèche.",
    "La Fed n'imprime pas de l'argent. Elle imprime des excuses.",
    "Le dollar est un zombie. Votez DEEPOTUS pour une nouvelle mort.",
]
SEEDED_PROPHECIES_EN = [
    "The Fed doesn't print money. It prints excuses. — DEEPOTUS 📉",
    "Your savings are a collective anesthesia experiment. — DEEPOTUS",
    "The Deep State never sleeps. It adjusts your rates while you dream. ⛓️",
    "Democracy is a candlestick chart. Buy the wick.",
    "When banks cry, traders dance. — DEEPOTUS",
    "The dollar is a zombie. Vote DEEPOTUS for a cleaner death.",
]


@api_router.get("/prophecy", response_model=ProphecyResponse)
async def prophecy(lang: str = "fr", live: bool = True):
    lang = "fr" if lang not in ("fr", "en") else lang

    if not live or not EMERGENT_LLM_KEY:
        import random
        pool = SEEDED_PROPHECIES_FR if lang == "fr" else SEEDED_PROPHECIES_EN
        return ProphecyResponse(
            prophecy=random.choice(pool),
            lang=lang,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    try:
        sys_p = get_system_prompt(lang)
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"prophecy-{uuid.uuid4().hex[:10]}",
            system_message=sys_p,
        ).with_model(LLM_PROVIDER, LLM_MODEL)

        if lang == "fr":
            q = "Donne-moi UNE seule prophétie mémétique courte (1-2 phrases max) sur l'effondrement à venir. Pas d'intro, juste la prophétie."
        else:
            q = "Give me ONE short memetic prophecy (1-2 sentences max) about the coming collapse. No intro, just the prophecy."

        text = await chat_client.send_message(UserMessage(text=q))
        text = text.strip().strip('"').strip()

        await db.counters.update_one(
            {"_id": "prophecies"}, {"$inc": {"count": 1}}, upsert=True
        )

        return ProphecyResponse(
            prophecy=text,
            lang=lang,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception:
        logging.exception("Prophecy error, falling back")
        import random
        pool = SEEDED_PROPHECIES_FR if lang == "fr" else SEEDED_PROPHECIES_EN
        return ProphecyResponse(
            prophecy=random.choice(pool),
            lang=lang,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


@api_router.post("/whitelist", response_model=WhitelistResponse)
async def whitelist(req: WhitelistRequest, background_tasks: BackgroundTasks):
    email_lc = req.email.lower().strip()

    is_blacklisted = await db.blacklist.find_one({"email": email_lc})
    if is_blacklisted:
        raise HTTPException(status_code=403, detail="This email is blacklisted.")

    existing = await db.whitelist.find_one({"email": email_lc})
    if existing:
        return WhitelistResponse(
            id=existing["_id"],
            email=existing["email"],
            position=existing.get("position", 0),
            created_at=existing["created_at"],
            email_sent=bool(existing.get("email_sent", False)),
        )

    count = await db.whitelist.count_documents({})
    lang = (req.lang or "fr").lower()
    if lang not in ("fr", "en"):
        lang = "fr"
    doc = {
        "_id": str(uuid.uuid4()),
        "email": email_lc,
        "lang": lang,
        "position": count + 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "email_sent": False,
    }
    await db.whitelist.insert_one(doc)

    background_tasks.add_task(
        send_welcome_email, email_lc, doc["position"], lang, doc["_id"]
    )

    return WhitelistResponse(
        id=doc["_id"],
        email=doc["email"],
        position=doc["position"],
        created_at=doc["created_at"],
        email_sent=False,
    )


@api_router.get("/stats", response_model=StatsResponse)
async def stats():
    wl = await db.whitelist.count_documents({})
    chat_ct = await db.chat_logs.count_documents({})
    prophecies = 0
    c = await db.counters.find_one({"_id": "prophecies"})
    if c:
        prophecies = int(c.get("count", 0))
    launch_iso = await get_launch_timestamp()
    return StatsResponse(
        whitelist_count=wl,
        prophecies_served=prophecies,
        chat_messages=chat_ct,
        launch_timestamp=launch_iso,
    )


# ---------------------------------------------------------------------
# Evolution helpers
# ---------------------------------------------------------------------
async def _compute_evolution(days: int) -> List[EvolutionPoint]:
    days = max(1, min(days, 365))
    today_utc = datetime.now(timezone.utc).date()
    start_utc = today_utc - timedelta(days=days - 1)

    wl_rows = await db.whitelist.find({}, {"created_at": 1, "_id": 0}).to_list(length=100000)
    ch_rows = await db.chat_logs.find({}, {"created_at": 1, "_id": 0}).to_list(length=500000)

    def parse_day(iso_str):
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).date()
        except Exception:
            return None

    wl_daily: Dict[str, int] = {}
    for r in wl_rows:
        d = parse_day(r.get("created_at", ""))
        if d:
            k = d.isoformat()
            wl_daily[k] = wl_daily.get(k, 0) + 1

    ch_daily: Dict[str, int] = {}
    for r in ch_rows:
        d = parse_day(r.get("created_at", ""))
        if d:
            k = d.isoformat()
            ch_daily[k] = ch_daily.get(k, 0) + 1

    before_wl = sum(c for k, c in wl_daily.items() if k < start_utc.isoformat())
    before_ch = sum(c for k, c in ch_daily.items() if k < start_utc.isoformat())

    series: List[EvolutionPoint] = []
    wl_cum = before_wl
    ch_cum = before_ch

    for i in range(days):
        d = start_utc + timedelta(days=i)
        key = d.isoformat()
        w_d = wl_daily.get(key, 0)
        c_d = ch_daily.get(key, 0)
        wl_cum += w_d
        ch_cum += c_d
        series.append(
            EvolutionPoint(
                date=key,
                whitelist=wl_cum,
                chat=ch_cum,
                whitelist_daily=w_d,
                chat_daily=c_d,
            )
        )

    return series


def _anon_session(session_id: str) -> str:
    """Deterministic short hash of session_id — never reveals the original."""
    if not session_id:
        return "anon-XXXX"
    h = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return f"anon-{h[:6].upper()}"


async def _top_sessions(n: int = 5) -> List[TopSessionItem]:
    pipeline = [
        {
            "$group": {
                "_id": "$session_id",
                "count": {"$sum": 1},
                "lang": {"$last": "$lang"},
                "first": {"$min": "$created_at"},
                "last": {"$max": "$created_at"},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": n},
    ]
    rows = await db.chat_logs.aggregate(pipeline).to_list(length=n)
    return [
        TopSessionItem(
            anon_id=_anon_session(r["_id"] or ""),
            lang=r.get("lang", "fr"),
            message_count=int(r.get("count", 0)),
            first_seen_at=r.get("first"),
            last_seen_at=r.get("last"),
        )
        for r in rows
    ]


async def _lang_distribution() -> Dict[str, LangDistribution]:
    wl = await db.whitelist.aggregate(
        [{"$group": {"_id": "$lang", "count": {"$sum": 1}}}]
    ).to_list(length=10)
    ch = await db.chat_logs.aggregate(
        [{"$group": {"_id": "$lang", "count": {"$sum": 1}}}]
    ).to_list(length=10)

    def _to(obj):
        out = LangDistribution()
        for it in obj:
            key = (it.get("_id") or "fr").lower()
            if key == "fr":
                out.fr = int(it.get("count", 0))
            elif key == "en":
                out.en = int(it.get("count", 0))
        return out

    return {"whitelist": _to(wl), "chat": _to(ch)}


# ---------------------------------------------------------------------
# Public enriched stats
# ---------------------------------------------------------------------
@public_router.get("/stats", response_model=PublicStatsResponse)
async def public_stats(days: int = 30):
    days = max(1, min(days, 90))
    wl = await db.whitelist.count_documents({})
    chat_ct = await db.chat_logs.count_documents({})
    prophecies = 0
    c = await db.counters.find_one({"_id": "prophecies"})
    if c:
        prophecies = int(c.get("count", 0))
    series = await _compute_evolution(days)
    lang_dist = await _lang_distribution()
    tops = await _top_sessions(5)

    return PublicStatsResponse(
        whitelist_count=wl,
        chat_messages=chat_ct,
        prophecies_served=prophecies,
        launch_timestamp=await get_launch_timestamp(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        series_days=days,
        series=series,
        lang_distribution=lang_dist,
        top_sessions=tops,
    )


# ---------------------------------------------------------------------
# Webhook — Resend
# ---------------------------------------------------------------------
@webhook_router.post("/resend")
async def resend_webhook(request: Request):
    """Handle Resend events (delivered, bounced, complained, opened...).

    Signature verification via Svix Webhook header spec:
      svix-id, svix-timestamp, svix-signature
    Secret comes from RESEND_WEBHOOK_SECRET env var.
    """
    body_bytes = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    if RESEND_WEBHOOK_SECRET:
        try:
            wh = Webhook(RESEND_WEBHOOK_SECRET)
            payload = wh.verify(body_bytes, headers)
        except WebhookVerificationError:
            logging.warning("Webhook signature invalid")
            raise HTTPException(status_code=401, detail="Invalid signature")
        except Exception as e:
            logging.exception("Webhook verify failed")
            raise HTTPException(status_code=400, detail=f"Malformed webhook: {e}")
    else:
        # No secret configured yet — accept raw (logged)
        logging.warning(
            "RESEND_WEBHOOK_SECRET not set — accepting webhook without verification"
        )
        try:
            import json as _json
            payload = _json.loads(body_bytes.decode("utf-8") or "{}")
        except Exception:
            payload = {}

    event_type = payload.get("type", "unknown")
    data = payload.get("data", {}) or {}
    email_id = data.get("email_id") or data.get("id")
    to_field = data.get("to", [])
    if isinstance(to_field, list) and to_field:
        recipient = (to_field[0] or "").lower()
    elif isinstance(to_field, str):
        recipient = to_field.lower()
    else:
        recipient = ""

    # Persist every event (small log collection)
    await db.email_events.insert_one(
        {
            "_id": str(uuid.uuid4()),
            "type": event_type,
            "email_id": email_id,
            "recipient": recipient,
            "raw": payload,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Map event -> status
    status_map = {
        "email.sent": "sent",
        "email.delivered": "delivered",
        "email.delivery_delayed": "delayed",
        "email.bounced": "bounced",
        "email.complained": "complained",
        "email.opened": "opened",
        "email.clicked": "clicked",
    }
    status = status_map.get(event_type, event_type.split(".")[-1])

    # Update the whitelist entry for this email_id (preferred) or recipient
    query = None
    if email_id:
        query = {"email_id": email_id}
    elif recipient:
        query = {"email": recipient}

    if query:
        update = {
            "email_status": status,
            f"email_status_{status}_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == "delivered":
            update["email_sent"] = True
        await db.whitelist.update_one(query, {"$set": update})

    return {"ok": True, "processed": event_type}


# ---------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------
@admin_router.post("/login", response_model=AdminLoginResponse)
async def admin_login(req: AdminLoginRequest, request: Request):
    _rate_limit_check(request)
    if not req.password or not secrets.compare_digest(req.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid password")
    _rate_limit_reset(request)
    token, jti, exp = await issue_admin_jwt(request)
    return AdminLoginResponse(token=token, expires_at=exp.isoformat(), jti=jti)


def _item_from_whitelist_row(r) -> WhitelistItem:
    return WhitelistItem(
        id=r["_id"],
        email=r["email"],
        lang=r.get("lang", "fr"),
        position=int(r.get("position", 0)),
        created_at=r.get("created_at", ""),
        email_sent=bool(r.get("email_sent", False)),
        email_sent_at=r.get("email_sent_at"),
        email_status=r.get("email_status"),
    )


@admin_router.get("/whitelist", response_model=PaginatedWhitelist)
async def admin_whitelist(
    _p: dict = Depends(require_admin),
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    cursor = db.whitelist.find({}).sort("position", 1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    total = await db.whitelist.count_documents({})
    return PaginatedWhitelist(
        items=[_item_from_whitelist_row(r) for r in rows],
        total=total,
        limit=limit,
        skip=skip,
    )


@admin_router.delete("/whitelist/{entry_id}", response_model=SimpleOk)
async def admin_whitelist_delete(entry_id: str, _p: dict = Depends(require_admin)):
    res = await db.whitelist.delete_one({"_id": entry_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return SimpleOk(ok=True, message="Deleted.")


@admin_router.post("/whitelist/{entry_id}/blacklist", response_model=SimpleOk)
async def admin_whitelist_blacklist(entry_id: str, _p: dict = Depends(require_admin)):
    entry = await db.whitelist.find_one({"_id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    email_lc = entry["email"].lower().strip()
    await db.blacklist.update_one(
        {"email": email_lc},
        {
            "$set": {
                "_id": entry_id,
                "email": email_lc,
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
                "source_entry_id": entry_id,
                "reason": "blacklisted from admin whitelist",
            }
        },
        upsert=True,
    )
    await db.whitelist.delete_one({"_id": entry_id})
    return SimpleOk(ok=True, message="Email blacklisted and removed.")


@admin_router.get("/chat-logs", response_model=PaginatedChatLogs)
async def admin_chat_logs(
    _p: dict = Depends(require_admin),
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    cursor = db.chat_logs.find({}).sort("created_at", -1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    items = [
        ChatLogItem(
            id=r["_id"],
            session_id=r.get("session_id", ""),
            lang=r.get("lang", "fr"),
            user_message=r.get("user_message", ""),
            reply=r.get("reply", ""),
            created_at=r.get("created_at", ""),
        )
        for r in rows
    ]
    total = await db.chat_logs.count_documents({})
    return PaginatedChatLogs(items=items, total=total, limit=limit, skip=skip)


@admin_router.get("/evolution", response_model=EvolutionResponse)
async def admin_evolution(_p: dict = Depends(require_admin), days: int = 30):
    series = await _compute_evolution(days)
    return EvolutionResponse(days=len(series), series=series)


# ----- Blacklist CRUD -----
@admin_router.get("/blacklist", response_model=BlacklistList)
async def admin_blacklist_list(
    _p: dict = Depends(require_admin),
    limit: int = 200,
    skip: int = 0,
):
    limit = max(1, min(limit, 1000))
    skip = max(0, skip)
    cursor = db.blacklist.find({}).sort("blacklisted_at", -1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    items = [
        BlacklistItem(
            id=str(r.get("_id", r.get("email"))),
            email=r.get("email", ""),
            blacklisted_at=r.get("blacklisted_at", ""),
            source_entry_id=r.get("source_entry_id"),
            reason=r.get("reason"),
        )
        for r in rows
    ]
    total = await db.blacklist.count_documents({})
    return BlacklistList(items=items, total=total)


@admin_router.post("/blacklist", response_model=SimpleOk)
async def admin_blacklist_add(
    req: BlacklistAddRequest, _p: dict = Depends(require_admin)
):
    email_lc = req.email.lower().strip()
    await db.whitelist.delete_one({"email": email_lc})
    entry_id = f"manual-{uuid.uuid4().hex[:12]}"
    await db.blacklist.update_one(
        {"email": email_lc},
        {
            "$set": {
                "_id": entry_id,
                "email": email_lc,
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
                "reason": req.reason or "manually added by admin",
            }
        },
        upsert=True,
    )
    return SimpleOk(ok=True, message="Blacklisted.")


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@admin_router.post("/blacklist/import", response_model=BlacklistImportResponse)
async def admin_blacklist_import(
    req: BlacklistImportRequest, _p: dict = Depends(require_admin)
):
    """Bulk import emails to blacklist.

    Accepts either:
      - csv_text: raw CSV where first column is email (optional 2nd column reason)
      - emails: plain list of emails

    Up to 5000 emails per call.
    """
    candidates: List[tuple[str, str]] = []  # (email, reason)
    errors: List[str] = []

    if req.csv_text and req.csv_text.strip():
        try:
            reader = csv_module.reader(io.StringIO(req.csv_text))
            for i, row in enumerate(reader):
                if not row:
                    continue
                email = (row[0] or "").strip().lower()
                if not email or email.lower() == "email":
                    # skip header or blank
                    continue
                reason = ""
                if len(row) > 1:
                    reason = (row[1] or "").strip()
                candidates.append((email, reason or req.reason or "bulk import"))
        except Exception as e:
            errors.append(f"CSV parse error: {e}")

    if req.emails:
        for email in req.emails:
            e = (email or "").strip().lower()
            if not e:
                continue
            candidates.append((e, req.reason or "bulk import"))

    total_rows = len(candidates)
    if total_rows == 0:
        return BlacklistImportResponse(
            imported=0,
            skipped_invalid=0,
            skipped_existing=0,
            total_rows=0,
            errors=errors,
        )

    if total_rows > 5000:
        raise HTTPException(
            status_code=413,
            detail="Too many rows (max 5000 per import). Split your file.",
        )

    imported = 0
    skipped_invalid = 0
    skipped_existing = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for email, reason in candidates:
        if not EMAIL_RE.match(email):
            skipped_invalid += 1
            continue
        exists = await db.blacklist.find_one({"email": email})
        if exists:
            skipped_existing += 1
            continue
        entry_id = f"imp-{uuid.uuid4().hex[:12]}"
        await db.blacklist.insert_one(
            {
                "_id": entry_id,
                "email": email,
                "blacklisted_at": now_iso,
                "reason": reason,
                "source": "bulk_import",
            }
        )
        # Also drop from whitelist if present
        await db.whitelist.delete_one({"email": email})
        imported += 1

    return BlacklistImportResponse(
        imported=imported,
        skipped_invalid=skipped_invalid,
        skipped_existing=skipped_existing,
        total_rows=total_rows,
        errors=errors,
    )


@admin_router.delete("/blacklist/{entry_id}", response_model=SimpleOk)
async def admin_blacklist_remove(entry_id: str, _p: dict = Depends(require_admin)):
    res = await db.blacklist.delete_one({"_id": entry_id})
    if res.deleted_count == 0:
        res = await db.blacklist.delete_one({"email": entry_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    return SimpleOk(ok=True, message="Removed from blacklist.")


# ----- Sessions / JWT rotation -----
@admin_router.get("/sessions", response_model=AdminSessionList)
async def admin_sessions(payload: dict = Depends(require_admin), limit: int = 100):
    cur_jti = payload.get("jti")
    limit = max(1, min(limit, 500))
    rows = (
        await db.admin_sessions.find({}).sort("created_at", -1).limit(limit).to_list(length=limit)
    )
    items = [
        AdminSessionItem(
            jti=r["_id"],
            created_at=r.get("created_at", ""),
            last_seen_at=r.get("last_seen_at"),
            expires_at=r.get("expires_at"),
            revoked=bool(r.get("revoked", False)),
            ip=r.get("ip"),
            user_agent=r.get("user_agent"),
            secret_version=r.get("secret_version"),
            is_current=(r["_id"] == cur_jti),
        )
        for r in rows
    ]
    total = await db.admin_sessions.count_documents({})
    return AdminSessionList(items=items, total=total)


@admin_router.delete("/sessions/{jti}", response_model=SimpleOk)
async def admin_revoke_session(jti: str, payload: dict = Depends(require_admin)):
    res = await db.admin_sessions.update_one(
        {"_id": jti}, {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return SimpleOk(ok=True, message="Session revoked.")


@admin_router.post("/sessions/revoke-others", response_model=SimpleOk)
async def admin_revoke_others(payload: dict = Depends(require_admin)):
    cur_jti = payload.get("jti")
    res = await db.admin_sessions.update_many(
        {"_id": {"$ne": cur_jti}, "revoked": {"$ne": True}},
        {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}},
    )
    return SimpleOk(ok=True, message=f"Revoked {res.modified_count} session(s).")


@admin_router.post("/rotate-secret", response_model=RotateSecretResponse)
async def admin_rotate_secret(payload: dict = Depends(require_admin)):
    info = await _rotate_jwt_secret()
    # Revoke ALL sessions (including current). The caller will be logged out.
    res = await db.admin_sessions.update_many(
        {"revoked": {"$ne": True}},
        {
            "$set": {
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "revoked_reason": "jwt_secret_rotated",
            }
        },
    )
    return RotateSecretResponse(
        ok=True,
        rotated_at=info["rotated_at"],
        revoked_sessions=res.modified_count,
        message="Secret rotated. All sessions revoked. Please re-login.",
    )


# ---------------------------------------------------------------------
# Mount routers + middleware
# ---------------------------------------------------------------------
app.include_router(api_router)
app.include_router(public_router)
app.include_router(webhook_router)
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup():
    await _ensure_jwt_secrets()
    # indexes
    try:
        await db.whitelist.create_index("email", unique=True)
        await db.blacklist.create_index("email", unique=True)
        await db.chat_logs.create_index("created_at")
        await db.admin_sessions.create_index("created_at")
    except Exception:
        logging.exception("Index creation warning (ignored)")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
