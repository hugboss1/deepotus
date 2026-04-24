"""Admin endpoints for the Prophet bot fleet (X / Telegram).

Phase 1 scope:
    - GET   /api/admin/bots/config            : read current config
    - PUT   /api/admin/bots/config            : patch config (merge semantics)
    - POST  /api/admin/bots/kill-switch       : emergency toggle {active: bool}
    - GET   /api/admin/bots/jobs              : list live APScheduler jobs
    - GET   /api/admin/bots/posts             : paginated post log
    - POST  /api/admin/bots/heartbeat         : manual heartbeat trigger (debug)

All endpoints are JWT-protected via `require_admin`. No public access.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from core.bot_scheduler import (
    POSTS_COLLECTION,
    describe_jobs,
    get_bot_config,
    log_post_attempt,
    sync_jobs_from_config,
    update_bot_config,
)
from core.config import db
from core.security import require_admin

router = APIRouter(prefix="/api/admin/bots", tags=["admin-bots"])


# ---------------------------------------------------------------------
# Pydantic payloads
# ---------------------------------------------------------------------
class PlatformPatch(BaseModel):
    enabled: Optional[bool] = None
    post_frequency_hours: Optional[int] = Field(default=None, ge=1, le=48)


class BotConfigPatch(BaseModel):
    kill_switch_active: Optional[bool] = None
    platforms: Optional[Dict[str, PlatformPatch]] = None
    content_modes: Optional[Dict[str, bool]] = None
    heartbeat_interval_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    max_posts_per_day: Optional[int] = Field(default=None, ge=0, le=500)


class KillSwitchPayload(BaseModel):
    active: bool


class BotConfigResponse(BaseModel):
    kill_switch_active: bool
    platforms: Dict[str, Dict[str, Any]]
    content_modes: Dict[str, bool]
    heartbeat_interval_minutes: int
    max_posts_per_day: int
    last_updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None


class BotJobItem(BaseModel):
    id: str
    next_run_time: Optional[str] = None
    trigger: str
    max_instances: int
    coalesce: bool


class BotPostItem(BaseModel):
    id: str
    platform: str
    content_type: str
    status: str
    content: Optional[str] = None
    error: Optional[str] = None
    external_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    created_at: str


class PaginatedBotPosts(BaseModel):
    items: List[BotPostItem]
    total: int
    limit: int
    skip: int
    status_counts: Dict[str, int]


# ---------------------------------------------------------------------
# Shaping helpers
# ---------------------------------------------------------------------
def _shape_config(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Strip Mongo-internal fields and ensure all expected keys exist."""
    return {
        "kill_switch_active": bool(doc.get("kill_switch_active", True)),
        "platforms": doc.get("platforms") or {},
        "content_modes": doc.get("content_modes") or {},
        "heartbeat_interval_minutes": int(doc.get("heartbeat_interval_minutes") or 5),
        "max_posts_per_day": int(doc.get("max_posts_per_day") or 12),
        "last_updated_at": doc.get("last_updated_at"),
        "updated_by": doc.get("updated_by"),
        "created_at": doc.get("created_at"),
    }


def _merge_platform_patch(
    current: Dict[str, Any], patch: Dict[str, PlatformPatch]
) -> Dict[str, Any]:
    """Shallow-merge per-platform fields so partial updates don't nuke state."""
    merged = dict(current or {})
    for pname, pdata in (patch or {}).items():
        existing = dict(merged.get(pname) or {})
        if pdata.enabled is not None:
            existing["enabled"] = pdata.enabled
        if pdata.post_frequency_hours is not None:
            existing["post_frequency_hours"] = pdata.post_frequency_hours
        merged[pname] = existing
    return merged


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------
@router.get("/config", response_model=BotConfigResponse)
async def get_config(_p: dict = Depends(require_admin)):
    doc = await get_bot_config()
    return _shape_config(doc)


@router.put("/config", response_model=BotConfigResponse)
async def put_config(
    payload: BotConfigPatch,
    _p: dict = Depends(require_admin),
):
    current = await get_bot_config()

    patch_dict: Dict[str, Any] = {}
    if payload.kill_switch_active is not None:
        patch_dict["kill_switch_active"] = payload.kill_switch_active
    if payload.platforms is not None:
        patch_dict["platforms"] = _merge_platform_patch(
            current.get("platforms") or {}, payload.platforms
        )
    if payload.content_modes is not None:
        # merge: allow partial toggles without nuking the rest
        merged = dict(current.get("content_modes") or {})
        for k, v in payload.content_modes.items():
            merged[k] = bool(v)
        patch_dict["content_modes"] = merged
    if payload.heartbeat_interval_minutes is not None:
        patch_dict["heartbeat_interval_minutes"] = payload.heartbeat_interval_minutes
    if payload.max_posts_per_day is not None:
        patch_dict["max_posts_per_day"] = payload.max_posts_per_day

    if not patch_dict:
        raise HTTPException(status_code=400, detail="empty_patch")

    updated_by = (_p or {}).get("jti") or "admin"
    doc = await update_bot_config(patch_dict, updated_by=updated_by)
    return _shape_config(doc)


@router.post("/kill-switch", response_model=BotConfigResponse)
async def toggle_kill_switch(
    payload: KillSwitchPayload,
    _p: dict = Depends(require_admin),
):
    """Dedicated emergency endpoint for the admin dashboard."""
    updated_by = (_p or {}).get("jti") or "admin"
    doc = await update_bot_config(
        {"kill_switch_active": bool(payload.active)},
        updated_by=updated_by,
    )
    return _shape_config(doc)


@router.get("/jobs", response_model=List[BotJobItem])
async def list_jobs(_p: dict = Depends(require_admin)):
    # Sync jobs in case config changed while scheduler was warming
    await sync_jobs_from_config()
    return describe_jobs()


@router.get("/posts", response_model=PaginatedBotPosts)
async def list_posts(
    _p: dict = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    platform: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
):
    query: Dict[str, Any] = {}
    if platform:
        query["platform"] = platform
    if status_filter:
        query["status"] = status_filter

    cursor = (
        db[POSTS_COLLECTION]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    rows = await cursor.to_list(length=limit)
    total = await db[POSTS_COLLECTION].count_documents(query)

    # Quick status histogram across the filter window
    pipeline = [
        {"$match": query} if query else {"$match": {}},
        {"$group": {"_id": "$status", "n": {"$sum": 1}}},
    ]
    status_counts: Dict[str, int] = {}
    async for r in db[POSTS_COLLECTION].aggregate(pipeline):
        status_counts[r["_id"]] = r["n"]

    items = [
        BotPostItem(
            id=str(r.get("_id")),
            platform=r.get("platform", "unknown"),
            content_type=r.get("content_type", "unknown"),
            status=r.get("status", "unknown"),
            content=r.get("content"),
            error=r.get("error"),
            external_id=r.get("external_id"),
            extra=r.get("extra") or {},
            created_at=r.get("created_at", ""),
        )
        for r in rows
    ]

    return PaginatedBotPosts(
        items=items,
        total=total,
        limit=limit,
        skip=skip,
        status_counts=status_counts,
    )


@router.post("/heartbeat", response_model=BotPostItem)
async def manual_heartbeat(_p: dict = Depends(require_admin)):
    """Force a heartbeat entry — useful to confirm writes from the dashboard."""
    cfg = await get_bot_config()
    status = "killed" if cfg.get("kill_switch_active") else "heartbeat"
    pid = await log_post_attempt(
        platform="system",
        content_type="heartbeat",
        status=status,
        content="manual heartbeat",
        error="kill_switch_active" if status == "killed" else None,
    )
    doc = await db[POSTS_COLLECTION].find_one({"_id": pid})
    return BotPostItem(
        id=str(doc.get("_id")),
        platform=doc.get("platform"),
        content_type=doc.get("content_type"),
        status=doc.get("status"),
        content=doc.get("content"),
        error=doc.get("error"),
        external_id=doc.get("external_id"),
        extra=doc.get("extra") or {},
        created_at=doc.get("created_at", ""),
    )
