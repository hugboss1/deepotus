"""Admin REST surface for the KOL X-Mention Listener (Sprint 16.4).

Endpoints (all admin-only — JWT required):

    GET   /api/admin/kol-listener/config          - read config + KOL list
    PATCH /api/admin/kol-listener/config          - toggle enabled, edit handles
    GET   /api/admin/kol-listener/mentions        - audit feed
    GET   /api/admin/kol-listener/stats           - dashboard widget data
    POST  /api/admin/kol-listener/simulate        - inject a synthetic mention

The polling loop is a TODO — see ``core/kol_listener.poll_x_api_once``
for the wiring point. Until that lands, the simulate endpoint provides
the only ingestion path and is sufficient to verify the full
propaganda dispatch pipeline end-to-end.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from core import kol_listener
from core.security import require_admin

admin_router = APIRouter(
    prefix="/api/admin/kol-listener",
    tags=["kol-listener-admin"],
)


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
class KolConfigPatch(BaseModel):
    enabled: Optional[bool] = None
    handles: Optional[List[str]] = Field(default=None, max_length=50)
    min_followers: Optional[int] = Field(default=None, ge=0, le=10_000_000)
    match_terms: Optional[List[str]] = Field(default=None, max_length=20)


@admin_router.get("/config")
async def get_config(_admin=Depends(require_admin)) -> Dict[str, Any]:
    cfg = await kol_listener.get_config()
    # Strip Mongo internals before returning
    return {
        "enabled": bool(cfg.get("enabled")),
        "handles": cfg.get("handles") or [],
        "min_followers": cfg.get("min_followers") or 0,
        "match_terms": cfg.get("match_terms") or [],
        "updated_at": cfg.get("updated_at"),
    }


@admin_router.patch("/config")
async def patch_config(
    payload: KolConfigPatch,
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    patch = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not patch:
        raise HTTPException(status_code=400, detail="no fields to update")
    cfg = await kol_listener.update_config(patch)
    return {
        "ok": True,
        "config": {
            "enabled": bool(cfg.get("enabled")),
            "handles": cfg.get("handles") or [],
            "min_followers": cfg.get("min_followers") or 0,
            "match_terms": cfg.get("match_terms") or [],
        },
    }


# ---------------------------------------------------------------------
# Audit feed
# ---------------------------------------------------------------------
@admin_router.get("/mentions")
async def list_mentions(
    status: Optional[str] = Query(None),
    handle: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    items = await kol_listener.list_mentions(
        status=status, handle=handle, limit=limit
    )
    return {"items": items, "count": len(items)}


@admin_router.get("/stats")
async def stats(_admin=Depends(require_admin)) -> Dict[str, Any]:
    return await kol_listener.stats_snapshot()


# ---------------------------------------------------------------------
# Simulate (E2E)
# ---------------------------------------------------------------------
class SimulateMentionPayload(BaseModel):
    handle: str = Field(..., min_length=2, max_length=64)
    tweet_text: str = Field(..., min_length=4, max_length=2_000)
    tweet_id: Optional[str] = Field(default=None, max_length=64)
    tweet_url: Optional[str] = Field(default=None, max_length=400)


@admin_router.post("/simulate")
async def simulate(
    payload: SimulateMentionPayload,
    request: Request,
    _admin=Depends(require_admin),
) -> Dict[str, Any]:
    """Inject a synthetic KOL mention.

    The APScheduler tick will pick it up within the next interval and
    propose a propaganda queue item (status ``proposed``, awaiting
    2FA-protected approval before any real X/Telegram dispatch).
    """
    import uuid as _uuid

    tweet_id = payload.tweet_id or f"sim-kol-{_uuid.uuid4().hex[:20]}"
    inserted = await kol_listener.enqueue_mention(
        handle=payload.handle,
        tweet_text=payload.tweet_text,
        tweet_id=tweet_id,
        tweet_url=payload.tweet_url,
        source="admin_simulate",
    )
    return {
        "ok": True,
        "duplicate": bool(inserted.get("duplicate")),
        "mention": {
            "id": inserted.get("_id"),
            "handle": inserted.get("handle"),
            "tweet_id": inserted.get("tweet_id"),
            "status": inserted.get("status"),
            "ts": inserted.get("ts"),
        },
    }
