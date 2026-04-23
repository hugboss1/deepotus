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
from typing import Optional, Dict, Any

import httpx

VAULT_DOC_ID = "protocol_delta_sigma"

# BONK ticker mint on Solana — highly active memecoin, perfect for demo
DEMO_TOKEN_ADDRESS = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"

POLL_SECONDS = 30
HTTP_TIMEOUT = 8.0
DEX_API = "https://api.dexscreener.com/latest/dex/tokens"

# Demo mode: emit 1 tick per N new buys detected (avoids blowing up the vault on BONK)
DEMO_BUYS_PER_TICK = 5
DEMO_MAX_TICKS_PER_POLL = 3


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _fetch_token_stats(address: str) -> Optional[Dict[str, Any]]:
    """Call DexScreener /tokens/{address} and return the BEST pair (highest liquidity)."""
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(f"{DEX_API}/{address}")
            if r.status_code != 200:
                logging.warning(f"[dex] non-200 for {address}: {r.status_code}")
                return None
            data = r.json()
            pairs = data.get("pairs") or []
            if not pairs:
                return None
            # Keep Solana pairs, sort by trade activity (buys + sells on 24h window)
            # This ensures we track the LIVELY pair, not the deepest-but-idle one.
            solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
            if not solana_pairs:
                return None

            def _activity_score(p):
                txns = (p.get("txns") or {}).get("h24") or {}
                return int(txns.get("buys") or 0) + int(txns.get("sells") or 0)

            solana_pairs.sort(key=_activity_score, reverse=True)
            return solana_pairs[0]
    except Exception as e:
        logging.exception(f"[dex] fetch error for {address}: {e}")
        return None


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


async def dex_poll_once(db, vault_mod) -> Dict[str, Any]:
    """One polling iteration. Returns a diagnostic dict."""
    doc = await db.vault_state.find_one({"_id": VAULT_DOC_ID}) or {}
    mode = (doc.get("dex_mode") or "off").lower()

    if mode == "off":
        return {"mode": "off", "skipped": True}

    if mode == "demo":
        address = doc.get("dex_demo_token_address") or DEMO_TOKEN_ADDRESS
    else:  # custom
        address = (doc.get("dex_token_address") or "").strip()
        if not address:
            return {"mode": mode, "skipped": True, "error": "no token_address"}

    stats_pair = await _fetch_token_stats(address)
    if not stats_pair:
        await db.vault_state.update_one(
            {"_id": VAULT_DOC_ID},
            {
                "$set": {
                    "dex_last_poll_at": _now_iso(),
                    "dex_error": "no pairs or HTTP error",
                }
            },
        )
        return {"mode": mode, "skipped": True, "error": "no pairs"}

    s = _extract_stats(stats_pair)
    pair_symbol = f"{s['base_symbol']}/{s['quote_symbol']}"
    label = f"{s['base_symbol']} \u00b7 {s['dex_id'] or 'dex'}"

    last_h24_buys = int(doc.get("dex_last_h24_buys") or 0)
    last_h24_sells = int(doc.get("dex_last_h24_sells") or 0)
    last_vol = float(doc.get("dex_last_h24_volume_usd") or 0)
    carry = float(doc.get("dex_carry_tokens") or 0)
    first_seen = not bool(doc.get("dex_last_poll_at"))

    # Delta buys since last poll (h24 is a rolling window; tiny drops can happen,
    # so we clamp to 0 when the window rolled over).
    delta_buys = max(0, s["buys_h24"] - last_h24_buys)
    delta_sells = max(0, s["sells_h24"] - last_h24_sells)
    delta_vol_usd = max(0.0, s["volume_h24"] - last_vol)

    # On the very first poll we cannot measure a delta — just record baselines.
    ticks_applied = 0
    new_carry = carry

    if first_seen or (delta_buys == 0 and delta_vol_usd == 0):
        pass
    elif mode == "demo":
        # Symbolic: 1 tick per DEMO_BUYS_PER_TICK new buys, capped
        potential_ticks = min(DEMO_MAX_TICKS_PER_POLL, delta_buys // DEMO_BUYS_PER_TICK)
        for i in range(potential_ticks):
            await vault_mod.apply_crack(
                db,
                tokens=int(doc.get("tokens_per_digit") or 1000),
                kind="purchase",
                agent_code=_agent_code_for(pair_symbol, agent_index=i + 1),
                note=f"dex demo: {s['base_symbol']} (+{delta_buys} buys h24 delta)",
            )
            ticks_applied += 1
    else:
        # custom: 1 tick per tokens_per_digit tokens bought
        # buy share of volume is approximated using the buy/sell txn ratio.
        total_txns = delta_buys + delta_sells
        buy_ratio = (delta_buys / total_txns) if total_txns > 0 else 0.5
        delta_buy_volume_usd = delta_vol_usd * buy_ratio
        if s["price_usd"] > 0:
            delta_tokens = delta_buy_volume_usd / s["price_usd"]
        else:
            delta_tokens = 0.0

        new_carry = carry + delta_tokens
        tokens_per_digit = int(doc.get("tokens_per_digit") or 1000)
        ticks = int(new_carry // tokens_per_digit)
        new_carry = new_carry - (ticks * tokens_per_digit)

        # Safety cap: never apply more than 6 ticks in one poll
        ticks = min(ticks, 6)
        for i in range(ticks):
            await vault_mod.apply_crack(
                db,
                tokens=tokens_per_digit,
                kind="purchase",
                agent_code=_agent_code_for(pair_symbol, agent_index=i + 1),
                note=(
                    f"dex custom: {s['base_symbol']} +{int(delta_tokens):,} tokens est."
                ),
            )
            ticks_applied += 1

    # Persist updated baselines
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
                "dex_error": None,
            }
        },
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
