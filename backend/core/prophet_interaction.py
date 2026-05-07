"""Prophet Interaction Bot — Sprint 17.5 conversational outreach.

Hourly job that:
  1. Picks 1-3 random Agents from the accredited pool with an X handle
     (excluding handles cited in the last 24h to avoid spam),
  2. Pulls the 1-2 most recent tweets from each via X API v2,
  3. Asks the Tone Engine to craft a Lore-compliant cynical reply,
  4. Posts it as ``in_reply_to_tweet_id`` so the agent gets the ping.

Why direct X dispatch instead of the propaganda queue?
  Replies need a tweet_id pointer that the queue's render path doesn't
  carry. We could plumb it through, but reply traffic is fundamentally
  reactive (tied to a specific source tweet) so it has its own pacing
  ceiling separate from the cadence engine. Auditing happens via the
  ``prophet_replies`` collection.

Cost & rate awareness
---------------------
* X API: ~3 user_id lookups (cached 7d) + ~3 timeline reads + 1-3
  POST tweets per hour ⇒ < 100 credits/day on Pay-Per-Use.
* LLM: 1-3 calls/hr via the existing Emergent LLM key (Tone Engine).
* Hard ceiling: ``max_replies_per_hour`` (default 3) + 60-sec cooldown
  between consecutive replies so a 3-reply tick spans ~2 minutes
  (enough for X's anti-spam heuristics to remain comfortable).

Reply persona signature
-----------------------
The Tone Engine is asked to sign every reply with ``— ΔΣ`` so the
recipient unmistakably knows it came from the Prophet, not a generic
bot. The signature is enforced post-rewrite (``_ensure_signed``) so
even an LLM that ignores the prompt still ships the brand mark.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.config import db
from core.secret_provider import get_twitter_bearer_token
from core import tone_engine
from core.dispatchers import x as x_dispatcher
from core.dispatchers.base import DispatchOutcome

logger = logging.getLogger("deepotus.prophet_interaction")

#: Storage of every reply we ship — auditable, debuggable, dedupable.
PROPHET_REPLIES = "prophet_replies"

#: Cache of tweet IDs we've replied to. Prevents double-replying when
#: the same source tweet survives two ticks (because their feed barely
#: moves). Indexed unique on ``source_tweet_id``.
_REPLY_DEDUP_INDEX_NAME = "prophet_replies_source_tweet_unique"

#: Per-agent cooldown — once we reply to @alice we don't re-engage them
#: for at least this many hours so the Prophet doesn't look like a
#: stalker reply-guy. Configurable via admin, but capped here.
_DEFAULT_PER_HANDLE_COOLDOWN_HOURS = 24

#: Hard ceiling on replies per hour. Past this we stop the tick early.
_HARD_MAX_REPLIES_PER_HOUR = 5

#: How many tweets to fetch per agent. We pick the freshest one that's
#: not a retweet/reply (via ``exclude=retweets,replies`` in the X v2
#: call) so we always engage on original content.
_TWEETS_PER_AGENT = 3

#: Minimum age of the source tweet — replying to a 12-second-old tweet
#: looks like a botswarm. We require the tweet to be at least 30s old.
#: This is a low bar but kills the "reply within 1s" pattern X flags.
_MIN_SOURCE_TWEET_AGE_S = 30

#: Maximum age — tweets older than this aren't worth engaging.
_MAX_SOURCE_TWEET_AGE_HOURS = 6

#: Where the engine stamps its meta (last fired, last skip reason).
#: Lives inside ``propaganda_settings.interaction_bot``.
_SETTINGS_ID = "settings"
_SUBKEY = "interaction_bot"

_X_API_BASE = "https://api.twitter.com/2"
_X_REQUEST_TIMEOUT_S = 12.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


# ---------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------
DEFAULT_INTERACTION_BOT_CFG: Dict[str, Any] = {
    "enabled": False,  # OFF by default — admin opts in once X creds verified
    "max_replies_per_hour": 3,
    "min_replies_per_hour": 1,
    "per_handle_cooldown_hours": _DEFAULT_PER_HANDLE_COOLDOWN_HOURS,
    "last_fired_at": None,
    "last_skip_reason": None,
    "last_replies": [],  # short ring buffer for the admin dashboard
    "total_replies_lifetime": 0,
}


async def get_settings() -> Dict[str, Any]:
    doc = await db.propaganda_settings.find_one({"_id": _SETTINGS_ID}) or {}
    cfg = dict(DEFAULT_INTERACTION_BOT_CFG)
    cfg.update(doc.get(_SUBKEY) or {})
    return cfg


async def patch_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {"enabled", "max_replies_per_hour", "min_replies_per_hour", "per_handle_cooldown_hours"}
    safe = {k: v for k, v in patch.items() if k in allowed}
    if not safe:
        return await get_settings()
    if "max_replies_per_hour" in safe:
        safe["max_replies_per_hour"] = max(
            1, min(_HARD_MAX_REPLIES_PER_HOUR, int(safe["max_replies_per_hour"])),
        )
    if "min_replies_per_hour" in safe:
        safe["min_replies_per_hour"] = max(
            0, min(_HARD_MAX_REPLIES_PER_HOUR, int(safe["min_replies_per_hour"])),
        )
    if "per_handle_cooldown_hours" in safe:
        safe["per_handle_cooldown_hours"] = max(
            1, min(7 * 24, int(safe["per_handle_cooldown_hours"])),
        )
    set_doc = {f"{_SUBKEY}.{k}": v for k, v in safe.items()}
    await db.propaganda_settings.update_one(
        {"_id": _SETTINGS_ID}, {"$set": set_doc}, upsert=True,
    )
    return await get_settings()


async def _stamp_meta(*, fired: int, reason: Optional[str], replies: List[Dict[str, Any]]) -> None:
    patch = {
        f"{_SUBKEY}.last_fired_at": _now_iso(),
        f"{_SUBKEY}.last_skip_reason": reason,
    }
    if replies:
        # Keep only the last 10 for the admin dashboard.
        patch[f"{_SUBKEY}.last_replies"] = replies[-10:]
        patch[f"{_SUBKEY}.total_replies_lifetime"] = await _bump_lifetime(len(replies))
    await db.propaganda_settings.update_one(
        {"_id": _SETTINGS_ID}, {"$set": patch}, upsert=True,
    )


async def _bump_lifetime(delta: int) -> int:
    """Increment + read the lifetime counter atomically."""
    if delta <= 0:
        cur = await db.propaganda_settings.find_one({"_id": _SETTINGS_ID}) or {}
        return int(((cur.get(_SUBKEY) or {}).get("total_replies_lifetime") or 0))
    res = await db.propaganda_settings.find_one_and_update(
        {"_id": _SETTINGS_ID},
        {"$inc": {f"{_SUBKEY}.total_replies_lifetime": int(delta)}},
        upsert=True,
        return_document=True,
    )
    return int(((res or {}).get(_SUBKEY) or {}).get("total_replies_lifetime") or 0)


# ---------------------------------------------------------------------
# Indexes (idempotent — called from start_scheduler bootstrap)
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    try:
        await db[PROPHET_REPLIES].create_index(
            [("source_tweet_id", 1)],
            unique=True, name=_REPLY_DEDUP_INDEX_NAME,
            partialFilterExpression={"source_tweet_id": {"$type": "string"}},
        )
        await db[PROPHET_REPLIES].create_index(
            [("agent_handle", 1), ("posted_at", -1)],
            name="prophet_replies_handle_recent",
        )
        await db[PROPHET_REPLIES].create_index(
            [("posted_at", -1)],
            name="prophet_replies_posted_at_desc",
        )
    except Exception:  # noqa: BLE001
        logger.exception("[prophet-interaction] index bootstrap failed")


# ---------------------------------------------------------------------
# Pool selection
# ---------------------------------------------------------------------
async def _select_target_handles(
    *, count: int, cooldown_hours: int,
) -> List[Dict[str, Any]]:
    """Pick at most ``count`` accredited rows with x_handle that haven't
    been engaged in the cooldown window. Random-ordered so consecutive
    ticks don't always engage the same agents."""
    cutoff_iso = (_now() - timedelta(hours=cooldown_hours)).isoformat()
    # Fetch a wider candidate pool then sample. Mongo $sample would be
    # cleaner but mixing it with $match on a sparse index is slow at
    # small collection sizes; the in-memory shuffle is fine for ≤ 5k
    # rows (well above our pre-launch reality).
    candidates_cursor = db.clearance_levels.find(
        {
            "x_handle": {"$exists": True, "$nin": [None, ""]},
            "$or": [
                {"interaction_last_engaged_at": {"$in": [None, False]}},
                {"interaction_last_engaged_at": {"$lt": cutoff_iso}},
            ],
        },
        {"_id": 1, "email": 1, "x_handle": 1, "display_name": 1},
    ).limit(80)
    pool = [doc async for doc in candidates_cursor]
    if not pool:
        return []
    random.shuffle(pool)
    return pool[: max(1, int(count))]


async def _mark_engaged(email: str) -> None:
    await db.clearance_levels.update_one(
        {"email": email.lower().strip()},
        {"$set": {
            "interaction_last_engaged_at": _now_iso(),
            "updated_at": _now_iso(),
        }},
    )


# ---------------------------------------------------------------------
# X API helpers (mirror of kol_listener pattern)
# ---------------------------------------------------------------------
import httpx  # noqa: E402  (kept after typing imports for clarity)


async def _resolve_user_id(handle: str, bearer: str) -> Optional[str]:
    handle_clean = (handle or "").strip().lstrip("@")
    if not handle_clean:
        return None
    cache_id = handle_clean.lower()
    cached = await db.kol_user_id_cache.find_one({"_id": cache_id})
    if cached and cached.get("user_id"):
        return str(cached["user_id"])
    url = f"{_X_API_BASE}/users/by/username/{handle_clean}"
    try:
        async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                url, headers={"Authorization": f"Bearer {bearer}"},
            )
    except Exception:  # noqa: BLE001
        logger.exception("[prophet-interaction] user_id lookup crashed handle=%s", handle_clean)
        return None
    if resp.status_code >= 400:
        logger.warning(
            "[prophet-interaction] user_id http_%d handle=%s body=%s",
            resp.status_code, handle_clean, (resp.text or "")[:160],
        )
        return None
    user_id = ((resp.json() or {}).get("data") or {}).get("id")
    if not user_id:
        return None
    await db.kol_user_id_cache.update_one(
        {"_id": cache_id},
        {"$set": {
            "user_id": str(user_id),
            "handle_cased": handle_clean,
            "cached_at": _now(),
        }},
        upsert=True,
    )
    return str(user_id)


async def _fetch_recent_tweet(user_id: str, bearer: str) -> Optional[Dict[str, Any]]:
    """Return the freshest eligible tweet for ``user_id``, or None.

    Eligibility:
        * Excludes retweets + replies (X-side filter).
        * In the [_MIN_SOURCE_TWEET_AGE_S, _MAX_SOURCE_TWEET_AGE_HOURS] window.
        * Not already replied to (via ``prophet_replies`` dedup).
    """
    url = f"{_X_API_BASE}/users/{user_id}/tweets"
    params: Dict[str, Any] = {
        "max_results": max(5, _TWEETS_PER_AGENT * 2),
        "exclude": "retweets,replies",
        "tweet.fields": "created_at,text,lang,conversation_id",
    }
    try:
        async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                url, params=params, headers={"Authorization": f"Bearer {bearer}"},
            )
    except Exception:  # noqa: BLE001
        logger.exception("[prophet-interaction] tweets fetch crashed user_id=%s", user_id)
        return None
    if resp.status_code >= 400:
        logger.warning(
            "[prophet-interaction] tweets http_%d user_id=%s body=%s",
            resp.status_code, user_id, (resp.text or "")[:160],
        )
        return None

    tweets: List[Dict[str, Any]] = ((resp.json() or {}).get("data") or [])
    now = _now()
    min_age = timedelta(seconds=_MIN_SOURCE_TWEET_AGE_S)
    max_age = timedelta(hours=_MAX_SOURCE_TWEET_AGE_HOURS)

    for tw in tweets:
        tw_id = str(tw.get("id") or "")
        if not tw_id:
            continue
        # Dedup: never reply twice to the same source tweet.
        already = await db[PROPHET_REPLIES].find_one(
            {"source_tweet_id": tw_id}, {"_id": 1},
        )
        if already:
            continue
        # Age window.
        created_raw = tw.get("created_at") or ""
        try:
            created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        age = now - created
        if age < min_age or age > max_age:
            continue
        return {
            "id": tw_id,
            "text": str(tw.get("text") or ""),
            "created_at": created.isoformat(),
        }
    return None


# ---------------------------------------------------------------------
# Reply rendering (Tone Engine + signature enforcement)
# ---------------------------------------------------------------------
_REPLY_BASE_TEMPLATE = (
    "{handle}, the chart whispers what the herd refuses to hear.\n"
    "Stay the course — the Cabinet keeps watch.\n"
    "— ΔΣ"
)

_SIG_RE = re.compile(r"(?:—|–|-)\s*[ΔΑΒ]?Σ\b", re.IGNORECASE)


def _build_seed(handle: str, source_text: str) -> str:
    """Produce the raw template the Tone Engine will rewrite from.

    We hand the LLM:
        * the agent's handle (so the rewrite stays addressed),
        * a 280-char excerpt of the source tweet (context),
        * the cynical frame ("the chart whispers..."),
        * an explicit signature requirement (``— ΔΣ``).
    """
    excerpt = (source_text or "").strip().replace("\n", " ")[:200]
    return (
        f"@{handle.lstrip('@')} — re: \"{excerpt}\". "
        "Reply as PROTOCOL ΔΣ: one sharp cynical observation, "
        "lore-aligned (Cabinet / Prophet / classified vault), "
        "max 240 chars, no hashtags, end with the signature ' — ΔΣ'."
    )


def _ensure_signed(text: str) -> str:
    """Guarantee the ΔΣ signature even if the LLM strips it."""
    cleaned = (text or "").strip()
    if not cleaned:
        return cleaned
    if _SIG_RE.search(cleaned[-30:]):
        return cleaned
    return f"{cleaned}\n— ΔΣ"


def _enforce_handle_prefix(text: str, handle: str) -> str:
    """X reply auto-prepends the handle in the conversation thread, but
    we keep an explicit ``@handle`` at the start for cleanliness in the
    raw text — most clients render this gracefully."""
    cleaned = text.lstrip()
    h = f"@{handle.lstrip('@')}"
    if cleaned.lower().startswith(h.lower()):
        return cleaned
    return f"{h} {cleaned}"


async def _render_reply(handle: str, source_text: str) -> str:
    """Compose the reply body. LLM-augmented when possible, deterministic
    fallback otherwise (Tone Engine handles the no-key path internally)."""
    seed = _build_seed(handle, source_text)
    enhanced = await tone_engine.maybe_enhance(seed)
    body = (enhanced or {}).get("content") or _REPLY_BASE_TEMPLATE.format(
        handle=f"@{handle.lstrip('@')}",
    )
    body = _enforce_handle_prefix(body, handle)
    body = _ensure_signed(body)
    # Hard cap — X allows 280 but our dispatcher already trims at 260.
    if len(body) > 260:
        body = body[:259] + "…"
    return body


# ---------------------------------------------------------------------
# Reply persistence
# ---------------------------------------------------------------------
async def _persist_reply(
    *,
    agent_email: str,
    agent_handle: str,
    source_tweet_id: str,
    source_excerpt: str,
    rendered: str,
    outcome: str,
    posted_tweet_id: Optional[str],
    error: Optional[str],
) -> str:
    doc_id = str(uuid.uuid4())
    await db[PROPHET_REPLIES].insert_one({
        "_id": doc_id,
        "agent_email": agent_email.lower().strip(),
        "agent_handle": agent_handle.lstrip("@"),
        "source_tweet_id": source_tweet_id,
        "source_excerpt": source_excerpt[:240],
        "rendered_reply": rendered[:500],
        "outcome": outcome,  # sent | failed | dry_run
        "posted_tweet_id": posted_tweet_id,
        "error": error,
        "posted_at": _now_iso(),
    })
    return doc_id


# ---------------------------------------------------------------------
# Tick — main entrypoint (scheduler + admin "Fire now")
# ---------------------------------------------------------------------
async def fire(*, manual: bool = False, dry_run: Optional[bool] = None) -> Dict[str, Any]:
    """Run a single interaction tick.

    ``dry_run=None`` → respect ``propaganda_settings.dispatch_dry_run``.
    Manual fires from the admin UI default to a real post unless the
    operator passes ``dry_run=True`` for a smoke test.
    """
    cfg = await get_settings()
    if not cfg.get("enabled") and not manual:
        return {"ok": False, "fired": 0, "reason": "disabled"}

    bearer = await get_twitter_bearer_token()
    if not bearer:
        await _stamp_meta(fired=0, reason="no_bearer_token", replies=[])
        return {"ok": False, "fired": 0, "reason": "no_bearer_token"}

    # Resolve dry_run from the central propaganda_settings if caller
    # didn't override (so flipping prod mode globally affects this too).
    if dry_run is None:
        prop = await db.propaganda_settings.find_one({"_id": _SETTINGS_ID}) or {}
        dry_run = bool(prop.get("dispatch_dry_run", False))

    max_replies = max(
        cfg.get("min_replies_per_hour", 1),
        min(_HARD_MAX_REPLIES_PER_HOUR, int(cfg.get("max_replies_per_hour", 3))),
    )
    # For each tick we randomise the actual count between min..max so
    # the Prophet's cadence doesn't feel mechanical.
    target_count = random.randint(
        max(1, int(cfg.get("min_replies_per_hour", 1))),
        max_replies,
    )
    cooldown_h = int(cfg.get("per_handle_cooldown_hours", _DEFAULT_PER_HANDLE_COOLDOWN_HOURS))

    pool = await _select_target_handles(count=target_count * 2, cooldown_hours=cooldown_h)
    if not pool:
        await _stamp_meta(fired=0, reason="empty_pool", replies=[])
        return {"ok": True, "fired": 0, "reason": "empty_pool"}

    fired_count = 0
    fired_log: List[Dict[str, Any]] = []
    for row in pool:
        if fired_count >= target_count:
            break
        handle = str(row.get("x_handle") or "").strip().lstrip("@")
        email = str(row.get("email") or "").strip().lower()
        if not handle or not email:
            continue
        user_id = await _resolve_user_id(handle, bearer)
        if not user_id:
            continue
        tw = await _fetch_recent_tweet(user_id, bearer)
        if not tw:
            continue
        rendered = await _render_reply(handle, tw["text"])
        # Build a synthetic queue-item shape for the dispatcher; the
        # ``meta.reply_to_tweet_id`` is the new escape hatch we're
        # adding to ``dispatchers/x.py``.
        item = {
            "id": str(uuid.uuid4()),
            "rendered_content": rendered,
            "meta": {"reply_to_tweet_id": tw["id"]},
        }
        result = await x_dispatcher.send(item, dry_run=bool(dry_run))
        outcome = "sent" if result.outcome == DispatchOutcome.SENT else "failed"
        await _persist_reply(
            agent_email=email,
            agent_handle=handle,
            source_tweet_id=tw["id"],
            source_excerpt=tw["text"],
            rendered=rendered,
            outcome=outcome if not dry_run else "dry_run",
            posted_tweet_id=result.platform_message_id,
            error=result.error,
        )
        if outcome == "sent" or dry_run:
            await _mark_engaged(email)
            fired_count += 1
            fired_log.append({
                "handle": handle,
                "source_tweet_id": tw["id"],
                "posted_tweet_id": result.platform_message_id,
                "dry_run": bool(dry_run),
                "preview": rendered[:120],
                "at": _now_iso(),
            })
            # 60-sec spacing between successive replies in the same tick.
            if fired_count < target_count:
                await asyncio.sleep(60)
        else:
            logger.warning(
                "[prophet-interaction] dispatch failed handle=%s err=%s",
                handle, result.error,
            )

    if fired_count == 0:
        await _stamp_meta(fired=0, reason="no_eligible_tweets", replies=[])
        return {"ok": True, "fired": 0, "reason": "no_eligible_tweets"}

    await _stamp_meta(fired=fired_count, reason=None, replies=fired_log)
    logger.info(
        "[prophet-interaction] fired=%d (manual=%s dry_run=%s)",
        fired_count, manual, dry_run,
    )
    return {
        "ok": True,
        "fired": fired_count,
        "manual": manual,
        "dry_run": bool(dry_run),
        "replies": fired_log,
    }


async def tick() -> Dict[str, Any]:
    """APScheduler hourly entry-point. Always returns — never raises."""
    try:
        return await fire(manual=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[prophet-interaction] tick crashed")
        return {"ok": False, "fired": 0, "reason": f"crash: {exc}"}


# ---------------------------------------------------------------------
# Read helpers (admin dashboard)
# ---------------------------------------------------------------------
async def list_replies(*, limit: int = 50) -> List[Dict[str, Any]]:
    cursor = db[PROPHET_REPLIES].find({}).sort("posted_at", -1).limit(int(limit))
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        out.append({
            "id": d["_id"],
            "agent_handle": d.get("agent_handle"),
            "source_tweet_id": d.get("source_tweet_id"),
            "rendered_reply": d.get("rendered_reply"),
            "outcome": d.get("outcome"),
            "posted_tweet_id": d.get("posted_tweet_id"),
            "error": d.get("error"),
            "posted_at": d.get("posted_at"),
        })
    return out


__all__ = [
    "DEFAULT_INTERACTION_BOT_CFG",
    "PROPHET_REPLIES",
    "ensure_indexes",
    "fire",
    "tick",
    "get_settings",
    "patch_settings",
    "list_replies",
    "_render_reply",
    "_ensure_signed",
    "_enforce_handle_prefix",
    "_build_seed",
]
