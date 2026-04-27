"""DB-backed message templates for the Propaganda Engine.

Schema (collection ``propaganda_templates``):
    _id            uuid
    trigger_key    str               # one of KNOWN_TRIGGERS
    language       "en" | "fr"
    content        str               # supports {placeholder} interpolation
    enabled        bool
    weight         float             # picker bias (0.1 → 5.0)
    mentions_vault bool              # marks this template as a vault-traffic line
    version        int               # bumped on every update
    created_at     iso
    updated_at     iso

The ``pick()`` helper applies enabled-only filtering, weighted random
choice and (when ``mentions_vault_required=True``) restricts the pool
to vault-mentioning templates so the engine can guarantee ‘every 3rd
message drives traffic to the site’.
"""

from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.propaganda.templates")

ALLOWED_LANGS = ("en", "fr")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def list_templates(
    trigger_key: Optional[str] = None,
    language: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if trigger_key:
        q["trigger_key"] = trigger_key
    if language:
        q["language"] = language
    cursor = db.propaganda_templates.find(q).sort("created_at", 1)
    return [_normalize(d) async for d in cursor]


async def get_template(template_id: str) -> Optional[Dict[str, Any]]:
    doc = await db.propaganda_templates.find_one({"_id": template_id})
    return _normalize(doc) if doc else None


async def create_template(
    *,
    trigger_key: str,
    language: str,
    content: str,
    weight: float = 1.0,
    mentions_vault: bool = False,
    enabled: bool = True,
) -> Dict[str, Any]:
    if language not in ALLOWED_LANGS:
        raise ValueError(f"language must be one of {ALLOWED_LANGS}")
    content = (content or "").strip()
    if not content:
        raise ValueError("content cannot be empty")
    if len(content) > 1000:
        raise ValueError("content too long (max 1000 chars)")
    doc = {
        "_id": str(uuid.uuid4()),
        "trigger_key": trigger_key,
        "language": language,
        "content": content,
        "weight": float(max(0.1, min(weight, 5.0))),
        "mentions_vault": bool(mentions_vault),
        "enabled": bool(enabled),
        "version": 1,
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.propaganda_templates.insert_one(doc)
    return _normalize(doc)


async def update_template(
    template_id: str, **patch: Any,
) -> Optional[Dict[str, Any]]:
    if "language" in patch and patch["language"] not in ALLOWED_LANGS:
        raise ValueError(f"language must be one of {ALLOWED_LANGS}")
    if "content" in patch:
        c = (patch["content"] or "").strip()
        if not c:
            raise ValueError("content cannot be empty")
        if len(c) > 1000:
            raise ValueError("content too long (max 1000 chars)")
        patch["content"] = c
    if "weight" in patch:
        patch["weight"] = float(max(0.1, min(float(patch["weight"]), 5.0)))
    patch["updated_at"] = _now()
    res = await db.propaganda_templates.find_one_and_update(
        {"_id": template_id},
        {"$set": patch, "$inc": {"version": 1}},
        return_document=True,
    )
    return _normalize(res) if res else None


async def delete_template(template_id: str) -> int:
    res = await db.propaganda_templates.delete_one({"_id": template_id})
    return res.deleted_count


async def pick(
    *,
    trigger_key: str,
    language: str = "en",
    mentions_vault_required: bool = False,
) -> Optional[Dict[str, Any]]:
    """Weighted random pick. Falls back to EN if FR pool is empty for the
    given language. Returns ``None`` if the trigger has no live templates
    at all (caller is expected to log + skip the dispatch)."""
    q: Dict[str, Any] = {"trigger_key": trigger_key, "enabled": True}
    if mentions_vault_required:
        q["mentions_vault"] = True
    candidates = [d async for d in db.propaganda_templates.find({**q, "language": language})]
    if not candidates and language != "en":
        candidates = [d async for d in db.propaganda_templates.find({**q, "language": "en"})]
    if not candidates:
        return None
    weights = [max(0.1, float(d.get("weight", 1.0))) for d in candidates]
    return _normalize(random.choices(candidates, weights=weights, k=1)[0])


def _normalize(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    return {
        "id": doc["_id"],
        "trigger_key": doc["trigger_key"],
        "language": doc["language"],
        "content": doc["content"],
        "weight": float(doc.get("weight", 1.0)),
        "mentions_vault": bool(doc.get("mentions_vault", False)),
        "enabled": bool(doc.get("enabled", True)),
        "version": int(doc.get("version", 1)),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# -------------------------------------------------------------------
# Initial seed — runs at startup (idempotent).
# -------------------------------------------------------------------
DEFAULT_TEMPLATES: List[Dict[str, Any]] = [
    # T-Zero (Trigger 1)
    {"trigger_key": "mint", "language": "en",
     "content": "The signal is live. The Deep State has chosen its candidate. $DEEPOTUS is now on the bonding curve. Don't say I didn't warn you. {buy_link}"},
    {"trigger_key": "mint", "language": "en",
     "content": "Deployment confirmed. PROTOCOL ΔΣ initiated. The Vault is waiting for your SOL. {buy_link}"},
    {"trigger_key": "mint", "language": "en",
     "content": "They told me to wait. I didn't. $DEEPOTUS is live. {buy_link}"},
    # MC milestones (Trigger 3)
    {"trigger_key": "mc_milestone", "language": "en",
     "content": "{mc_label} MC: One dial turns. The Vault chimes. You're starting to see the pattern, aren't you?",
     "mentions_vault": True},
    {"trigger_key": "mc_milestone", "language": "en",
     "content": "{mc_label} MC: Halfway to the Raydium Ascension. The elites are starting to notice the noise. Keep pushing."},
    {"trigger_key": "mc_milestone", "language": "en",
     "content": "{mc_label} reached. Six figures or zero — the prophecy doesn't allow middle ground."},
    # Jeet dip (Trigger 2) — seeded for 13.2 readiness
    {"trigger_key": "jeet_dip", "language": "en",
     "content": "Look at them scramble for pennies. The weak hands are being purged. The Deep State loves a discount."},
    {"trigger_key": "jeet_dip", "language": "en",
     "content": "Predictable. The small-time speculators are exiting. Good — more room in the bunker for the real believers."},
    {"trigger_key": "jeet_dip", "language": "en",
     "content": "A dip? No. This is a redistribution of power. Buy the fear, or stay poor in the old world."},
    # Whale (Trigger 4)
    {"trigger_key": "whale_buy", "language": "en",
     "content": "A silent player just moved a mountain. Someone with a high clearance level just entered the chat. Watch the chart. ({whale_amount} SOL)"},
    {"trigger_key": "whale_buy", "language": "en",
     "content": "{whale_amount} SOL in one go. That's not a retail buyer. That's an insider. Follow the smart money."},
    # Raydium (Trigger 5)
    {"trigger_key": "raydium_migration", "language": "en",
     "content": "The Bonding Curve has collapsed. We have ascended to Raydium. The old world is dead. Long live $DEEPOTUS. {raydium_link}"},
    {"trigger_key": "raydium_migration", "language": "en",
     "content": "PROTOCOL ΔΣ is evolving. Raydium migration complete. The LP is being locked. The Vault is permanent now. {raydium_link}",
     "mentions_vault": True},
]


async def seed_default_templates() -> int:
    """Idempotent — only inserts templates whose exact content+trigger pair
    is missing. Safe to run on every startup."""
    inserted = 0
    for t in DEFAULT_TEMPLATES:
        existing = await db.propaganda_templates.find_one({
            "trigger_key": t["trigger_key"],
            "language": t.get("language", "en"),
            "content": t["content"],
        })
        if existing:
            continue
        await create_template(
            trigger_key=t["trigger_key"],
            language=t.get("language", "en"),
            content=t["content"],
            mentions_vault=bool(t.get("mentions_vault", False)),
        )
        inserted += 1
    if inserted:
        logger.info("[propaganda] Seeded %d default templates.", inserted)
    return inserted
