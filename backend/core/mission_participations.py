"""Mission participations storage (Sprint 21).

Opt-in form intake from ``/missions``: visitors give us their email +
optional wallet address to be notified about a specific mission. Every
submission is persisted, de-duplicated by (mission_id, email), and the
admin Command Center can list / re-trigger emails.

The Helius-driven auto-trigger (post-mint detection of $DEEP holders)
shares the same ``record_participation`` helper but with
``source='helius_webhook'`` so admin can filter the two streams.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import db, logger

VALID_SOURCES = {"form", "helius_webhook", "admin_manual"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


async def ensure_indexes() -> None:
    await db.mission_participations.create_index(
        [("mission_id", 1), ("email_hash", 1)], unique=True
    )
    await db.mission_participations.create_index("created_at")
    await db.mission_participations.create_index("email_sent")
    await db.mission_participations.create_index("source")
    logger.info("[mission_participations] indexes ready")


async def record_participation(
    *,
    mission_id: str,
    email: str,
    wallet_address: Optional[str] = None,
    locale: str = "fr",
    source: str = "form",
    ip_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """Idempotent insert (upsert) keyed by (mission_id, email_hash).

    Returns the persisted doc (with ``email_sent=False`` initially).
    """
    if source not in VALID_SOURCES:
        source = "form"
    eh = _email_hash(email)
    now = _now_utc()
    doc = {
        "_id": str(uuid.uuid4()),
        "mission_id": mission_id,
        "email": email.strip().lower(),
        "email_hash": eh,
        "wallet_address": (wallet_address or "").strip() or None,
        "locale": locale if locale in ("fr", "en") else "fr",
        "source": source,
        "ip_hash": ip_hash,
        "email_sent": False,
        "email_sent_at": None,
        "email_message_id": None,
        "email_last_error": None,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await db.mission_participations.insert_one(doc)
        logger.info(
            "[mission_participations] new mission=%s source=%s",
            mission_id, source,
        )
        return doc
    except Exception:  # duplicate or transient — update timestamp
        existing = await db.mission_participations.find_one_and_update(
            {"mission_id": mission_id, "email_hash": eh},
            {
                "$set": {
                    "updated_at": now,
                    "wallet_address": doc["wallet_address"],
                    "locale": doc["locale"],
                }
            },
            return_document=True,
        )
        return existing or doc


async def mark_email_sent(
    participation_id: str,
    *,
    message_id: Optional[str] = None,
) -> None:
    await db.mission_participations.update_one(
        {"_id": participation_id},
        {
            "$set": {
                "email_sent": True,
                "email_sent_at": _now_utc(),
                "email_message_id": message_id,
                "email_last_error": None,
                "updated_at": _now_utc(),
            }
        },
    )


async def mark_email_failed(participation_id: str, *, error: str) -> None:
    await db.mission_participations.update_one(
        {"_id": participation_id},
        {
            "$set": {
                "email_last_error": error[:300],
                "updated_at": _now_utc(),
            }
        },
    )


async def list_participations(
    *, mission_id: Optional[str] = None, limit: int = 200
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if mission_id:
        q["mission_id"] = mission_id
    cursor = db.mission_participations.find(q).sort("created_at", -1).limit(limit)
    return [d async for d in cursor]


async def count_by_mission() -> Dict[str, int]:
    pipeline = [
        {"$group": {"_id": "$mission_id", "n": {"$sum": 1}}},
    ]
    out: Dict[str, int] = {}
    async for row in db.mission_participations.aggregate(pipeline):
        out[row["_id"]] = int(row["n"])
    return out


__all__ = [
    "VALID_SOURCES",
    "ensure_indexes",
    "record_participation",
    "mark_email_sent",
    "mark_email_failed",
    "list_participations",
    "count_by_mission",
]
