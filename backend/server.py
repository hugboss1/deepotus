"""
$DEEPOTUS Backend — Landing + Admin API

Admin security:
  - Password login is rate-limited per IP (5 attempts / 10 minutes)
  - Sessions are issued as HS256 JWT (24h expiration)

Public routes:
  - POST /api/chat
  - GET  /api/prophecy
  - POST /api/whitelist
  - GET  /api/stats

Admin routes (all require `Authorization: Bearer <jwt>` or legacy `X-Admin-Token`):
  - POST   /api/admin/login
  - GET    /api/admin/whitelist
  - DELETE /api/admin/whitelist/{id}        (remove)
  - POST   /api/admin/whitelist/{id}/blacklist (remove + blacklist the email)
  - GET    /api/admin/chat-logs
  - GET    /api/admin/evolution?days=30
"""

from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import secrets
import time
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal, Dict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

import jwt  # PyJWT (already in requirements)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------------------------------------------------
# Mongo
# ---------------------------------------------------------------------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# ---------------------------------------------------------------------
# Emergent LLM
# ---------------------------------------------------------------------
from emergentintegrations.llm.chat import LlmChat, UserMessage

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "deepotus2026")
JWT_SECRET = os.environ.get("JWT_SECRET", "deepotus-jwt-secret-change-me")
JWT_ALGO = "HS256"
JWT_TTL_HOURS = 24

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


# ---------------------------------------------------------------------
# Rate limiter (in-memory, per-IP sliding window)
# ---------------------------------------------------------------------
RATE_LIMIT_WINDOW = 600  # 10 min
RATE_LIMIT_MAX = 5  # attempts
_login_attempts: Dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Respect common proxy headers in containerized / k8s setups
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
    # Drop old entries
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
    """Clear attempts for this IP on successful login."""
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
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token, exp


def verify_admin_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])


def require_admin(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
) -> bool:
    # Prefer Authorization: Bearer <jwt>
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


class WhitelistList(BaseModel):
    items: List[WhitelistItem]
    total: int


class ChatLogItem(BaseModel):
    id: str
    session_id: str
    lang: str
    user_message: str
    reply: str
    created_at: str


class ChatLogList(BaseModel):
    items: List[ChatLogItem]
    total: int


class SimpleOk(BaseModel):
    ok: bool
    message: str = ""


class EvolutionPoint(BaseModel):
    date: str  # YYYY-MM-DD
    whitelist: int  # cumulative
    chat: int  # cumulative
    whitelist_daily: int  # new that day
    chat_daily: int  # new that day


class EvolutionResponse(BaseModel):
    days: int
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
async def whitelist(req: WhitelistRequest):
    email_lc = req.email.lower().strip()

    # Blacklist check
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
        )

    count = await db.whitelist.count_documents({})
    doc = {
        "_id": str(uuid.uuid4()),
        "email": email_lc,
        "lang": req.lang or "fr",
        "position": count + 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.whitelist.insert_one(doc)
    return WhitelistResponse(
        id=doc["_id"],
        email=doc["email"],
        position=doc["position"],
        created_at=doc["created_at"],
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


@admin_router.get("/whitelist", response_model=WhitelistList)
async def admin_whitelist(_auth: bool = Depends(require_admin), limit: int = 500):
    capped = max(1, min(limit, 2000))
    cursor = (
        db.whitelist.find(
            {},
            {"_id": 1, "email": 1, "lang": 1, "position": 1, "created_at": 1},
        )
        .sort("position", 1)
        .limit(capped)
    )
    rows = await cursor.to_list(length=capped)
    items = [
        WhitelistItem(
            id=r["_id"],
            email=r["email"],
            lang=r.get("lang", "fr"),
            position=int(r.get("position", 0)),
            created_at=r.get("created_at", ""),
        )
        for r in rows
    ]
    total = await db.whitelist.count_documents({})
    return WhitelistList(items=items, total=total)


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
                "email": email_lc,
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
                "source_entry_id": entry_id,
            }
        },
        upsert=True,
    )
    await db.whitelist.delete_one({"_id": entry_id})
    return SimpleOk(ok=True, message="Email blacklisted and removed.")


@admin_router.get("/chat-logs", response_model=ChatLogList)
async def admin_chat_logs(_auth: bool = Depends(require_admin), limit: int = 300):
    capped = max(1, min(limit, 1000))
    cursor = db.chat_logs.find({}).sort("created_at", -1).limit(capped)
    rows = await cursor.to_list(length=capped)
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
    return ChatLogList(items=items, total=total)


@admin_router.get("/evolution", response_model=EvolutionResponse)
async def admin_evolution(
    _auth: bool = Depends(require_admin), days: int = 30
):
    days = max(1, min(days, 365))
    today_utc = datetime.now(timezone.utc).date()
    start_utc = today_utc - timedelta(days=days - 1)

    # Fetch all relevant docs, group locally (simple & robust across Mongo versions)
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
            key = d.isoformat()
            wl_daily[key] = wl_daily.get(key, 0) + 1

    ch_daily: Dict[str, int] = {}
    for r in ch_rows:
        d = parse_day(r.get("created_at", ""))
        if d:
            key = d.isoformat()
            ch_daily[key] = ch_daily.get(key, 0) + 1

    # Cumulative before start
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

    return EvolutionResponse(days=days, series=series)


# Mount routers
app.include_router(api_router)
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
