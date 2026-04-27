"""Approval queue + outbox pipeline for the Propaganda Engine.

Lifecycle of a queue item:

    propose()  →  proposed
                    │
                    ├─ admin approves → approved → (cron) sent | failed
                    ├─ admin rejects → rejected
                    └─ panic        → killed

    Auto-policy triggers skip the ``proposed→approved`` hop and land
    directly in ``approved`` (still subject to panic + rate limits).

The queue intentionally lives in Mongo (not memory) so:
  * a backend restart never loses pending dispatches,
  * audit replays are trivial,
  * the cron worker can pick up any approved item without IPC.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.propaganda.queue")

STATUSES = ("proposed", "approved", "sent", "failed", "rejected", "killed")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_idem(trigger_key: str, idem: str) -> str:
    raw = f"{trigger_key}|{idem}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


async def propose(
    *,
    trigger_key: str,
    template_id: Optional[str],
    rendered_content: str,
    platforms: List[str],
    payload: Dict[str, Any],
    policy: str,
    idempotency_key: Optional[str] = None,
    delay_seconds: int = 20,
    by_jti: Optional[str] = None,
    manual: bool = False,
) -> Dict[str, Any]:
    """Insert a new queue item. Auto-policy items are immediately approved.

    Idempotency: a same-day duplicate (same trigger_key + idempotency_key)
    is silently merged — the existing queue doc is returned untouched.
    Without this safety net Helius retries would flood the channel.
    """
    now = _now()
    idem_hash = _hash_idem(trigger_key, idempotency_key or now)
    if idempotency_key:
        existing = await db.propaganda_queue.find_one({"idem_hash": idem_hash})
        if existing and existing.get("status") not in ("rejected", "killed", "failed"):
            return _normalize(existing)

    status = "approved" if policy == "auto" else "proposed"
    doc = {
        "_id": str(uuid.uuid4()),
        "trigger_key": trigger_key,
        "template_id": template_id,
        "rendered_content": rendered_content,
        "platforms": list(platforms),
        "payload": payload,
        "status": status,
        "idem_hash": idem_hash,
        "proposed_at": now,
        "approved_at": now if status == "approved" else None,
        "approved_by_jti": (by_jti if status == "approved" else None),
        "scheduled_for": _shift(now, delay_seconds) if status == "approved" else None,
        "sent_at": None,
        "manual": bool(manual),
        "results": {},
        "error": None,
    }
    await db.propaganda_queue.insert_one(doc)
    return _normalize(doc)


async def approve(item_id: str, *, by_jti: str, delay_seconds: int = 20) -> Optional[Dict[str, Any]]:
    now = _now()
    res = await db.propaganda_queue.find_one_and_update(
        {"_id": item_id, "status": "proposed"},
        {"$set": {
            "status": "approved",
            "approved_at": now,
            "approved_by_jti": by_jti,
            "scheduled_for": _shift(now, delay_seconds),
        }},
        return_document=True,
    )
    return _normalize(res) if res else None


async def reject(item_id: str, *, by_jti: str, reason: str = "") -> Optional[Dict[str, Any]]:
    res = await db.propaganda_queue.find_one_and_update(
        {"_id": item_id, "status": "proposed"},
        {"$set": {
            "status": "rejected",
            "rejected_at": _now(),
            "rejected_by_jti": by_jti,
            "reject_reason": (reason or "").strip()[:200],
        }},
        return_document=True,
    )
    return _normalize(res) if res else None


async def kill_all_pending() -> int:
    """Panic: mark every non-terminal item as ``killed``.
    Returns the number of items affected."""
    res = await db.propaganda_queue.update_many(
        {"status": {"$in": ["proposed", "approved"]}},
        {"$set": {"status": "killed", "killed_at": _now()}},
    )
    if res.modified_count:
        logger.warning("[propaganda] panic: killed %d queue item(s)", res.modified_count)
    return res.modified_count


async def list_queue(
    *,
    statuses: Optional[List[str]] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if statuses:
        q["status"] = {"$in": list(statuses)}
    cursor = db.propaganda_queue.find(q).sort("proposed_at", -1).limit(min(max(limit, 1), 500))
    return [_normalize(d) async for d in cursor]


async def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    doc = await db.propaganda_queue.find_one({"_id": item_id})
    return _normalize(doc) if doc else None


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _shift(iso: str, seconds: int) -> str:
    base = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    from datetime import timedelta

    return (base + timedelta(seconds=max(0, seconds))).isoformat()


def _normalize(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": doc["_id"],
        "trigger_key": doc.get("trigger_key"),
        "template_id": doc.get("template_id"),
        "rendered_content": doc.get("rendered_content"),
        "platforms": list(doc.get("platforms") or []),
        "payload": doc.get("payload") or {},
        "status": doc.get("status"),
        "manual": bool(doc.get("manual", False)),
        "proposed_at": doc.get("proposed_at"),
        "approved_at": doc.get("approved_at"),
        "scheduled_for": doc.get("scheduled_for"),
        "sent_at": doc.get("sent_at"),
        "error": doc.get("error"),
        "approved_by_jti": doc.get("approved_by_jti"),
        "rejected_at": doc.get("rejected_at"),
        "reject_reason": doc.get("reject_reason"),
        "results": doc.get("results") or {},
    }
