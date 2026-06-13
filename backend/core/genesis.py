"""Genesis list management (Sprint 20).

Captures emails from the ecosystem page (Roman card → 'Join Genesis list'
and Mobile game card → 'Be notified'). Single collection,
de-duplicated by (email, source).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.config import db, logger

VALID_SOURCES = {
    "genesis_roman",
    "genesis_mobile",
    "genesis_secret",  # explicit secret-project waitlist
    "genesis_generic",  # fallback (e.g. footer)
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


async def ensure_indexes() -> None:
    await db.genesis_subscribers.create_index(
        [("email_hash", 1), ("source", 1)], unique=True
    )
    await db.genesis_subscribers.create_index("created_at")
    logger.info("[genesis] subscribers indexes ready")


async def subscribe(
    *, email: str, source: str, locale: str = "fr", ip_hash: Optional[str] = None
) -> Dict[str, Any]:
    """Upsert a subscription. Returns the persisted doc (without raw email
    once stored, the email hash is the unique key).
    """
    email = email.strip().lower()
    if source not in VALID_SOURCES:
        source = "genesis_generic"
    eh = _hash_email(email)
    now = _now_utc()
    doc = {
        "_id": str(uuid.uuid4()),
        "email": email,
        "email_hash": eh,
        "source": source,
        "locale": locale,
        "ip_hash": ip_hash,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.genesis_subscribers.insert_one(doc)
        logger.info("[genesis] new subscriber source=%s", source)
        return doc
    except Exception:
        # duplicate — update timestamp only
        existing = await db.genesis_subscribers.find_one_and_update(
            {"email_hash": eh, "source": source},
            {"$set": {"updated_at": now, "locale": locale}},
            return_document=True,
        )
        return existing or doc


async def count_by_source() -> Dict[str, int]:
    """Aggregate count per source. Used by admin dashboard."""
    pipeline = [
        {"$group": {"_id": "$source", "n": {"$sum": 1}}},
        {"$project": {"_id": 0, "source": "$_id", "n": 1}},
    ]
    out: Dict[str, int] = {}
    async for row in db.genesis_subscribers.aggregate(pipeline):
        out[row["source"]] = int(row["n"])
    return out


__all__ = [
    "ensure_indexes",
    "subscribe",
    "count_by_source",
    "VALID_SOURCES",
]
