"""Sprint 19+ admin endpoints for the Giveaway Extraction pipeline.

Routes (all admin-protected):

  * ``POST /api/admin/giveaway/preview``
      Dry-run an extraction. Persists a ``kind=preview`` snapshot so
      the operator can review eligibility + holdings before commiting.
      Idempotent (multiple previews per draw_date are allowed).

  * ``POST /api/admin/giveaway/extract``
      Persist a ``kind=extraction`` snapshot. Enforces uniqueness
      against ``draw_date_iso`` (only one active extraction per date).
      The DB rejects duplicates via the partial unique index.

  * ``GET  /api/admin/giveaway/snapshots``
      List recent snapshots (newest first). Optional ?kind= filter.

  * ``GET  /api/admin/giveaway/snapshots/{id}``
      Full snapshot detail (winners + per-candidate audit).

  * ``POST /api/admin/giveaway/snapshots/{id}/announce``
      Fire the ``giveaway_extraction`` Propaganda trigger so the
      announcement lands in the X + Telegram approval queue.

  * ``POST /api/admin/giveaway/snapshots/{id}/cancel``
      Soft-delete (frees the unique-index slot for a re-extraction
      on the same draw_date).

  * ``GET  /api/admin/giveaway/eligible``
      Quick eligibility readout without persisting a snapshot —
      useful for the admin UI's "live candidates" panel.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from core import giveaway, propaganda_engine
from core.config import db
from core.security import require_admin
from core.wallet_registry import get_mint_address

router = APIRouter(prefix="/api/admin/giveaway", tags=["giveaway-admin"])


# =====================================================================
# Schemas
# =====================================================================
class ExtractRequest(BaseModel):
    """Body for both /preview and /extract.

    Defaults mirror ``core.giveaway`` constants and the public
    /giveaway page so the operator can post an empty body and it
    'just works' for the May 20 draw.
    """

    model_config = ConfigDict(extra="ignore")

    draw_date_iso: str = Field(..., min_length=10, max_length=64)
    pool_sol: float = Field(5.0, gt=0)
    winners_count: int = Field(giveaway.DEFAULT_WINNERS_COUNT, ge=1, le=20)
    min_holding_usd: float = Field(giveaway.DEFAULT_MIN_HOLDING_USD, ge=0)
    min_level: int = Field(0, ge=0, le=3)
    # Optional override: when the operator wants to run the draw
    # against a specific mint different from the one stored in
    # wallet_registry (e.g. testnet, or a fork). Falls back to the
    # registry value when omitted.
    token_mint_override: Optional[str] = Field(None, max_length=64)
    # ``{x_handle: wallet_address}`` overrides for participants who
    # haven't linked a wallet via the Terminal but have provided one
    # off-band. Keys are normalised (strip "@") downstream.
    manual_wallets: Optional[Dict[str, str]] = None


class AnnounceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    language: Optional[str] = Field(None, pattern="^(en|fr)$")


# =====================================================================
# Helpers
# =====================================================================
def _admin_jti(admin: Any) -> Optional[str]:
    try:
        if isinstance(admin, dict):
            return admin.get("jti") or admin.get("sub")
        return getattr(admin, "jti", None) or getattr(admin, "sub", None)
    except Exception:  # noqa: BLE001
        return None


async def _resolve_token_mint(override: Optional[str]) -> Optional[str]:
    """Token mint resolution rules:
       1. Explicit override from the request body (advanced use).
       2. wallet_registry's authoritative value.
       3. None → triggers PRE-MINT mode downstream.
    """
    if override and override.strip():
        return override.strip()
    try:
        return (await get_mint_address()) or None
    except Exception:  # noqa: BLE001
        return None


# =====================================================================
# Endpoints
# =====================================================================
@router.post("/preview")
async def preview_extraction(
    payload: ExtractRequest,
    admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    """Dry-run — does NOT block a future real extraction."""
    mint = await _resolve_token_mint(payload.token_mint_override)
    result = await giveaway.run_extraction(
        draw_date_iso=payload.draw_date_iso,
        token_mint=mint,
        pool_sol=payload.pool_sol,
        winners_count=payload.winners_count,
        min_holding_usd=payload.min_holding_usd,
        manual_wallets=payload.manual_wallets,
        dry_run=True,
        min_level=payload.min_level,
        created_by=_admin_jti(admin),
    )
    return {"ok": True, "snapshot": result}


@router.post("/extract")
async def real_extraction(
    payload: ExtractRequest,
    admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    """Real extraction — locks the draw_date via the partial unique
    index. If another active extraction exists for the same date, a
    structured ``duplicate_active_extraction`` error surfaces in the
    snapshot's ``errors`` array and the snapshot is NOT persisted."""
    mint = await _resolve_token_mint(payload.token_mint_override)
    result = await giveaway.run_extraction(
        draw_date_iso=payload.draw_date_iso,
        token_mint=mint,
        pool_sol=payload.pool_sol,
        winners_count=payload.winners_count,
        min_holding_usd=payload.min_holding_usd,
        manual_wallets=payload.manual_wallets,
        dry_run=False,
        min_level=payload.min_level,
        created_by=_admin_jti(admin),
    )
    if "duplicate_active_extraction" in (result.get("errors") or []):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "duplicate_active_extraction",
                "draw_date_iso": payload.draw_date_iso,
                "hint": "Cancel the existing extraction before re-running.",
            },
        )
    return {"ok": True, "snapshot": result}


@router.get("/snapshots")
async def admin_list_snapshots(
    limit: int = Query(default=50, ge=1, le=200),
    kind: Optional[str] = Query(default=None, pattern="^(preview|extraction)$"),
    _admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    items = await giveaway.list_snapshots(limit=limit, kind=kind)
    return {"items": items, "count": len(items)}


@router.get("/snapshots/{snapshot_id}")
async def admin_get_snapshot(
    snapshot_id: str,
    _admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    snap = await giveaway.get_snapshot(snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    return {"ok": True, "snapshot": snap}


@router.post("/snapshots/{snapshot_id}/cancel")
async def admin_cancel_snapshot(
    snapshot_id: str,
    admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    snap, err = await giveaway.cancel_snapshot(snapshot_id, _admin_jti(admin))
    if err == "not_found":
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    if err == "already_cancelled":
        return {"ok": True, "snapshot": snap, "noop": True}
    return {"ok": True, "snapshot": snap}


@router.post("/snapshots/{snapshot_id}/announce")
async def admin_announce(
    snapshot_id: str,
    payload: AnnounceRequest,
    request: Request,
    admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    """Fire the giveaway_extraction propaganda trigger from a
    persisted snapshot. Refuses preview snapshots and cancelled rows."""
    snap = await giveaway.get_snapshot(snapshot_id)
    if not snap:
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    if snap.get("kind") != "extraction":
        raise HTTPException(
            status_code=400,
            detail={"error": "only_real_extractions_can_be_announced"},
        )
    if snap.get("cancelled_at"):
        raise HTTPException(
            status_code=400, detail={"error": "snapshot_cancelled"},
        )
    if not snap.get("winners"):
        raise HTTPException(
            status_code=400, detail={"error": "no_winners_to_announce"},
        )

    winners_formatted = giveaway.format_winners_for_template(snap["winners"])
    seed_fp = (snap.get("seed") or {}).get("fingerprint") or ""

    res = await propaganda_engine.fire(
        trigger_key="giveaway_extraction",
        manual=True,
        payload_override={
            "snapshot_id": snapshot_id,
            "winners_formatted": winners_formatted,
            "winners_count": len(snap["winners"]),
            "pool_sol": snap.get("pool_sol") or 0,
            "per_winner_sol": snap.get("per_winner_sol") or 0,
            "draw_date_iso": snap.get("draw_date_iso") or "",
            "seed_fingerprint": seed_fp,
        },
        locale_override=payload.language,
        jti=_admin_jti(admin),
        ip=(request.client.host if request and request.client else None),
    )
    queue_item_id: Optional[str] = None
    announce_error: Optional[str] = None
    if res and res.get("ok"):
        queue_item_id = (res.get("queue_item") or {}).get("id")
        if queue_item_id:
            await db[giveaway.COLLECTION].update_one(
                {"_id": snapshot_id},
                {"$set": {"announced_queue_item_id": queue_item_id}},
            )
    else:
        announce_error = (res or {}).get("reason") or "propaganda_fire_failed"

    return {
        "ok": bool(queue_item_id),
        "queue_item_id": queue_item_id,
        "announce_error": announce_error,
        "snapshot_id": snapshot_id,
    }


@router.get("/eligible")
async def admin_eligible(
    min_level: int = Query(default=0, ge=0, le=3),
    limit: int = Query(default=500, ge=1, le=2000),
    _admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    """Lightweight readout — eligibility query without on-chain calls.
    Surfaces who has an X handle, who has a wallet, etc. so the
    operator can decide whether to collect manual wallets first."""
    rows = await giveaway.list_eligible_candidates(min_level=min_level, limit=limit)
    with_wallet = sum(1 for r in rows if r.get("wallet_address"))
    return {
        "items": rows,
        "count": len(rows),
        "with_wallet": with_wallet,
        "without_wallet": len(rows) - with_wallet,
    }
