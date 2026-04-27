"""REST surface for the Pre-Launch Infiltration Brain (Sprint 14.1).

Two tiers:

  1. **Public endpoints** (mounted under ``/api/infiltration/*``) — consumed
     by the landing-page Terminal:

        GET  /riddles                       list riddles (no keywords leaked)
        POST /riddles/{slug}/attempt        submit an answer + get verdict
        GET  /clearance/{email}             current level for an agent
        POST /clearance/link-wallet         bind a Solana wallet to the row
        GET  /sleeper-cell/status           public view of the pre-launch flag

  2. **Admin endpoints** (under ``/api/admin/infiltration/*``) — consumed by
     the admin dashboard:

        GET/POST/PATCH/DELETE /riddles      CRUD
        GET  /clearance                     ledger (filter ?level=N)
        GET  /clearance/stats               dashboard cards
        GET  /clearance/snapshot.csv        download Level-3 agents
        PATCH /clearance/{email}            operator override (level / wallet / notes)
        GET  /sleeper-cell                  full state
        PATCH /sleeper-cell                 toggle + messages + blocked triggers
        GET  /attempts                      recent riddle attempts (audit)

The admin mutation endpoints require 2FA (same posture as panic / cabinet
vault); the public endpoints are rate-limited at the riddle layer itself.
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field

from core import clearance_levels, riddles, sleeper_cell
from core.security import get_twofa_config, require_admin

public_router = APIRouter(prefix="/api/infiltration", tags=["infiltration"])
admin_router = APIRouter(prefix="/api/admin/infiltration", tags=["infiltration-admin"])


# ---------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------
def _client_ip(req: Request) -> Optional[str]:
    return req.client.host if req.client else None


async def require_2fa_for_admin(p: dict = Depends(require_admin)) -> dict:
    """Gatekeeper for admin mutations. Same posture as cabinet_vault /
    propaganda panic — protects operations that can move money or
    change who's eligible for the airdrop."""
    cfg = await get_twofa_config()
    if not (cfg and cfg.get("enabled")):
        raise HTTPException(
            status_code=403,
            detail={"code": "TWOFA_REQUIRED",
                    "message": "Enable 2FA before managing the Infiltration Brain."},
        )
    return p


# ---------------------------------------------------------------------
# Public models
# ---------------------------------------------------------------------
class AttemptRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=500)
    email: Optional[EmailStr] = None
    locale: Optional[str] = None


class LinkWalletRequest(BaseModel):
    email: EmailStr
    wallet_address: str = Field(..., min_length=32, max_length=44)


# ---------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------
@public_router.get("/riddles")
async def public_list_riddles(locale: str = "fr") -> Dict[str, Any]:
    items = await riddles.list_public_riddles(locale=locale)
    return {"items": items, "locale": locale}


@public_router.post("/riddles/{slug}/attempt")
async def public_submit_attempt(
    slug: str, body: AttemptRequest, request: Request,
) -> Dict[str, Any]:
    res = await riddles.submit_attempt(
        slug=slug,
        answer=body.answer,
        email=body.email,
        ip=_client_ip(request),
    )
    code = res.get("code")
    if code == "UNKNOWN_RIDDLE":
        raise HTTPException(status_code=404, detail=res)
    if code == "RIDDLE_DISABLED":
        raise HTTPException(status_code=410, detail=res)
    if code == "RATE_LIMITED":
        raise HTTPException(status_code=429, detail=res)
    return res


@public_router.get("/clearance/{email}")
async def public_clearance(email: str) -> Dict[str, Any]:
    row = await clearance_levels.get_status(email)
    if not row:
        return {
            "email": email.lower().strip(),
            "level": 0,
            "riddles_solved": [],
            "wallet_address": None,
        }
    # Strip the audit `events` array from the public projection.
    return {k: v for k, v in row.items() if k != "events"}


@public_router.post("/clearance/link-wallet")
async def public_link_wallet(body: LinkWalletRequest) -> Dict[str, Any]:
    try:
        return await clearance_levels.link_wallet(
            email=body.email, wallet_address=body.wallet_address,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@public_router.get("/sleeper-cell/status")
async def public_sleeper_status() -> Dict[str, Any]:
    """Minimal public projection — the landing-page hook calls this on
    every load, so we keep the payload compact and cacheable."""
    state = await sleeper_cell.get_state()
    return {
        "active": bool(state.get("active")),
        "message_fr": state.get("message_fr"),
        "message_en": state.get("message_en"),
    }


# ---------------------------------------------------------------------
# Admin models
# ---------------------------------------------------------------------
class RiddleCreateRequest(BaseModel):
    slug: str = Field(..., min_length=2, max_length=80)
    title: str = Field(..., min_length=2, max_length=120)
    question_fr: str = Field(..., min_length=10, max_length=2000)
    question_en: str = Field(..., min_length=10, max_length=2000)
    accepted_keywords: List[str] = Field(..., min_length=1, max_length=30)
    order: int = 100
    hint: Optional[str] = Field(default=None, max_length=200)
    enabled: bool = True


class RiddleUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    question_fr: Optional[str] = Field(default=None, max_length=2000)
    question_en: Optional[str] = Field(default=None, max_length=2000)
    accepted_keywords: Optional[List[str]] = None
    order: Optional[int] = None
    hint: Optional[str] = Field(default=None, max_length=200)
    enabled: Optional[bool] = None


class ClearancePatchRequest(BaseModel):
    level: Optional[int] = Field(default=None, ge=0, le=3)
    wallet_address: Optional[str] = Field(default=None, max_length=44)
    notes: Optional[str] = Field(default=None, max_length=500)


class SleeperCellPatchRequest(BaseModel):
    active: Optional[bool] = None
    message_fr: Optional[str] = Field(default=None, max_length=500)
    message_en: Optional[str] = Field(default=None, max_length=500)
    blocked_triggers: Optional[List[str]] = None


# ---------------------------------------------------------------------
# Admin — Riddles CRUD
# ---------------------------------------------------------------------
@admin_router.get("/riddles")
async def admin_list_riddles(_p: dict = Depends(require_admin)) -> Dict[str, Any]:
    return {"items": await riddles.list_admin_riddles()}


@admin_router.post("/riddles")
async def admin_create_riddle(
    body: RiddleCreateRequest, _p: dict = Depends(require_2fa_for_admin),
) -> Dict[str, Any]:
    try:
        return await riddles.create_riddle(
            slug=body.slug, title=body.title,
            question_fr=body.question_fr, question_en=body.question_en,
            accepted_keywords=body.accepted_keywords,
            order=body.order, hint=body.hint, enabled=body.enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@admin_router.patch("/riddles/{riddle_id}")
async def admin_update_riddle(
    riddle_id: str, body: RiddleUpdateRequest,
    _p: dict = Depends(require_2fa_for_admin),
) -> Dict[str, Any]:
    try:
        patch = body.model_dump(exclude_unset=True)
        item = await riddles.update_riddle(riddle_id, **patch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not item:
        raise HTTPException(status_code=404, detail="Riddle not found")
    return item


@admin_router.delete("/riddles/{riddle_id}")
async def admin_delete_riddle(
    riddle_id: str, _p: dict = Depends(require_2fa_for_admin),
) -> Dict[str, Any]:
    n = await riddles.delete_riddle(riddle_id)
    if not n:
        raise HTTPException(status_code=404, detail="Riddle not found")
    return {"ok": True, "deleted": n}


# ---------------------------------------------------------------------
# Admin — Clearance ledger
# ---------------------------------------------------------------------
@admin_router.get("/clearance")
async def admin_list_clearance(
    level: Optional[int] = None, limit: int = 500,
    _p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    rows = await clearance_levels.list_all(level=level, limit=limit)
    return {"items": rows}


@admin_router.get("/clearance/stats")
async def admin_clearance_stats(_p: dict = Depends(require_admin)) -> Dict[str, Any]:
    return await clearance_levels.stats()


@admin_router.patch("/clearance/{email}")
async def admin_patch_clearance(
    email: str, body: ClearancePatchRequest,
    p: dict = Depends(require_2fa_for_admin),
) -> Dict[str, Any]:
    try:
        if body.level is not None:
            await clearance_levels.admin_set_level(
                email=email, level=body.level,
                by_jti=p.get("jti"), notes=body.notes,
            )
        if body.wallet_address is not None:
            await clearance_levels.admin_set_wallet(
                email=email, wallet_address=body.wallet_address or None,
                by_jti=p.get("jti"),
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return (await clearance_levels.get_status(email)) or {}


@admin_router.get("/clearance/snapshot.csv")
async def admin_snapshot_csv(_p: dict = Depends(require_admin)):
    """Stream a CSV with every Level-3 agent, wallet status included.

    The CSV schema matches what the airdrop distributor will consume
    (one row per agent, ``_snapshot_status`` flags rows that still need
    a wallet before they can be dropped).
    """
    rows = await clearance_levels.snapshot_level3()

    def _generate():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=[
            "email", "wallet_address", "level",
            "level_1_achieved_at", "level_2_achieved_at", "level_3_achieved_at",
            "riddles_solved_count", "source", "snapshot_status",
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "email": r.get("email"),
                "wallet_address": r.get("wallet_address") or "",
                "level": r.get("level"),
                "level_1_achieved_at": r.get("level_1_achieved_at") or "",
                "level_2_achieved_at": r.get("level_2_achieved_at") or "",
                "level_3_achieved_at": r.get("level_3_achieved_at") or "",
                "riddles_solved_count": len(r.get("riddles_solved") or []),
                "source": r.get("source") or "",
                "snapshot_status": r.get("_snapshot_status") or "eligible",
            })
        yield buf.getvalue()

    filename = "deepotus_level3_snapshot.csv"
    return StreamingResponse(
        _generate(), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------
# Admin — Sleeper Cell toggle
# ---------------------------------------------------------------------
@admin_router.get("/sleeper-cell")
async def admin_get_sleeper(_p: dict = Depends(require_admin)) -> Dict[str, Any]:
    return await sleeper_cell.get_state()


@admin_router.patch("/sleeper-cell")
async def admin_patch_sleeper(
    body: SleeperCellPatchRequest, p: dict = Depends(require_2fa_for_admin),
) -> Dict[str, Any]:
    return await sleeper_cell.set_state(
        active=body.active,
        message_fr=body.message_fr,
        message_en=body.message_en,
        blocked_triggers=body.blocked_triggers,
        by_jti=p.get("jti"),
    )


# ---------------------------------------------------------------------
# Admin — Attempts audit
# ---------------------------------------------------------------------
@admin_router.get("/attempts")
async def admin_list_attempts(
    email: Optional[str] = None, slug: Optional[str] = None,
    limit: int = 100, _p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    items = await riddles.recent_attempts(email=email, slug=slug, limit=limit)
    return {"items": items}
