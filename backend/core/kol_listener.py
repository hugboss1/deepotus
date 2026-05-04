"""KOL X-Mention Listener — Sprint 16.4 + Sprint P1 (live polling).

Architecture:

    Source (X API v2 polling | admin simulate)
        └─► kol_listener.enqueue_mention()
                └─► Mongo `kol_mentions` (dedup on tweet_id)
                        └─► APScheduler tick `kol_listener_tick` every 5 min
                                └─► process_pending_mentions()
                                        └─► propaganda_engine.fire("kol_mention", payload)

Live polling contract (Sprint P1):
    For each handle in ``kol_config.handles`` where ``enabled=true``:
      1. Resolve handle → user_id via ``GET /2/users/by/username/:handle``
         (cached for 7 days in ``kol_user_id_cache``).
      2. Fetch recent tweets via ``GET /2/users/:id/tweets`` using
         ``since_id=last_seen_id`` to avoid re-processing.
      3. Filter by ``match_terms`` (case-insensitive substring match).
      4. ``enqueue_mention()`` for each hit — dedup on tweet_id.
      5. Persist the new ``last_seen_id`` to ``kol_poll_state`` so the
         next tick picks up where we left off.

Auth strategy:
    The GET endpoints accept **App-only Bearer auth** (higher rate
    limits, single token), which is cheaper than OAuth1.0a. We pull
    ``X_BEARER_TOKEN`` from the Cabinet Vault (``x_twitter/X_BEARER_TOKEN``)
    via ``get_twitter_bearer_token()``. If absent, polling stays inert
    (logs a warning once per tick; queue drainage continues).

Rate-limit awareness:
    With the Pay-Per-Use tier + Bearer, both endpoints we use share
    the Essential/Basic ceilings:
      • GET /2/users/by/username/:handle  → 300/15min (user-tier)
      • GET /2/users/:id/tweets           → 1500/15min (per user token)
    At 10 handles × ~1 tick / 5 min → 120 req/hour → well under caps.
    A transient 429 bails out of the current tick cleanly.

FSM:
  detected → analyzing → propaganda_proposed | skipped | error
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

from core.config import db
from core.secret_provider import get_twitter_bearer_token

logger = logging.getLogger("deepotus.kol_listener")

KOL_MENTIONS = "kol_mentions"
KOL_CONFIG_COLLECTION = "kol_config"
KOL_CONFIG_SINGLETON_ID = "kol_config_v1"
KOL_USER_ID_CACHE = "kol_user_id_cache"
KOL_POLL_STATE = "kol_poll_state"

# ---- X API v2 configuration ----------------------------------------
_X_API_BASE = "https://api.twitter.com/2"
_X_REQUEST_TIMEOUT_S = 12.0
# TTL for the handle → user_id resolution. Handles almost never rotate;
# 7 days strikes a balance between freshness and X request budget.
_USER_ID_CACHE_TTL_S = 7 * 24 * 3600
# Hard ceiling on tweets fetched per handle per tick. X's minimum is 5
# and maximum is 100; 10 is plenty given we poll every 5 min.
_MAX_TWEETS_PER_HANDLE = 10

# Default KOL list (configured by the founder, Sprint 16 onboarding).
# Stored verbatim — handles only, no wallets (β scope per user choice).
DEFAULT_KOL_HANDLES: List[str] = [
    "aeyakovenko",
    "Ansem",
    "SolBigBrain",
    "pumpdotfun",
    "JupiterExchange",
    "phantom",
    "solana",
    "blknoiz06",
    "weremeow",
    "SBF_Is_Free",
]


# ---------------------------------------------------------------------
# Indexes / bootstrap
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    try:
        await db[KOL_MENTIONS].create_index(
            [("tweet_id", 1)],
            unique=True,
            name="kol_mentions_tweet_id_unique",
            partialFilterExpression={
                "tweet_id": {"$exists": True, "$type": "string"},
            },
        )
        await db[KOL_MENTIONS].create_index(
            [("status", 1), ("ts", 1)],
            name="kol_mentions_status_ts",
        )
        await db[KOL_MENTIONS].create_index(
            [("ts", -1)], name="kol_mentions_ts_desc"
        )
        # New (Sprint P1 live polling): indexes for the user_id cache
        # and the per-handle poll state. Both are keyed on the
        # lowercased handle as ``_id`` so no secondary index is
        # strictly required — but we add a TTL on the user_id cache to
        # auto-expire stale resolutions in case the handle rotates.
        await db[KOL_USER_ID_CACHE].create_index(
            [("cached_at", 1)],
            name="kol_user_id_cache_ttl",
            expireAfterSeconds=_USER_ID_CACHE_TTL_S,
        )
    except Exception:  # noqa: BLE001
        logger.exception("[kol-listener] index bootstrap failed")


async def seed_default_config() -> Dict[str, Any]:
    """Idempotent: seed the singleton config row on first boot."""
    existing = await db[KOL_CONFIG_COLLECTION].find_one(
        {"_id": KOL_CONFIG_SINGLETON_ID}
    )
    if existing:
        return existing
    row = {
        "_id": KOL_CONFIG_SINGLETON_ID,
        "enabled": False,  # OFF by default — admin enables explicitly
        "handles": list(DEFAULT_KOL_HANDLES),
        "min_followers": 10_000,  # noise filter on real polling
        "match_terms": ["$DEEPOTUS", "deepotus", "PROTOCOL ΔΣ", "protocol delta sigma"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db[KOL_CONFIG_COLLECTION].insert_one(row)
    return row


# ---------------------------------------------------------------------
# Config getters/setters
# ---------------------------------------------------------------------
async def get_config() -> Dict[str, Any]:
    row = await db[KOL_CONFIG_COLLECTION].find_one(
        {"_id": KOL_CONFIG_SINGLETON_ID}
    )
    if not row:
        row = await seed_default_config()
    return row


async def update_config(patch: Dict[str, Any]) -> Dict[str, Any]:
    """Whitelist-style update — refuses unknown keys."""
    allowed = {"enabled", "handles", "min_followers", "match_terms"}
    safe = {k: v for k, v in patch.items() if k in allowed}
    if "handles" in safe:
        # Strip leading @ and trim whitespace so the admin can paste either form.
        cleaned = []
        seen = set()
        for h in safe["handles"]:
            s = str(h or "").strip().lstrip("@")
            if not s or s in seen:
                continue
            seen.add(s)
            cleaned.append(s)
        safe["handles"] = cleaned
    safe["updated_at"] = datetime.now(timezone.utc)
    await db[KOL_CONFIG_COLLECTION].update_one(
        {"_id": KOL_CONFIG_SINGLETON_ID},
        {"$set": safe},
        upsert=True,
    )
    return await get_config()


# ---------------------------------------------------------------------
# Mention enqueue (called by polling OR admin simulate)
# ---------------------------------------------------------------------
async def enqueue_mention(
    *,
    handle: str,
    tweet_text: str,
    tweet_id: Optional[str] = None,
    tweet_url: Optional[str] = None,
    source: str = "x_polling",
) -> Dict[str, Any]:
    """Idempotent insert. Returns the inserted doc on first hit, the
    existing one on duplicate (with ``duplicate=True`` flag)."""
    handle_clean = (handle or "").strip().lstrip("@")
    excerpt = (tweet_text or "")[:240]
    doc = {
        "_id": str(uuid.uuid4()),
        "handle": handle_clean,
        "tweet_id": tweet_id,
        "tweet_url": tweet_url,
        "tweet_text_excerpt": excerpt,
        "status": "detected",
        "source": source,
        "ts": datetime.now(timezone.utc),
        "propaganda_queue_id": None,
        "error": None,
    }
    try:
        await db[KOL_MENTIONS].insert_one(doc)
        return doc
    except Exception as e:  # noqa: BLE001
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            existing = await db[KOL_MENTIONS].find_one({"tweet_id": tweet_id})
            if existing:
                existing["duplicate"] = True
                return existing
            doc["duplicate"] = True
            return doc
        logger.exception("[kol-listener] enqueue insert failed")
        raise


# ---------------------------------------------------------------------
# Worker tick (drain detected -> propaganda_proposed)
# ---------------------------------------------------------------------
async def process_pending_mentions(limit: int = 1) -> Dict[str, int]:
    from core import propaganda_engine  # circular-safe local import

    processed = 0
    skipped = 0
    errored = 0
    for _ in range(max(1, int(limit))):
        claimed = await db[KOL_MENTIONS].find_one_and_update(
            {"status": "detected"},
            {
                "$set": {
                    "status": "analyzing",
                    "claimed_at": datetime.now(timezone.utc),
                }
            },
            sort=[("ts", 1)],
            return_document=True,
        )
        if not claimed:
            break

        try:
            payload = {
                "kol_handle": claimed.get("handle") or "",
                "kol_tweet_excerpt": (
                    claimed.get("tweet_text_excerpt") or ""
                )[:200],
                "kol_tweet_url": claimed.get("tweet_url") or "",
            }
            res = await propaganda_engine.fire(
                trigger_key="kol_mention",
                manual=True,
                payload_override=payload,
            )
            now = datetime.now(timezone.utc)
            if res and res.get("ok") and res.get("queue_item"):
                await db[KOL_MENTIONS].update_one(
                    {"_id": claimed["_id"]},
                    {
                        "$set": {
                            "status": "propaganda_proposed",
                            "propaganda_queue_id": res["queue_item"].get("id"),
                            "propaganda_proposed_at": now,
                        }
                    },
                )
                processed += 1
            else:
                reason = (res or {}).get("reason") or "fire_returned_none"
                await db[KOL_MENTIONS].update_one(
                    {"_id": claimed["_id"]},
                    {
                        "$set": {
                            "status": "skipped",
                            "skip_reason": f"propaganda:{reason}",
                            "skipped_at": now,
                        }
                    },
                )
                skipped += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "[kol-listener] failed to process mention %s",
                claimed.get("_id"),
            )
            await db[KOL_MENTIONS].update_one(
                {"_id": claimed["_id"]},
                {
                    "$set": {
                        "status": "error",
                        "error": str(exc)[:500],
                        "errored_at": datetime.now(timezone.utc),
                    }
                },
            )
            errored += 1

    return {"processed": processed, "skipped": skipped, "errored": errored}


# ---------------------------------------------------------------------
# Live X API v2 polling (Sprint P1)
# ---------------------------------------------------------------------
async def _resolve_user_id(handle: str, bearer: str) -> Optional[str]:
    """Resolve a handle to its numeric X user_id.

    Cached in ``kol_user_id_cache`` for 7 days. A cache miss (or
    staleness) triggers ``GET /2/users/by/username/:handle``. Returns
    ``None`` if X says the handle doesn't exist or the call fails — the
    caller logs + skips that handle for this tick.
    """
    handle = (handle or "").strip().lstrip("@")
    if not handle:
        return None
    now = datetime.now(timezone.utc)
    cached = await db[KOL_USER_ID_CACHE].find_one({"_id": handle.lower()})
    if cached and cached.get("user_id"):
        # Staleness check. The cache doc stores the resolution time so
        # we can force a refresh after the TTL.
        cached_at: datetime = cached.get("cached_at") or now
        if isinstance(cached_at, str):  # defensive: legacy rows
            try:
                cached_at = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
            except ValueError:
                cached_at = now - timedelta(seconds=_USER_ID_CACHE_TTL_S + 1)
        age_s = (now - cached_at).total_seconds()
        if age_s < _USER_ID_CACHE_TTL_S:
            return str(cached["user_id"])

    # Cache miss or stale — hit X.
    url = f"{_X_API_BASE}/users/by/username/{handle}"
    try:
        async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {bearer}"},
            )
    except httpx.TimeoutException:
        logger.warning("[kol-listener] user_id lookup timeout handle=%s", handle)
        return None
    except Exception:  # noqa: BLE001
        logger.exception("[kol-listener] user_id lookup crashed handle=%s", handle)
        return None

    if resp.status_code == 429:
        logger.warning(
            "[kol-listener] user_id rate-limited handle=%s — skipping tick",
            handle,
        )
        return None
    if resp.status_code >= 400:
        logger.warning(
            "[kol-listener] user_id lookup http_%d handle=%s body=%s",
            resp.status_code,
            handle,
            (resp.text or "")[:160],
        )
        return None
    data = (resp.json() or {}).get("data") or {}
    user_id = data.get("id")
    if not user_id:
        logger.warning(
            "[kol-listener] user_id not in response handle=%s body=%s",
            handle,
            (resp.text or "")[:160],
        )
        return None
    # Persist. We do an upsert keyed on the lowercased handle so
    # casing differences don't churn the cache.
    await db[KOL_USER_ID_CACHE].update_one(
        {"_id": handle.lower()},
        {
            "$set": {
                "user_id": str(user_id),
                "handle_cased": handle,
                "cached_at": now,
            }
        },
        upsert=True,
    )
    return str(user_id)


async def _fetch_kol_recent_tweets(
    user_id: str,
    *,
    since_id: Optional[str],
    bearer: str,
    limit: int = _MAX_TWEETS_PER_HANDLE,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Fetch recent tweets for ``user_id`` via X API v2.

    Returns ``(tweets, newest_id_seen)``. ``tweets`` is a list of dicts
    shaped like ``{"id", "text", "created_at"}``. ``newest_id_seen`` is
    the X-reported ``meta.newest_id`` (or None when the feed was empty).

    Args:
      user_id: numeric X user id (from ``_resolve_user_id``).
      since_id: if set, X returns only tweets *strictly newer*. First
        tick after enabling the listener passes ``None`` so the baseline
        is established from the next poll onwards (we drop the initial
        batch to avoid flooding the queue on bootstrap).
      bearer: App-only bearer token.
      limit: 5–100 per X's validation.

    Failure modes are logged (not raised) so a bad handle doesn't brick
    the tick — the caller treats an empty list as "no hits".
    """
    url = f"{_X_API_BASE}/users/{user_id}/tweets"
    # Ask X for the few fields we actually use downstream. Excluding
    # retweets + replies keeps the signal-to-noise high for KOL
    # mentions (KOLs rarely retweet a memecoin post they care about).
    params: Dict[str, Any] = {
        "max_results": max(5, min(100, int(limit))),
        "exclude": "retweets,replies",
        "tweet.fields": "created_at,text,lang",
    }
    if since_id:
        params["since_id"] = str(since_id)
    try:
        async with httpx.AsyncClient(timeout=_X_REQUEST_TIMEOUT_S) as client:
            resp = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {bearer}"},
            )
    except httpx.TimeoutException:
        logger.warning("[kol-listener] tweets fetch timeout user_id=%s", user_id)
        return [], None
    except Exception:  # noqa: BLE001
        logger.exception("[kol-listener] tweets fetch crashed user_id=%s", user_id)
        return [], None

    if resp.status_code == 429:
        logger.warning(
            "[kol-listener] tweets rate-limited user_id=%s — skipping", user_id,
        )
        return [], None
    if resp.status_code >= 400:
        logger.warning(
            "[kol-listener] tweets http_%d user_id=%s body=%s",
            resp.status_code,
            user_id,
            (resp.text or "")[:160],
        )
        return [], None
    payload = resp.json() or {}
    tweets: List[Dict[str, Any]] = payload.get("data") or []
    meta: Dict[str, Any] = payload.get("meta") or {}
    newest_id = meta.get("newest_id")
    return tweets, newest_id


async def _get_poll_state(handle_lower: str) -> Dict[str, Any]:
    """Return the persisted ``{last_seen_id}`` row for a handle, or an
    empty dict if we've never polled it before."""
    row = await db[KOL_POLL_STATE].find_one({"_id": handle_lower})
    return row or {}


async def _set_last_seen_id(handle_lower: str, tweet_id: str) -> None:
    await db[KOL_POLL_STATE].update_one(
        {"_id": handle_lower},
        {
            "$set": {
                "last_seen_id": str(tweet_id),
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )


def _match_terms_hit(text: str, match_terms: List[str]) -> bool:
    """Case-insensitive substring match. Any hit is a hit."""
    lowered = (text or "").lower()
    for term in match_terms or []:
        t = str(term or "").strip().lower()
        if t and t in lowered:
            return True
    return False


# ---------------------------------------------------------------------
# Polling tick (REAL — Sprint P1)
# ---------------------------------------------------------------------
async def poll_x_api_once() -> Dict[str, Any]:
    """Outer poll loop, called every 5 min by the APScheduler job.

    Contract:
      * ``cfg.enabled == False`` → skip the inbound polling path but
        still drain ``detected`` mentions (admin-simulate path is
        independent of the kill-switch).
      * ``X_BEARER_TOKEN`` missing → same behaviour as disabled, plus a
        one-line warning (no loud alerting; this is the expected state
        during the first post-deploy boot).
      * For each handle:
          - resolve user_id (cached)
          - fetch tweets since ``last_seen_id``
          - enqueue any match (dedup by tweet_id)
          - persist newest_id as the new last_seen_id
    """
    cfg = await get_config()
    match_terms = cfg.get("match_terms") or []

    # Always drain whatever was queued (admin-simulate + previous ticks).
    drain = await process_pending_mentions(limit=2)

    if not cfg.get("enabled"):
        return {"polled": False, "reason": "disabled", "drain": drain}

    bearer = await get_twitter_bearer_token()
    if not bearer:
        logger.warning(
            "[kol-listener] enabled=true but X_BEARER_TOKEN missing in vault — skipping poll",
        )
        return {"polled": False, "reason": "no_bearer_token", "drain": drain}

    handles = cfg.get("handles") or []
    total_fetched = 0
    total_enqueued = 0
    handles_processed = 0
    handles_skipped = 0

    for handle in handles:
        handle = (handle or "").strip().lstrip("@")
        if not handle:
            handles_skipped += 1
            continue
        handle_lower = handle.lower()
        user_id = await _resolve_user_id(handle, bearer)
        if not user_id:
            handles_skipped += 1
            continue

        state = await _get_poll_state(handle_lower)
        last_seen_id = state.get("last_seen_id")

        tweets, newest_id = await _fetch_kol_recent_tweets(
            user_id,
            since_id=last_seen_id,
            bearer=bearer,
        )
        total_fetched += len(tweets)
        handles_processed += 1

        # Bootstrap rule: on the very first poll for a handle
        # (``last_seen_id`` is None) we DON'T enqueue the batch — we
        # only record ``newest_id`` so the next tick picks up from
        # there. This prevents a 100-tweet historic dump from swamping
        # the propaganda queue on day 1.
        if last_seen_id is None:
            if newest_id:
                await _set_last_seen_id(handle_lower, newest_id)
                logger.info(
                    "[kol-listener] bootstrap baseline set handle=%s newest_id=%s (dropped %d historic tweets)",
                    handle,
                    newest_id,
                    len(tweets),
                )
            continue

        # Normal path — filter + enqueue.
        for tw in tweets:
            text = (tw.get("text") or "")
            if not _match_terms_hit(text, match_terms):
                continue
            tweet_url = f"https://x.com/{handle}/status/{tw.get('id')}"
            res = await enqueue_mention(
                handle=handle,
                tweet_text=text,
                tweet_id=str(tw.get("id") or ""),
                tweet_url=tweet_url,
                source="x_polling",
            )
            if not res.get("duplicate"):
                total_enqueued += 1

        # Update the bookmark so the next tick is scoped to the newer
        # tail. We prefer X's own ``newest_id`` because it reflects the
        # exact slice X served us (accounting for exclude=retweets).
        if newest_id:
            await _set_last_seen_id(handle_lower, newest_id)

    # Second drain pass so newly-enqueued mentions can be processed in
    # the same tick (avoids a 5-min latency between detection and
    # queue proposal when the listener is catching up).
    if total_enqueued:
        drain2 = await process_pending_mentions(limit=max(1, total_enqueued))
        drain = {
            k: int(drain.get(k, 0) or 0) + int(drain2.get(k, 0) or 0)
            for k in {"processed", "skipped", "errored"}
        }

    return {
        "polled": True,
        "handles_processed": handles_processed,
        "handles_skipped": handles_skipped,
        "fetched": total_fetched,
        "enqueued": total_enqueued,
        "drain": drain,
    }


# ---------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------
async def list_mentions(
    *,
    status: Optional[str] = None,
    handle: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if status:
        q["status"] = status
    if handle:
        q["handle"] = handle.strip().lstrip("@")
    cursor = db[KOL_MENTIONS].find(q).sort("ts", -1).limit(int(limit))
    return [d async for d in cursor]


async def stats_snapshot() -> Dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    pipeline = [
        {"$match": {"ts": {"$gte": cutoff}}},
        {"$group": {"_id": "$status", "n": {"$sum": 1}}},
    ]
    by_status: Dict[str, int] = {}
    async for row in db[KOL_MENTIONS].aggregate(pipeline):
        by_status[row["_id"]] = int(row["n"])
    pending = await db[KOL_MENTIONS].count_documents({"status": "detected"})
    cfg = await get_config()
    return {
        "by_status_24h": by_status,
        "pending": pending,
        "enabled": bool(cfg.get("enabled")),
        "kol_count": len(cfg.get("handles") or []),
    }
