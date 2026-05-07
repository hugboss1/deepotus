"""Welcome Signal — Sprint 17.5 daily Cabinet recognition broadcast.

Every day (default: 14:00 UTC) we tweet a short thread that publicly
acknowledges the 5 most recent Agents who got accredited AND provided
their X handle, so The Cabinet visibly grows in real time.

Selection contract
------------------
We pick the 5 most recent ``clearance_levels`` rows where:
    * ``x_handle`` is set (non-empty),
    * ``welcome_signaled_at`` is **null** (never celebrated yet),
    * the row was created in the last 14 days (anti-stale guard).

After a successful broadcast we stamp ``welcome_signaled_at`` on each
cited row so the same agent is never re-cited.

Anti-pollution guard
--------------------
If fewer than 2 fresh handles are available we **skip the day's
broadcast** rather than tweeting a thin shoutout — better silence than
"The Cabinet grows. Agent @bob identified.". The skip is logged so the
admin can inspect why nothing fired.

Output shape
------------
The message is rendered locally (no LLM round-trip — we want it
deterministic) and pushed into the propaganda queue with policy=auto
so it dispatches on the next worker tick. Format:

    The Cabinet grows.
    Agents @h1, @h2, @h3, @h4, @h5 identified.
    Clearance LEVEL 02 confirmed.
    PROTOCOL ΔΣ — the Prophet's reach is absolute.

Admin can override the cadence in ``propaganda_settings.welcome_signal``:
    * ``enabled``           bool  — master kill-switch (default True)
    * ``hour_utc``          int   — daily firing hour (default 14)
    * ``min_handles``       int   — skip-threshold (default 2)
    * ``max_handles``       int   — citation cap (default 5)
    * ``last_fired_at``     str   — ISO timestamp (engine-managed)
    * ``last_skip_reason``  str   — debugging breadcrumb (engine-managed)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.welcome_signal")

#: How far back we'll look for "recently accredited" rows before we
#: consider them stale and stop celebrating them. 14 days gives the
#: feature a tolerant catch-up window if the bot was paused.
_RECENCY_WINDOW_DAYS = 14

#: Hard cap on cited handles per broadcast. 5 keeps the tweet under
#: the 260-char dispatcher safety budget even with 15-char handles.
_HARD_MAX_HANDLES = 5

#: Don't broadcast unless we have at least this many fresh handles —
#: a shoutout to a single agent feels lonelier than no shoutout.
_DEFAULT_MIN_HANDLES = 2

#: Where the engine stamps its last-fire / last-skip metadata. We use
#: the ``propaganda_settings`` singleton to keep all toggles in one row.
_SETTINGS_ID = "settings"
_SUBKEY = "welcome_signal"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


# ---------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------
DEFAULT_WELCOME_SIGNAL_CFG: Dict[str, Any] = {
    "enabled": True,
    "hour_utc": 14,
    "min_handles": _DEFAULT_MIN_HANDLES,
    "max_handles": _HARD_MAX_HANDLES,
    "last_fired_at": None,
    "last_skip_reason": None,
    "last_cited_handles": [],
}


async def get_settings() -> Dict[str, Any]:
    """Return the welcome_signal sub-config, hydrated with defaults."""
    doc = await db.propaganda_settings.find_one({"_id": _SETTINGS_ID}) or {}
    cfg = dict(DEFAULT_WELCOME_SIGNAL_CFG)
    cfg.update(doc.get(_SUBKEY) or {})
    return cfg


async def patch_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    """Whitelist-style merge — refuses unknown keys."""
    allowed = {"enabled", "hour_utc", "min_handles", "max_handles"}
    safe = {k: v for k, v in patch.items() if k in allowed}
    if not safe:
        return await get_settings()
    if "hour_utc" in safe:
        safe["hour_utc"] = max(0, min(23, int(safe["hour_utc"])))
    if "min_handles" in safe:
        safe["min_handles"] = max(1, min(_HARD_MAX_HANDLES, int(safe["min_handles"])))
    if "max_handles" in safe:
        safe["max_handles"] = max(1, min(_HARD_MAX_HANDLES, int(safe["max_handles"])))
    set_doc = {f"{_SUBKEY}.{k}": v for k, v in safe.items()}
    await db.propaganda_settings.update_one(
        {"_id": _SETTINGS_ID}, {"$set": set_doc}, upsert=True,
    )
    return await get_settings()


async def _stamp_meta(*, fired: bool, reason: Optional[str], cited: List[str]) -> None:
    patch = {
        f"{_SUBKEY}.last_fired_at": _now_iso() if fired else None,
        f"{_SUBKEY}.last_skip_reason": reason,
        f"{_SUBKEY}.last_cited_handles": cited,
    }
    await db.propaganda_settings.update_one(
        {"_id": _SETTINGS_ID}, {"$set": patch}, upsert=True,
    )


# ---------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------
async def select_eligible_handles(*, max_handles: int) -> List[Dict[str, Any]]:
    """Return up to ``max_handles`` rows ready for the next broadcast.

    Sorted by ``created_at`` DESC so the freshest agents lead the
    citation list — newer agents naturally take precedence. We deliberately
    do NOT randomise: the operator wants chronological "Cabinet grows"
    storytelling, not lottery shoutouts.
    """
    cutoff = (_now() - timedelta(days=_RECENCY_WINDOW_DAYS)).isoformat()
    cursor = (
        db.clearance_levels.find(
            {
                "x_handle": {"$exists": True, "$nin": [None, ""]},
                "welcome_signaled_at": {"$in": [None, False]},
                "created_at": {"$gte": cutoff},
            },
            {"_id": 1, "email": 1, "x_handle": 1, "display_name": 1, "created_at": 1},
        )
        .sort("created_at", -1)
        .limit(max(1, min(_HARD_MAX_HANDLES, int(max_handles))))
    )
    return [doc async for doc in cursor]


def render_message(handles: List[str]) -> str:
    """Render the deterministic Welcome Signal copy.

    Kept template-only on purpose — no LLM rewrite — so the propaganda
    cadence stays predictable and we never accidentally tweet a
    hallucinated handle. Emoji omitted for the same reason (X strips
    some unicode and we don't want \\ufffd in our shoutouts).
    """
    if not handles:
        return ""
    cleaned = [h.strip().lstrip("@") for h in handles if h and h.strip()]
    cited = " ".join(f"@{h}" for h in cleaned)
    return (
        "The Cabinet grows.\n"
        f"Agents {cited} identified.\n"
        "Clearance LEVEL 02 confirmed.\n"
        "PROTOCOL ΔΣ — the Prophet's reach is absolute."
    )


# ---------------------------------------------------------------------
# Mark-as-signaled
# ---------------------------------------------------------------------
async def mark_signaled(emails: List[str], *, queue_item_id: Optional[str]) -> int:
    """Stamp ``welcome_signaled_at`` on every row we just cited so the
    next broadcast doesn't repeat them."""
    if not emails:
        return 0
    now = _now_iso()
    res = await db.clearance_levels.update_many(
        {"email": {"$in": [e.lower().strip() for e in emails]}},
        {
            "$set": {
                "welcome_signaled_at": now,
                "welcome_signaled_queue_id": queue_item_id,
                "updated_at": now,
            }
        },
    )
    return int(res.modified_count or 0)


# ---------------------------------------------------------------------
# Manual fire (admin button) + scheduler tick
# ---------------------------------------------------------------------
async def fire(*, manual: bool = False, by_jti: Optional[str] = None) -> Dict[str, Any]:
    """Run one Welcome Signal broadcast.

    ``manual=True`` skips the daily-once gate so the admin can preview /
    re-fire ad hoc; the scheduler tick passes ``manual=False`` and we
    enforce a 23h cooldown to avoid double-fires across DST or manual
    reschedules.

    Returns a structured report consumable by the admin UI.
    """
    cfg = await get_settings()
    if not cfg.get("enabled") and not manual:
        await _stamp_meta(fired=False, reason="disabled", cited=[])
        return {"ok": False, "fired": False, "reason": "disabled"}

    # Daily-once gate (manual fires bypass this).
    if not manual:
        last = cfg.get("last_fired_at")
        if last:
            try:
                last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                if (_now() - last_dt) < timedelta(hours=23):
                    await _stamp_meta(
                        fired=False, reason="cooldown_active",
                        cited=cfg.get("last_cited_handles") or [],
                    )
                    return {"ok": False, "fired": False, "reason": "cooldown_active"}
            except ValueError:
                pass

    max_handles = int(cfg.get("max_handles") or _HARD_MAX_HANDLES)
    min_handles = int(cfg.get("min_handles") or _DEFAULT_MIN_HANDLES)

    rows = await select_eligible_handles(max_handles=max_handles)
    if len(rows) < min_handles:
        await _stamp_meta(
            fired=False, reason=f"insufficient_handles ({len(rows)} < {min_handles})",
            cited=[],
        )
        return {
            "ok": True, "fired": False, "reason": "insufficient_handles",
            "candidates": len(rows), "min_required": min_handles,
        }

    handles = [str(r.get("x_handle") or "").strip().lstrip("@") for r in rows]
    handles = [h for h in handles if h]
    if len(handles) < min_handles:
        await _stamp_meta(fired=False, reason="empty_after_clean", cited=[])
        return {"ok": True, "fired": False, "reason": "empty_after_clean"}

    message = render_message(handles)
    if not message:
        await _stamp_meta(fired=False, reason="empty_message", cited=[])
        return {"ok": True, "fired": False, "reason": "empty_message"}

    # Push into the propaganda queue with auto-policy so the dispatch
    # worker fires it on the next tick (no admin approval needed —
    # this is a recurring ritual, not an ad-hoc post).
    from core import dispatch_queue  # local import — avoids circular cost on cold start

    queue_item = await dispatch_queue.propose(
        trigger_key="welcome_signal",
        template_id=None,
        rendered_content=message,
        platforms=["x"],
        payload={
            "kind": "welcome_signal",
            "cited_handles": handles,
            "cited_emails": [r.get("email") for r in rows],
        },
        policy="auto",
        delay_seconds=5,
        by_jti=by_jti,
        manual=bool(manual),
    )

    queue_item_id = (queue_item or {}).get("id") or (queue_item or {}).get("_id")
    cited_emails = [r.get("email") for r in rows if r.get("email")]
    marked = await mark_signaled(cited_emails, queue_item_id=queue_item_id)
    await _stamp_meta(fired=True, reason=None, cited=handles)

    logger.info(
        "[welcome_signal] fired manual=%s cited=%d marked=%d queue_id=%s",
        manual, len(handles), marked, queue_item_id,
    )
    return {
        "ok": True,
        "fired": True,
        "manual": manual,
        "cited_handles": handles,
        "cited_count": len(handles),
        "marked": marked,
        "queue_item_id": queue_item_id,
        "message_preview": message,
    }


async def tick() -> Dict[str, Any]:
    """APScheduler tick — fires when the configured ``hour_utc`` matches.

    The job runs every 30 minutes so a slight desync (DST, container
    restart) still fires within the same hour. The 23h cooldown inside
    ``fire()`` prevents double-fires.
    """
    cfg = await get_settings()
    if not cfg.get("enabled"):
        return {"ok": True, "fired": False, "reason": "disabled"}
    target_hour = int(cfg.get("hour_utc") or 14)
    now = _now()
    if now.hour != target_hour:
        return {"ok": True, "fired": False, "reason": "hour_mismatch", "hour_utc": now.hour}
    return await fire(manual=False)


__all__ = [
    "DEFAULT_WELCOME_SIGNAL_CFG",
    "fire",
    "tick",
    "get_settings",
    "patch_settings",
    "select_eligible_handles",
    "render_message",
    "mark_signaled",
]
