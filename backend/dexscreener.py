"""
DexScreener integration for PROTOCOL ΔΣ.

Polls https://api.dexscreener.com every 30 seconds, detects NEW buy activity on
the configured Solana token, and converts that activity into vault crack events.

Modes (stored in vault_state.dex_mode):
  - "off"    : no polling, vault only advances via admin/hourly
  - "demo"   : poll a well-known demo token (BONK by default) to illustrate
               activity end-to-end before $DEEPOTUS is deployed on Solana.
               Ticks are SYMBOLIC (1 tick per N new buys detected) to avoid
               saturating the vault.
  - "custom" : poll the real $DEEPOTUS token address. Strict math: 1 tick per
               `tokens_per_digit` (default 1,000) tokens bought (choice `b` from user).

State fields on vault_state (all optional; defaulted on initialize):
  - dex_mode                  : "off" | "demo" | "custom"
  - dex_token_address         : str (Solana mint address) or null
  - dex_demo_token_address    : str (default BONK mint)
  - dex_last_poll_at          : ISO datetime
  - dex_last_h24_buys         : int   (last observed txns.h24.buys)
  - dex_last_h24_sells        : int   (last observed txns.h24.sells)
  - dex_last_h24_volume_usd   : float (last observed volume.h24)
  - dex_last_price_usd        : float (last observed priceUsd)
  - dex_carry_tokens          : float (carry-over tokens < tokens_per_digit)
  - dex_pair_symbol           : str (e.g. "BONK/SOL" for display)
  - dex_label                 : str  short display string for public UI
  - dex_error                 : str | null (last error, if any)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

VAULT_DOC_ID = "protocol_delta_sigma"

# BONK ticker mint on Solana — highly active memecoin, perfect for demo
DEMO_TOKEN_ADDRESS = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"

# Sprint 17.5c — DexScreener public API rate-limit hardening.
# DexScreener throttles aggressive callers to ~300 req/min per IP. Our
# pre-mint demo loop was polling every 30s which collided with the
# whale watcher + holders poller hitting the same host, occasionally
# returning HTTP 429. Two mitigations apply:
#   1. POLL_SECONDS bumped from 30 → 60s — halves baseline traffic.
#   2. ``_BACKOFF_SCHEDULE`` kicks in on 429: each successive 429
#      doubles the wait (capped at 30 min) and the loop sleeps until
#      ``dex_backoff_until`` clears. The counter resets to 0 the next
#      time we get a 200.
POLL_SECONDS = 60
HTTP_TIMEOUT = 8.0
DEX_API = "https://api.dexscreener.com/latest/dex/tokens"

# Exponential backoff schedule when DexScreener returns 429. Index =
# consecutive 429 count; capped via the last entry so a stuck loop
# can't melt down to silence forever (a 30-min cap means a worst-case
# 1 missed cycle on the public site every half-hour).
_BACKOFF_SCHEDULE_S: tuple[int, ...] = (
    60,    # 1 min
    180,   # 3 min
    300,   # 5 min
    600,   # 10 min
    1200,  # 20 min
    1800,  # 30 min — cap
)


def _backoff_seconds_for(attempt: int) -> int:
    """Return the wait seconds for the Nth consecutive 429."""
    if attempt <= 0:
        return 0
    idx = min(attempt - 1, len(_BACKOFF_SCHEDULE_S) - 1)
    return _BACKOFF_SCHEDULE_S[idx]

# Demo mode: emit 1 tick per N new buys detected (avoids blowing up the vault on BONK)
DEMO_BUYS_PER_TICK = 5
DEMO_MAX_TICKS_PER_POLL = 3


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------
# Low-level fetch + normalization
# ---------------------------------------------------------------------
async def _fetch_token_stats(address: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Call DexScreener /tokens/{address} and return ``(pair, error)``.

    Returns:
        ``(pair, None)`` on success — pair is the most-active Solana pair.
        ``(None, "rate_limited")`` when DexScreener answered HTTP 429 —
            the orchestrator arms exponential backoff.
        ``(None, "http_<status>")`` for other non-200 responses
            (transient: 5xx, permanent: 4xx other than 429).
        ``(None, "no_pairs")`` when the token has no Solana pair yet.
        ``(None, "fetch_error")`` on network exceptions.
    """
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(f"{DEX_API}/{address}")
            if r.status_code == 429:
                logging.warning("[dex] HTTP 429 from DexScreener — backing off")
                return None, "rate_limited"
            if r.status_code != 200:
                logging.warning(
                    "[dex] non-200 for %s: %d", address, r.status_code,
                )
                return None, f"http_{r.status_code}"
            data = r.json()
            pairs = data.get("pairs") or []
            if not pairs:
                return None, "no_pairs"
            # Keep Solana pairs, sort by trade activity (buys + sells on 24h window)
            # This ensures we track the LIVELY pair, not the deepest-but-idle one.
            solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
            if not solana_pairs:
                return None, "no_solana_pair"

            def _activity_score(p):
                txns = (p.get("txns") or {}).get("h24") or {}
                return int(txns.get("buys") or 0) + int(txns.get("sells") or 0)

            solana_pairs.sort(key=_activity_score, reverse=True)
            return solana_pairs[0], None
    except Exception as e:
        logging.exception(f"[dex] fetch error for {address}: {e}")
        return None, "fetch_error"


def _extract_stats(pair: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize DexScreener pair payload to just what we need."""
    price = pair.get("priceUsd") or 0
    try:
        price = float(price)
    except Exception:
        price = 0.0

    vol = pair.get("volume") or {}
    txns = pair.get("txns") or {}
    h24 = txns.get("h24") or {}
    base = pair.get("baseToken") or {}
    quote = pair.get("quoteToken") or {}

    return {
        "price_usd": price,
        "volume_h24": float(vol.get("h24") or 0),
        "buys_h24": int(h24.get("buys") or 0),
        "sells_h24": int(h24.get("sells") or 0),
        "liquidity_usd": float((pair.get("liquidity") or {}).get("usd") or 0),
        "pair_address": pair.get("pairAddress"),
        "dex_id": pair.get("dexId"),
        "base_symbol": base.get("symbol", "?"),
        "quote_symbol": quote.get("symbol", "?"),
    }


def _agent_code_for(pair_symbol: str, agent_index: int = 0) -> str:
    tag = (pair_symbol or "DEX").upper().split("/")[0][:8]
    return f"DEX-{tag}-{agent_index:04d}"


# ---------------------------------------------------------------------
# Mode-specific helpers (split from dex_poll_once for readability)
# ---------------------------------------------------------------------
def _resolve_token_address(
    doc: Dict[str, Any], mode: str
) -> Tuple[Optional[str], Optional[str]]:
    """Return (address, error). `address` is None when polling should be skipped."""
    if mode == "demo":
        return doc.get("dex_demo_token_address") or DEMO_TOKEN_ADDRESS, None
    address = (doc.get("dex_token_address") or "").strip()
    if not address:
        return None, "no token_address"
    return address, None


def _compute_deltas(
    doc: Dict[str, Any], s: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare the newly-fetched stats to the last-known snapshot on the doc.

    The DexScreener h24 window is rolling, so counts can occasionally decrease.
    We clamp negative deltas to zero to avoid spurious 'activity'.
    """
    last_buys = int(doc.get("dex_last_h24_buys") or 0)
    last_sells = int(doc.get("dex_last_h24_sells") or 0)
    last_vol = float(doc.get("dex_last_h24_volume_usd") or 0)
    first_seen = not bool(doc.get("dex_last_poll_at"))
    return {
        "delta_buys": max(0, s["buys_h24"] - last_buys),
        "delta_sells": max(0, s["sells_h24"] - last_sells),
        "delta_vol_usd": max(0.0, s["volume_h24"] - last_vol),
        "carry": float(doc.get("dex_carry_tokens") or 0),
        "first_seen": first_seen,
    }


async def _apply_demo_ticks(
    db,
    vault_mod,
    doc: Dict[str, Any],
    s: Dict[str, Any],
    pair_symbol: str,
    delta_buys: int,
) -> int:
    """Emit up to DEMO_MAX_TICKS_PER_POLL symbolic purchase events.

    Each event is sized so that the demo feels alive without instantly cracking
    the vault at production scale (100M per dial).
    """
    tokens_per_digit = int(doc.get("tokens_per_digit") or 1000)
    tokens_per_micro = int(doc.get("tokens_per_micro") or 10_000)
    # Aim for a single buy event to produce roughly ~3-10 micro-rotations visibly
    demo_tick_tokens = max(
        tokens_per_micro * 3, min(tokens_per_digit // 50, 2_000_000)
    )
    potential_ticks = min(
        DEMO_MAX_TICKS_PER_POLL, delta_buys // DEMO_BUYS_PER_TICK
    )

    applied = 0
    for i in range(potential_ticks):
        await vault_mod.apply_crack(
            db,
            tokens=int(demo_tick_tokens),
            kind="purchase",
            agent_code=_agent_code_for(pair_symbol, agent_index=i + 1),
            note=f"dex demo: {s['base_symbol']} (+{delta_buys} buys h24 delta)",
        )
        applied += 1
    return applied


async def _apply_custom_ticks(
    db,
    vault_mod,
    carry: float,
    s: Dict[str, Any],
    delta_buys: int,
    delta_sells: int,
    delta_vol_usd: float,
    pair_symbol: str,
) -> Tuple[int, float]:
    """Apply the REAL estimated token volume to the vault for `custom` mode.

    Returns (ticks_applied, new_carry). The fractional portion of the estimated
    token count is stored in `carry` so we never lose sub-token activity.
    """
    total_txns = delta_buys + delta_sells
    buy_ratio = (delta_buys / total_txns) if total_txns > 0 else 0.5
    delta_buy_volume_usd = delta_vol_usd * buy_ratio
    if s["price_usd"] > 0:
        delta_tokens = delta_buy_volume_usd / s["price_usd"]
    else:
        delta_tokens = 0.0

    new_carry = carry + delta_tokens
    tokens_to_apply = int(new_carry)
    new_carry = new_carry - tokens_to_apply

    if tokens_to_apply <= 0:
        return 0, new_carry

    await vault_mod.apply_crack(
        db,
        tokens=tokens_to_apply,
        kind="purchase",
        agent_code=_agent_code_for(pair_symbol, agent_index=1),
        note=(
            f"dex custom: {s['base_symbol']} "
            f"+{int(delta_tokens):,} tokens (Δbuys={delta_buys})"
        ),
    )
    return 1, new_carry


async def _persist_baselines(
    db,
    s: Dict[str, Any],
    pair_symbol: str,
    label: str,
    new_carry: float,
    *,
    error: Optional[str] = None,
) -> None:
    """Write the observed stats back to vault_state so the next poll can diff."""
    await db.vault_state.update_one(
        {"_id": VAULT_DOC_ID},
        {
            "$set": {
                "dex_last_poll_at": _now_iso(),
                "dex_last_h24_buys": s["buys_h24"],
                "dex_last_h24_sells": s["sells_h24"],
                "dex_last_h24_volume_usd": s["volume_h24"],
                "dex_last_price_usd": s["price_usd"],
                "dex_carry_tokens": new_carry,
                "dex_pair_symbol": pair_symbol,
                "dex_label": label,
                "dex_error": error,
            }
        },
    )


async def _persist_fetch_error(db, error: str) -> None:
    await db.vault_state.update_one(
        {"_id": VAULT_DOC_ID},
        {"$set": {"dex_last_poll_at": _now_iso(), "dex_error": error}},
    )


# ---------------------------------------------------------------------
# Orchestrator (cyclomatic complexity slimmed down from 24 → ~7)
# ---------------------------------------------------------------------
async def dex_poll_once(db, vault_mod) -> Dict[str, Any]:
    """One polling iteration. Returns a diagnostic dict.

    Sprint 17.5c — exponential backoff. The vault_state doc tracks:
      * ``dex_backoff_until``      — ISO timestamp; when in the future,
                                     poll() short-circuits with ``skipped``.
      * ``dex_429_streak``         — consecutive 429 counter; resets on a
                                     successful 200 fetch.
      * ``dex_last_429_at``        — observability breadcrumb.
    """
    doc = await db.vault_state.find_one({"_id": VAULT_DOC_ID}) or {}
    mode = (doc.get("dex_mode") or "off").lower()

    if mode in ("off", "helius"):
        # `helius` mode uses push webhooks as the authoritative source — do not
        # double-count by polling the DexScreener aggregate window too.
        return {"mode": mode, "skipped": True}

    # Honour an active backoff window. We compare ISO timestamps as
    # strings only as a fast-path — real comparison goes through
    # datetime to handle malformed values gracefully.
    backoff_until = doc.get("dex_backoff_until")
    if backoff_until:
        try:
            bo_dt = datetime.fromisoformat(str(backoff_until).replace("Z", "+00:00"))
            if datetime.now(timezone.utc) < bo_dt:
                return {
                    "mode": mode,
                    "skipped": True,
                    "reason": "backoff_active",
                    "backoff_until": backoff_until,
                    "consecutive_429": int(doc.get("dex_429_streak") or 0),
                }
        except (TypeError, ValueError):
            # Malformed value — clear it so we don't get stuck.
            await db.vault_state.update_one(
                {"_id": VAULT_DOC_ID},
                {"$set": {"dex_backoff_until": None}},
            )

    address, err = _resolve_token_address(doc, mode)
    if err or not address:
        return {"mode": mode, "skipped": True, "error": err or "no address"}

    stats_pair, fetch_err = await _fetch_token_stats(address)

    # 429 → arm exponential backoff and short-circuit.
    if fetch_err == "rate_limited":
        streak = int(doc.get("dex_429_streak") or 0) + 1
        wait_s = _backoff_seconds_for(streak)
        backoff_until_iso = (
            datetime.now(timezone.utc) + _td_seconds(wait_s)
        ).isoformat()
        await db.vault_state.update_one(
            {"_id": VAULT_DOC_ID},
            {"$set": {
                "dex_last_poll_at": _now_iso(),
                "dex_error": "rate_limited",
                "dex_backoff_until": backoff_until_iso,
                "dex_429_streak": streak,
                "dex_last_429_at": _now_iso(),
            }},
        )
        logging.warning(
            "[dex] arming backoff streak=%d wait=%ds until=%s",
            streak, wait_s, backoff_until_iso,
        )
        return {
            "mode": mode,
            "skipped": True,
            "error": "rate_limited",
            "backoff_until": backoff_until_iso,
            "consecutive_429": streak,
            "wait_seconds": wait_s,
        }

    if not stats_pair:
        await _persist_fetch_error(db, fetch_err or "no pairs or HTTP error")
        return {"mode": mode, "skipped": True, "error": fetch_err or "no pairs"}

    s = _extract_stats(stats_pair)
    pair_symbol = f"{s['base_symbol']}/{s['quote_symbol']}"
    label = f"{s['base_symbol']} · {s['dex_id'] or 'dex'}"

    deltas = _compute_deltas(doc, s)
    delta_buys = deltas["delta_buys"]
    delta_sells = deltas["delta_sells"]
    delta_vol_usd = deltas["delta_vol_usd"]
    carry = deltas["carry"]
    first_seen = deltas["first_seen"]

    ticks_applied = 0
    new_carry = carry

    # Only apply crack events when we have a real delta to measure against.
    quiet = first_seen or (delta_buys == 0 and delta_vol_usd == 0)
    if not quiet:
        if mode == "demo":
            ticks_applied = await _apply_demo_ticks(
                db, vault_mod, doc, s, pair_symbol, delta_buys
            )
        else:  # custom
            ticks_applied, new_carry = await _apply_custom_ticks(
                db,
                vault_mod,
                carry,
                s,
                delta_buys,
                delta_sells,
                delta_vol_usd,
                pair_symbol,
            )

    # 200 OK — reset the 429 streak + clear any lingering backoff.
    await _persist_baselines(db, s, pair_symbol, label, new_carry)
    if doc.get("dex_429_streak") or doc.get("dex_backoff_until"):
        await db.vault_state.update_one(
            {"_id": VAULT_DOC_ID},
            {"$set": {"dex_429_streak": 0, "dex_backoff_until": None}},
        )

    return {
        "mode": mode,
        "address": address,
        "pair": pair_symbol,
        "price_usd": s["price_usd"],
        "volume_h24": s["volume_h24"],
        "buys_h24": s["buys_h24"],
        "sells_h24": s["sells_h24"],
        "delta_buys": delta_buys,
        "delta_vol_usd": delta_vol_usd,
        "ticks_applied": ticks_applied,
        "carry_after": new_carry,
        "first_seen": first_seen,
    }


def _td_seconds(s: int):
    """Tiny helper — ``datetime.timedelta`` import-free shortcut."""
    from datetime import timedelta
    return timedelta(seconds=int(s))


async def dex_loop(db, vault_mod):
    """Long-running coroutine launched at app startup."""
    logging.info("[dex] poll loop started")
    await asyncio.sleep(45)  # boot grace period
    while True:
        try:
            result = await dex_poll_once(db, vault_mod)
            if not result.get("skipped"):
                logging.info(
                    f"[dex] poll mode={result.get('mode')} pair={result.get('pair')} "
                    f"delta_buys={result.get('delta_buys')} ticks={result.get('ticks_applied')}"
                )
        except Exception:
            logging.exception("[dex] poll_once error (will retry)")
        await asyncio.sleep(POLL_SECONDS)
