"""
$DEEPOTUS Backend — Landing + Admin API + Public Stats + Email

Public:
  - POST /api/chat
  - GET  /api/prophecy
  - POST /api/whitelist     (triggers async welcome email)
  - GET  /api/stats         (basic counters)
  - GET  /api/public/stats  (public read-only dashboard: counters + timeseries, no PII)

Admin (JWT required):
  - POST   /api/admin/login  (rate-limited 5/10min/IP, returns JWT)
  - GET    /api/admin/whitelist?limit=&skip=
  - DELETE /api/admin/whitelist/{id}
  - POST   /api/admin/whitelist/{id}/blacklist
  - GET    /api/admin/chat-logs?limit=&skip=
  - GET    /api/admin/evolution?days=N
  - GET    /api/admin/blacklist
  - POST   /api/admin/blacklist            (manual add)
  - DELETE /api/admin/blacklist/{id}       (unblock)
"""

from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends, Request, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import secrets
import time
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal, Dict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

import jwt
import resend

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
# Emergent LLM + Resend
# ---------------------------------------------------------------------
from emergentintegrations.llm.chat import LlmChat, UserMessage

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "deepotus2026")
JWT_SECRET = os.environ.get("JWT_SECRET", "deepotus-jwt-secret-change-me")
JWT_ALGO = "HS256"
JWT_TTL_HOURS = 24

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
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


# ---------------------------------------------------------------------
# Rate limiter (per-IP sliding window)
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
    ip = _client_ip(request)
    _login_attempts.pop(ip, None)


# ---------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------
def issue_admin_jwt() -> tuple[str, datetime]:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)
    payload = {
        "sub": "deepotus-admin",
        "role": "admin",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(exp.timestamp()),
        "jti": secrets.token_urlsafe(12),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO), exp


def verify_admin_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])


def require_admin(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
) -> bool:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(None, 1)[1].strip()
    elif x_admin_token:
        token = x_admin_token.strip()

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        verify_admin_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


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


class WhitelistItem(BaseModel):
    id: str
    email: str
    lang: str
    position: int
    created_at: str
    email_sent: bool = False
    email_sent_at: Optional[str] = None


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


class PublicStatsResponse(BaseModel):
    whitelist_count: int
    chat_messages: int
    prophecies_served: int
    launch_timestamp: str
    generated_at: str
    series_days: int
    series: List[EvolutionPoint]


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
    """Send the bilingual welcome email and update Mongo status."""
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

    # Fire-and-forget email (non-blocking)
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
# Evolution helpers (shared by admin + public)
# ---------------------------------------------------------------------
async def _compute_evolution(days: int) -> List[EvolutionPoint]:
    days = max(1, min(days, 365))
    today_utc = datetime.now(timezone.utc).date()
    start_utc = today_utc - timedelta(days=days - 1)

    wl_rows = await db.whitelist.find(
        {}, {"created_at": 1, "_id": 0}
    ).to_list(length=100000)
    ch_rows = await db.chat_logs.find(
        {}, {"created_at": 1, "_id": 0}
    ).to_list(length=500000)

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


# ---------------------------------------------------------------------
# Public stats route
# ---------------------------------------------------------------------
@public_router.get("/stats", response_model=PublicStatsResponse)
async def public_stats(days: int = 30):
    days = max(1, min(days, 90))  # cap at 90 for public
    wl = await db.whitelist.count_documents({})
    chat_ct = await db.chat_logs.count_documents({})
    prophecies = 0
    c = await db.counters.find_one({"_id": "prophecies"})
    if c:
        prophecies = int(c.get("count", 0))
    series = await _compute_evolution(days)
    return PublicStatsResponse(
        whitelist_count=wl,
        chat_messages=chat_ct,
        prophecies_served=prophecies,
        launch_timestamp=await get_launch_timestamp(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        series_days=days,
        series=series,
    )


# ---------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------
@admin_router.post("/login", response_model=AdminLoginResponse)
async def admin_login(req: AdminLoginRequest, request: Request):
    _rate_limit_check(request)
    if not req.password or not secrets.compare_digest(req.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid password")
    _rate_limit_reset(request)
    token, exp = issue_admin_jwt()
    return AdminLoginResponse(token=token, expires_at=exp.isoformat())


def _item_from_whitelist_row(r) -> WhitelistItem:
    return WhitelistItem(
        id=r["_id"],
        email=r["email"],
        lang=r.get("lang", "fr"),
        position=int(r.get("position", 0)),
        created_at=r.get("created_at", ""),
        email_sent=bool(r.get("email_sent", False)),
        email_sent_at=r.get("email_sent_at"),
    )


@admin_router.get("/whitelist", response_model=PaginatedWhitelist)
async def admin_whitelist(
    _auth: bool = Depends(require_admin),
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    cursor = (
        db.whitelist.find({}).sort("position", 1).skip(skip).limit(limit)
    )
    rows = await cursor.to_list(length=limit)
    total = await db.whitelist.count_documents({})
    return PaginatedWhitelist(
        items=[_item_from_whitelist_row(r) for r in rows],
        total=total,
        limit=limit,
        skip=skip,
    )


@admin_router.delete("/whitelist/{entry_id}", response_model=SimpleOk)
async def admin_whitelist_delete(entry_id: str, _auth: bool = Depends(require_admin)):
    res = await db.whitelist.delete_one({"_id": entry_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return SimpleOk(ok=True, message="Deleted.")


@admin_router.post("/whitelist/{entry_id}/blacklist", response_model=SimpleOk)
async def admin_whitelist_blacklist(
    entry_id: str, _auth: bool = Depends(require_admin)
):
    entry = await db.whitelist.find_one({"_id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    email_lc = entry["email"].lower().strip()
    await db.blacklist.update_one(
        {"email": email_lc},
        {
            "$set": {
                "_id": entry_id,  # keep stable id if possible
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
    _auth: bool = Depends(require_admin),
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    cursor = (
        db.chat_logs.find({}).sort("created_at", -1).skip(skip).limit(limit)
    )
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
async def admin_evolution(
    _auth: bool = Depends(require_admin), days: int = 30
):
    series = await _compute_evolution(days)
    return EvolutionResponse(days=len(series), series=series)


# ----- Blacklist CRUD -----
@admin_router.get("/blacklist", response_model=BlacklistList)
async def admin_blacklist_list(
    _auth: bool = Depends(require_admin),
    limit: int = 200,
    skip: int = 0,
):
    limit = max(1, min(limit, 1000))
    skip = max(0, skip)
    cursor = (
        db.blacklist.find({}).sort("blacklisted_at", -1).skip(skip).limit(limit)
    )
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
    req: BlacklistAddRequest, _auth: bool = Depends(require_admin)
):
    email_lc = req.email.lower().strip()
    # Remove from whitelist if present
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


@admin_router.delete("/blacklist/{entry_id}", response_model=SimpleOk)
async def admin_blacklist_remove(
    entry_id: str, _auth: bool = Depends(require_admin)
):
    # Try by _id first, fallback to email field (legacy)
    res = await db.blacklist.delete_one({"_id": entry_id})
    if res.deleted_count == 0:
        res = await db.blacklist.delete_one({"email": entry_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    return SimpleOk(ok=True, message="Removed from blacklist.")


# ---------------------------------------------------------------------
# Mount routers + middleware
# ---------------------------------------------------------------------
app.include_router(api_router)
app.include_router(public_router)
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


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
