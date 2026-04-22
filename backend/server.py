"""
$DEEPOTUS Backend — Landing Page + Admin API

Routes (landing):
  - POST /api/chat        → Chat with AI Prophet (bilingual, persona preserved)
  - GET  /api/prophecy    → Generate single memetic prophecy
  - POST /api/whitelist   → Email capture for whitelist
  - GET  /api/stats       → Landing page stats

Routes (admin):
  - POST /api/admin/login       → Authenticate with ADMIN_PASSWORD, returns a token
  - GET  /api/admin/whitelist   → List whitelist entries (auth required)
  - GET  /api/admin/chat-logs   → List chat logs (auth required)
"""

from fastapi import FastAPI, APIRouter, HTTPException, Header, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import secrets
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta

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
# Admin token store (in-memory, expires 24h)
# ---------------------------------------------------------------------
# Tokens are simple opaque bearer strings kept in-process. For a multi-worker
# deployment, persist to Mongo. For now (single uvicorn worker) this is fine
# and avoids external dependencies.
_admin_tokens: dict[str, datetime] = {}
TOKEN_TTL = timedelta(hours=24)


def _cleanup_tokens():
    now = datetime.now(timezone.utc)
    expired = [t for t, exp in _admin_tokens.items() if exp < now]
    for t in expired:
        _admin_tokens.pop(t, None)


def require_admin(x_admin_token: Optional[str] = Header(default=None)):
    _cleanup_tokens()
    if not x_admin_token or x_admin_token not in _admin_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # refresh
    _admin_tokens[x_admin_token] = datetime.now(timezone.utc) + TOKEN_TTL
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
async def admin_login(req: AdminLoginRequest):
    if not req.password or not secrets.compare_digest(req.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid password")
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + TOKEN_TTL
    _admin_tokens[token] = expires
    return AdminLoginResponse(token=token, expires_at=expires.isoformat())


@admin_router.get("/whitelist", response_model=WhitelistList)
async def admin_whitelist(_auth: bool = Depends(require_admin), limit: int = 500):
    cursor = db.whitelist.find({}, {"_id": 1, "email": 1, "lang": 1, "position": 1, "created_at": 1}).sort("position", 1).limit(max(1, min(limit, 2000)))
    rows = await cursor.to_list(length=max(1, min(limit, 2000)))
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


@admin_router.get("/chat-logs", response_model=ChatLogList)
async def admin_chat_logs(_auth: bool = Depends(require_admin), limit: int = 300):
    cursor = db.chat_logs.find({}).sort("created_at", -1).limit(max(1, min(limit, 1000)))
    rows = await cursor.to_list(length=max(1, min(limit, 1000)))
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
