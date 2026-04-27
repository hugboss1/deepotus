"""News repost engine — auto-relay top RSS headlines to X & Telegram.

Concept (validated by user):
    - The Prophet bot keeps generating LLM commentary inspired by news on
      its OWN cadence (existing `prophet_studio.generate_post`).
    - This module RUNS IN PARALLEL and reposts the *raw* top kept headlines
      from the news_feed cache, prefixed with "⚡ INTERCEPTÉ ·" / "⚡
      INTERCEPT ·", at a configurable interval. No LLM calls, no editorial.
    - Dedup ensures the same link is never reposted on the same platform.
    - Daily cap prevents flooding (default 10).
    - "Wait for Prophet": if the Prophet has just posted in the last
      `wait_after_prophet_post_minutes` minutes, the repost tick yields
      and retries on the next scheduler firing.

Dispatch modes:
    - "real":     Telegram or X dispatcher available (creds present)
    - "dry_run":  no creds → we still log what WOULD be sent so the admin
                  can see the queue building up. When credentials arrive,
                  flip the platform toggle and the next tick sends real.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.bot_config_repo import get_bot_config
from core.config import db, logger

REPOSTS_COLLECTION = "news_reposts"
NEWS_COLLECTION = "news_items"
BOT_POSTS_COLLECTION = "bot_posts"

# --- Defaults (also injected into bot_config when missing) ---
DEFAULT_NEWS_REPOST_CONFIG: Dict[str, Any] = {
    "enabled_for": {"x": False, "telegram": False},
    "interval_minutes": 30,
    "delay_after_refresh_minutes": 5,
    "wait_after_prophet_post_minutes": 2,
    "daily_cap": 10,
    "prefix_fr": "⚡ INTERCEPTÉ ·",
    "prefix_en": "⚡ INTERCEPT ·",
}

# Maximum chars per platform (we leave a safety buffer).
PLATFORM_LIMITS = {
    "x": 270,
    "telegram": 1024,
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _link_hash(link: str) -> str:
    """Stable identifier for dedup, independent of platform."""
    h = hashlib.sha1()
    h.update((link or "").strip().lower().encode("utf-8", errors="ignore"))
    return h.hexdigest()[:16]


def _config() -> Dict[str, Any]:
    """Sync helper not used directly — see _resolve_config below."""
    return DEFAULT_NEWS_REPOST_CONFIG


async def _resolve_config() -> Dict[str, Any]:
    """Merge defaults with the live bot_config.news_repost block."""
    cfg = await get_bot_config()
    rp = (cfg.get("news_repost") or {}) if isinstance(cfg, dict) else {}
    merged: Dict[str, Any] = {**DEFAULT_NEWS_REPOST_CONFIG, **rp}
    # Nested merge for enabled_for so partial patches don't blow it away.
    enabled = {**DEFAULT_NEWS_REPOST_CONFIG["enabled_for"], **(rp.get("enabled_for") or {})}
    merged["enabled_for"] = enabled
    return merged


def _platform_creds_present(platform: str) -> bool:
    """Whether the dispatcher *could* actually post to this platform.

    Phases 3/4/5 are not implemented yet — the env vars below are
    placeholders. Until they exist, every dispatch falls back to dry_run.
    """
    if platform == "telegram":
        return bool(
            os.environ.get("TELEGRAM_BOT_TOKEN")
            and os.environ.get("TELEGRAM_CHAT_ID"),
        )
    if platform == "x":
        return bool(
            os.environ.get("TWITTER_BEARER_TOKEN")
            or os.environ.get("X_API_KEY"),
        )
    return False


def _truncate(text: str, max_len: int) -> str:
    text = text or ""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return "…"
    return text[: max_len - 1].rstrip() + "…"


# ---------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------
def format_repost(
    *,
    item: Dict[str, Any],
    platform: str,
    prefix: str,
) -> str:
    """Build the final repost text for a given platform.

    Plain-text for X (URL is auto-shortened by the platform), Markdown
    light for Telegram (with a clickable [Source →] link).
    """
    title = (item.get("title") or "").strip()
    url = (item.get("url") or "").strip()
    source = (item.get("source") or "").strip()

    if platform == "telegram":
        # Telegram supports Markdown; keep title plain to avoid bracket
        # collisions with [link](url).
        head = f"{prefix} *{source}*" if source else prefix
        body = title
        link = f"\n[Source →]({url})" if url else ""
        return _truncate(f"{head}\n{body}{link}", PLATFORM_LIMITS["telegram"])

    # X: hard 280 cap; we budget URL = ~24 chars (X t.co), prefix+source
    # variable, body fills the rest. We fit in PLATFORM_LIMITS['x']=270.
    head = f"{prefix} {source}".strip() if source else prefix
    url_part = f"\n🔗 {url}" if url else ""
    head_with_break = f"{head}\n" if head else ""
    static_len = len(head_with_break) + len(url_part)
    body_budget = max(60, PLATFORM_LIMITS["x"] - static_len)
    body = _truncate(title, body_budget)
    return f"{head_with_break}{body}{url_part}"


# ---------------------------------------------------------------------
# State queries
# ---------------------------------------------------------------------
async def _was_already_reposted(link: str, platform: str) -> bool:
    """Has this link already been processed (sent or dry_run) on this platform?"""
    if not link:
        return False
    doc = await db[REPOSTS_COLLECTION].find_one(
        {"link_hash": _link_hash(link), "platform": platform}
    )
    return doc is not None


async def _count_today(platform: str) -> int:
    """Count reposts dispatched today (UTC) for this platform — counts both
    real sends and dry_run entries so the cap behaves consistently."""
    midnight = _now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
    return await db[REPOSTS_COLLECTION].count_documents(
        {"platform": platform, "posted_at": {"$gte": midnight.isoformat()}}
    )


async def _last_repost_at(platform: str) -> Optional[datetime]:
    last = await db[REPOSTS_COLLECTION].find_one(
        {"platform": platform},
        sort=[("posted_at", -1)],
    )
    if not last:
        return None
    raw = last.get("posted_at")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


async def _last_prophet_post_at() -> Optional[datetime]:
    """When did the Prophet last post (any platform)?

    We treat ANY persisted bot_post as a Prophet output. If a generated
    post is not yet dispatched ('preview' only), we still skip — it's a
    safe over-estimation that never causes a missed window (the next tick
    fires 5 min later).
    """
    last = await db[BOT_POSTS_COLLECTION].find_one(
        {},
        sort=[("created_at", -1)],
    )
    if not last:
        return None
    raw = last.get("created_at") or last.get("dispatched_at")
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


async def _pick_candidate(platform: str, limit: int = 5) -> Optional[Dict[str, Any]]:
    """Pick the most recent kept news item that hasn't been reposted yet
    on this platform. Picks from the top-`limit` (default 5) latest kept
    headlines, matching the user's "top 5" wording.
    """
    cursor = (
        db[NEWS_COLLECTION]
        .find({"url": {"$exists": True, "$ne": ""}})
        .sort("kept_at", -1)
        .limit(limit)
    )
    candidates = [doc async for doc in cursor]
    if not candidates:
        # Some news_items docs may not have kept_at — fallback on _id order
        cursor = (
            db[NEWS_COLLECTION]
            .find({"url": {"$exists": True, "$ne": ""}})
            .sort("_id", -1)
            .limit(limit)
        )
        candidates = [doc async for doc in cursor]
    for doc in candidates:
        if not await _was_already_reposted(doc.get("url", ""), platform):
            return doc
    return None


# ---------------------------------------------------------------------
# Dispatchers (real + dry_run)
# ---------------------------------------------------------------------
async def _dispatch_telegram(text: str) -> Dict[str, Any]:
    """Real Telegram dispatch — currently stubbed (Phase 3 not shipped).

    When TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID are present, this is the
    place to call the Bot API. Returning a non-empty `id` triggers a
    'sent' status; returning {} downgrades to dry_run.
    """
    if not await _platform_creds_present("telegram"):
        return {}
    # Phase 3: import + call telegram bot API here.
    # For now we never actually reach this branch.
    return {}


async def _dispatch_x(text: str) -> Dict[str, Any]:
    """Real X dispatch — currently stubbed (Phase 4 not shipped)."""
    if not await _platform_creds_present("x"):
        return {}
    # Phase 4: tweepy OAuth2 client call.
    return {}


# ---------------------------------------------------------------------
# Send-one + tick — broken into small helpers for testability
# ---------------------------------------------------------------------
async def _check_pre_send_gates(
    *,
    item: Dict[str, Any],
    platform: str,
    cfg: Dict[str, Any],
    force: bool,
) -> Optional[Dict[str, Any]]:
    """Return a skip-status dict if the candidate must NOT be sent, else None."""
    link = (item.get("url") or "").strip()
    if not link:
        return {"status": "skipped_no_link", "platform": platform}

    if not force:
        cap = int(cfg.get("daily_cap") or 10)
        sent_today = await _count_today(platform)
        if sent_today >= cap:
            return {
                "status": "skipped_daily_cap",
                "platform": platform,
                "sent_today": sent_today,
                "cap": cap,
            }

    if await _was_already_reposted(link, platform):
        return {"status": "skipped_already_reposted", "platform": platform}

    return None


async def _do_dispatch(
    *,
    text: str,
    platform: str,
) -> Dict[str, Optional[str]]:
    """Call the platform-specific dispatcher (or no-op if no creds).

    Returns {"id": <post_id_or_None>, "error": <err_or_None>}.
    """
    if not await _platform_creds_present(platform):
        return {"id": None, "error": None}

    try:
        res = (
            await _dispatch_telegram(text)
            if platform == "telegram"
            else await _dispatch_x(text)
        )
        return {"id": (res or {}).get("id"), "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.exception("[news_repost] dispatch failed")
        return {"id": None, "error": str(exc)[:250]}


def _classify_status(*, dispatch_id: Optional[str], error: Optional[str]) -> str:
    if dispatch_id:
        return "sent"
    if error:
        return "failed"
    return "dry_run"


async def _persist_repost(
    *,
    link: str,
    platform: str,
    text: str,
    dispatch_id: Optional[str],
    error: Optional[str],
    item: Dict[str, Any],
    lang: str,
    status: str,
) -> None:
    """Insert the dedup + audit record into the news_reposts collection."""
    doc = {
        "_id": str(uuid.uuid4()),
        "link": link,
        "link_hash": _link_hash(link),
        "platform": platform,
        "posted_at": _now_utc().isoformat(),
        "post_id": dispatch_id,
        "raw_title": item.get("title", ""),
        "source": item.get("source", ""),
        "lang": lang,
        "status": status,
        "preview_text": text,
        "error": error,
    }
    await db[REPOSTS_COLLECTION].insert_one(doc)


async def _send_one(
    *,
    item: Dict[str, Any],
    platform: str,
    cfg: Dict[str, Any],
    lang: str = "fr",
    force: bool = False,
) -> Dict[str, Any]:
    """Format + dispatch (or dry_run) one repost.

    `force=True` bypasses cap + interval for admin "Test repost now".
    Dedup is ALWAYS enforced — an item already in news_reposts is never
    re-sent on the same platform.
    """
    skip = await _check_pre_send_gates(
        item=item, platform=platform, cfg=cfg, force=force,
    )
    if skip is not None:
        return skip

    link = (item.get("url") or "").strip()
    prefix = cfg.get(f"prefix_{lang}") or cfg.get("prefix_fr") or "⚡"
    text = format_repost(item=item, platform=platform, prefix=prefix)

    dispatch = await _do_dispatch(text=text, platform=platform)
    status = _classify_status(
        dispatch_id=dispatch["id"], error=dispatch["error"],
    )

    await _persist_repost(
        link=link,
        platform=platform,
        text=text,
        dispatch_id=dispatch["id"],
        error=dispatch["error"],
        item=item,
        lang=lang,
        status=status,
    )

    return {
        "status": status,
        "platform": platform,
        "post_id": dispatch["id"],
        "preview_text": text,
        "link": link,
        "title": item.get("title", ""),
        "error": dispatch["error"],
    }


# ---------------------------------------------------------------------
# Tick + per-platform helpers
# ---------------------------------------------------------------------
async def _wait_for_prophet_skip_reason(cfg: Dict[str, Any]) -> Optional[str]:
    """Return a skip-reason string if the Prophet just posted, else None."""
    wait_min = int(cfg.get("wait_after_prophet_post_minutes", 2) or 0)
    if wait_min <= 0:
        return None
    last_prophet = await _last_prophet_post_at()
    if not last_prophet:
        return None
    elapsed_min = (_now_utc() - last_prophet).total_seconds() / 60.0
    if elapsed_min < wait_min:
        return f"prophet_just_posted ({elapsed_min:.1f}<{wait_min}min)"
    return None


async def _interval_skip_reason(
    *,
    platform: str,
    interval_min: int,
) -> Optional[Dict[str, Any]]:
    """Return a skip-result dict if it's too soon to post on this platform."""
    last_at = await _last_repost_at(platform)
    if not last_at:
        return None
    elapsed_min = (_now_utc() - last_at).total_seconds() / 60.0
    if elapsed_min < interval_min:
        return {
            "platform": platform,
            "status": "skipped_interval",
            "elapsed_min": round(elapsed_min, 1),
            "interval_min": interval_min,
        }
    return None


async def _process_platform(
    *,
    platform: str,
    cfg: Dict[str, Any],
    interval_min: int,
) -> Dict[str, Any]:
    """Decide whether to post on `platform` and act on it. Always returns a
    result dict suitable for inclusion in the tick summary.
    """
    if not cfg["enabled_for"].get(platform):
        return {"platform": platform, "status": "disabled"}

    interval_skip = await _interval_skip_reason(
        platform=platform, interval_min=interval_min,
    )
    if interval_skip:
        return interval_skip

    item = await _pick_candidate(platform)
    if not item:
        return {"platform": platform, "status": "skipped_no_candidate"}

    return await _send_one(
        item=item, platform=platform, cfg=cfg, lang="fr",
    )


async def news_repost_tick() -> Dict[str, Any]:
    """Entry point called every 5 min by APScheduler.

    Applies (in order): kill_switch gate, wait-after-Prophet guard, then
    walks each platform applying interval gate, dedup, daily cap, dispatch.
    """
    cfg_top = await get_bot_config()
    if cfg_top.get("kill_switch_active", True):
        return {"ran_at": _now_utc().isoformat(), "skipped": "kill_switch"}

    cfg = await _resolve_config()
    summary: Dict[str, Any] = {
        "ran_at": _now_utc().isoformat(),
        "config": {
            "interval_minutes": cfg["interval_minutes"],
            "daily_cap": cfg["daily_cap"],
        },
        "results": [],
    }

    prophet_skip = await _wait_for_prophet_skip_reason(cfg)
    if prophet_skip:
        summary["skipped"] = prophet_skip
        return summary

    interval_min = int(cfg.get("interval_minutes") or 30)
    for platform in ("x", "telegram"):
        result = await _process_platform(
            platform=platform, cfg=cfg, interval_min=interval_min,
        )
        summary["results"].append(result)
        if result.get("status") in ("sent", "dry_run"):
            logger.info(
                "[news_repost] %s status=%s title=%s…",
                platform,
                result["status"],
                (result.get("title") or "")[:60],
            )
    return summary


async def get_news_repost_status() -> Dict[str, Any]:
    """Snapshot for the admin dashboard — counters + queue preview."""
    cfg = await _resolve_config()

    today_per_platform = {
        p: await _count_today(p) for p in ("x", "telegram")
    }
    last_per_platform: Dict[str, Optional[str]] = {}
    for p in ("x", "telegram"):
        d = await _last_repost_at(p)
        last_per_platform[p] = d.isoformat() if d else None

    # Build a 3-deep preview queue per platform — what would go out next.
    preview: Dict[str, List[Dict[str, Any]]] = {"x": [], "telegram": []}
    for platform in ("x", "telegram"):
        cursor = (
            db[NEWS_COLLECTION]
            .find({"url": {"$exists": True, "$ne": ""}})
            .sort("kept_at", -1)
            .limit(8)  # over-fetch so we can skip already-reposted items
        )
        seen = 0
        async for doc in cursor:
            url = doc.get("url", "")
            if not url:
                continue
            if await _was_already_reposted(url, platform):
                continue
            preview[platform].append(
                {
                    "title": doc.get("title", ""),
                    "source": doc.get("source", ""),
                    "url": url,
                    "preview_text": format_repost(
                        item=doc,
                        platform=platform,
                        prefix=cfg.get("prefix_fr", "⚡"),
                    ),
                }
            )
            seen += 1
            if seen >= 3:
                break

    return {
        "config": cfg,
        "credentials_present": {
            "x": await _platform_creds_present("x"),
            "telegram": await _platform_creds_present("telegram"),
        },
        "today_per_platform": today_per_platform,
        "last_per_platform": last_per_platform,
        "queue_preview": preview,
    }


async def force_repost(
    *,
    platform: str,
    lang: str = "fr",
) -> Dict[str, Any]:
    """Admin "Test repost now" — bypasses cap + interval but still respects
    dedup so we don't double-post the same headline.
    """
    cfg = await _resolve_config()
    item = await _pick_candidate(platform)
    if not item:
        return {
            "status": "skipped_no_candidate",
            "platform": platform,
            "hint": "Refresh the news feed first or wait for new headlines.",
        }
    return await _send_one(
        item=item, platform=platform, cfg=cfg, lang=lang, force=True
    )
