"""Public routes: root, chat, prophecy, whitelist, stats (basic).

These endpoints are unauthenticated. They drive the landing page, the
Prophet chat and the countdown/KPI strip.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage
from fastapi import APIRouter, BackgroundTasks, HTTPException

from core.config import (
    LAUNCH_ISO,
    LLM_MODEL,
    LLM_PROVIDER,
    db,
    get_system_prompt,
)
from core.secret_provider import get_emergent_llm_key
from core.email_service import send_welcome_email
from core.models import (
    ChatRequest,
    ChatResponse,
    ProphecyResponse,
    StatsResponse,
    WhitelistRequest,
    WhitelistResponse,
)

router = APIRouter(prefix="/api", tags=["public"])


# ---------------------------------------------------------------------
# Launch timestamp
# ---------------------------------------------------------------------
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
# Seeded prophecies (offline fallback)
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@router.get("/")
async def root():
    return {"name": "DEEPOTUS API", "status": "online", "prophet": "awake"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    api_key = await get_emergent_llm_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="LLM key not configured")

    session_id = req.session_id or f"chat-{uuid.uuid4().hex[:12]}"
    system_prompt = get_system_prompt(req.lang)

    try:
        chat_client = LlmChat(
            api_key=api_key,
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


@router.get("/prophecy", response_model=ProphecyResponse)
async def prophecy(lang: str = "fr", live: bool = True):
    lang = "fr" if lang not in ("fr", "en") else lang

    api_key = await get_emergent_llm_key() if live else None
    if not live or not api_key:
        pool = SEEDED_PROPHECIES_FR if lang == "fr" else SEEDED_PROPHECIES_EN
        return ProphecyResponse(
            prophecy=secrets.choice(pool),
            lang=lang,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    try:
        sys_p = get_system_prompt(lang)
        chat_client = LlmChat(
            api_key=api_key,
            session_id=f"prophecy-{uuid.uuid4().hex[:10]}",
            system_message=sys_p,
        ).with_model(LLM_PROVIDER, LLM_MODEL)

        if lang == "fr":
            q = (
                "Donne-moi UNE seule prophétie mémétique courte (1-2 phrases max) "
                "sur l'effondrement à venir. Pas d'intro, juste la prophétie."
            )
        else:
            q = (
                "Give me ONE short memetic prophecy (1-2 sentences max) about "
                "the coming collapse. No intro, just the prophecy."
            )

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
        pool = SEEDED_PROPHECIES_FR if lang == "fr" else SEEDED_PROPHECIES_EN
        return ProphecyResponse(
            prophecy=secrets.choice(pool),
            lang=lang,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


@router.post("/whitelist", response_model=WhitelistResponse)
async def whitelist(
    req: WhitelistRequest, background_tasks: BackgroundTasks
):
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


@router.get("/stats", response_model=StatsResponse)
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
