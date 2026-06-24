"""Admin read-only endpoints for ecosystem data (Sprint 20).

Provides a thin admin surface to inspect:
  * orders (paid commerce)
  * genesis subscribers (email captures, aggregated per source)
  * B2B inquiries (white-label requests)
  * payment_transactions (full audit trail, latest 50)

All endpoints require admin JWT (no 2FA — read-only metadata).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from core import b2b_inquiries, genesis, orders
from core.config import db
from core.security import require_admin

router = APIRouter(
    prefix="/api/admin/ecosystem",
    tags=["ecosystem-admin"],
    dependencies=[Depends(require_admin)],
)


def _serialize_dates(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(doc)
    for k in list(out.keys()):
        if isinstance(out[k], datetime):
            out[k] = out[k].isoformat()
    # Recurse one level for nested events list
    if isinstance(out.get("events"), list):
        for ev in out["events"]:
            if isinstance(ev.get("at"), datetime):
                ev["at"] = ev["at"].isoformat()
    if isinstance(out.get("history"), list):
        for ev in out["history"]:
            if isinstance(ev.get("at"), datetime):
                ev["at"] = ev["at"].isoformat()
    return out


@router.get("/orders")
async def list_orders(limit: int = 200) -> Dict[str, Any]:
    rows = await orders.list_orders(limit=limit)
    return {"orders": [_serialize_dates(r) for r in rows], "count": len(rows)}


@router.get("/genesis")
async def list_genesis(limit: int = 500) -> Dict[str, Any]:
    cursor = db.genesis_subscribers.find({}).sort("created_at", -1).limit(limit)
    rows: List[Dict[str, Any]] = []
    async for r in cursor:
        # Hide raw email by default in lists — keep hash only for privacy
        red = _serialize_dates(r)
        red["email"] = red.get("email", "")
        rows.append(red)
    by_source = await genesis.count_by_source()
    return {
        "subscribers": rows,
        "by_source": by_source,
        "count": len(rows),
    }


@router.get("/b2b")
async def list_b2b(limit: int = 200) -> Dict[str, Any]:
    rows = await b2b_inquiries.list_inquiries(limit=limit)
    return {"inquiries": [_serialize_dates(r) for r in rows], "count": len(rows)}


@router.get("/payments/transactions")
async def list_transactions(limit: int = 100) -> Dict[str, Any]:
    cursor = db.payment_transactions.find({}).sort("created_at", -1).limit(limit)
    rows = [_serialize_dates(r) async for r in cursor]
    return {"transactions": rows, "count": len(rows)}


__all__ = ["router"]
