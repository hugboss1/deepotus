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

from core import dispatch_queue, propaganda_engine, templates_repo, tone_engine
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


class ToneSettingsPatch(BaseModel):
    """Live-tunable LLM + persona settings exposed to the admin UI."""

    llm_enabled: Optional[bool] = None
    llm_enhance_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    personality_prompt: Optional[str] = Field(default=None, max_length=4000)
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


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
    tone = await tone_engine.get_tone_settings()
    s.update(tone)  # llm_enabled, llm_enhance_ratio, personality_prompt, …
    return s


@router.patch("/settings")
async def patch_tone(body: ToneSettingsPatch, _p: dict = Depends(require_admin)):
    """Live-update the LLM + persona settings.

    Power users can flip the LLM hybrid mix from this single endpoint —
    no restart needed. Personality prompt edits propagate to the next
    fire that wins the dice roll for an LLM rewrite.
    """
    try:
        tone = await tone_engine.patch_tone_settings(
            llm_enabled=body.llm_enabled,
            llm_enhance_ratio=body.llm_enhance_ratio,
            personality_prompt=body.personality_prompt,
            llm_provider=body.llm_provider,
            llm_model=body.llm_model,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return tone


@router.post("/panic")
async def toggle_panic(req: PanicRequest, request: Request,
                       p: dict = Depends(require_2fa_for_send)):
    s = await propaganda_engine.set_panic(req.panic, jti=p.get("jti"))
    s.pop("_id", None)
    return s


# ---- Dispatch toggles (Sprint 13.3) ----------------------------------------
class DispatchToggleRequest(BaseModel):
    """Either or both knobs may be patched. Both default to None
    (= leave unchanged) so the admin UI can issue partial updates."""

    enabled: Optional[bool] = Field(
        default=None,
        description=(
            "Master switch. When False the dispatch worker reads the "
            "queue but does not touch any item. When True it starts "
            "moving items through 'in_flight → sent | failed'."
        ),
    )
    dry_run: Optional[bool] = Field(
        default=None,
        description=(
            "When True (default and recommended until creds are vaulted) "
            "the dispatchers short-circuit the actual HTTP call and just "
            "log the would-be payload. Items still transition to 'sent' "
            "so admin can validate the full pipeline. Flip to False ONLY "
            "after credentials have been verified via 'tick now'."
        ),
    )


@router.post("/dispatch/toggle")
async def toggle_dispatch(
    req: DispatchToggleRequest,
    request: Request,
    p: dict = Depends(require_2fa_for_send),
):
    """Flip the dispatch worker's enabled / dry_run knobs.

    Both gated behind 2FA (same as panic): turning ``dry_run`` OFF is
    the moment real money / brand reputation is on the line, so we
    require strong proof of intent.
    """
    s = await propaganda_engine.set_dispatch_toggle(
        enabled=req.enabled,
        dry_run=req.dry_run,
        jti=p.get("jti"),
    )
    s.pop("_id", None)
    return s


@router.get("/dispatch/status")
async def dispatch_status(_p: dict = Depends(require_admin)):
    """Snapshot view for the admin UI: settings + queue counts."""
    settings = await propaganda_engine.get_settings()
    settings.pop("_id", None)
    counts = await dispatch_queue.queue_counts()
    return {
        "settings": {
            "panic": settings.get("panic", False),
            "dispatch_enabled": settings.get("dispatch_enabled", False),
            "dispatch_dry_run": settings.get("dispatch_dry_run", True),
            "rate_limits": settings.get("rate_limits"),
            "platforms": settings.get("platforms", []),
        },
        "queue": counts,
    }


@router.post("/dispatch/tick-now")
async def dispatch_tick_now(p: dict = Depends(require_2fa_for_send)):
    """Force one immediate drain pass without waiting up to 30s for the
    scheduler. Useful to test the pipeline after a settings change.

    Honours all the same gates as the scheduled tick (panic /
    dispatch_enabled / dry_run / rate limits)."""
    from core.dispatch_worker import force_tick

    summary = await force_tick()
    summary["triggered_by"] = p.get("jti")
    return summary


@router.get("/dispatch/preflight")
async def dispatch_preflight(_p: dict = Depends(require_admin)):
    """Non-destructive credentials probe (Sprint 13.3.x).

    Reports — for each platform — whether all required secrets are
    resolvable (vault → env). NEVER returns the actual values; only
    presence flags + source. Use this BEFORE flipping
    ``dispatch_dry_run`` to ``false`` to confirm everything is wired
    up.

    Output shape::
        {
          "telegram": {"ready": bool, "missing": [...], "details": {...}},
          "x":        {"ready": bool, "missing": [...], "details": {...}},
          "current_settings": {"dispatch_enabled": bool, "dispatch_dry_run": bool}
        }
    """
    from core.secret_provider import describe_resolution

    # ---- Telegram ----
    tg_token = await describe_resolution(
        "telegram", "TELEGRAM_BOT_TOKEN"
    )
    tg_chat = await describe_resolution(
        "telegram", "TELEGRAM_CHAT_ID"
    )
    tg_missing = []
    if not tg_token["set"]:
        tg_missing.append("TELEGRAM_BOT_TOKEN")
    if not tg_chat["set"]:
        tg_missing.append("TELEGRAM_CHAT_ID")

    # ---- X (Twitter) ----
    x_keys = ("X_API_KEY", "X_API_SECRET",
              "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
    x_details: Dict[str, Any] = {}
    x_missing: List[str] = []
    for k in x_keys:
        info = await describe_resolution("x_twitter", k)
        x_details[k] = info
        if not info["set"]:
            x_missing.append(k)

    settings = await propaganda_engine.get_settings()
    return {
        "telegram": {
            "ready": len(tg_missing) == 0,
            "missing": tg_missing,
            "details": {
                "TELEGRAM_BOT_TOKEN": tg_token,
                "TELEGRAM_CHAT_ID": tg_chat,
            },
        },
        "x": {
            "ready": len(x_missing) == 0,
            "missing": x_missing,
            "details": x_details,
        },
        "current_settings": {
            "dispatch_enabled": settings.get("dispatch_enabled", False),
            "dispatch_dry_run": settings.get("dispatch_dry_run", True),
            "panic": settings.get("panic", False),
        },
        "next_step_hint": (
            "All ready → POST /dispatch/toggle {enabled:true, dry_run:true} → "
            "POST /dispatch/tick-now → check 'recent_events' → if OK then "
            "{dry_run:false} for live mode."
        ),
    }


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
