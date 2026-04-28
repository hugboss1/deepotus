"""KOL X-Mention Listener — foundation (Sprint 16.4).

Architecture (delivered in this commit):

    Source (X API polling | admin simulate)
        └─► kol_listener.enqueue_mention()
                └─► Mongo `kol_mentions` (dedup on tweet_id)
                        └─► APScheduler tick `kol_listener_tick` every 5 min
                                └─► process_pending_mentions()
                                        └─► propaganda_engine.fire("kol_mention", payload)

The actual X-API polling code is **NOT** wired in this commit. It
requires a paid tier (X API v2 user_tweets or filtered stream — both
need at least Basic $100/mo) and the credential the founder shared with
us is currently Bearer-only. Once the tier question is answered, the
polling fetcher slots into ``_fetch_kol_recent_tweets`` (TODO marker
left in code).

What works today:
  * Admin can configure the KOL list via PATCH endpoint.
  * Admin can simulate a mention to E2E-test the propaganda pipeline.
  * Mention dedup, idempotency, status FSM, and tier-aware scheduling
    are all in place.
  * The trigger ``kol_mention`` is registered and 4 templates are
    seeded so any real or simulated mention immediately produces a
    Cabinet-style reply post.

FSM:
  detected → analyzing → propaganda_proposed → notified | skipped | error
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.kol_listener")

KOL_MENTIONS = "kol_mentions"
KOL_CONFIG_COLLECTION = "kol_config"
KOL_CONFIG_SINGLETON_ID = "kol_config_v1"

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
# Polling tick (TODO — wired once X API tier confirmed)
# ---------------------------------------------------------------------
async def poll_x_api_once() -> Dict[str, Any]:
    """Outer poll loop, called by the APScheduler job.

    For now this only drains the queue; the actual X API call is left
    as a TODO so the foundation can ship without depending on a paid
    X tier.
    """
    cfg = await get_config()
    if not cfg.get("enabled"):
        # Still drain whatever is sitting in the queue (e.g. admin
        # simulates) — the kill-switch is for inbound polling, not
        # for the dispatch path.
        drain = await process_pending_mentions(limit=2)
        return {"polled": False, "reason": "disabled", "drain": drain}

    # TODO(sprint-17): hit X API v2 here once tier is confirmed.
    # Pseudo-code:
    #   for handle in cfg["handles"]:
    #       user_id = await _resolve_user_id(handle)
    #       tweets = await _fetch_user_tweets(user_id, since_id=last_seen[handle])
    #       for t in tweets:
    #           if any(term.lower() in t["text"].lower() for term in cfg["match_terms"]):
    #               await enqueue_mention(handle=handle, tweet_text=t["text"], tweet_id=t["id"], tweet_url=...)
    drain = await process_pending_mentions(limit=2)
    return {"polled": True, "fetched": 0, "drain": drain}


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
