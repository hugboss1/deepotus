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
from core.news_feed import (
    DEFAULT_NEWS_FEEDS,
    DEFAULT_NEWS_KEYWORDS,
    build_news_context_block,
    get_recent_items,
    refresh_all,
)
from core.prophet_studio import (
    PLATFORM_CHAR_BUDGETS,
    VALID_CONTENT_TYPES,
    generate_image,
    generate_post,
    list_content_types,
)
from core.security import require_admin

router = APIRouter(prefix="/api/admin/bots", tags=["admin-bots"])


# ---------------------------------------------------------------------
# Pydantic payloads
# ---------------------------------------------------------------------
class PlatformPatch(BaseModel):
    enabled: Optional[bool] = None
    post_frequency_hours: Optional[int] = Field(default=None, ge=1, le=48)


class LlmPatch(BaseModel):
    provider: Optional[str] = Field(default=None, max_length=32)
    model: Optional[str] = Field(default=None, max_length=80)


class NewsFeedPatch(BaseModel):
    """Partial patch for the news_feed sub-document.

    Each field is optional so the admin can update one knob at a time.
    Lists are REPLACE semantics (passing [] resets to the defaults at
    runtime; passing None leaves them untouched).
    """

    enabled_for: Optional[Dict[str, bool]] = None
    fetch_interval_hours: Optional[int] = Field(default=None, ge=1, le=24)
    feeds: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    headlines_per_post: Optional[int] = Field(default=None, ge=0, le=10)


class BotConfigPatch(BaseModel):
    kill_switch_active: Optional[bool] = None
    platforms: Optional[Dict[str, PlatformPatch]] = None
    content_modes: Optional[Dict[str, bool]] = None
    llm: Optional[LlmPatch] = None
    news_feed: Optional[NewsFeedPatch] = None
    heartbeat_interval_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    max_posts_per_day: Optional[int] = Field(default=None, ge=0, le=500)


class KillSwitchPayload(BaseModel):
    active: bool


class GeneratePreviewRequest(BaseModel):
    content_type: str = Field(..., description="prophecy | market_commentary | vault_update | kol_reply")
    platform: str = Field(default="x", description="x | telegram")
    kol_post: Optional[str] = Field(default=None, max_length=600)
    extra_context: Optional[str] = Field(default=None, max_length=1000)
    include_image: bool = Field(default=False, description="Also generate an X illustration via Nano Banana")
    image_aspect_ratio: str = Field(default="16:9", description="16:9 | 3:4 | 1:1")
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Optional list of admin-supplied keywords / topics. The Prophet uses them as the spark of the post.",
        max_length=12,
    )
    use_news_context: bool = Field(
        default=False,
        description="When true, inject the freshest geopolitics/macro headlines (top N from the RSS aggregator) into extra_context.",
    )


class GeneratedImage(BaseModel):
    content_type: str
    aspect_ratio: str
    provider: str
    model: str
    mime_type: str
    image_base64: str
    size_bytes: int


class GeneratePreviewResponse(BaseModel):
    content_type: str
    platform: str
    char_budget: int
    provider: str
    model: str
    content_fr: str
    content_en: str
    hashtags: List[str]
    primary_emoji: str
    image: Optional[GeneratedImage] = None
    image_error: Optional[str] = None


class ContentTypeMeta(BaseModel):
    id: str
    label_fr: str
    label_en: str
    description_fr: str
    description_en: str
    suggested_hashtags: List[str]


class BotConfigResponse(BaseModel):
    kill_switch_active: bool
    platforms: Dict[str, Dict[str, Any]]
    content_modes: Dict[str, bool]
    llm: Dict[str, Any]
    news_feed: Dict[str, Any]
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
    nf_raw = doc.get("news_feed") or {}
    news_feed = {
        "enabled_for": nf_raw.get("enabled_for")
        or {"x": True, "telegram": False},
        "fetch_interval_hours": int(nf_raw.get("fetch_interval_hours") or 6),
        "feeds": list(nf_raw.get("feeds") or []),
        "keywords": list(nf_raw.get("keywords") or []),
        "headlines_per_post": int(nf_raw.get("headlines_per_post") or 5),
        "last_refresh_at": nf_raw.get("last_refresh_at"),
        "last_refresh_stats": nf_raw.get("last_refresh_stats"),
        # Surface the curated defaults so the UI can offer "Reset to default"
        "default_feeds": DEFAULT_NEWS_FEEDS,
        "default_keywords": DEFAULT_NEWS_KEYWORDS,
    }
    return {
        "kill_switch_active": bool(doc.get("kill_switch_active", True)),
        "platforms": doc.get("platforms") or {},
        "content_modes": doc.get("content_modes") or {},
        "llm": doc.get("llm")
        or {"provider": "anthropic", "model": "claude-sonnet-4-5-20250929"},
        "news_feed": news_feed,
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
    if payload.llm is not None:
        merged_llm = dict(current.get("llm") or {})
        if payload.llm.provider is not None:
            merged_llm["provider"] = payload.llm.provider
        if payload.llm.model is not None:
            merged_llm["model"] = payload.llm.model
        patch_dict["llm"] = merged_llm
    if payload.news_feed is not None:
        merged_nf = dict(current.get("news_feed") or {})
        nf = payload.news_feed
        if nf.enabled_for is not None:
            merged_enabled = dict(merged_nf.get("enabled_for") or {})
            for plat, val in nf.enabled_for.items():
                merged_enabled[plat] = bool(val)
            merged_nf["enabled_for"] = merged_enabled
        if nf.fetch_interval_hours is not None:
            merged_nf["fetch_interval_hours"] = int(nf.fetch_interval_hours)
        if nf.feeds is not None:
            # `[]` → reset to defaults (user clicked "Reset to default")
            merged_nf["feeds"] = [u.strip() for u in nf.feeds if (u or "").strip()]
        if nf.keywords is not None:
            merged_nf["keywords"] = [
                k.strip() for k in nf.keywords if (k or "").strip()
            ]
        if nf.headlines_per_post is not None:
            merged_nf["headlines_per_post"] = int(nf.headlines_per_post)
        patch_dict["news_feed"] = merged_nf
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



# ---------------------------------------------------------------------
# Phase 2 — Prophet Studio preview endpoints
# ---------------------------------------------------------------------
@router.get("/content-types", response_model=List[ContentTypeMeta])
async def get_content_types(_p: dict = Depends(require_admin)):
    """Metadata for the 4 content archetypes the Prophet can broadcast."""
    return list_content_types()


@router.post("/generate-preview", response_model=GeneratePreviewResponse)
async def generate_preview(
    payload: GeneratePreviewRequest,
    _p: dict = Depends(require_admin),
):
    """Dry-run content generation (no posting, not logged as a post).

    Useful to preview exactly what the Prophet will produce before
    enabling a platform or adjusting prompts. Available even when the
    kill-switch is active (admin-only, read-only for external services).
    """
    if payload.content_type not in VALID_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"invalid content_type — expected one of {sorted(VALID_CONTENT_TYPES)}",
        )
    if payload.platform not in PLATFORM_CHAR_BUDGETS:
        raise HTTPException(
            status_code=400,
            detail=f"invalid platform — expected one of {sorted(PLATFORM_CHAR_BUDGETS.keys())}",
        )
    if payload.content_type == "kol_reply" and not payload.kol_post:
        raise HTTPException(
            status_code=400,
            detail="kol_reply requires a non-empty 'kol_post' field",
        )
    try:
        # Compose `extra_context` from 3 optional sources (in priority order):
        #   1. The admin's manual `keywords` (always wins — explicit signal)
        #   2. The admin's free-form `extra_context` text
        #   3. The freshest geopolitics/macro headlines (when use_news_context=True)
        composed_context_parts: List[str] = []
        if payload.keywords:
            cleaned_kw = [k.strip() for k in payload.keywords if (k or "").strip()]
            if cleaned_kw:
                composed_context_parts.append(
                    "Spark inspiration KEYWORDS — riff loosely on at least one of these "
                    "(do not list them verbatim, weave them into the post): "
                    + ", ".join(cleaned_kw)
                )
        if payload.extra_context:
            composed_context_parts.append(payload.extra_context.strip())
        if payload.use_news_context:
            news_block = await build_news_context_block(n=5)
            if news_block:
                composed_context_parts.append(news_block)

        composed_context = (
            "\n\n".join(composed_context_parts)
            if composed_context_parts
            else None
        )

        result = await generate_post(
            content_type=payload.content_type,
            platform=payload.platform,
            kol_post=payload.kol_post,
            extra_context=composed_context,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Optional image generation — failure is non-fatal for text preview.
    image_payload: Optional[GeneratedImage] = None
    image_error: Optional[str] = None
    if payload.include_image:
        try:
            img = await generate_image(
                content_type=payload.content_type,
                aspect_ratio=payload.image_aspect_ratio,
                text_hint=result.get("content_en"),
            )
            image_payload = GeneratedImage(
                content_type=img["content_type"],
                aspect_ratio=img["aspect_ratio"],
                provider=img["provider"],
                model=img["model"],
                mime_type=img["mime_type"],
                image_base64=img["image_base64"],
                size_bytes=img["size_bytes"],
            )
        except ValueError as exc:
            image_error = f"invalid_image_request: {exc}"
        except RuntimeError as exc:
            image_error = str(exc)

    return GeneratePreviewResponse(
        **result,
        image=image_payload,
        image_error=image_error,
    )


# ---------------------------------------------------------------------
# News feed — geopolitics / macro RSS aggregator (for X bot inspiration)
# ---------------------------------------------------------------------
class NewsItemModel(BaseModel):
    id: str
    title: str
    summary: str
    url: str
    source: str
    published_raw: str
    fetched_at: str


class NewsListResponse(BaseModel):
    items: List[NewsItemModel]
    last_refresh_at: Optional[str] = None
    last_refresh_stats: Optional[Dict[str, Any]] = None


class NewsRefreshResponse(BaseModel):
    fetched: int
    kept: int
    added: int
    feeds: int
    ts: str


@router.get("/news", response_model=NewsListResponse)
async def list_news_items(
    hours: int = Query(default=48, ge=1, le=168),
    limit: int = Query(default=30, ge=1, le=100),
    _p: dict = Depends(require_admin),
):
    """Return the most recent kept geopolitics / macro headlines.

    Used by the AdminBots dashboard to preview what the Prophet would
    have access to as inspiration for its next post.
    """
    items = await get_recent_items(hours=hours, limit=limit)
    cfg = await get_bot_config()
    nf = cfg.get("news_feed") or {}
    return NewsListResponse(
        items=[NewsItemModel(**it) for it in items],
        last_refresh_at=nf.get("last_refresh_at"),
        last_refresh_stats=nf.get("last_refresh_stats"),
    )


@router.post("/news/refresh", response_model=NewsRefreshResponse)
async def trigger_news_refresh(_p: dict = Depends(require_admin)):
    """Manually trigger an immediate RSS refresh.

    Uses the configured feeds + keywords (or curated defaults when
    those are empty). Updates `news_feed.last_refresh_*` on the
    bot_config doc so the UI can show the fresh stats.
    """
    cfg = await get_bot_config()
    nf = cfg.get("news_feed") or {}
    feeds = nf.get("feeds") or None
    keywords = nf.get("keywords") or None
    stats = await refresh_all(urls=feeds, keywords=keywords)

    from datetime import datetime, timezone

    now_iso = datetime.now(timezone.utc).isoformat()
    await db["bot_config"].update_one(
        {"_id": "bot_config_singleton"},
        {
            "$set": {
                "news_feed.last_refresh_at": now_iso,
                "news_feed.last_refresh_stats": stats,
            }
        },
    )
    return NewsRefreshResponse(**stats)
