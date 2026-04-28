"""Market analytics for the Propaganda Engine.

Responsibilities:
  * Persist a rolling window of price / market-cap snapshots so triggers
    like ``jeet_dip`` can answer “did we drop 20 % in the last 2 min?”
    without keeping volatile state in process memory (which would be lost
    on every backend restart).
  * Convert ``tokens_sold`` from ``vault_state`` into a USD market-cap
    using a simplified Pump.fun bonding-curve formula. The formula is a
    *first-order approximation* — good enough to drive milestone
    triggers; the production figure ultimately comes from DexScreener /
    Helius data once the mint is live.
  * Provide a single ``current_market_snapshot()`` helper so triggers
    don't have to know about Mongo at all.

The price-snapshot collection ``propaganda_price_snapshots`` is created
lazily and gets a TTL index (1 h) so we never accumulate stale rows.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.propaganda.analytics")

# ---------------------------------------------------------------------
# Bonding-curve constants (Pump.fun first-order approximation)
# ---------------------------------------------------------------------
# Pump.fun coins ship with a fixed total supply of 1 000 000 000 tokens
# and a virtual reserves model. We approximate the launch curve as
# ``mc_usd ≈ sol_raised * sol_usd``. Once the mint is live we will pull
# the real MC straight from Helius / DexScreener responses.
TOTAL_SUPPLY = 1_000_000_000


# ---------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    """Create the TTL index on first call. Idempotent."""
    try:
        await db.propaganda_price_snapshots.create_index(
            [("ts", 1)],
            expireAfterSeconds=3600,  # 1 h rolling window
        )
    except Exception:  # noqa: BLE001 — index races on first boot
        pass


async def record_snapshot(
    *,
    price_sol: float,
    mc_usd: float,
    sol_usd: Optional[float] = None,
    source: str = "helius",
) -> None:
    """Append a market snapshot. Cheap — fire-and-forget from any handler."""
    await db.propaganda_price_snapshots.insert_one({
        "ts": datetime.now(timezone.utc),
        "price_sol": float(price_sol),
        "mc_usd": float(mc_usd),
        "sol_usd": float(sol_usd) if sol_usd is not None else None,
        "source": source,
    })


async def recent_snapshots(window_minutes: int) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=max(1, window_minutes))
    cursor = db.propaganda_price_snapshots.find({"ts": {"$gte": cutoff}}).sort("ts", 1)
    return [d async for d in cursor]


# ---------------------------------------------------------------------
# Dip detection
# ---------------------------------------------------------------------
async def detect_dip(
    window_minutes: int = 2,
    threshold_pct: float = 20.0,
) -> Dict[str, Any]:
    """Detect a (≥ threshold_pct) % drop within the last ``window_minutes``.

    We compare the **highest** snapshot in the window to the **latest**
    one — this catches the spike-then-dump pattern the spec describes
    (“price drops 20 % within 2 min after a rally”).

    Returns ``{detected: bool, peak_price, current_price, drop_pct,
    peak_at, current_at}``. Always safe to call — returns
    ``{detected: False, reason: "insufficient_data"}`` when fewer than
    two snapshots exist.
    """
    rows = await recent_snapshots(window_minutes)
    if len(rows) < 2:
        return {"detected": False, "reason": "insufficient_data", "sample_count": len(rows)}
    peak = max(rows, key=lambda r: r.get("price_sol") or 0)
    current = rows[-1]
    peak_price = float(peak.get("price_sol") or 0)
    cur_price = float(current.get("price_sol") or 0)
    if peak_price <= 0:
        return {"detected": False, "reason": "zero_peak"}
    drop_pct = (1.0 - cur_price / peak_price) * 100.0
    return {
        "detected": drop_pct >= float(threshold_pct),
        "drop_pct": round(drop_pct, 2),
        "peak_price": peak_price,
        "current_price": cur_price,
        "peak_at": peak.get("ts").isoformat() if peak.get("ts") else None,
        "current_at": current.get("ts").isoformat() if current.get("ts") else None,
        "window_minutes": window_minutes,
        "threshold_pct": threshold_pct,
    }


# ---------------------------------------------------------------------
# Single-source-of-truth snapshot
# ---------------------------------------------------------------------
async def current_market_snapshot() -> Dict[str, Any]:
    """Return everything a trigger detector might want to read.

    Fields:
      * ``mc_usd``  — latest derived USD market cap (0 when no data)
      * ``price_sol`` — latest token price in SOL (0 when no data)
      * ``last_milestone_usd`` — highest tier we've already announced
      * ``milestone_tiers`` — configured tier list
      * ``dex_token_address`` / ``dex_mode`` — from ``vault_state``
      * ``buy_link`` / ``raydium_link`` — resolved from settings / Cabinet Vault
        when available, else empty strings (templates safely degrade).
    """
    vs = await db.vault_state.find_one({"_id": "protocol_delta_sigma"}) or {}
    settings = await db.propaganda_settings.find_one({"_id": "settings"}) or {}

    # ---- price/MC snapshot ----------------------------------------
    last = await db.propaganda_price_snapshots.find_one(
        {}, sort=[("ts", -1)],
    )
    price_sol = float((last or {}).get("price_sol") or 0)
    mc_usd = float((last or {}).get("mc_usd") or 0)

    # ---- mc_milestone bookkeeping ---------------------------------
    trig_doc = await db.propaganda_triggers.find_one({"_id": "mc_milestone"}) or {}
    meta = trig_doc.get("metadata") or {}
    last_announced = int(meta.get("last_announced_usd") or 0)
    tiers = list(meta.get("tiers_usd") or [10_000, 25_000, 50_000, 100_000])

    # ---- links ----------------------------------------------------
    buy_link = (
        settings.get("buy_link_override")
        or _build_pump_link(vs.get("dex_token_address") or "")
    )
    raydium_link = (
        settings.get("raydium_link_override")
        or _build_raydium_link(vs.get("dex_token_address") or "")
    )

    return {
        "mc_usd": mc_usd,
        "price_sol": price_sol,
        "last_milestone_usd": last_announced,
        "milestone_tiers": tiers,
        "dex_token_address": vs.get("dex_token_address"),
        "dex_mode": vs.get("dex_mode"),
        "helius_pool_address": vs.get("helius_pool_address"),
        "buy_link": buy_link,
        "raydium_link": raydium_link,
        "last_buy": await _last_buy_safe(),
    }


async def _last_buy_safe() -> Dict[str, Any]:
    """Best-effort fetch of the latest whale alert for the trigger
    detectors. Defensive: if the watcher module isn't importable yet
    (cold start race), return an empty dict so the snapshot is still
    usable."""
    try:
        from core import whale_watcher
        return await whale_watcher.last_buy_for_market_snapshot()
    except Exception:  # noqa: BLE001
        return {}


async def bump_last_milestone(amount_usd: int) -> None:
    """Persist the highest milestone we've already announced so we never
    repeat the same tier even if Helius re-emits."""
    await db.propaganda_triggers.update_one(
        {"_id": "mc_milestone"},
        {"$max": {"metadata.last_announced_usd": int(amount_usd)}},
        upsert=True,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _build_pump_link(mint: str) -> str:
    if not mint:
        return ""
    return f"https://pump.fun/{mint}"


def _build_raydium_link(mint: str) -> str:
    if not mint:
        return ""
    return f"https://raydium.io/swap/?inputCurrency=sol&outputCurrency={mint}"
