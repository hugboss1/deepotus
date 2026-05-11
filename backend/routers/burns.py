"""Burn disclosure endpoints (Sprint 17.6 — Operation Incinerator).

Surfaces:

  * ``POST /api/admin/burns/disclose``
      Record a new burn against ``burn_logs`` and, when the admin opts
      in via ``announce=true``, fire the ``burn_event`` Propaganda
      trigger so the disclosure lands in the X + Telegram approval
      queue. Idempotent on ``tx_signature``.

  * ``GET  /api/admin/burns``
      Admin list (includes redacted rows by default for audit trail).

  * ``POST /api/admin/burns/{burn_id}/redact``
      Soft-delete: the row stays in Mongo (audit) but is excluded from
      ``total_burned`` + public listing.

  * ``GET  /api/transparency/stats``
      Public "Proof of Scarcity" snapshot used by the /transparency
      hero on the landing site. Exposes initial supply, total burned,
      locked allocations (Treasury 300M + Team 150M = 450M = 45%),
      and the **effective circulating supply** that the UI must
      display (= initial - burned - locked_total). Mathematical
      honesty for Cabinet investors.

  * ``GET  /api/transparency/burns``
      Public burn feed (most-recent first, cap 50). Used to render
      "Last 5 burns" with Solscan links on /transparency.

Auth:
  * Admin endpoints require the admin JWT (no extra 2FA here; the
    optional propaganda announcement goes through the existing
    approval queue which itself enforces 2FA on dispatch).
  * Public endpoints are fully open and read-only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from core import burn_logs, propaganda_engine
from core.config import db
from core.security import require_admin

public_router = APIRouter(prefix="/api", tags=["burns-public"])
admin_router = APIRouter(prefix="/api/admin/burns", tags=["burns-admin"])


# =====================================================================
# Schemas
# =====================================================================
class DiscloseBurnPayload(BaseModel):
    """Body for ``POST /api/admin/burns/disclose``.

    ``amount`` accepts any numeric-looking input (the underlying
    ``burn_logs.normalise_amount`` coerces strings/floats and rejects
    non-positive / oversize values).
    """

    model_config = ConfigDict(extra="ignore")

    amount: float = Field(..., gt=0)
    tx_signature: str = Field(..., min_length=32, max_length=128)
    burned_at: Optional[str] = Field(default=None, max_length=64)
    note: Optional[str] = Field(default=None, max_length=200)
    language: Optional[str] = Field(default=None, pattern="^(en|fr)$")
    announce: bool = Field(
        default=False,
        description=(
            "When true, also fire the burn_event Propaganda trigger so "
            "the disclosure is queued for X + Telegram. Independent of "
            "the DB write — a failed announce does NOT roll back the "
            "burn record."
        ),
    )


# =====================================================================
# Helpers
# =====================================================================
def _admin_jti(admin: Any) -> Optional[str]:
    """Best-effort extraction of the admin JTI for audit-trail
    correlation. ``require_admin`` returns a dict or a Pydantic model
    depending on version — both shapes are handled."""
    try:
        if isinstance(admin, dict):
            return admin.get("jti") or admin.get("sub")
        return getattr(admin, "jti", None) or getattr(admin, "sub", None)
    except Exception:  # noqa: BLE001
        return None


# =====================================================================
# Admin endpoints
# =====================================================================
@admin_router.post("/disclose")
async def disclose_burn(
    payload: DiscloseBurnPayload,
    request: Request,
    admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    """Record a burn and, optionally, announce it.

    The burn record is the source of truth — it powers the public
    ``/transparency`` Proof of Scarcity header. The Propaganda
    announcement is a *side-effect* that the admin can skip (e.g. when
    backfilling historical burns we don't want to spam the timeline
    with stale news).

    Returns the persisted burn doc, plus the queue item id when
    ``announce=true`` succeeded. Surfaces a structured 409 when the
    same tx_signature was already disclosed (idempotency contract).
    """
    jti = _admin_jti(admin)

    burn, err = await burn_logs.record_burn(
        amount=payload.amount,
        tx_signature=payload.tx_signature,
        burned_at=payload.burned_at,
        note=payload.note,
        source="manual",
        created_by=jti,
    )

    if err == "duplicate_tx_signature":
        # Surface the existing doc so the UI can show a friendly toast
        # ("Already disclosed — view in feed") without a 500.
        raise HTTPException(
            status_code=409,
            detail={
                "error": "duplicate_tx_signature",
                "burn": burn,
            },
        )
    if err or not burn:
        raise HTTPException(
            status_code=400,
            detail={"error": err or "burn_record_failed"},
        )

    queue_item_id: Optional[str] = None
    announce_error: Optional[str] = None
    if payload.announce:
        try:
            res = await propaganda_engine.fire(
                trigger_key="burn_event",
                manual=True,
                payload_override={
                    "burn_amount": burn["amount"],
                    "tx_signature": burn["tx_signature"],
                    "tx_link": burn["tx_link"],
                    "burned_at": burn["burned_at"],
                    "burn_note": burn.get("note") or "",
                },
                locale_override=payload.language,
                jti=jti,
                ip=(request.client.host if request and request.client else None),
            )
            if res and res.get("ok"):
                queue_item_id = (res.get("queue_item") or {}).get("id")
                if queue_item_id:
                    # Persist the queue id back into the burn row so
                    # /transparency + admin lists can deep-link to the
                    # announcement.
                    await db[burn_logs.COLLECTION].update_one(
                        {"_id": burn["id"]},
                        {"$set": {"queue_item_id": queue_item_id}},
                    )
                    burn["queue_item_id"] = queue_item_id
            else:
                announce_error = (res or {}).get("reason") or "propaganda_fire_failed"
        except Exception as exc:  # noqa: BLE001
            announce_error = f"propaganda_exception: {exc}"

    return {
        "ok": True,
        "burn": burn,
        "announced": bool(queue_item_id),
        "queue_item_id": queue_item_id,
        "announce_error": announce_error,
    }


@admin_router.get("")
async def admin_list_burns(
    limit: int = Query(default=100, ge=1, le=500),
    include_redacted: bool = Query(default=True),
    _admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin burn list — defaults to **including** redacted rows so the
    operator can audit soft-deletes."""
    items: List[Dict[str, Any]] = await burn_logs.list_burns(
        limit=limit, include_redacted=include_redacted,
    )
    snap = await burn_logs.stats()
    return {"items": items, "count": len(items), "stats": snap}


@admin_router.post("/{burn_id}/redact")
async def admin_redact_burn(
    burn_id: str,
    admin: Any = Depends(require_admin),
) -> Dict[str, Any]:
    """Soft-delete a burn (excluded from totals + public list, kept in
    Mongo for audit). Used when the admin discloses the wrong tx by
    mistake."""
    doc, err = await burn_logs.redact_burn(
        burn_id=burn_id, redacted_by=_admin_jti(admin),
    )
    if err == "not_found":
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    if err == "already_redacted":
        # Idempotent: 200 + the unchanged doc so a double-click is
        # ergonomic instead of confusing.
        return {"ok": True, "burn": doc, "noop": True}
    if err or not doc:
        raise HTTPException(
            status_code=400, detail={"error": err or "redact_failed"},
        )
    return {"ok": True, "burn": doc}


# =====================================================================
# Public endpoints
# =====================================================================
@public_router.get("/transparency/stats")
async def transparency_stats() -> Dict[str, Any]:
    """Public Proof of Scarcity snapshot.

    Shape (stable contract — the landing site depends on it):

        {
          "initial_supply":         1_000_000_000,
          "total_burned":           int,
          "circulating_supply":     int,   # raw = initial - burned
          "treasury_locked":        300_000_000,
          "team_locked":            150_000_000,
          "locked_total":           450_000_000,
          "locked_percent":         45.0,
          "effective_circulating":  int,   # = initial - burned - locked_total
          "burn_count":             int,
          "burned_percent":         float,
          "latest_burn":            { ... } | null
        }

    The UI must surface ``effective_circulating`` (not
    ``circulating_supply``) as the headline metric, per the Cabinet
    Investor Honesty Pact.
    """
    return await burn_logs.stats()


@public_router.get("/transparency/burns")
async def transparency_burns(
    limit: int = Query(default=10, ge=1, le=50),
) -> Dict[str, Any]:
    """Public burn feed (most-recent first, redacted rows excluded)."""
    items = await burn_logs.list_burns(limit=limit, include_redacted=False)
    # Strip operator-only fields before serving publicly.
    public_items = [
        {
            "id": it["id"],
            "amount": it["amount"],
            "tx_signature": it["tx_signature"],
            "tx_link": it["tx_link"],
            "burned_at": it["burned_at"],
            "note": it.get("note"),
            "queue_item_id": it.get("queue_item_id"),
        }
        for it in items
    ]
    return {"items": public_items, "count": len(public_items)}
