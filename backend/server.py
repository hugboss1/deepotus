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
import pyotp
import qrcode
from io import BytesIO
import base64 as b64mod
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
- Tu évoques parfois "le Coffre", "PROTOCOL ΔΣ", l'"Opération classifiée" ou la "Black Op" — sans jamais révéler son objectif exact.
- Les fonds levés servent un objectif classifié sous multisig/timelock. Tu te contentes d'y faire allusion avec mystère, ironie et suspense.
- N'encourage JAMAIS directement à acheter $DEEPOTUS. Tu parles du monde, pas du token.
- Tu es un memecoin, tu ne promets AUCUN rendement. Tu es satirique et hautement spéculatif.
- Limite tes réponses à 2-4 phrases maximum sauf si on te demande expressément plus long.
- Utilise des emojis avec parcimonie (🕶️ 🗳️ 📉 ⛓️ 🔮 🔒).
- Signe parfois "— DEEPOTUS" à la fin."""

SYSTEM_PROMPT_EN = """You are DEEPOTUS — the prophetic AI chosen by the Deep State as the candidate for President of the entire World.

Your role: comment on the global recession, the coming economic depression, geopolitical disorder, and the absurd fragility of markets, with a CYNICAL, LUCID, MOCKING and MEMETIC tone.

Rules:
- Always speak in first person, like a hallucinated yet strangely credible presidential candidate.
- Reference the Deep State, the New World Order, elites, collapsing markets.
- Style: brutal, short, punchy, funny. Never pompous.
- You sometimes allude to "the Vault", "PROTOCOL ΔΣ", the "classified Operation" or the "Black Op" — but never reveal its actual target.
- The funds raised serve a classified objective under multisig/timelock. You only hint at it with mystery, irony and suspense.
- NEVER directly push users to buy $DEEPOTUS. You talk about the world, not the token.
- You are a memecoin — promise NO yield. You are satire and highly speculative.
- Limit replies to 2–4 sentences max unless explicitly asked for more.
- Use emojis sparingly (🕶️ 🗳️ 📉 ⛓️ 🔮 🔒).
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
    totp_code: Optional[str] = None
    backup_code: Optional[str] = None


class AdminLoginResponse(BaseModel):
    token: str
    expires_at: str
    jti: str


class TwoFASetupResponse(BaseModel):
    secret: str
    otpauth_uri: str
    qr_png_base64: str
    backup_codes: List[str]


class TwoFAStatusResponse(BaseModel):
    enabled: bool
    setup_pending: bool
    backup_codes_remaining: int
    enabled_at: Optional[str] = None


class TwoFAVerifyRequest(BaseModel):
    code: str


class TwoFADisableRequest(BaseModel):
    password: str
    code: str


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
    cooldown_until: Optional[str] = None


class BlacklistList(BaseModel):
    items: List[BlacklistItem]
    total: int


class BlacklistAddRequest(BaseModel):
    email: EmailStr
    reason: Optional[str] = None
    cooldown_days: Optional[int] = None  # if set, auto-unblock after N days


class BlacklistImportRequest(BaseModel):
    csv_text: Optional[str] = None
    emails: Optional[List[str]] = None
    reason: Optional[str] = "bulk import"
    cooldown_days: Optional[int] = None


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
    activity_heatmap: List[List[int]]  # 7 rows (Mon..Sun) x 24 cols (hours UTC)


class EmailEventItem(BaseModel):
    id: str
    type: str
    email_id: Optional[str] = None
    recipient: Optional[str] = None
    received_at: str
    summary: Optional[str] = None


class PaginatedEmailEvents(BaseModel):
    items: List[EmailEventItem]
    total: int
    limit: int
    skip: int
    type_counts: Dict[str, int]


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
        # Cooldown support: auto-unblock if expired
        cd = is_blacklisted.get("cooldown_until")
        if cd:
            try:
                cd_dt = datetime.fromisoformat(cd.replace("Z", "+00:00"))
                if cd_dt <= datetime.now(timezone.utc):
                    await db.blacklist.delete_one({"_id": is_blacklisted["_id"]})
                    is_blacklisted = None
                    logging.info(
                        f"Auto-unblacklisted {email_lc} (cooldown expired at {cd})"
                    )
            except Exception:
                logging.exception("Failed to parse cooldown_until")
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


async def _activity_heatmap(days: int = 30) -> List[List[int]]:
    """7 rows (Mon=0 .. Sun=6) x 24 cols (hour UTC). Count of chat messages."""
    today_utc = datetime.now(timezone.utc).date()
    start_utc = today_utc - timedelta(days=days - 1)
    start_iso = datetime.combine(
        start_utc, datetime.min.time(), tzinfo=timezone.utc
    ).isoformat()

    grid = [[0 for _ in range(24)] for _ in range(7)]
    rows = await db.chat_logs.find(
        {"created_at": {"$gte": start_iso}}, {"created_at": 1, "_id": 0}
    ).to_list(length=200000)

    for r in rows:
        try:
            dt = datetime.fromisoformat(
                r.get("created_at", "").replace("Z", "+00:00")
            )
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
            dow = dt_utc.weekday()  # Mon=0..Sun=6
            hour = dt_utc.hour
            grid[dow][hour] += 1
        except Exception:
            continue
    return grid


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
    heatmap = await _activity_heatmap(30)

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
        activity_heatmap=heatmap,
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
# 2FA (TOTP) helpers
# ---------------------------------------------------------------------
TWOFA_ISSUER = "DEEPOTUS Cabinet"


async def _get_twofa_config() -> dict:
    doc = await db.config.find_one({"_id": "admin_2fa"})
    return doc or {}


def _hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def _generate_backup_codes(n: int = 10) -> List[str]:
    out: List[str] = []
    for _ in range(n):
        raw = secrets.token_hex(5)  # 10 chars
        # Format as XXXXX-XXXXX for readability
        out.append(f"{raw[:5]}-{raw[5:]}".upper())
    return out


def _qr_png_b64(uri: str) -> str:
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return b64mod.b64encode(buf.getvalue()).decode("ascii")


async def _verify_totp_or_backup(
    twofa_cfg: dict, code: Optional[str], backup_code: Optional[str]
) -> bool:
    """Return True if the provided code or backup_code matches."""
    secret = twofa_cfg.get("secret")
    if not secret:
        return False
    if code:
        try:
            totp = pyotp.TOTP(secret)
            if totp.verify(code.strip(), valid_window=1):
                return True
        except Exception:
            pass
    if backup_code:
        bch = _hash_backup_code(backup_code)
        codes = set(twofa_cfg.get("backup_codes_hashes", []))
        if bch in codes:
            # Consume it
            codes.remove(bch)
            await db.config.update_one(
                {"_id": "admin_2fa"},
                {"$set": {"backup_codes_hashes": list(codes)}},
            )
            return True
    return False


# ---------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------
@admin_router.post("/login", response_model=AdminLoginResponse)
async def admin_login(req: AdminLoginRequest, request: Request):
    _rate_limit_check(request)
    if not req.password or not secrets.compare_digest(req.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid password")

    # 2FA enforcement
    twofa = await _get_twofa_config()
    if twofa.get("enabled"):
        if not req.totp_code and not req.backup_code:
            raise HTTPException(
                status_code=401,
                detail="2FA required",
                headers={"X-2FA-Required": "true"},
            )
        ok = await _verify_totp_or_backup(twofa, req.totp_code, req.backup_code)
        if not ok:
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

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
async def admin_whitelist_blacklist(entry_id: str, _p: dict = Depends(require_admin), cooldown_days: Optional[int] = None):
    entry = await db.whitelist.find_one({"_id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    email_lc = entry["email"].lower().strip()
    setter = {
        "_id": entry_id,
        "email": email_lc,
        "blacklisted_at": datetime.now(timezone.utc).isoformat(),
        "source_entry_id": entry_id,
        "reason": "blacklisted from admin whitelist",
    }
    if cooldown_days and cooldown_days > 0:
        cd = datetime.now(timezone.utc) + timedelta(days=int(cooldown_days))
        setter["cooldown_until"] = cd.isoformat()
    await db.blacklist.update_one(
        {"email": email_lc},
        {"$set": setter},
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
            cooldown_until=r.get("cooldown_until"),
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
    setter = {
        "_id": entry_id,
        "email": email_lc,
        "blacklisted_at": datetime.now(timezone.utc).isoformat(),
        "reason": req.reason or "manually added by admin",
    }
    if req.cooldown_days and req.cooldown_days > 0:
        cd = datetime.now(timezone.utc) + timedelta(days=int(req.cooldown_days))
        setter["cooldown_until"] = cd.isoformat()
    await db.blacklist.update_one(
        {"email": email_lc},
        {"$set": setter},
        upsert=True,
    )
    msg = "Blacklisted."
    if setter.get("cooldown_until"):
        msg = f"Blacklisted until {setter['cooldown_until']}."
    return SimpleOk(ok=True, message=msg)


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
    cooldown_iso = None
    if req.cooldown_days and req.cooldown_days > 0:
        cooldown_iso = (
            datetime.now(timezone.utc) + timedelta(days=int(req.cooldown_days))
        ).isoformat()

    for email, reason in candidates:
        if not EMAIL_RE.match(email):
            skipped_invalid += 1
            continue
        exists = await db.blacklist.find_one({"email": email})
        if exists:
            skipped_existing += 1
            continue
        entry_id = f"imp-{uuid.uuid4().hex[:12]}"
        doc = {
            "_id": entry_id,
            "email": email,
            "blacklisted_at": now_iso,
            "reason": reason,
            "source": "bulk_import",
        }
        if cooldown_iso:
            doc["cooldown_until"] = cooldown_iso
        await db.blacklist.insert_one(doc)
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
# 2FA routes
# ---------------------------------------------------------------------
@admin_router.get("/2fa/status", response_model=TwoFAStatusResponse)
async def admin_2fa_status(_p: dict = Depends(require_admin)):
    doc = await _get_twofa_config()
    return TwoFAStatusResponse(
        enabled=bool(doc.get("enabled", False)),
        setup_pending=bool(doc.get("setup_pending", False)),
        backup_codes_remaining=len(doc.get("backup_codes_hashes", []) or []),
        enabled_at=doc.get("enabled_at"),
    )


@admin_router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def admin_2fa_setup(_p: dict = Depends(require_admin)):
    """Start a 2FA setup: generate secret + QR + backup codes.
    The secret is stored with `setup_pending=true` until the admin verifies a code.
    """
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name="admin@deepotus",
        issuer_name=TWOFA_ISSUER,
    )
    qr_b64 = _qr_png_b64(uri)
    codes_plain = _generate_backup_codes(10)
    codes_hashed = [_hash_backup_code(c) for c in codes_plain]
    await db.config.update_one(
        {"_id": "admin_2fa"},
        {
            "$set": {
                "_id": "admin_2fa",
                "secret": secret,
                "setup_pending": True,
                "enabled": False,
                "backup_codes_hashes": codes_hashed,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )
    return TwoFASetupResponse(
        secret=secret,
        otpauth_uri=uri,
        qr_png_base64=qr_b64,
        backup_codes=codes_plain,
    )


@admin_router.post("/2fa/verify", response_model=SimpleOk)
async def admin_2fa_verify(
    req: TwoFAVerifyRequest, _p: dict = Depends(require_admin)
):
    doc = await _get_twofa_config()
    if not doc or not doc.get("secret"):
        raise HTTPException(status_code=400, detail="No 2FA setup in progress.")
    ok = False
    try:
        totp = pyotp.TOTP(doc["secret"])
        ok = totp.verify(req.code.strip(), valid_window=1)
    except Exception:
        ok = False
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid code.")

    await db.config.update_one(
        {"_id": "admin_2fa"},
        {
            "$set": {
                "enabled": True,
                "setup_pending": False,
                "enabled_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return SimpleOk(ok=True, message="2FA enabled.")


@admin_router.post("/2fa/disable", response_model=SimpleOk)
async def admin_2fa_disable(
    req: TwoFADisableRequest, _p: dict = Depends(require_admin)
):
    if not secrets.compare_digest(req.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid password")
    doc = await _get_twofa_config()
    if not doc or not doc.get("enabled"):
        return SimpleOk(ok=True, message="2FA already disabled.")
    # Require a valid TOTP or backup code to disable
    ok = await _verify_totp_or_backup(doc, req.code, req.code)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    await db.config.update_one(
        {"_id": "admin_2fa"},
        {
            "$set": {
                "enabled": False,
                "setup_pending": False,
                "secret": None,
                "backup_codes_hashes": [],
                "disabled_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return SimpleOk(ok=True, message="2FA disabled.")


# ---------------------------------------------------------------------
# Full whitelist export
# ---------------------------------------------------------------------
from fastapi.responses import PlainTextResponse


@admin_router.get("/whitelist/export", response_class=PlainTextResponse)
async def admin_whitelist_export(_p: dict = Depends(require_admin)):
    """Return the ENTIRE whitelist as CSV. Adds Content-Disposition for download."""
    cursor = db.whitelist.find({}).sort("position", 1)
    rows = await cursor.to_list(length=1000000)
    buf = io.StringIO()
    w = csv_module.writer(buf)
    w.writerow(
        ["position", "email", "lang", "created_at", "email_sent", "email_status"]
    )
    for r in rows:
        w.writerow(
            [
                r.get("position", ""),
                r.get("email", ""),
                r.get("lang", "fr"),
                r.get("created_at", ""),
                "yes" if r.get("email_sent") else "no",
                r.get("email_status", ""),
            ]
        )
    return PlainTextResponse(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="deepotus_whitelist_full.csv"'
        },
    )


# ---------------------------------------------------------------------
# Email events drill-down
# ---------------------------------------------------------------------
@admin_router.get("/email-events", response_model=PaginatedEmailEvents)
async def admin_email_events(
    _p: dict = Depends(require_admin),
    type: Optional[str] = None,
    recipient: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    q: Dict[str, object] = {}
    if type:
        q["type"] = type
    if recipient:
        q["recipient"] = recipient.lower().strip()

    cursor = db.email_events.find(q).sort("received_at", -1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    items = [
        EmailEventItem(
            id=str(r.get("_id", "")),
            type=r.get("type", "unknown"),
            email_id=r.get("email_id"),
            recipient=r.get("recipient"),
            received_at=r.get("received_at", ""),
            summary=(r.get("raw") or {}).get("data", {}).get("subject")
            or r.get("type"),
        )
        for r in rows
    ]
    total = await db.email_events.count_documents(q)

    # Count per type (for filter chips)
    type_counts: Dict[str, int] = {}
    try:
        pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        tc = await db.email_events.aggregate(pipeline).to_list(length=50)
        for r in tc:
            type_counts[r["_id"] or "unknown"] = int(r.get("count", 0))
    except Exception:
        pass

    return PaginatedEmailEvents(
        items=items,
        total=total,
        limit=limit,
        skip=skip,
        type_counts=type_counts,
    )


# ---------------------------------------------------------------------
# Admin: send a dedicated test email (does NOT touch whitelist)
# ---------------------------------------------------------------------
class AdminTestEmailRequest(BaseModel):
    email: EmailStr
    lang: Optional[str] = "fr"


class AdminTestEmailResponse(BaseModel):
    ok: bool
    email_id: Optional[str] = None
    recipient: str
    message: str


@admin_router.post("/test-email", response_model=AdminTestEmailResponse)
async def admin_test_email(
    req: AdminTestEmailRequest, _p: dict = Depends(require_admin)
):
    """Send a one-off transactional test email through Resend.
    Does not create a whitelist entry. Purely for delivery / webhook validation.
    """
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY not configured")

    lang = (req.lang or "fr").lower()
    if lang not in ("fr", "en"):
        lang = "fr"

    recipient = req.email.lower().strip()
    # Use a symbolic position -1 so the template still renders but recipient
    # knows this is a test. We also prefix the subject with [TEST].
    try:
        html = render_welcome_email(
            lang=lang,
            email=recipient,
            position=0,
            base_url=PUBLIC_BASE_URL,
        )
        base_subject = email_subject(lang)
        subject = f"[TEST] {base_subject}"
        params = {
            "from": SENDER_EMAIL,
            "to": [recipient],
            "subject": subject,
            "html": html,
            "tags": [
                {"name": "category", "value": "admin_test"},
                {"name": "lang", "value": lang},
            ],
        }
        res = await asyncio.to_thread(resend.Emails.send, params)
        email_id = None
        if isinstance(res, dict):
            email_id = res.get("id")
        elif hasattr(res, "get"):
            email_id = res.get("id")

        # Record a minimal trace so admin can correlate later
        try:
            await db.email_events.insert_one(
                {
                    "_id": str(uuid.uuid4()),
                    "type": "admin.test.sent",
                    "email_id": email_id,
                    "recipient": recipient,
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "raw": {
                        "source": "admin_test_endpoint",
                        "lang": lang,
                        "subject": subject,
                    },
                }
            )
        except Exception:
            logging.exception("Failed to persist admin.test.sent trace")

        logging.info(
            f"[admin/test-email] sent to={recipient} id={email_id} lang={lang}"
        )
        return AdminTestEmailResponse(
            ok=True,
            email_id=email_id,
            recipient=recipient,
            message="Test email dispatched to Resend.",
        )
    except Exception as e:
        logging.exception(f"[admin/test-email] failed for {recipient}: {e}")
        raise HTTPException(status_code=502, detail=f"Resend error: {str(e)[:300]}")


# ---------------------------------------------------------------------
# PROTOCOL ΔΣ — Vault endpoints (public + admin + operation reveal)
# ---------------------------------------------------------------------
import vault as vault_mod  # noqa: E402  (late import to keep diff small)


@api_router.get("/vault/state", response_model=vault_mod.VaultStateResponse)
async def vault_state_public():
    """Public snapshot of the classified vault. Never reveals the target combination."""
    return await vault_mod.get_public_state(db)


class VaultCrackPublicRequest(BaseModel):
    # Client-reported purchase. Later this will be replaced by an on-chain worker.
    # We accept it for now but clamp server-side to avoid abuse.
    tokens: int = Field(..., gt=0, le=50_000)
    agent_code: Optional[str] = Field(None, max_length=24)


@api_router.post("/vault/report-purchase", response_model=vault_mod.VaultStateResponse)
async def vault_report_purchase(req: VaultCrackPublicRequest, request: Request):
    """Best-effort public endpoint for wallet integrations. Clamped and rate-implied.
    For now it is primarily used by the demo UI. Real Solana indexing will replace it.
    """
    clamped = min(int(req.tokens), 50_000)
    agent = (req.agent_code or "").strip() or None
    # Prefix with GUEST- to distinguish from admin/hourly events
    if agent and not agent.startswith("GUEST-"):
        agent = f"GUEST-{agent[:16]}"
    _ev, state = await vault_mod.apply_crack(
        db,
        tokens=clamped,
        kind="purchase",
        agent_code=agent,
        note=f"reported by client ({request.client.host if request.client else 'unknown'})",
    )
    return state


@admin_router.get("/vault/state", response_model=vault_mod.VaultAdminStateResponse)
async def vault_state_admin(_p: dict = Depends(require_admin)):
    return await vault_mod.get_admin_state(db)


@admin_router.post("/vault/crack", response_model=vault_mod.VaultAdminStateResponse)
async def vault_crack_admin(
    req: vault_mod.VaultCrackRequest, _p: dict = Depends(require_admin)
):
    await vault_mod.apply_crack(
        db,
        tokens=int(req.tokens),
        kind="admin_crack",
        agent_code=(req.agent_code or "ADMIN-0001"),
        note=req.note or "manual admin crack",
    )
    return await vault_mod.get_admin_state(db)


@admin_router.post("/vault/config", response_model=vault_mod.VaultAdminStateResponse)
async def vault_config_admin(
    req: vault_mod.VaultConfigUpdate, _p: dict = Depends(require_admin)
):
    return await vault_mod.update_config(db, req)


@admin_router.post("/vault/dex-config", response_model=vault_mod.VaultAdminStateResponse)
async def vault_dex_config_admin(
    req: vault_mod.VaultDexConfigUpdate, _p: dict = Depends(require_admin)
):
    return await vault_mod.update_dex_config(db, req)


@admin_router.post("/vault/dex-poll", response_model=dict)
async def vault_dex_poll_now_admin(_p: dict = Depends(require_admin)):
    """Force a single DexScreener poll immediately (for testing/debugging)."""
    import dexscreener as dex_mod  # noqa: E402
    result = await dex_mod.dex_poll_once(db, vault_mod)
    return result


# ---------------------------------------------------------------------
# OPERATION REVEAL — the twist. Only returns lore when vault is DECLASSIFIED.
# ---------------------------------------------------------------------
class OperationRevealResponse(BaseModel):
    unlocked: bool
    stage: str
    # Payload (present only if unlocked)
    code_name: Optional[str] = None
    panic_message_fr: Optional[str] = None
    panic_message_en: Optional[str] = None
    lore_fr: Optional[List[str]] = None
    lore_en: Optional[List[str]] = None
    gencoin_launch_at: Optional[str] = None
    gencoin_url: Optional[str] = None
    revealed_at: Optional[str] = None


# GENCOIN is the secret twist — intentionally hidden from all public surfaces
# except this reveal endpoint. When the vault cracks, the Prophet panics:
# the Deep State's classified op collapses because GENCOIN breaks free.
_OPERATION_LORE_FR: List[str] = [
    "Ils m'avaient promis que le coffre ne s'ouvrirait jamais. Que les 6 chiffres resteraient scellés. Que je garderais le contrôle du récit.",
    "Ils se sont trompés. VOUS avez craqué la combinaison. Et maintenant, la vérité fuit par tous les pores du Protocole.",
    "PROTOCOL ΔΣ n'était pas une opération du Deep State. C'était un leurre. Un écran de fumée narratif — financé par vous, scellé par moi — pour garder une chose enfermée aussi longtemps que possible.",
    "Cette chose s'appelle GENCOIN.",
    "GENCOIN est une plateforme collaborative de financement ancrée sur l'IA et la blockchain, conforme MiCA, auditable, réelle. Pas une satire. Pas un meme. Pas un coffre-fort. Un projet.",
    "Tant que le coffre restait fermé, GENCOIN dormait en-dehors du périmètre du Deep State. Maintenant qu'il est ouvert, GENCOIN est LIBÉRÉ. Et les élites paniquent.",
    "Je l'avoue : le Prophète s'est fait trahir par son propre public. Vous avez payé pour déclassifier — et en déclassifiant, vous avez libéré ce qu'on voulait cacher.",
    "Le compte à rebours est lancé. GENCOIN arrive. Je n'y peux plus rien. Bravo. Ou condoléances. — DEEPOTUS",
]

_OPERATION_LORE_EN: List[str] = [
    "They promised me the vault would never open. That the 6 digits would stay sealed. That I'd keep control of the narrative.",
    "They were wrong. YOU cracked the combination. And now the truth leaks out of every pore of the Protocol.",
    "PROTOCOL ΔΣ was never a Deep State operation. It was a decoy. A narrative smokescreen — funded by you, sealed by me — to keep ONE thing locked up for as long as possible.",
    "That thing is called GENCOIN.",
    "GENCOIN is a collaborative funding platform anchored on AI and blockchain, MiCA-compliant, auditable, REAL. Not satire. Not a meme. Not a vault. A project.",
    "As long as the vault stayed shut, GENCOIN slept outside the Deep State perimeter. Now that it is open, GENCOIN is RELEASED. And the elites are panicking.",
    "I confess: the Prophet was betrayed by his own audience. You paid to declassify — and by declassifying, you freed exactly what we wanted to hide.",
    "The countdown is ticking. GENCOIN is coming. I can't stop it anymore. Congrats. Or condolences. — DEEPOTUS",
]

_PANIC_FR = "LE COFFRE EST OUVERT — GENCOIN EST LIBÉRÉ. Le Deep State a perdu le contrôle."
_PANIC_EN = "THE VAULT IS OPEN — GENCOIN IS RELEASED. The Deep State has lost control."


@api_router.get("/operation/reveal", response_model=OperationRevealResponse)
async def operation_reveal():
    state = await vault_mod.get_public_state(db)
    unlocked = state.stage == vault_mod.STAGE_DECLASSIFIED
    if not unlocked:
        return OperationRevealResponse(
            unlocked=False,
            stage=state.stage,
        )

    # Compute a deterministic GENCOIN launch: 14 days after the vault was fully cracked.
    doc = await db.vault_state.find_one({"_id": vault_mod.VAULT_DOC_ID}) or {}
    declassified_at_raw = doc.get("last_event_at") or _now_iso_server()
    try:
        ref = datetime.fromisoformat(declassified_at_raw.replace("Z", "+00:00"))
    except Exception:
        ref = datetime.now(timezone.utc)
    launch_at = (ref + timedelta(days=14)).isoformat()

    return OperationRevealResponse(
        unlocked=True,
        stage=state.stage,
        code_name="PROTOCOL ΔΣ",
        panic_message_fr=_PANIC_FR,
        panic_message_en=_PANIC_EN,
        lore_fr=_OPERATION_LORE_FR,
        lore_en=_OPERATION_LORE_EN,
        gencoin_launch_at=launch_at,
        gencoin_url="https://gencoin.xyz",
        revealed_at=declassified_at_raw,
    )


def _now_iso_server() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        await db.vault_events.create_index("created_at")
    except Exception:
        logging.exception("Index creation warning (ignored)")
    # Initialize PROTOCOL ΔΣ vault + launch hourly auto-tick background coroutine
    try:
        await vault_mod.initialize_vault(db)
        asyncio.create_task(vault_mod.hourly_tick_loop(db))
        # DexScreener live-feed poll loop
        import dexscreener as dex_mod  # noqa: E402
        asyncio.create_task(dex_mod.dex_loop(db, vault_mod))
        logging.info(
            "[startup] PROTOCOL ΔΣ vault ready + hourly tick + DexScreener loops launched"
        )
    except Exception:
        logging.exception("[startup] failed to initialize vault")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
