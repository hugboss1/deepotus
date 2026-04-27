"""Admin REST API — PROTOCOL ΔΣ Propaganda Engine.

Endpoints (all behind ``require_admin``; mutating ones require 2FA):

    GET    /api/admin/propaganda/settings              — panic flag, locale, rate limits…
    POST   /api/admin/propaganda/panic                  — toggle kill-switch
    GET    /api/admin/propaganda/triggers               — list + per-trigger config
    PATCH  /api/admin/propaganda/triggers/{key}         — enable / policy / cooldown
    POST   /api/admin/propaganda/fire                   — manual fire (admin button)

    GET    /api/admin/propaganda/templates              — list templates (filter trigger/lang)
    POST   /api/admin/propaganda/templates              — create
    PATCH  /api/admin/propaganda/templates/{id}         — partial update
    DELETE /api/admin/propaganda/templates/{id}         — delete

    GET    /api/admin/propaganda/queue                  — list queue items
    POST   /api/admin/propaganda/queue/{id}/approve     — approve a proposed item
    POST   /api/admin/propaganda/queue/{id}/reject      — reject a proposed item

    GET    /api/admin/propaganda/activity               — audit feed
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core import dispatch_queue, propaganda_engine, templates_repo
from core.security import get_twofa_config, require_admin

router = APIRouter(prefix="/api/admin/propaganda", tags=["propaganda"])


# ---- Guards ----------------------------------------------------------------
async def require_2fa_for_send(p: dict = Depends(require_admin)) -> dict:
    """Approval / reject / panic toggle require 2FA — these can move money
    by attracting buyers, so we treat them like a Cabinet Vault write.

    NOTE: keeping consistency with cabinet_vault behaviour. Bootstrap mode is
    not relevant here — propaganda is purely operational, not setup.
    """
    cfg = await get_twofa_config()
    if not (cfg and cfg.get("enabled")):
        raise HTTPException(
            status_code=403,
            detail={"code": "TWOFA_REQUIRED",
                    "message": "Enable 2FA before approving or rejecting messages."},
        )
    return p


def _client_ip(req: Request) -> Optional[str]:
    return req.client.host if req.client else None


# ---- Models ----------------------------------------------------------------
class PanicRequest(BaseModel):
    panic: bool


class TriggerPatch(BaseModel):
    enabled: Optional[bool] = None
    policy: Optional[str] = None
    cooldown_minutes: Optional[int] = Field(default=None, ge=0, le=60 * 24)
    metadata: Optional[Dict[str, Any]] = None


class TemplateCreate(BaseModel):
    trigger_key: str
    language: str = "en"
    content: str = Field(..., min_length=1, max_length=1000)
    weight: float = 1.0
    mentions_vault: bool = False
    enabled: bool = True


class TemplatePatch(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    language: Optional[str] = None
    weight: Optional[float] = None
    mentions_vault: Optional[bool] = None
    enabled: Optional[bool] = None


class FireRequest(BaseModel):
    trigger_key: str
    payload_override: Dict[str, Any] = Field(default_factory=dict)
    locale_override: Optional[str] = None
    platforms: Optional[List[str]] = None


class RejectRequest(BaseModel):
    reason: Optional[str] = None


# ---- Settings + Panic ------------------------------------------------------
@router.get("/settings")
async def get_settings(_p: dict = Depends(require_admin)):
    s = await propaganda_engine.get_settings()
    s.pop("_id", None)
    return s


@router.post("/panic")
async def toggle_panic(req: PanicRequest, request: Request,
                       p: dict = Depends(require_2fa_for_send)):
    s = await propaganda_engine.set_panic(req.panic, jti=p.get("jti"))
    s.pop("_id", None)
    return s


# ---- Triggers --------------------------------------------------------------
@router.get("/triggers")
async def list_triggers(_p: dict = Depends(require_admin)):
    return {"items": await propaganda_engine.list_triggers()}


@router.patch("/triggers/{key}")
async def patch_trigger(key: str, body: TriggerPatch,
                        _p: dict = Depends(require_admin)):
    try:
        cfg = await propaganda_engine.update_trigger_cfg(
            key,
            enabled=body.enabled,
            policy=body.policy,
            cooldown_minutes=body.cooldown_minutes,
            metadata=body.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    cfg.pop("_id", None)
    return cfg


# ---- Manual fire -----------------------------------------------------------
@router.post("/fire")
async def manual_fire(req: FireRequest, request: Request,
                      p: dict = Depends(require_admin)):
    """Force-fire a trigger (used pre-mint for testing, or in emergencies).

    The trigger detector still runs in *manual* mode, so each trigger
    decides what payload it wants to expose. The resulting message lands
    in the queue (auto-policy = directly approved, approval-policy = held).
    """
    out = await propaganda_engine.fire(
        req.trigger_key,
        manual=True,
        payload_override=req.payload_override,
        locale_override=req.locale_override,
        platforms=req.platforms,
        jti=p.get("jti"),
        ip=_client_ip(request),
    )
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=out)
    return out


# ---- Templates -------------------------------------------------------------
@router.get("/templates")
async def list_templates(
    trigger_key: Optional[str] = None,
    language: Optional[str] = None,
    _p: dict = Depends(require_admin),
):
    items = await templates_repo.list_templates(trigger_key=trigger_key, language=language)
    return {"items": items}


@router.post("/templates")
async def create_template(body: TemplateCreate, _p: dict = Depends(require_admin)):
    try:
        item = await templates_repo.create_template(
            trigger_key=body.trigger_key,
            language=body.language,
            content=body.content,
            weight=body.weight,
            mentions_vault=body.mentions_vault,
            enabled=body.enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return item


@router.patch("/templates/{template_id}")
async def patch_template(template_id: str, body: TemplatePatch,
                         _p: dict = Depends(require_admin)):
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    try:
        item = await templates_repo.update_template(template_id, **patch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not item:
        raise HTTPException(status_code=404, detail="Template not found")
    return item


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, _p: dict = Depends(require_admin)):
    n = await templates_repo.delete_template(template_id)
    if not n:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True, "deleted": n}


# ---- Queue + approval ------------------------------------------------------
@router.get("/queue")
async def list_queue(
    statuses: Optional[str] = None,
    limit: int = 100,
    _p: dict = Depends(require_admin),
):
    parsed = [s.strip() for s in (statuses or "").split(",") if s.strip()] or None
    items = await dispatch_queue.list_queue(statuses=parsed, limit=limit)
    return {"items": items}


@router.post("/queue/{item_id}/approve")
async def approve_item(item_id: str, request: Request,
                       p: dict = Depends(require_2fa_for_send)):
    item = await dispatch_queue.approve(item_id, by_jti=p.get("jti"))
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found or already in a terminal state.",
        )
    await propaganda_engine.audit(
        "approve", trigger_key=item["trigger_key"],
        queue_item_id=item["id"], jti=p.get("jti"), ip=_client_ip(request),
    )
    return item


@router.post("/queue/{item_id}/reject")
async def reject_item(item_id: str, body: RejectRequest, request: Request,
                      p: dict = Depends(require_2fa_for_send)):
    item = await dispatch_queue.reject(
        item_id, by_jti=p.get("jti"), reason=body.reason or "",
    )
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found or already in a terminal state.",
        )
    await propaganda_engine.audit(
        "reject", trigger_key=item["trigger_key"],
        queue_item_id=item["id"], jti=p.get("jti"), ip=_client_ip(request),
        meta={"reason": (body.reason or "").strip()[:200]},
    )
    return item


# ---- Activity feed ---------------------------------------------------------
@router.get("/activity")
async def list_activity(limit: int = 100, _p: dict = Depends(require_admin)):
    items = await propaganda_engine.list_activity(limit=limit)
    return {"items": items}
