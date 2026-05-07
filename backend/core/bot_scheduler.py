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

from core.bot_config_repo import (
    ALLOWED_PATCH_KEYS,
    CONFIG_COLLECTION,
    CONFIG_SINGLETON_ID,
    DEFAULT_BOT_CONFIG,
    POSTS_COLLECTION,
    ensure_bot_config,
    get_bot_config,
    persist_bot_config_patch,
)
from core.config import db, logger

# Re-export for backward compat — older callers may have imported these
# names from this module before the bot_config_repo split.
__all__ = [
    "ALLOWED_PATCH_KEYS",
    "CONFIG_COLLECTION",
    "CONFIG_SINGLETON_ID",
    "DEFAULT_BOT_CONFIG",
    "POSTS_COLLECTION",
    "ensure_bot_config",
    "force_run_all_now",
    "get_bot_config",
    "update_bot_config",
    "log_post_attempt",
    "sync_jobs_from_config",
    "start_scheduler",
    "shutdown_scheduler",
    "get_scheduler",
    "describe_jobs",
]

# ---------------------------------------------------------------------
# Default config + read helpers + persist helper now live in
# `core/bot_config_repo.py` (extracted to break the circular import
# between this module and its consumers — loyalty_email, news_repost,
# news_feed, prophet_studio).
#
# We keep `update_bot_config` here because it is the ONLY config-write
# path that must trigger `sync_jobs_from_config()` afterwards (changing
# news_feed.fetch_interval_hours, for instance, must reschedule the
# corresponding APScheduler job). Routers should always call
# `update_bot_config` rather than `persist_bot_config_patch` directly.
# ---------------------------------------------------------------------

# Singleton scheduler instance (created on startup)
_scheduler: Optional[AsyncIOScheduler] = None


async def update_bot_config(
    patch: Dict[str, Any],
    updated_by: str = "admin",
) -> Dict[str, Any]:
    """Persist a partial config patch *and* refresh live scheduler jobs."""
    await persist_bot_config_patch(patch, updated_by=updated_by)
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


async def _whale_watcher_job() -> None:
    """Drain pending whale alerts (Sprint 15.2).

    Runs every 5 s with `max_instances=1, coalesce=True` so two ticks
    can never overlap. Each tick processes at most ONE alert which
    keeps the propaganda dispatcher rate-limit (X / Telegram) under
    control during whale-burst events.

    NOT gated by the bot kill-switch: the whale watcher is read-only
    (it observes on-chain activity and feeds the propaganda *queue*,
    which has its own panic switch).
    """
    from core.whale_watcher import process_pending_alerts  # noqa: WPS433

    try:
        await process_pending_alerts(limit=1)
    except Exception:
        logging.exception("[bot_scheduler] whale watcher tick failed")


async def _kol_listener_job() -> None:
    """Drain pending KOL mentions + (future) poll X API (Sprint 16.4).

    Runs every 5 minutes. The polling half is currently a TODO — see
    ``core.kol_listener.poll_x_api_once``. The drain half always runs
    so an admin who simulates a mention sees it land in the propaganda
    queue within one tick, regardless of whether real polling is
    enabled.
    """
    from core.kol_listener import poll_x_api_once  # noqa: WPS433

    try:
        await poll_x_api_once()
    except Exception:
        logging.exception("[bot_scheduler] kol listener tick failed")


async def _cadence_tick_job() -> None:
    """Run the Sprint-19 cadence engine tick (daily + reactive).

    Runs every 60 s. Internally honours kill-switch + quiet hours +
    per-platform enabled toggles + per-day / per-milestone dedup, so
    flipping `cadence.daily_schedule.x.enabled` off in the admin
    dashboard pauses the daily slots within ~1 minute without any
    rescheduling on our side.

    Decoupled from `_run_guarded` because cadence is platform-agnostic
    (it pushes into the propaganda queue; the dispatch worker is what
    eventually calls X / Telegram and is itself kill-switch-aware).
    """
    from core.cadence_engine import cadence_combined_tick  # noqa: WPS433

    try:
        await cadence_combined_tick()
    except Exception:
        logging.exception("[bot_scheduler] cadence tick failed")


async def _holders_poll_job() -> None:
    """Refresh the live holders count for the $DEEPOTUS mint.

    Sprint-19.1 — feeds ``vault_state.dex_holders_count``, which the
    cadence reactive tick reads to fire holder-milestone posts. Runs
    every ``POLL_INTERVAL_SECONDS`` (5 minutes by default). Holders
    move slowly relative to trades, so this cadence is a sweet spot
    between freshness and Helius RPC budget.

    Skipped silently when no mint is configured yet (pre-mint state).
    """
    from core.holders_poller import poll_holders_once  # noqa: WPS433

    try:
        await poll_holders_once()
    except Exception:
        logging.exception("[bot_scheduler] holders poll tick failed")


async def _welcome_signal_job() -> None:
    """Sprint 17.5 — daily Cabinet recognition broadcast.

    Runs every 30 min so a slight desync (DST, container restart) still
    fires within the configured ``hour_utc`` window. The 23h cooldown
    inside ``welcome_signal.fire`` keeps double-fires impossible.

    NOT gated by the bot kill-switch: this is a pre-launch growth signal,
    not a trading bot. The propaganda kill-switch (``panic``) and the
    dispatcher's own ``dispatch_enabled`` toggle still apply downstream.
    """
    from core import welcome_signal  # noqa: WPS433

    try:
        await welcome_signal.tick()
    except Exception:
        logging.exception("[bot_scheduler] welcome signal tick failed")


async def _prophet_interaction_job() -> None:
    """Sprint 17.5 — hourly Lore-compliant replies to accredited followers.

    The job reads ``propaganda_settings.interaction_bot.enabled`` on
    every tick and short-circuits when off, so flipping the toggle in
    the admin dashboard pauses the bot within the next hour. The
    dispatcher's panic + dispatch_enabled toggles also apply.
    """
    from core import prophet_interaction  # noqa: WPS433

    try:
        await prophet_interaction.tick()
    except Exception:
        logging.exception("[bot_scheduler] prophet interaction tick failed")


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

    # ---- Whale watcher tick (Sprint 15.2) — every 5 s, isolated ----
    # Drains the `whale_alerts` queue ONE row per tick so the
    # propaganda dispatcher (Telegram, X) is never asked to fire 30
    # messages in a single second when a viral candle hits.
    # `coalesce=True` collapses missed ticks (e.g. after a brief
    # process pause) into a single make-up run instead of replaying
    # the backlog and bursting the rate-limit.
    if _scheduler.get_job("whale_watcher"):
        _scheduler.reschedule_job(
            "whale_watcher",
            trigger=IntervalTrigger(seconds=5),
        )
    else:
        _scheduler.add_job(
            _whale_watcher_job,
            trigger=IntervalTrigger(seconds=5),
            id="whale_watcher",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )

    # ---- KOL listener tick (Sprint 16.4) — every 5 min ----
    # Drains kol_mentions queue + (future) polls X API for new
    # mentions. The `enabled` toggle gates the polling half; the
    # drain half always runs so admin simulates always reach the
    # propaganda queue. `max_instances=1` to guarantee no overlap on
    # slow X API responses.
    if _scheduler.get_job("kol_listener"):
        _scheduler.reschedule_job(
            "kol_listener",
            trigger=IntervalTrigger(minutes=5),
        )
    else:
        _scheduler.add_job(
            _kol_listener_job,
            trigger=IntervalTrigger(minutes=5),
            id="kol_listener",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120,
        )

    # ---- Propaganda dispatch worker (Sprint 13.3) ----
    # Drains the propaganda_queue every DISPATCH_TICK_SECONDS. The
    # worker is ALWAYS scheduled but reads propaganda_settings on
    # each tick to decide whether to no-op (panic / dispatch_enabled
    # / dispatch_dry_run). This decouples the worker lifecycle from
    # the bot_config toggles owned by the older bot fleet.
    from core.dispatch_worker import DISPATCH_TICK_SECONDS, tick_async

    _scheduler.add_job(
        tick_async,
        trigger=IntervalTrigger(seconds=DISPATCH_TICK_SECONDS),
        id="propaganda_dispatch",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    # ---- Cadence engine tick (Sprint 19) ----
    # Runs every 60 s and pushes V2 posts into the propaganda queue
    # when the configured daily slots fire OR when holder/marketcap
    # milestones are crossed. The job is unconditionally scheduled —
    # the engine itself reads `bot_config.cadence` on every tick and
    # short-circuits when nothing is enabled, so no rescheduling is
    # required when the admin flips toggles.
    if _scheduler.get_job("cadence_tick"):
        _scheduler.reschedule_job(
            "cadence_tick",
            trigger=IntervalTrigger(seconds=60),
        )
    else:
        _scheduler.add_job(
            _cadence_tick_job,
            trigger=IntervalTrigger(seconds=60),
            id="cadence_tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )

    # ---- Holders poller (Sprint 19.1) ----
    # Feeds `vault_state.dex_holders_count` so the cadence reactive
    # tick can fire holder-milestone posts. Helius DAS getTokenAccounts
    # is the primary source; the job no-ops (with an info log) until
    # the mint address is set on the vault state, so it's safe to run
    # in pre-mint preview mode.
    from core.holders_poller import POLL_INTERVAL_SECONDS as _HOLDERS_INTERVAL

    if _scheduler.get_job("holders_poll"):
        _scheduler.reschedule_job(
            "holders_poll",
            trigger=IntervalTrigger(seconds=_HOLDERS_INTERVAL),
        )
    else:
        _scheduler.add_job(
            _holders_poll_job,
            trigger=IntervalTrigger(seconds=_HOLDERS_INTERVAL),
            id="holders_poll",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )

    # ---- Welcome Signal (Sprint 17.5) — every 30 min ----
    # The job itself reads ``propaganda_settings.welcome_signal.hour_utc``
    # and short-circuits unless the current UTC hour matches; a 23h
    # cooldown inside ``welcome_signal.fire`` prevents double-fires.
    if _scheduler.get_job("welcome_signal"):
        _scheduler.reschedule_job(
            "welcome_signal",
            trigger=IntervalTrigger(minutes=30),
        )
    else:
        _scheduler.add_job(
            _welcome_signal_job,
            trigger=IntervalTrigger(minutes=30),
            id="welcome_signal",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600,
        )

    # ---- Prophet Interaction Bot (Sprint 17.5) — every 60 min ----
    # 1-3 random replies per tick (config-driven). The bot is OFF by
    # default; admin enables it explicitly once X creds are vaulted.
    if _scheduler.get_job("prophet_interaction"):
        _scheduler.reschedule_job(
            "prophet_interaction",
            trigger=IntervalTrigger(minutes=60),
        )
    else:
        _scheduler.add_job(
            _prophet_interaction_job,
            trigger=IntervalTrigger(minutes=60),
            id="prophet_interaction",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600,
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



async def force_run_all_now(*, skip_when_killed: bool = False) -> Dict[str, list]:
    """Force every registered job to fire on the next scheduler loop.

    Implementation: APScheduler exposes ``modify_job(next_run_time=...)``
    which reschedules the next firing without altering the underlying
    trigger. We set ``next_run_time = utcnow()`` so the scheduler's main
    loop (`_run_jobs`) picks it up within its tick interval (~1s).

    Sprint 17.5 follow-up — backs the admin "Release" button which now
    serves a dual purpose:
        * when the kill-switch is armed → the existing PUT
          /kill-switch path releases it,
        * when bots are live → this path forces every cadence /
          background job to run immediately so the operator can verify
          end-to-end before the next scheduled tick.

    Args:
        skip_when_killed: When True, return an empty triggered list and
            stamp every job under ``skipped`` so the UI can render a
            "kill-switch active" toast without changing scheduler state.

    Returns:
        ``{"triggered": [...], "skipped": [...]}`` — each entry carries
        ``{"id", "next_run_time"}`` for the operator dashboard.
    """
    triggered: list[Dict[str, Any]] = []
    skipped: list[Dict[str, Any]] = []

    if _scheduler is None:
        return {"triggered": triggered, "skipped": skipped}

    now = datetime.now(timezone.utc)
    for job in _scheduler.get_jobs():
        if skip_when_killed:
            skipped.append({
                "id": job.id,
                "reason": "kill_switch_active",
                "next_run_time": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
            })
            continue
        try:
            _scheduler.modify_job(job.id, next_run_time=now)
            triggered.append({
                "id": job.id,
                "forced_at": now.isoformat(),
            })
        except Exception:  # noqa: BLE001
            logging.exception(
                "[bot_scheduler.force_run_all_now] could not modify job=%s",
                job.id,
            )
            skipped.append({
                "id": job.id,
                "reason": "modify_failed",
            })
    return {"triggered": triggered, "skipped": skipped}
