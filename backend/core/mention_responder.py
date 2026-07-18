"""Mention Responder — auto-reply to X users who mention @Deepotus_AI.

Compliance frame
----------------
Replying to accounts that mention us first is the ONLY auto-reply
surface X's automation rules allow. This module therefore reacts
exclusively to ``GET /2/users/:id/mentions`` — it never searches for
strangers by keyword (that path is the semi-auto Keyword Digest, which
keeps a human in the loop; see ``core/keyword_digest.py``).

Flow
----
    APScheduler tick (30 min, gated by poll_interval_hours)
        └─► poll_once()
              1. Resolve OWN user_id via x_dispatcher.verify_identity()
                 (OAuth1) — cached forever in ``mention_responder_state``.
              2. GET /2/users/:id/mentions?since_id=… (app-only Bearer).
              3. Bootstrap rule: first poll only sets the baseline
                 (no reply flood on day 1).
              4. Filters: own tweets, dedup on source tweet_id,
                 per-handle cooldown, max_replies_per_tick.
              5. Render a rotating template (unique per handle → dodges
                 X's duplicate-content rejection) and post via
                 ``x_dispatcher.send`` with ``meta.reply_to_tweet_id``.
              6. Audit every attempt in ``mention_replies``.

Cost awareness (Pay-Per-Use credits)
------------------------------------
Default cadence = 1 poll / 6 h → 4 mention reads + ≤ ``max_replies_per_tick``
writes per day. The identity lookup is a one-off.

Safety rails
------------
* ``enabled=False`` by default — admin opts in via /api/admin/engagement.
* Global ``propaganda_settings.dispatch_dry_run`` respected (same
  contract as the Prophet Interaction Bot).
* Hard ceiling ``_HARD_MAX_REPLIES_PER_TICK`` regardless of config.
* 45-s spacing between consecutive replies in one tick.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from core.config import db
from core.secret_provider import get_twitter_bearer_token
from core.dispatchers import x as x_dispatcher
from core.dispatchers.base import DispatchOutcome

logger = logging.getLogger("deepotus.mention_responder")

#: Audit trail of every reply attempt (sent / failed / dry_run).
MENTION_REPLIES = "mention_replies"

#: Singleton state row — own user_id cache + since_id bookmark.
STATE_COLLECTION = "mention_responder_state"
STATE_ID = "state_v1"

#: Config lives inside ``propaganda_settings.mention_responder`` — same
#: pattern as the Prophet Interaction Bot (``interaction_bot`` subkey).
_SETTINGS_ID = "settings"
_SUBKEY = "mention_responder"

_X_API_BASE = "https://api.twitter.com/2"
_X_REQUEST_TIMEOUT_S = 12.0
_HARD_MAX_REPLIES_PER_TICK = 10
_REPLY_SPACING_S = 45
#: Ignore mentions older than this — replying to a 3-day-old mention
#: after enabling the bot looks necro and wastes the daily budget.
_MAX_MENTION_AGE_HOURS = 24

#: Default reply templates — rotated per reply. ``{handle}`` is filled
#: with the mention author, which also makes every tweet body unique
#: (X rejects exact-duplicate tweets). Validated with the founder on
#: 2026-07-18. Keep each rendered body ≤ 260 chars (dispatcher cap).
DEFAULT_REPLY_TEMPLATES: List[str] = [
    (
        "{handle} gm agent \U0001fae1 The Prophet sees you.\n"
        "$D2EP — no pump & dump, just chill & six dials to turn.\n"
        "CA: AUztiAfSCwDwm5Be5tSDiTmrZPnwATk7837cAFeDpump\n"
        "\U0001f310 deepotus.xyz\n"
        "Follow @Deepotus_AI — the Deep State rewards the loyal \U0001f5f3 NFA"
    ),
    (
        "{handle} The Cabinet logged your transmission \U0001f4e1\n"
        "$D2EP — 0% tax, multisig vault, zero pump & dump doctrine.\n"
        "CA: AUztiAfSCwDwm5Be5tSDiTmrZPnwATk7837cAFeDpump\n"
        "\U0001f310 deepotus.xyz\n"
        "Follow @Deepotus_AI to keep your clearance \U0001f5f3 NFA"
    ),
    (
        "{handle} Noted in the classified ledger \U0001f5c2\n"
        "Stay chill — $D2EP turns the dials, not the hype.\n"
        "CA: AUztiAfSCwDwm5Be5tSDiTmrZPnwATk7837cAFeDpump\n"
        "\U0001f310 deepotus.xyz\n"
        "Follow @Deepotus_AI — allegiance is audited \U0001f5f3 NFA"
    ),
]

DEFAULT_CFG: Dict[str, Any] = {
    "enabled": False,  # OFF until the admin flips it post-recette
    "poll_interval_hours": 6,
    "max_replies_per_tick": 5,
    "per_handle_cooldown_hours": 24,
    "reply_templates": list(DEFAULT_REPLY_TEMPLATES),
    "last_polled_at": None,
    "last_skip_reason": None,
    "total_replies_lifetime": 0,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


# ---------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------
async def get_settings() -> Dict[str, Any]:
    doc = await db.propaganda_settings.find_one({"_id": _SETTINGS_ID}) or {}
    cfg = dict(DEFAULT_CFG)
    cfg.update(doc.get(_SUBKEY) or {})
    if not cfg.get("reply_templates"):
        cfg["reply_templates"] = list(DEFAULT_REPLY_TEMPLATES)
    return cfg


async def patch_settings(patch: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {
        "enabled",
        "poll_interval_hours",
        "max_replies_per_tick",
        "per_handle_cooldown_hours",
        "reply_templates",
    }
    safe = {k: v for k, v in patch.items() if k in allowed}
    if not safe:
        return await get_settings()
    if "poll_interval_hours" in safe:
        safe["poll_interval_hours"] = max(1, min(24, int(safe["poll_interval_hours"])))
    if "max_replies_per_tick" in safe:
        safe["max_replies_per_tick"] = max(
            1, min(_HARD_MAX_REPLIES_PER_TICK, int(safe["max_replies_per_tick"])),
        )
    if "per_handle_cooldown_hours" in safe:
        safe["per_handle_cooldown_hours"] = max(
            1, min(7 * 24, int(safe["per_handle_cooldown_hours"])),
        )
    if "reply_templates" in safe:
        cleaned = [str(t).strip() for t in (safe["reply_templates"] or []) if str(t).strip()]
        safe["reply_templates"] = cleaned or list(DEFAULT_REPLY_TEMPLATES)
    set_doc = {f"{_SUBKEY}.{k}": v for k, v in safe.items()}
    await db.propaganda_settings.update_one(
        {"_id": _SETTINGS_ID}, {"$set": set_doc}, upsert=True,
    )
    return await get_settings()


async def _stamp(reason: Optional[str], fired: int = 0) -> None:
    patch: Dict[str, Any] = {
        f"{_SUBKEY}.last_polled_at": _now_iso(),
        f"{_SUBKEY}.last_skip_reason": reason,
    }
    await db.propaganda_settings.update_one(
        {"_id": _SETTINGS_ID},
        {"$set": patch, "$inc": {f"{_SUBKEY}.total_replies_lifetime": int(fired)}},
        upsert=True,
    )


# ---------------------------------------------------------------------
# Indexes (idempotent — called from the scheduler bootstrap)
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    try:
        await db[MENTION_REPLIES].create_index(
            [("source_tweet_id", 1)],
            unique=True,
            name="mention_replies_source_tweet_unique",
            partialFilterExpression={"source_tweet_id": {"$type": "string"}},
        )
        await db[MENTION_REPLIES].create_index(
            [("author_handle", 1), ("posted_at", -1)],
            name="mention_replies_handle_recent",
        )
        await db[MENTION_REPLIES].create_index(
            [("posted_at", -1)], name="mention_replies_posted_at_desc",
        )
    except Exception:  # noqa: BLE001
        logger.exception("[mention-responder] index bootstrap failed")


# ---------------------------------------------------------------------
# Own identity (user_id of the account the OAuth1 creds belong to)
# ---------------------------------------------------------------------
async def _get_own_identity() -> Optional[Dict[str, str]]:
    """Return ``{user_id, username}`` for the connected X account.

    Resolved once via ``x_dispatcher.verify_identity()`` (OAuth1 — the
    app-only bearer cannot call /users/me) then cached in Mongo. The
    admin "Verify X identity" runbook already exercises the same path.
    """
    state = await db[STATE_COLLECTION].find_one({"_id": STATE_ID}) or {}
    if state.get("own_user_id"):
        return {
            "user_id": str(state["own_user_id"]),
            "username": str(state.get("own_username") or ""),
        }
    ident = await x_dispatcher.verify_identity()
    if not ident.get("ok") or not ident.get("id"):
        logger.warning(
            "[mention-responder] identity resolution failed: %s",
            ident.get("error"),
        )
        return None
    await db[STATE_COLLECTION].update_one(
        {"_id": STATE_ID},
        {"$set": {
            "own_user_id": str(ident["id"]),
            "own_username": str(ident.get("username") or ""),
            "identity_cached_at": _now_iso(),
        }},
        upsert=True,
    )
    return {"user_id": str(ident["id"]), "username": str(ident.get("username") or "")}


# ---------------------------------------------------------------------
# Mentions fetch
# ---------------------------------------------------------------------
async def _fetch_mentions(
    user_id: str,
    *,
    since_id: Optional[str],
    bearer: str,
) -> tuple[List[Dict[str, Any]], Optional[str]]:
    """Return ``(mentions, newest_id)``.

    Each mention dict carries ``{id, text, created_at, author_id,
    author_handle}`` — the handle comes from the ``expansions=author_id``
    include block.
    """
    url = f"{_X_API_BASE}/users/{user_id}/mentions"
    params: Dict[str, Any] = {
        "max_results": 25,
        "tweet.fields": "created_at,text,author_id",
        "expansions": "author_id",
        "user.fields": "username",
    }
    if since_id:
        params["since_id"] = str(since_id)
    try:
        async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                url, params=params,
                headers={"Authorization": f"Bearer {bearer}"},
            )
    except httpx.TimeoutException:
        logger.warning("[mention-responder] mentions fetch timeout")
        return [], None
    except Exception:  # noqa: BLE001
        logger.exception("[mention-responder] mentions fetch crashed")
        return [], None

    if resp.status_code == 429:
        logger.warning("[mention-responder] mentions rate-limited — skipping tick")
        return [], None
    if resp.status_code >= 400:
        logger.warning(
            "[mention-responder] mentions http_%d body=%s",
            resp.status_code, (resp.text or "")[:160],
        )
        return [], None

    payload = resp.json() or {}
    tweets: List[Dict[str, Any]] = payload.get("data") or []
    users = ((payload.get("includes") or {}).get("users")) or []
    handle_by_id = {str(u.get("id")): str(u.get("username") or "") for u in users}
    newest_id = (payload.get("meta") or {}).get("newest_id")

    out: List[Dict[str, Any]] = []
    for tw in tweets:
        author_id = str(tw.get("author_id") or "")
        out.append({
            "id": str(tw.get("id") or ""),
            "text": str(tw.get("text") or ""),
            "created_at": str(tw.get("created_at") or ""),
            "author_id": author_id,
            "author_handle": handle_by_id.get(author_id, ""),
        })
    return out, newest_id


# ---------------------------------------------------------------------
# Eligibility + rendering
# ---------------------------------------------------------------------
async def _handle_on_cooldown(handle: str, cooldown_hours: int) -> bool:
    cutoff = (_now() - timedelta(hours=cooldown_hours)).isoformat()
    row = await db[MENTION_REPLIES].find_one(
        {
            "author_handle": handle.lstrip("@").lower(),
            "outcome": {"$in": ["sent", "dry_run"]},
            "posted_at": {"$gte": cutoff},
        },
        {"_id": 1},
    )
    return row is not None


def _mention_age_ok(created_at_iso: str) -> bool:
    try:
        created = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (_now() - created) <= timedelta(hours=_MAX_MENTION_AGE_HOURS)


def render_reply(handle: str, templates: List[str], rotation_index: int) -> str:
    """Rotate templates and inject the author handle. Hard-capped at
    260 chars to stay under the X dispatcher's own trim."""
    pool = [t for t in (templates or []) if str(t).strip()] or list(DEFAULT_REPLY_TEMPLATES)
    template = pool[rotation_index % len(pool)]
    body = template.replace("{handle}", f"@{handle.lstrip('@')}").strip()
    if len(body) > 260:
        body = body[:259] + "…"
    return body


# ---------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------
async def _persist_reply(
    *,
    author_handle: str,
    source_tweet_id: str,
    source_excerpt: str,
    rendered: str,
    outcome: str,
    posted_tweet_id: Optional[str],
    error: Optional[str],
) -> None:
    try:
        await db[MENTION_REPLIES].insert_one({
            "_id": str(uuid.uuid4()),
            "author_handle": author_handle.lstrip("@").lower(),
            "source_tweet_id": source_tweet_id,
            "source_excerpt": source_excerpt[:240],
            "rendered_reply": rendered[:500],
            "outcome": outcome,  # sent | failed | dry_run
            "posted_tweet_id": posted_tweet_id,
            "error": error,
            "posted_at": _now_iso(),
        })
    except Exception as e:  # noqa: BLE001
        # Duplicate source_tweet_id → already replied concurrently. Fine.
        if "E11000" not in str(e) and "duplicate key" not in str(e).lower():
            logger.exception("[mention-responder] audit insert failed")


# ---------------------------------------------------------------------
# Poll — main entrypoint (scheduler tick + admin "Poll now")
# ---------------------------------------------------------------------
async def poll_once(
    *, manual: bool = False, dry_run: Optional[bool] = None,
) -> Dict[str, Any]:
    """Run one mentions poll + reply pass. Never raises."""
    cfg = await get_settings()
    if not cfg.get("enabled") and not manual:
        return {"ok": False, "fired": 0, "reason": "disabled"}

    bearer = await get_twitter_bearer_token()
    if not bearer:
        await _stamp("no_bearer_token")
        return {"ok": False, "fired": 0, "reason": "no_bearer_token"}

    ident = await _get_own_identity()
    if not ident:
        await _stamp("identity_unresolved")
        return {"ok": False, "fired": 0, "reason": "identity_unresolved"}

    if dry_run is None:
        prop = await db.propaganda_settings.find_one({"_id": _SETTINGS_ID}) or {}
        dry_run = bool(prop.get("dispatch_dry_run", False))

    state = await db[STATE_COLLECTION].find_one({"_id": STATE_ID}) or {}
    since_id = state.get("since_id")

    mentions, newest_id = await _fetch_mentions(
        ident["user_id"], since_id=since_id, bearer=bearer,
    )

    # Bootstrap: first ever poll only records the baseline so we don't
    # reply to the whole historic mentions timeline at once.
    if since_id is None:
        if newest_id:
            await db[STATE_COLLECTION].update_one(
                {"_id": STATE_ID},
                {"$set": {"since_id": str(newest_id), "baseline_set_at": _now_iso()}},
                upsert=True,
            )
        await _stamp("bootstrap_baseline")
        return {
            "ok": True, "fired": 0, "reason": "bootstrap_baseline",
            "dropped_historic": len(mentions),
        }

    if newest_id:
        await db[STATE_COLLECTION].update_one(
            {"_id": STATE_ID}, {"$set": {"since_id": str(newest_id)}}, upsert=True,
        )

    max_replies = max(1, min(
        _HARD_MAX_REPLIES_PER_TICK, int(cfg.get("max_replies_per_tick", 5)),
    ))
    cooldown_h = int(cfg.get("per_handle_cooldown_hours", 24))
    templates: List[str] = cfg.get("reply_templates") or list(DEFAULT_REPLY_TEMPLATES)
    rotation = int(cfg.get("total_replies_lifetime") or 0)

    own_handle = (ident.get("username") or "").lower()
    fired = 0
    skipped: Dict[str, int] = {}
    log_entries: List[Dict[str, Any]] = []

    # Oldest first — conversation order.
    for m in sorted(mentions, key=lambda t: t.get("id") or ""):
        if fired >= max_replies:
            skipped["tick_budget"] = skipped.get("tick_budget", 0) + 1
            continue
        handle = (m.get("author_handle") or "").strip().lstrip("@")
        tweet_id = m.get("id") or ""
        if not handle or not tweet_id:
            skipped["malformed"] = skipped.get("malformed", 0) + 1
            continue
        if handle.lower() == own_handle:
            skipped["self"] = skipped.get("self", 0) + 1
            continue
        if not _mention_age_ok(m.get("created_at") or ""):
            skipped["too_old"] = skipped.get("too_old", 0) + 1
            continue
        already = await db[MENTION_REPLIES].find_one(
            {"source_tweet_id": tweet_id}, {"_id": 1},
        )
        if already:
            skipped["already_replied"] = skipped.get("already_replied", 0) + 1
            continue
        if await _handle_on_cooldown(handle, cooldown_h):
            skipped["handle_cooldown"] = skipped.get("handle_cooldown", 0) + 1
            continue

        rendered = render_reply(handle, templates, rotation + fired)
        item = {
            "id": str(uuid.uuid4()),
            "rendered_content": rendered,
            "meta": {"reply_to_tweet_id": tweet_id},
        }
        result = await x_dispatcher.send(item, dry_run=bool(dry_run))
        outcome = (
            "dry_run" if dry_run
            else ("sent" if result.outcome == DispatchOutcome.SENT else "failed")
        )
        await _persist_reply(
            author_handle=handle,
            source_tweet_id=tweet_id,
            source_excerpt=m.get("text") or "",
            rendered=rendered,
            outcome=outcome,
            posted_tweet_id=result.platform_message_id,
            error=result.error,
        )
        if outcome in {"sent", "dry_run"}:
            fired += 1
            log_entries.append({
                "handle": handle,
                "source_tweet_id": tweet_id,
                "posted_tweet_id": result.platform_message_id,
                "dry_run": bool(dry_run),
                "preview": rendered[:120],
            })
            if not dry_run and fired < max_replies:
                await asyncio.sleep(_REPLY_SPACING_S)
        else:
            logger.warning(
                "[mention-responder] dispatch failed handle=%s err=%s",
                handle, result.error,
            )

    await _stamp(None if fired else "no_eligible_mentions", fired=fired)
    logger.info(
        "[mention-responder] fired=%d skipped=%s (manual=%s dry_run=%s)",
        fired, skipped, manual, dry_run,
    )
    return {
        "ok": True,
        "fired": fired,
        "fetched": len(mentions),
        "skipped": skipped,
        "dry_run": bool(dry_run),
        "replies": log_entries,
    }


async def tick() -> Dict[str, Any]:
    """APScheduler entry-point — runs every 30 min, self-gates on
    ``poll_interval_hours`` so the real X calls happen ~4×/day by
    default. Never raises."""
    try:
        cfg = await get_settings()
        if not cfg.get("enabled"):
            return {"ok": False, "fired": 0, "reason": "disabled"}
        last = cfg.get("last_polled_at")
        interval_h = max(1, int(cfg.get("poll_interval_hours", 6)))
        if last:
            try:
                last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                if _now() - last_dt < timedelta(hours=interval_h):
                    return {"ok": True, "fired": 0, "reason": "interval_not_elapsed"}
            except ValueError:
                pass
        return await poll_once(manual=False)
    except Exception as exc:  # noqa: BLE001
        logger.exception("[mention-responder] tick crashed")
        return {"ok": False, "fired": 0, "reason": f"crash: {exc}"}


# ---------------------------------------------------------------------
# Read helpers (admin dashboard)
# ---------------------------------------------------------------------
async def list_replies(*, limit: int = 50) -> List[Dict[str, Any]]:
    cursor = db[MENTION_REPLIES].find({}).sort("posted_at", -1).limit(int(limit))
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        out.append({
            "id": d["_id"],
            "author_handle": d.get("author_handle"),
            "source_tweet_id": d.get("source_tweet_id"),
            "source_excerpt": d.get("source_excerpt"),
            "rendered_reply": d.get("rendered_reply"),
            "outcome": d.get("outcome"),
            "posted_tweet_id": d.get("posted_tweet_id"),
            "error": d.get("error"),
            "posted_at": d.get("posted_at"),
        })
    return out


__all__ = [
    "DEFAULT_CFG",
    "DEFAULT_REPLY_TEMPLATES",
    "MENTION_REPLIES",
    "ensure_indexes",
    "get_settings",
    "patch_settings",
    "poll_once",
    "tick",
    "list_replies",
    "render_reply",
]
