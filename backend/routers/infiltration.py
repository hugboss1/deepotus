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

from core import clearance_levels, infiltration_auto, riddles, sleeper_cell
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



# ---------------------------------------------------------------------
# Sprint 14.2 — Auto-validation L1/L2 + KOL DM drafts
# ---------------------------------------------------------------------
class VerifyTelegramRequest(BaseModel):
    email: EmailStr
    tg_user_id: str = Field(..., min_length=4, max_length=20)


class SubmitShareRequest(BaseModel):
    email: EmailStr
    share_url: str = Field(..., min_length=20, max_length=500)


class ReviewShareRequest(BaseModel):
    approve: bool
    reviewer_note: Optional[str] = Field(default=None, max_length=500)


class ApproveKolDmRequest(BaseModel):
    final_body: Optional[str] = Field(default=None, max_length=1000)


@public_router.post("/verify/telegram")
async def infiltration_verify_tg(req: VerifyTelegramRequest) -> Dict[str, Any]:
    """Public endpoint — user provides their email + numeric Telegram
    user_id. We ping Bot API's getChatMember to confirm they're in the
    group, then auto-promote to Level 1.

    Returns a structured code (``ok``, ``tg_not_member``, ``tg_timeout``,
    ``tg_creds_missing``, ``invalid_tg_id``, ``x_tier_required``) so the
    frontend can render the right hint.
    """
    ok, code, detail = await infiltration_auto.verify_telegram_member(
        email=req.email,
        tg_user_id=req.tg_user_id,
    )
    status_code = 200 if ok else 400
    return {
        "ok": ok,
        "code": code,
        "detail": detail,
        "http_status": status_code,
    }


@public_router.post("/verify/x-follow")
async def infiltration_verify_x_follow(
    email: EmailStr, x_handle: str,
) -> Dict[str, Any]:
    """Public endpoint — placeholder for Level 1 via X follow check.
    Currently always returns ``x_tier_required`` because the live
    implementation depends on X API Basic. The frontend uses this
    response to show a "feature coming soon" state while still
    offering the Telegram verification path."""
    ok, code, detail = await infiltration_auto.verify_x_follow(
        email=email, x_handle=x_handle,
    )
    return {"ok": ok, "code": code, "detail": detail}


@public_router.post("/verify/share")
async def infiltration_submit_share(req: SubmitShareRequest) -> Dict[str, Any]:
    """Public endpoint — user pastes the URL of their post mentioning
    $DEEPOTUS. Submission goes to admin review queue. The user is told
    they'll get promoted within 24h if approved."""
    ok, code, detail = await infiltration_auto.submit_share_for_review(
        email=req.email, share_url=req.share_url,
    )
    return {"ok": ok, "code": code, "detail": detail}


# ----- Admin surface -------------------------------------------------
@admin_router.get("/auto/status")
async def admin_auto_status(_p: dict = Depends(require_admin)) -> Dict[str, Any]:
    """Which auto-verifiers are live vs blocked, and how many items
    are awaiting review. Drives the admin UI's feature chips."""
    return await infiltration_auto.feature_status()


@admin_router.get("/shares")
async def admin_list_shares(
    status: Optional[str] = None,
    limit: int = 100,
    _p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """List Level 2 share submissions (defaults to all statuses;
    admin UI typically filters on ``status=pending_review``)."""
    items = await infiltration_auto.list_share_submissions(
        status=status, limit=min(max(limit, 1), 500),
    )
    return {"items": items, "count": len(items)}


@admin_router.post("/shares/{submission_id}/review")
async def admin_review_share(
    submission_id: str,
    req: ReviewShareRequest,
    p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    ok, status, detail = await infiltration_auto.review_share_submission(
        submission_id,
        approve=req.approve,
        reviewer_note=req.reviewer_note,
        jti=p.get("jti") or "admin",
    )
    if not ok and status == "not_found":
        raise HTTPException(status_code=404, detail="submission not found")
    return {"ok": ok, "status": status, "detail": detail}


@admin_router.get("/kol-dm-drafts")
async def admin_list_kol_drafts(
    status: Optional[str] = None,
    limit: int = 100,
    _p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    items = await infiltration_auto.list_kol_dm_drafts(
        status=status, limit=min(max(limit, 1), 500),
    )
    return {"items": items, "count": len(items)}


@admin_router.post("/kol-dm-drafts/{draft_id}/approve")
async def admin_approve_kol_dm(
    draft_id: str,
    req: ApproveKolDmRequest,
    p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    ok, status, detail = await infiltration_auto.approve_kol_dm(
        draft_id,
        jti=p.get("jti") or "admin",
        final_body=req.final_body,
    )
    if not ok and status == "not_found":
        raise HTTPException(status_code=404, detail="draft not found")
    return {"ok": ok, "status": status, "detail": detail}

