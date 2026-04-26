"""APScheduler-based async scheduler for the $DEEPOTUS bot fleet.

Phase 1 responsibilities (foundation only — no actual posting):
    - Boot an AsyncIOScheduler bound to the app's event loop.
    - Provide helpers to register/refresh/clear jobs from config.
    - Expose a global KILL-SWITCH: even if jobs trigger, they MUST no-op
      whenever `bot_config.kill_switch_active` is True.
    - Persist every run/skip in the `bot_posts` collection (audit trail).
    - Run a lightweight heartbeat job so we can observe scheduler health
      from the admin dashboard without any external integration yet.

Later phases will plug platform-specific posters (X, Telegram) into the
same `execute_job` dispatcher — without touching the scheduler code.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.config import db, logger

# ---------------------------------------------------------------------
# Mongo collection names
# ---------------------------------------------------------------------
CONFIG_COLLECTION = "bot_config"
POSTS_COLLECTION = "bot_posts"
CONFIG_SINGLETON_ID = "singleton"

# ---------------------------------------------------------------------
# Default config — created on first boot if missing
# ---------------------------------------------------------------------
DEFAULT_BOT_CONFIG: Dict[str, Any] = {
    "_id": CONFIG_SINGLETON_ID,
    "kill_switch_active": True,  # Fail safe: start paused until admin turns ON
    "platforms": {
        "x": {"enabled": False, "post_frequency_hours": 4},
        "telegram": {"enabled": False, "post_frequency_hours": 6},
    },
    "content_modes": {
        "prophecy": True,
        "market_commentary": True,
        "vault_update": True,
        "kol_reply": False,
    },
    "llm": {
        # Default: Claude Sonnet 4.5 — best satirical voice for the Prophet.
        # Swap via PUT /api/admin/bots/config with {"llm": {...}}.
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
    },
    # ---- News feed (Phase X · 4×/day RSS aggregator) ----
    # When `enabled_for.<platform>` is True and the kill switch is OFF,
    # the scheduled bot job for that platform will inject the freshest
    # geopolitics/macro headlines into the LLM prompt as inspiration.
    "news_feed": {
        "enabled_for": {"x": True, "telegram": False},
        "fetch_interval_hours": 6,  # 4×/jour (00, 06, 12, 18 UTC)
        "feeds": [],   # falls back to DEFAULT_NEWS_FEEDS when empty
        "keywords": [],  # falls back to DEFAULT_NEWS_KEYWORDS when empty
        "headlines_per_post": 5,
        "last_refresh_at": None,
        "last_refresh_stats": None,
    },
    # ---- Loyalty narrative (Sprint 3 + Sprint 4) ----
    # When enabled, the prophet studio injects a tier-aware hint into the
    # LLM prompt so social posts gradually escalate the "stay-loyal"
    # signal as the Vault fills. Email-side toggle is wired in Sprint 4.
    "loyalty": {
        "hints_enabled": False,
        "email_enabled": False,
        "email_delay_hours": 12,
    },
    # ---- News repost (auto-relay top RSS headlines) ----
    "news_repost": {
        "enabled_for": {"x": False, "telegram": False},
        "interval_minutes": 30,
        "delay_after_refresh_minutes": 5,
        "wait_after_prophet_post_minutes": 2,
        "daily_cap": 10,
        "prefix_fr": "⚡ INTERCEPTÉ ·",
        "prefix_en": "⚡ INTERCEPT ·",
    },
    "heartbeat_interval_minutes": 5,
    "max_posts_per_day": 12,
    "last_updated_at": None,
    "updated_by": None,
    "created_at": datetime.now(timezone.utc).isoformat(),
}

# Singleton scheduler instance (created on startup)
_scheduler: Optional[AsyncIOScheduler] = None


# ---------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------
async def ensure_bot_config() -> Dict[str, Any]:
    """Return the bot config doc, creating it from defaults if absent."""
    doc = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_SINGLETON_ID})
    if doc is None:
        doc = dict(DEFAULT_BOT_CONFIG)
        await db[CONFIG_COLLECTION].insert_one(doc)
        logger.info("[bot_scheduler] bot_config initialized with safe defaults (kill-switch ON).")
    return doc


async def get_bot_config() -> Dict[str, Any]:
    """Fast read of current bot config (raises only if Mongo is down)."""
    doc = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_SINGLETON_ID})
    return doc or await ensure_bot_config()


async def update_bot_config(patch: Dict[str, Any], updated_by: str = "admin") -> Dict[str, Any]:
    """Shallow-merge patch into the config doc, stamp metadata, refresh jobs."""
    # Whitelist of keys we allow to be updated via the admin endpoint.
    allowed_top = {
        "kill_switch_active",
        "platforms",
        "content_modes",
        "llm",
        "news_feed",
        "loyalty",
        "news_repost",
        "heartbeat_interval_minutes",
        "max_posts_per_day",
    }
    update: Dict[str, Any] = {}
    for key, value in (patch or {}).items():
        if key in allowed_top:
            update[key] = value

    if not update:
        return await get_bot_config()

    update["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = updated_by

    await db[CONFIG_COLLECTION].update_one(
        {"_id": CONFIG_SINGLETON_ID},
        {"$set": update},
        upsert=True,
    )

    # Reconfigure live jobs based on the new config.
    await sync_jobs_from_config()
    return await get_bot_config()


# ---------------------------------------------------------------------
# Post audit trail
# ---------------------------------------------------------------------
async def log_post_attempt(
    *,
    platform: str,
    content_type: str,
    status: str,
    content: Optional[str] = None,
    error: Optional[str] = None,
    external_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Persist a single attempt (posted / skipped / killed / failed)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    doc = {
        "_id": str(uuid.uuid4()),
        "platform": platform,
        "content_type": content_type,
        "status": status,  # posted | killed | skipped | failed | heartbeat
        "content": (content or "")[:2000],
        "error": error,
        "external_id": external_id,
        "extra": extra or {},
        "created_at": now_iso,
    }
    await db[POSTS_COLLECTION].insert_one(doc)
    return doc["_id"]


# ---------------------------------------------------------------------
# Job execution — all jobs funnel through this guard
# ---------------------------------------------------------------------
async def _run_guarded(platform: str, content_type: str, fn) -> None:
    """Kill-switch aware wrapper. Every job MUST be dispatched via this.

    If the kill-switch is active, we log a `killed` entry and skip the
    real work entirely. This is intentionally defensive — even if the
    sync layer lags, the runtime guard holds.
    """
    try:
        cfg = await get_bot_config()
    except Exception as exc:
        logging.exception("[bot_scheduler] failed to read bot_config — hard-stopping job")
        await log_post_attempt(
            platform=platform,
            content_type=content_type,
            status="failed",
            error=f"config_read_error: {exc}",
        )
        return

    if cfg.get("kill_switch_active"):
        await log_post_attempt(
            platform=platform,
            content_type=content_type,
            status="killed",
            error="kill_switch_active",
        )
        return

    platform_cfg = (cfg.get("platforms") or {}).get(platform) or {}
    if platform != "system" and not platform_cfg.get("enabled"):
        await log_post_attempt(
            platform=platform,
            content_type=content_type,
            status="skipped",
            error="platform_disabled",
        )
        return

    try:
        await fn()
    except Exception as exc:
        logging.exception("[bot_scheduler] job failure platform=%s type=%s", platform, content_type)
        await log_post_attempt(
            platform=platform,
            content_type=content_type,
            status="failed",
            error=str(exc)[:500],
        )


# ---------------------------------------------------------------------
# Phase 1 built-in jobs
# ---------------------------------------------------------------------
async def _heartbeat_job() -> None:
    """Tick every N minutes so we can see the scheduler is alive."""
    async def _work():
        await log_post_attempt(
            platform="system",
            content_type="heartbeat",
            status="heartbeat",
            content="scheduler OK",
        )

    await _run_guarded(platform="system", content_type="heartbeat", fn=_work)


async def _news_refresh_job() -> None:
    """Refresh the geopolitics / macro RSS aggregator on a cron schedule.

    Runs unconditionally (i.e. NOT gated by the kill-switch) — we want
    the feed corpus to keep being maintained even when the bot is
    paused, so that the admin can trigger a Preview at any time and
    have fresh inspiration ready. The kill-switch only stops *posts*.
    """
    # Local import — avoids creating a hard import-time dependency on
    # feedparser when the scheduler module is imported in tests.
    from core.news_feed import refresh_all  # noqa: WPS433

    cfg = await get_bot_config()
    nf = cfg.get("news_feed") or {}
    feeds = nf.get("feeds") or None  # None → use DEFAULT_NEWS_FEEDS
    keywords = nf.get("keywords") or None  # None → use DEFAULT_NEWS_KEYWORDS

    try:
        stats = await refresh_all(urls=feeds, keywords=keywords)
    except Exception as exc:  # noqa: BLE001
        logging.exception("[bot_scheduler] news refresh failed")
        stats = {"error": str(exc)[:300]}

    await db[CONFIG_COLLECTION].update_one(
        {"_id": CONFIG_SINGLETON_ID},
        {
            "$set": {
                "news_feed.last_refresh_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "news_feed.last_refresh_stats": stats,
            }
        },
    )


async def _loyalty_email_job() -> None:
    """Trigger the loyalty-email tick (Sprint 4).

    Runs every 30 min. Internally checks `bot_config.loyalty.email_enabled`
    and the `email_delay_hours` window before doing anything — so toggling
    it off in the admin panel pauses dispatch within minutes.

    NOT gated by the kill-switch: loyalty emails are transactional, not
    promotional. The kill-switch stops bot *posts*, not user-bound emails.
    """
    from core.loyalty_email import loyalty_email_tick  # noqa: WPS433

    try:
        summary = await loyalty_email_tick()
        if summary.get("sent") or summary.get("failed"):
            await db[CONFIG_COLLECTION].update_one(
                {"_id": CONFIG_SINGLETON_ID},
                {
                    "$set": {
                        "loyalty.last_run_at": datetime.now(timezone.utc).isoformat(),
                        "loyalty.last_run_summary": {
                            "sent": summary.get("sent", 0),
                            "skipped": summary.get("skipped", 0),
                            "failed": summary.get("failed", 0),
                        },
                    }
                },
            )
    except Exception:
        logging.exception("[bot_scheduler] loyalty email tick failed")


async def _news_repost_job() -> None:
    """Trigger the news-repost tick.

    Runs every 5 min. Internally honours kill_switch + per-platform
    toggles + interval gating + dedup + daily cap. When neither X nor
    Telegram is enabled, this is a no-op.
    """
    from core.news_repost import news_repost_tick  # noqa: WPS433

    try:
        summary = await news_repost_tick()
        # Persist a small breadcrumb on the singleton so the admin can
        # inspect when the last tick fired and what it produced.
        await db[CONFIG_COLLECTION].update_one(
            {"_id": CONFIG_SINGLETON_ID},
            {
                "$set": {
                    "news_repost.last_run_at": datetime.now(timezone.utc).isoformat(),
                    "news_repost.last_run_summary": {
                        "skipped": summary.get("skipped"),
                        "results": [
                            {
                                "platform": r.get("platform"),
                                "status": r.get("status"),
                            }
                            for r in (summary.get("results") or [])
                        ],
                    },
                }
            },
        )
    except Exception:
        logging.exception("[bot_scheduler] news repost tick failed")


# ---------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------
async def sync_jobs_from_config() -> None:
    """Reconcile APScheduler jobs with the current config doc.

    Registers the heartbeat plus the news-feed refresh cron. Platform
    posting jobs are still done elsewhere; this function is the single
    source of truth for *system-level* jobs.
    """
    if _scheduler is None:
        return
    cfg = await get_bot_config()

    hb_minutes = max(1, int(cfg.get("heartbeat_interval_minutes") or 5))

    if _scheduler.get_job("heartbeat"):
        _scheduler.reschedule_job(
            "heartbeat",
            trigger=IntervalTrigger(minutes=hb_minutes),
        )
    else:
        _scheduler.add_job(
            _heartbeat_job,
            trigger=IntervalTrigger(minutes=hb_minutes),
            id="heartbeat",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # ---- News-feed refresh job (4×/day by default) ----
    nf_hours = max(
        1,
        int(((cfg.get("news_feed") or {}).get("fetch_interval_hours")) or 6),
    )
    if _scheduler.get_job("news_refresh"):
        _scheduler.reschedule_job(
            "news_refresh",
            trigger=IntervalTrigger(hours=nf_hours),
        )
    else:
        _scheduler.add_job(
            _news_refresh_job,
            trigger=IntervalTrigger(hours=nf_hours),
            id="news_refresh",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # ---- Loyalty email tick (Sprint 4) — every 30 min ----
    if _scheduler.get_job("loyalty_email"):
        _scheduler.reschedule_job(
            "loyalty_email",
            trigger=IntervalTrigger(minutes=30),
        )
    else:
        _scheduler.add_job(
            _loyalty_email_job,
            trigger=IntervalTrigger(minutes=30),
            id="loyalty_email",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # ---- News repost tick — every 5 min (rate-gated internally) ----
    if _scheduler.get_job("news_repost"):
        _scheduler.reschedule_job(
            "news_repost",
            trigger=IntervalTrigger(minutes=5),
        )
    else:
        _scheduler.add_job(
            _news_repost_job,
            trigger=IntervalTrigger(minutes=5),
            id="news_repost",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )


async def start_scheduler() -> AsyncIOScheduler:
    """Boot the scheduler and attach Phase-1 jobs."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    await ensure_bot_config()

    # Run in the current asyncio loop
    _scheduler = AsyncIOScheduler(
        timezone="UTC",
        event_loop=asyncio.get_event_loop(),
    )
    await sync_jobs_from_config()
    _scheduler.start()
    logger.info("[bot_scheduler] AsyncIOScheduler started (Phase 1 — heartbeat only).")
    return _scheduler


async def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[bot_scheduler] scheduler shut down.")
    _scheduler = None


def get_scheduler() -> Optional[AsyncIOScheduler]:
    return _scheduler


def describe_jobs() -> list[Dict[str, Any]]:
    """Return a JSON-safe snapshot of currently registered jobs."""
    if _scheduler is None:
        return []
    out: list[Dict[str, Any]] = []
    for job in _scheduler.get_jobs():
        trig = str(job.trigger)
        out.append(
            {
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": trig,
                "max_instances": job.max_instances,
                "coalesce": job.coalesce,
            }
        )
    return out
