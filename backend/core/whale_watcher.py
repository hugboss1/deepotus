"""Whale Watcher — Brain Connect (Sprint 15.2).

Bridges the Helius on-chain BUY stream with the Propaganda Engine.
This module is **observation-only**: it reads what the public chain
shows and turns large public buys into Lore prophecies. It NEVER
holds a private key, NEVER writes a transaction, and NEVER acts on
project wallets.

Pipeline (designed for resilience under bursts of 20+ simultaneous
whales without stalling FastAPI):

    Helius webhook (≤ 200 ms)
        └─► whale_watcher.enqueue_alert()           ◄── stateless DB insert
                └─► Mongo collection `whale_alerts` ◄── single source of truth
                        └─► APScheduler tick (every 5 s, isolated)
                                └─► whale_watcher.process_pending_alerts(limit=1)
                                        └─► propaganda_engine.fire("whale_buy", payload)
                                                └─► propaganda_queue (existing)

FSM (`status` field on every row):
    detected               -> just inserted from Helius (or simulate)
    analyzed               -> tier resolved, ready for propaganda
    propaganda_proposed    -> pushed into propaganda_queue OK
    notified               -> *future*: post 2FA dispatch confirmed
    skipped                -> e.g. below threshold (kept for audit)
    error                  -> exception during processing (kept for replay)

Idempotence: `tx_signature` is unique-indexed at startup, so re-emits
from Helius (or replay polling) cannot double-fire a prophecy.

Why a queue and not direct fire from the webhook? Two reasons:
1. **Latency to Helius**: their webhook expects a 2xx within 5s. Doing
   propaganda dispatch + LLM tone enhancement inline can blow that.
2. **Burst absorption**: at viral peaks 30+ swaps can land in one
   second. The queue + APScheduler tick caps the propaganda fire rate
   at `LIMIT × tick_seconds = 1/5s = 12/min` so the dispatcher rate
   limit (Telegram, X) is respected.

Tiers (public, see /app/docs/TOKENOMICS_TREASURY_POLICY.md §8):
    T1: 5  SOL ≤ amount < 15 SOL   ("Cabinet noted a Class-3 acquisition")
    T2: 15 SOL ≤ amount < 50 SOL   ("Clearance Level 2 detected")
    T3:        amount ≥ 50 SOL      ("Cabinet has been notified")
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.whale_watcher")

WHALE_ALERTS = "whale_alerts"

# ---------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------
THRESHOLD_SOL = 5.0
TIER_T2_LOWER = 15.0
TIER_T3_LOWER = 50.0

TierKey = str  # "T1" | "T2" | "T3"


def tier_for(amount_sol: float) -> Optional[TierKey]:
    """Map a SOL amount to a tier. Returns ``None`` when below threshold
    so callers can early-exit cheaply."""
    try:
        amt = float(amount_sol)
    except (TypeError, ValueError):
        return None
    if amt < THRESHOLD_SOL:
        return None
    if amt < TIER_T2_LOWER:
        return "T1"
    if amt < TIER_T3_LOWER:
        return "T2"
    return "T3"


# ---------------------------------------------------------------------
# Index bootstrap — called from server startup
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    """Idempotent: safe to call multiple times.

    * `tx_signature` is unique-but-partial: only indexed when present so
      simulated alerts (which have no tx) coexist with real ones.
    * `(status, ts)` powers the worker's atomic dequeue and the admin
      audit feed.
    """
    try:
        await db[WHALE_ALERTS].create_index(
            [("tx_signature", 1)],
            unique=True,
            name="whale_alerts_tx_signature_unique",
            partialFilterExpression={
                "tx_signature": {"$exists": True, "$type": "string"},
            },
        )
        await db[WHALE_ALERTS].create_index(
            [("status", 1), ("ts", 1)],
            name="whale_alerts_status_ts",
        )
        await db[WHALE_ALERTS].create_index(
            [("ts", -1)], name="whale_alerts_ts_desc"
        )
    except Exception:  # noqa: BLE001
        logger.exception("[whale-watcher] index bootstrap failed (non-fatal)")


# ---------------------------------------------------------------------
# Truncation helpers (privacy: never publish full wallets in Lore)
# ---------------------------------------------------------------------
def _truncate(addr: Optional[str]) -> str:
    if not addr:
        return ""
    s = str(addr).strip()
    if len(s) < 9:
        return s
    return f"{s[:4]}…{s[-4:]}"


# ---------------------------------------------------------------------
# Enqueue
# ---------------------------------------------------------------------
async def enqueue_alert(
    *,
    buyer: str,
    amount_sol: float,
    tx_signature: Optional[str] = None,
    mint: Optional[str] = None,
    source: str = "helius",
    applied_tokens: Optional[float] = None,
) -> Dict[str, Any]:
    """Insert a fresh `detected` row.

    Returns the inserted document on success. On idempotent re-emit
    (same `tx_signature`) the existing row is returned with status
    `duplicate=True` so the caller can log without raising.
    """
    tier = tier_for(amount_sol)
    if tier is None:
        # Below threshold: still log it for forensics but mark `skipped`
        # so the worker doesn't waste a tick analyzing.
        doc = {
            "_id": str(uuid.uuid4()),
            "buyer": buyer or "",
            "amount_sol": float(amount_sol or 0),
            "tx_signature": tx_signature,
            "mint": mint,
            "tier": None,
            "status": "skipped",
            "skip_reason": f"below_threshold({THRESHOLD_SOL}_sol)",
            "source": source,
            "applied_tokens": applied_tokens,
            "ts": datetime.now(timezone.utc),
        }
        await _insert_idempotent(doc)
        return doc

    doc = {
        "_id": str(uuid.uuid4()),
        "buyer": buyer or "",
        "buyer_short": _truncate(buyer),
        "amount_sol": float(amount_sol),
        "tx_signature": tx_signature,
        "mint": mint,
        "tier": tier,
        "status": "detected",
        "source": source,
        "applied_tokens": applied_tokens,
        "ts": datetime.now(timezone.utc),
        "propaganda_queue_id": None,
        "error": None,
    }
    inserted = await _insert_idempotent(doc)
    if inserted is None:
        # Duplicate tx_signature already enqueued — return the existing row
        # so the caller can short-circuit without breaking idempotence.
        existing = await db[WHALE_ALERTS].find_one(
            {"tx_signature": tx_signature}
        )
        if existing:
            existing["duplicate"] = True
            return existing
        # Race condition: someone else created then deleted between our
        # insert and the find. Return the (un-persisted) doc with a flag.
        doc["duplicate"] = True
        return doc
    return doc


async def _insert_idempotent(doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Insert and absorb DuplicateKey errors silently (idempotence).
    Returns the doc on success or None on duplicate."""
    try:
        await db[WHALE_ALERTS].insert_one(doc)
        return doc
    except Exception as e:  # pymongo.errors.DuplicateKeyError + friends
        msg = str(e)
        if "duplicate key" in msg.lower() or "E11000" in msg:
            return None
        logger.exception("[whale-watcher] enqueue insert failed")
        raise


# ---------------------------------------------------------------------
# Worker loop (called by APScheduler every 5s)
# ---------------------------------------------------------------------
async def process_pending_alerts(limit: int = 1) -> Dict[str, int]:
    """Drain up to `limit` `detected` alerts and forward each to the
    Propaganda Engine.

    Each pop is atomic via `find_one_and_update` so a second concurrent
    worker (e.g. a misfire grace catch-up) cannot double-process the
    same row.

    Returns counters: {processed, skipped, errored, drained}.
    """
    # Lazy import to avoid a circular import at module load time
    # (propaganda_engine imports market_analytics which is read-only).
    from core import propaganda_engine

    processed = 0
    skipped = 0
    errored = 0

    for _ in range(max(1, int(limit))):
        # Atomic claim: flip detected -> analyzing in a single op
        claimed = await db[WHALE_ALERTS].find_one_and_update(
            {"status": "detected"},
            {
                "$set": {
                    "status": "analyzing",
                    "claimed_at": datetime.now(timezone.utc),
                },
            },
            sort=[("ts", 1)],  # FIFO
            return_document=True,  # post-update doc
        )
        if not claimed:
            break

        try:
            payload = {
                "whale_amount": round(float(claimed["amount_sol"]), 2),
                "buyer_short": claimed.get("buyer_short")
                or _truncate(claimed.get("buyer", "")),
                "tx_signature": claimed.get("tx_signature") or "",
                "tier": claimed.get("tier") or "T1",
            }

            # Build a market context the trigger detector can consume.
            # `current_market_snapshot()` is enriched with `last_buy` via
            # our own helper so the snapshot path stays consistent — but
            # we override here too because (a) the snapshot is at most
            # 1 second behind and (b) the burst path may pop multiple
            # rows in a row, each needing its own `last_buy` view.
            from core import market_analytics  # local import — circular safe

            market = await market_analytics.current_market_snapshot()
            market["last_buy"] = {
                "amount_sol": float(claimed["amount_sol"]),
                "buyer": claimed.get("buyer", ""),
                "tx_signature": claimed.get("tx_signature") or "",
                "tier": claimed.get("tier"),
            }

            # Push into Propaganda — this proposes a queue item using the
            # `whale_buy` trigger which, in turn, picks a template (with
            # tier-aware filtering once 15.2.5 lands).
            res = await propaganda_engine.fire(
                trigger_key="whale_buy",
                manual=False,
                market=market,
                payload_override=payload,
            )

            now = datetime.now(timezone.utc)
            if res and res.get("ok") and res.get("queue_item"):
                queue_item = res["queue_item"]
                await db[WHALE_ALERTS].update_one(
                    {"_id": claimed["_id"]},
                    {
                        "$set": {
                            "status": "propaganda_proposed",
                            "propaganda_queue_id": queue_item.get("id"),
                            "propaganda_proposed_at": now,
                            "llm_used": bool(res.get("llm_used")),
                        }
                    },
                )
                processed += 1
            else:
                # Fire returned ok=False — likely panic ON, trigger disabled,
                # cooldown active, or no template. Mark skipped (with
                # context) so the audit feed still shows the alert.
                reason = (res or {}).get("reason") or "propaganda_fire_returned_none"
                await db[WHALE_ALERTS].update_one(
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
                "[whale-watcher] failed to process alert %s",
                claimed.get("_id"),
            )
            await db[WHALE_ALERTS].update_one(
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
# Read helpers (used by routers)
# ---------------------------------------------------------------------
async def list_alerts(
    *,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if status:
        q["status"] = status
    if tier:
        q["tier"] = tier
    cursor = db[WHALE_ALERTS].find(q).sort("ts", -1).limit(int(limit))
    return [d async for d in cursor]


async def public_recent(*, limit: int = 10) -> List[Dict[str, Any]]:
    """Return a privacy-respectful projection for the public Lore feed.

    Drops `buyer` (full pubkey), `tx_signature`, and any internal field.
    Keeps only what the Cabinet narrative needs.
    """
    cursor = (
        db[WHALE_ALERTS]
        .find({"status": {"$in": ["propaganda_proposed", "notified"]}})
        .sort("ts", -1)
        .limit(int(limit))
    )
    out: List[Dict[str, Any]] = []
    async for d in cursor:
        out.append(
            {
                "id": d["_id"],
                "tier": d.get("tier"),
                "amount_sol": _bucket(d.get("amount_sol", 0)),
                "buyer_short": d.get("buyer_short") or "",
                "ts": d.get("ts"),
            }
        )
    return out


def _bucket(amt: float) -> float:
    """Round to a coarse bucket so the public feed never reveals the
    exact buy size (privacy + makes the chart-watching less actionable
    for would-be front-runners)."""
    try:
        v = float(amt)
    except (TypeError, ValueError):
        return 0.0
    if v < 10:
        return round(v, 1)
    if v < 50:
        return round(v / 5) * 5
    if v < 200:
        return round(v / 10) * 10
    return round(v / 50) * 50


async def stats_snapshot() -> Dict[str, Any]:
    """Used by the admin dashboard widget."""
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    pipeline = [
        {"$match": {"ts": {"$gte": cutoff_24h}}},
        {
            "$group": {
                "_id": "$tier",
                "n": {"$sum": 1},
                "sol_sum": {"$sum": "$amount_sol"},
            }
        },
    ]
    by_tier: Dict[str, Dict[str, float]] = {}
    async for row in db[WHALE_ALERTS].aggregate(pipeline):
        by_tier[row["_id"] or "_skipped"] = {
            "n": int(row["n"]),
            "sol_sum": round(float(row["sol_sum"] or 0), 2),
        }
    pending = await db[WHALE_ALERTS].count_documents({"status": "detected"})
    errored = await db[WHALE_ALERTS].count_documents({"status": "error"})
    return {
        "by_tier_24h": by_tier,
        "pending": pending,
        "errored": errored,
    }


# ---------------------------------------------------------------------
# Last-buy projection — feeds market_analytics.current_market_snapshot()
# ---------------------------------------------------------------------
async def last_buy_for_market_snapshot() -> Dict[str, Any]:
    """Latest non-skipped alert, packaged for the Propaganda trigger
    detector. Returns an empty dict if there's nothing to report."""
    doc = await db[WHALE_ALERTS].find_one(
        {"status": {"$in": ["detected", "analyzing", "propaganda_proposed", "notified"]}},
        sort=[("ts", -1)],
    )
    if not doc:
        return {}
    return {
        "amount_sol": float(doc.get("amount_sol", 0)),
        "buyer": doc.get("buyer", ""),
        "tx_signature": doc.get("tx_signature", ""),
        "tier": doc.get("tier"),
    }
