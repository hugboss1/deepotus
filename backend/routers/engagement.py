"""Admin REST surface for the organic-engagement modules.

Two sub-systems, one router:

Mention Responder (auto, X-rules compliant — replies only to accounts
that mentioned @Deepotus_AI first):

    GET   /api/admin/engagement/mentions/config
    PATCH /api/admin/engagement/mentions/config
    GET   /api/admin/engagement/mentions/replies      - audit feed
    POST  /api/admin/engagement/mentions/poll-now     - manual tick
          ?dry_run=true|false (default true — recette-safe)

Keyword Digest (semi-auto — NEVER posts to X; sends the founder a
private Telegram digest with ready-to-paste replies):

    GET   /api/admin/engagement/digest/config
    PATCH /api/admin/engagement/digest/config
    GET   /api/admin/engagement/digest/runs           - audit feed
    POST  /api/admin/engagement/digest/run-now        - manual run

Both are OFF by default; the PATCH endpoints flip ``enabled``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core import keyword_digest, mention_responder
from core.security import require_admin

admin_router = APIRouter(
    prefix="/api/admin/engagement",
    tags=["engagement-admin"],
)


# =====================================================================
# Mention Responder
# =====================================================================
class MentionResponderPatch(BaseModel):
    enabled: Optional[bool] = None
    poll_interval_hours: Optional[int] = Field(default=None, ge=1, le=24)
    max_replies_per_tick: Optional[int] = Field(default=None, ge=1, le=10)
    per_handle_cooldown_hours: Optional[int] = Field(default=None, ge=1, le=168)
    reply_templates: Optional[List[str]] = Field(default=None, max_length=10)


def _mention_cfg_view(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "enabled": bool(cfg.get("enabled")),
        "poll_interval_hours": cfg.get("poll_interval_hours"),
        "max_replies_per_tick": cfg.get("max_replies_per_tick"),
        "per_handle_cooldown_hours": cfg.get("per_handle_cooldown_hours"),
        "reply_templates": cfg.get("reply_templates") or [],
        "last_polled_at": cfg.get("last_polled_at"),
        "last_skip_reason": cfg.get("last_skip_reason"),
        "total_replies_lifetime": cfg.get("total_replies_lifetime") or 0,
    }


@admin_router.get("/mentions/config")
async def get_mentions_config(_admin=Depends(require_admin)) -> Dict[str, Any]:
    return _mention_cfg_view(await mention_responder.get_settings())


@admin_router.patch("/mentions/config")
async def patch_mentions_config(
    payload: MentionResponderPatch,
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="no fields to update")
    cfg = await mention_responder.patch_settings(patch)
    return {"ok": True, "config": _mention_cfg_view(cfg)}


@admin_router.get("/mentions/replies")
async def list_mention_replies(
    limit: int = Query(50, ge=1, le=500),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    items = await mention_responder.list_replies(limit=limit)
    return {"items": items, "count": len(items)}


@admin_router.post("/mentions/poll-now")
async def mentions_poll_now(
    dry_run: bool = Query(
        True,
        description=(
            "true (défaut) = tout le pipeline tourne mais AUCUN tweet "
            "n'est posté — c'est le mode recette. false = envoi réel."
        ),
    ),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    """Manual tick. First-ever call only sets the since_id baseline
    (no reply flood) — run it once, mention the account from a test
    profile, then run it again."""
    result = await mention_responder.poll_once(manual=True, dry_run=dry_run)
    return {"ok": True, "result": result}


# =====================================================================
# Keyword Digest
# =====================================================================
class DigestRule(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    query: str = Field(..., min_length=2, max_length=500)
    template: str = Field(..., min_length=4, max_length=500)


class DigestConfigPatch(BaseModel):
    enabled: Optional[bool] = None
    hours_utc: Optional[List[int]] = Field(default=None, max_length=6)
    lang: Optional[str] = Field(default=None, max_length=8)
    min_author_followers: Optional[int] = Field(default=None, ge=0, le=10_000_000)
    max_hits_per_rule: Optional[int] = Field(default=None, ge=1, le=10)
    rules: Optional[List[DigestRule]] = Field(default=None, max_length=10)


def _digest_cfg_view(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "enabled": bool(cfg.get("enabled")),
        "hours_utc": cfg.get("hours_utc") or [],
        "lang": cfg.get("lang"),
        "min_author_followers": cfg.get("min_author_followers"),
        "max_hits_per_rule": cfg.get("max_hits_per_rule"),
        "rules": cfg.get("rules") or [],
        "last_run_at": cfg.get("last_run_at"),
        "last_run_summary": cfg.get("last_run_summary"),
    }


@admin_router.get("/digest/config")
async def get_digest_config(_admin=Depends(require_admin)) -> Dict[str, Any]:
    return _digest_cfg_view(await keyword_digest.get_config())


@admin_router.patch("/digest/config")
async def patch_digest_config(
    payload: DigestConfigPatch,
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    dumped = payload.model_dump()
    patch = {k: v for k, v in dumped.items() if v is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="no fields to update")
    cfg = await keyword_digest.update_config(patch)
    return {"ok": True, "config": _digest_cfg_view(cfg)}


@admin_router.get("/digest/runs")
async def list_digest_runs(
    limit: int = Query(20, ge=1, le=100),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    items = await keyword_digest.list_runs(limit=limit)
    return {"items": items, "count": len(items)}


@admin_router.post("/digest/run-now")
async def digest_run_now(_admin=Depends(require_admin)) -> Dict[str, Any]:
    """Run a digest immediately (ignores the hours_utc window, keeps
    the dedup). Requires ``telegram/TELEGRAM_ADMIN_CHAT_ID`` in the
    vault or env — returns ``reason=no_admin_chat_id`` otherwise.
    Nothing is ever posted to X by this path."""
    result = await keyword_digest.run_digest(manual=True)
    return {"ok": True, "result": result}
