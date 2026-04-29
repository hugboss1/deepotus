"""Dispatch worker — drains the propaganda queue.

Drives the lifecycle ``approved → sent | failed`` for every queue
item whose ``scheduled_for`` is due. One tick = one batch. Triggered
by APScheduler at a 30-second cadence (``DISPATCH_TICK_SECONDS``).

Safety gates (in order)
-----------------------
1. **panic kill switch** — if ``propaganda_settings.panic == True``
   the worker no-ops the entire tick.
2. **dispatch_enabled** — when False the worker reads the queue but
   does NOT touch any item (useful to debug schedule logic without
   sending). Default: False (safe scaffold mode).
3. **rate limits** — propaganda_settings.rate_limits caps:
       * per_hour
       * per_day
       * per_trigger_minutes (cooldown per trigger_key)
4. **dispatch_dry_run** — when True the dispatchers short-circuit
   the HTTP call and just log. Default: True (until live creds OK'd).

Failure handling
----------------
For now we treat every dispatcher failure as terminal — item moves
to ``status=failed`` with the per-platform error stored in
``results``. The admin re-approves the original item to retry. This
keeps the scaffold simple; a retry counter + backoff is a 13.3.x
follow-up.

Idempotency
-----------
Each tick uses ``find_one_and_update`` with a status filter so two
ticks colliding on the same item are safe (the first one moves it
out of ``approved`` before the second one looks).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from core.config import db
from core.dispatchers import (
    DispatchOutcome,
    DispatchResult,
    get_dispatcher,
)

logger = logging.getLogger("deepotus.propaganda.dispatch_worker")

#: How often APScheduler invokes ``run_tick``. 30 s is short enough
#: that an admin-approved post fires within a minute, long enough not
#: to spam Mongo at idle.
DISPATCH_TICK_SECONDS = 30

#: Hard ceiling per tick to protect against a sudden flush of 1000
#: items (e.g. unkilled queue from a panic recovery). Drains
#: incrementally instead.
MAX_ITEMS_PER_TICK = 5

#: Default settings used if the propaganda_settings doc is missing
#: a key. Mirrors what the admin UI exposes.
_DEFAULT_RATE_LIMITS = {
    "per_hour": 8,
    "per_day": 24,
    "per_trigger_minutes": 15,
}


# =====================================================================
# Public API
# =====================================================================

async def run_tick() -> Dict[str, Any]:
    """Execute one drain pass. Returns a summary dict (used by the
    admin status endpoint).

    Always returns — never raises. Errors inside individual items are
    captured in their ``results`` field; errors at the worker level are
    logged and reflected in the summary.
    """
    summary: Dict[str, Any] = {
        "tick_at": _now_iso(),
        "panic": False,
        "dispatch_enabled": False,
        "dry_run": True,
        "candidates": 0,
        "rate_limited": 0,
        "dispatched": 0,
        "failed": 0,
        "errors": [],
    }
    try:
        settings = await _read_settings()
        summary["panic"] = bool(settings.get("panic", False))
        summary["dispatch_enabled"] = bool(settings.get("dispatch_enabled", False))
        summary["dry_run"] = bool(settings.get("dispatch_dry_run", True))

        if summary["panic"]:
            logger.info("[dispatch_worker] panic ON → skipping tick")
            return summary
        if not summary["dispatch_enabled"]:
            # Soft pause — no-op. We still report counts for observability.
            logger.debug("[dispatch_worker] dispatch_enabled=False → skipping")
            return summary

        rate_limits = {**_DEFAULT_RATE_LIMITS, **(settings.get("rate_limits") or {})}

        # Cap per-tick to enforce overall hourly/daily limits across multiple ticks.
        sent_last_hour = await _count_sent_within(minutes=60)
        sent_last_day = await _count_sent_within(minutes=24 * 60)
        budget_hour = max(0, int(rate_limits["per_hour"]) - sent_last_hour)
        budget_day = max(0, int(rate_limits["per_day"]) - sent_last_day)
        if budget_hour <= 0 or budget_day <= 0:
            summary["rate_limited"] = 1  # marker only — actual cap below
            logger.info(
                "[dispatch_worker] rate-limited (hour=%d/%d day=%d/%d)",
                sent_last_hour,
                rate_limits["per_hour"],
                sent_last_day,
                rate_limits["per_day"],
            )
            return summary

        per_tick_budget = min(MAX_ITEMS_PER_TICK, budget_hour, budget_day)
        candidates = await _fetch_due_items(limit=per_tick_budget)
        summary["candidates"] = len(candidates)

        if not candidates:
            return summary

        cooldown_min = int(rate_limits["per_trigger_minutes"])

        for item in candidates:
            trigger_key = item.get("trigger_key") or ""
            # Per-trigger cooldown: skip if same trigger_key was sent
            # in the last ``cooldown_min`` minutes. Keeps one trigger
            # from monopolising the channel.
            if cooldown_min > 0 and await _trigger_in_cooldown(
                trigger_key, minutes=cooldown_min
            ):
                summary["rate_limited"] += 1
                continue

            try:
                report = await _dispatch_item(item, dry_run=summary["dry_run"])
            except Exception as exc:  # noqa: BLE001
                logger.exception("[dispatch_worker] item crashed")
                summary["errors"].append(f"{item['id']}: {exc}")
                continue

            if report.get("status") == "sent":
                summary["dispatched"] += 1
            else:
                summary["failed"] += 1

        return summary
    except Exception as exc:  # noqa: BLE001
        logger.exception("[dispatch_worker] tick crashed at top-level")
        summary["errors"].append(str(exc))
        return summary


# =====================================================================
# Internals
# =====================================================================

async def _read_settings() -> Dict[str, Any]:
    doc = await db.propaganda_settings.find_one({})
    return dict(doc or {})


async def _fetch_due_items(*, limit: int) -> List[Dict[str, Any]]:
    """Items eligible for dispatch: status=approved AND scheduled_for ≤ now.
    Ordered oldest-first so backlog drains chronologically."""
    now_iso = _now_iso()
    cursor = (
        db.propaganda_queue.find(
            {
                "status": "approved",
                "$or": [
                    {"scheduled_for": {"$lte": now_iso}},
                    {"scheduled_for": None},
                ],
            }
        )
        .sort("approved_at", 1)
        .limit(max(1, limit))
    )
    return [doc async for doc in cursor]


async def _trigger_in_cooldown(trigger_key: str, *, minutes: int) -> bool:
    if not trigger_key or minutes <= 0:
        return False
    cutoff = (
        datetime.now(timezone.utc) - timedelta(minutes=minutes)
    ).isoformat()
    doc = await db.propaganda_queue.find_one(
        {
            "trigger_key": trigger_key,
            "status": "sent",
            "sent_at": {"$gte": cutoff},
        }
    )
    return doc is not None


async def _count_sent_within(*, minutes: int) -> int:
    cutoff = (
        datetime.now(timezone.utc) - timedelta(minutes=minutes)
    ).isoformat()
    return await db.propaganda_queue.count_documents(
        {"status": "sent", "sent_at": {"$gte": cutoff}}
    )


async def _dispatch_item(
    item: Dict[str, Any],
    *,
    dry_run: bool,
) -> Dict[str, Any]:
    """Send one queue item across all its platforms.

    All platforms must succeed for the item to be marked ``sent``.
    Otherwise it's ``failed`` with per-platform errors stored.
    """
    item_id = item["_id"]
    platforms = list(item.get("platforms") or [])
    if not platforms:
        return await _finalise_failed(item_id, "no_platforms", {})

    # Atomically claim the item: status approved → in_flight, so a
    # concurrent tick can't double-send. We track in_flight with a
    # synthetic status that's NEVER persisted long-term — we always
    # transition it to sent/failed before the tick returns.
    claimed = await db.propaganda_queue.find_one_and_update(
        {"_id": item_id, "status": "approved"},
        {"$set": {"status": "in_flight", "in_flight_at": _now_iso()}},
        return_document=True,
    )
    if not claimed:
        # Already picked up by another tick — skip silently.
        return {"status": "skipped"}

    results: Dict[str, Any] = {}
    all_ok = True
    for platform in platforms:
        send_fn = get_dispatcher(platform)
        if send_fn is None:
            results[platform] = DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error="unsupported_platform",
                dry_run=dry_run,
            ).to_dict()
            all_ok = False
            continue
        try:
            res = await send_fn(item, dry_run=dry_run)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[dispatch_worker] platform=%s crashed", platform)
            res = DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error=f"crash: {exc}",
                dry_run=dry_run,
            )
        results[platform] = res.to_dict()
        if res.outcome != DispatchOutcome.SENT:
            all_ok = False

    final_status = "sent" if all_ok else "failed"
    update = {
        "status": final_status,
        "results": results,
        "sent_at": _now_iso() if all_ok else None,
        "error": None if all_ok else _summarise_errors(results),
    }
    await db.propaganda_queue.update_one({"_id": item_id}, {"$set": update})
    logger.info(
        "[dispatch_worker] item=%s status=%s (platforms=%s, dry_run=%s)",
        item_id, final_status, platforms, dry_run,
    )
    return {"status": final_status, "results": results}


async def _finalise_failed(
    item_id: str, error: str, results: Dict[str, Any]
) -> Dict[str, Any]:
    await db.propaganda_queue.update_one(
        {"_id": item_id},
        {"$set": {"status": "failed", "error": error, "results": results}},
    )
    return {"status": "failed", "error": error}


def _summarise_errors(results: Dict[str, Any]) -> str:
    parts = []
    for platform, r in results.items():
        if r.get("outcome") != "sent":
            parts.append(f"{platform}={r.get('error') or 'unknown'}")
    return "; ".join(parts) or "unknown"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Manual tick (used by /api/admin/propaganda/dispatch/tick-now)
# =====================================================================
async def force_tick() -> Dict[str, Any]:
    """Run a tick immediately, bypassing the scheduler. Used by the
    admin "Tick now" button to flush the queue on demand without
    waiting up to 30 s."""
    return await run_tick()


# Compatibility export — the scheduler module imports this name.
async def tick_async() -> None:
    """APScheduler-friendly coroutine. Logs result, swallows return."""
    summary = await run_tick()
    if summary["errors"]:
        logger.warning(
            "[dispatch_worker] tick had %d error(s): %s",
            len(summary["errors"]), summary["errors"],
        )


__all__ = [
    "DISPATCH_TICK_SECONDS",
    "run_tick",
    "force_tick",
    "tick_async",
]


if __name__ == "__main__":  # pragma: no cover — manual one-shot
    asyncio.run(run_tick())
