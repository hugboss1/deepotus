"""Order lifecycle (Sprint 20 — Ecosystem & Payment).

The ``orders`` collection records every fulfilled purchase. It is
decoupled from ``payment_transactions`` (which records EVERY session
attempt, paid or not). A new row is created **once** when the Stripe
webhook confirms ``checkout.session.completed`` with
``payment_status == 'paid'``, and never mutated afterwards — making
audit trivially correct.

Schema (UUID id, timezone.utc datetimes per CRITICAL rules):

    {
      _id: str (uuid4),
      type: 'boardgame' | 'videogen',
      stripe_session_id: str (unique sparse),
      amount_eur: float,
      currency: 'eur',
      founder_number: Optional[int],       # boardgame only
      founder_tier: Optional[str],         # boardgame only
      license_key: Optional[str],          # videogen only
      download_token: Optional[str],       # videogen only (temporary)
      download_expires_at: Optional[dt],
      customer: { email, name, locale, address? },
      status: 'pending' | 'fulfilled' | 'shipped' | 'cancelled' | 'refunded',
      events: [ { at, kind, note } ],
      created_at: dt,
      updated_at: dt,
    }
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.config import db, logger


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def create_order(
    *,
    order_type: str,
    stripe_session_id: str,
    amount_eur: float,
    currency: str,
    customer: Dict[str, Any],
    metadata: Dict[str, str],
    license_key: Optional[str] = None,
    download_token: Optional[str] = None,
    download_expires_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create a new order row. Idempotent on ``stripe_session_id``
    (returns the existing row if already present).
    """
    existing = await db.orders.find_one({"stripe_session_id": stripe_session_id})
    if existing:
        return existing

    now = _now_utc()
    founder_number_raw = metadata.get("founder_number")
    founder_number = int(founder_number_raw) if founder_number_raw and founder_number_raw.isdigit() else None
    doc: Dict[str, Any] = {
        "_id": str(uuid.uuid4()),
        "type": order_type,
        "stripe_session_id": stripe_session_id,
        "amount_eur": float(amount_eur),
        "currency": currency,
        "founder_number": founder_number,
        "founder_tier": metadata.get("founder_tier"),
        "license_key": license_key,
        "download_token": download_token,
        "download_expires_at": download_expires_at,
        "customer": customer,
        "metadata": metadata,
        "status": "fulfilled" if order_type == "videogen" else "pending",
        "events": [{"at": now, "kind": "created", "note": "webhook checkout.session.completed"}],
        "created_at": now,
        "updated_at": now,
    }
    await db.orders.insert_one(doc)
    logger.info(
        "[orders] created %s order %s for %s session=%s",
        order_type, doc["_id"], (customer or {}).get("email", "-"),
        stripe_session_id[:14] + "…" if stripe_session_id else "-",
    )
    return doc


async def get_order_by_session(stripe_session_id: str) -> Optional[Dict[str, Any]]:
    return await db.orders.find_one({"stripe_session_id": stripe_session_id})


async def list_orders(limit: int = 200) -> list[Dict[str, Any]]:
    cursor = db.orders.find({}).sort("created_at", -1).limit(limit)
    return [o async for o in cursor]


async def append_event(order_id: str, kind: str, note: str = "") -> None:
    await db.orders.update_one(
        {"_id": order_id},
        {
            "$push": {"events": {"at": _now_utc(), "kind": kind, "note": note}},
            "$set": {"updated_at": _now_utc()},
        },
    )


__all__ = [
    "create_order",
    "get_order_by_session",
    "list_orders",
    "append_event",
]
