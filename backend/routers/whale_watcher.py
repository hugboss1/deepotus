"""REST surface for the Whale Watcher (Sprint 15.2 — Brain Connect).

Two tiers:

  1. **Public endpoints** (mounted under ``/api/whale-watcher/*``) — consumed
     by the landing-page "Cabinet detected" Lore feed:

        GET  /recent              latest N alerts (anonymized projection)

  2. **Admin endpoints** (under ``/api/admin/whale-watcher/*``) — consumed
     by the admin dashboard:

        GET   /alerts              list (filter by status/tier)
        GET   /stats               24h aggregates by tier + queue counters
        POST  /simulate            inject a fake whale alert (admin-only)

The simulate endpoint is the bread-and-butter of demo-mode validation —
it lets the operator confirm that the full pipeline (alert → analyzer →
propaganda queue → dispatcher) works end-to-end without waiting on
on-chain activity.

Auth posture (mirrors infiltration/propaganda admin routes):
  * Public ``GET /recent`` is open and returns a privacy-respectful
    projection (no full wallet, no tx signature, amount bucketed).
  * Admin endpoints require a valid admin JWT.
  * ``POST /simulate`` is admin-only — no 2FA required because the
    only side-effect is a propaganda queue item which itself needs
    ``approve`` (2FA-protected) before any real dispatch happens.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from core import whale_watcher
from core.security import require_admin

public_router = APIRouter(prefix="/api/whale-watcher", tags=["whale-watcher"])
admin_router = APIRouter(
    prefix="/api/admin/whale-watcher",
    tags=["whale-watcher-admin"],
)


# ---------------------------------------------------------------------
# Public — Lore feed projection
# ---------------------------------------------------------------------
@public_router.get("/recent")
async def public_recent(limit: int = Query(10, ge=1, le=50)) -> Dict[str, Any]:
    """Return the most recent whale alerts in a public-safe shape.

    Drops the full wallet, tx signature, and any internal status field.
    Amount is bucketed to prevent the feed from doubling as a precise
    whale-tracking tool.
    """
    items = await whale_watcher.public_recent(limit=limit)
    return {"items": items}


# ---------------------------------------------------------------------
# Admin — operator-grade audit + simulate
# ---------------------------------------------------------------------
@admin_router.get("/alerts")
async def admin_list_alerts(
    status: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    """Full audit feed.

    Supports filters:
      * status: detected | analyzing | propaganda_proposed | notified
                | skipped | error
      * tier:   T1 | T2 | T3
    """
    items = await whale_watcher.list_alerts(
        status=status, tier=tier, limit=limit
    )
    return {"items": items, "count": len(items)}


@admin_router.get("/stats")
async def admin_stats(_admin=Depends(require_admin)) -> Dict[str, Any]:
    """Dashboard widget: 24h aggregates by tier + queue counters."""
    return await whale_watcher.stats_snapshot()


class SimulatePayload(BaseModel):
    amount_sol: float = Field(..., ge=0.01, le=10000.0)
    buyer: str = Field(default="SimulatedBuyerWallet1111111111111111111111", min_length=4, max_length=64)
    tx_signature: Optional[str] = Field(default=None, max_length=128)
    mint: Optional[str] = Field(default=None, max_length=64)


@admin_router.post("/simulate")
async def admin_simulate(
    payload: SimulatePayload,
    request: Request,
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    """Insert a synthetic whale alert.

    Useful for end-to-end testing in demo mode — the APScheduler tick
    will pick it up within 5 seconds and propose a propaganda queue
    item exactly as if the swap had been observed on-chain.
    """
    # Generate a unique synthetic tx_signature when none was provided
    # so two consecutive simulates don't collide on the unique index.
    import uuid as _uuid

    tx_sig = payload.tx_signature or f"sim-{_uuid.uuid4().hex[:24]}"
    inserted = await whale_watcher.enqueue_alert(
        buyer=payload.buyer,
        amount_sol=float(payload.amount_sol),
        tx_signature=tx_sig,
        mint=payload.mint,
        source="admin_simulate",
    )
    if inserted.get("duplicate"):
        # Stable response shape: 200 with a flag rather than 409 so the
        # admin UI can render a "already queued" toast without error noise.
        return {
            "ok": True,
            "duplicate": True,
            "alert": _public_admin_view(inserted),
        }
    return {"ok": True, "duplicate": False, "alert": _public_admin_view(inserted)}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _public_admin_view(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip Mongo internals / large fields before returning to the UI."""
    if not doc:
        return {}
    return {
        "id": doc.get("_id"),
        "buyer": doc.get("buyer"),
        "buyer_short": doc.get("buyer_short"),
        "amount_sol": doc.get("amount_sol"),
        "tier": doc.get("tier"),
        "status": doc.get("status"),
        "tx_signature": doc.get("tx_signature"),
        "source": doc.get("source"),
        "ts": doc.get("ts"),
        "propaganda_queue_id": doc.get("propaganda_queue_id"),
        "skip_reason": doc.get("skip_reason"),
        "error": doc.get("error"),
    }
