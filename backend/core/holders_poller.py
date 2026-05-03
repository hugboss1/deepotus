"""
core/holders_poller.py — Sprint 19.1

Periodic, defensive holders-count poller for the live $DEEPOTUS mint.

Why this module exists
----------------------
The cadence engine (`core.cadence_engine`) reads
``vault_state.dex_holders_count`` to fire reactive posts when the holder
base crosses a configured milestone. Until this poller landed, that
field was never populated — so the holders branch silently no-op'd
even when ``cadence.reactive_triggers.enabled`` was true.

This poller fills that gap by writing the live holder count into
``vault_state.dex_holders_count`` every ``POLL_INTERVAL_SECONDS``.

Source resolution chain
-----------------------
We try sources in the order below, falling back on the next one only
if the previous one is not configured / fails:

  1. **Helius DAS ``getTokenAccounts``** (preferred) — uses the
     ``HELIUS_API_KEY`` already configured in the Cabinet Vault. We
     paginate through all token accounts of the mint up to a hard
     cap of ``MAX_PAGES`` × ``PAGE_SIZE`` (= 100 × 1000 = 100k accounts)
     and count those whose ``amount > 0``. The cap prevents runaway
     polls if the token ever explodes — when reached, we return the
     count we got and tag the result as approximate.

  2. **DexScreener** — DexScreener does NOT expose holder counts as of
     early 2026 (only volume/liquidity/price). We keep the source slot
     here as a placeholder so a future provider swap is a one-line
     change in ``_fetch_via_dexscreener``.

  3. **Skip silently** — if no source resolved a count, leave the
     ``vault_state.dex_holders_count`` field untouched and log once at
     INFO. The cadence reactive tick already handles ``holders is
     None`` gracefully.

Outputs
-------
On success:
  - sets ``vault_state.dex_holders_count`` to an int,
  - sets ``vault_state.dex_holders_polled_at`` to an ISO UTC timestamp,
  - sets ``vault_state.dex_holders_source`` to ``"helius"`` (the source
    that resolved the value),
  - sets ``vault_state.dex_holders_approximate`` to True iff the cap
    was reached.

On any failure, persists ``dex_holders_error`` for observability and
leaves the existing count alone.
"""

from __future__ import annotations

import base64
import logging
import struct
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from core.config import db
from core.secret_provider import get_helius_api_key

logger = logging.getLogger("deepotus.holders_poller")

# Singleton id used everywhere else in vault.py + dexscreener.py.
VAULT_DOC_ID = "protocol_delta_sigma"

# How often the scheduler runs us. Holders move slowly relative to
# trade activity, so 5 minutes is plenty granular for milestone-crossing
# detection without hammering the RPC.
POLL_INTERVAL_SECONDS = 5 * 60

# Hard pagination caps for the Helius DAS endpoint.
PAGE_SIZE = 1_000      # max documented page size
MAX_PAGES = 100        # so 100k accounts max — safety net

# Helius RPC endpoint (also covers their DAS extensions).
HELIUS_RPC_BASE = "https://mainnet.helius-rpc.com"
HTTP_TIMEOUT = 15.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Source 1 — Helius DAS getTokenAccounts (the workhorse)
# =====================================================================
async def _fetch_via_helius(mint: str, api_key: str) -> Dict[str, Any]:
    """Count holders via Helius DAS ``getTokenAccounts`` pagination.

    Returns a dict shaped:
      {
        "ok": True / False,
        "count": int | None,
        "approximate": bool,
        "error": str | None,
      }
    """
    url = f"{HELIUS_RPC_BASE}/?api-key={api_key}"
    cursor: Optional[str] = None
    holders = 0
    pages = 0

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        while pages < MAX_PAGES:
            payload: Dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": "holders-poller",
                "method": "getTokenAccounts",
                "params": {
                    "mint": mint,
                    "limit": PAGE_SIZE,
                    "cursor": cursor,
                },
            }
            try:
                resp = await client.post(url, json=payload)
            except httpx.HTTPError as exc:
                return {
                    "ok": False,
                    "count": None,
                    "approximate": False,
                    "error": f"helius http: {exc}",
                }
            if resp.status_code != 200:
                return {
                    "ok": False,
                    "count": None,
                    "approximate": False,
                    "error": f"helius status {resp.status_code}",
                }
            try:
                body = resp.json()
            except ValueError:
                return {
                    "ok": False,
                    "count": None,
                    "approximate": False,
                    "error": "helius non-json body",
                }
            if "error" in body:
                return {
                    "ok": False,
                    "count": None,
                    "approximate": False,
                    "error": f"helius rpc: {body['error']}",
                }
            result = body.get("result") or {}
            accounts = result.get("token_accounts") or []
            for acc in accounts:
                # Helius returns `amount` as either int or string. We treat
                # absence / 0 as a frozen-or-empty account (not a real
                # holder).
                try:
                    amt = int(acc.get("amount") or 0)
                except (TypeError, ValueError):
                    amt = 0
                if amt > 0:
                    holders += 1

            cursor = result.get("cursor")
            pages += 1
            if not cursor or len(accounts) < PAGE_SIZE:
                # Reached the end of the iterator.
                return {
                    "ok": True,
                    "count": holders,
                    "approximate": False,
                    "error": None,
                }

    # Hit the page cap — return what we have, tagged approximate.
    logger.warning(
        "[holders] Helius pagination cap reached (pages=%s, count=%s) — "
        "result is approximate",
        pages,
        holders,
    )
    return {
        "ok": True,
        "count": holders,
        "approximate": True,
        "error": None,
    }


# =====================================================================
# Source 2 — DexScreener placeholder (no holders field today)
# =====================================================================
async def _fetch_via_dexscreener(mint: str) -> Dict[str, Any]:  # noqa: ARG001
    """DexScreener does not expose a holder count — keep the slot ready."""
    return {
        "ok": False,
        "count": None,
        "approximate": False,
        "error": "dexscreener does not expose holders",
    }


# =====================================================================
# Persistence
# =====================================================================
async def _persist_success(
    *,
    count: int,
    approximate: bool,
    source: str,
) -> None:
    await db.vault_state.update_one(
        {"_id": VAULT_DOC_ID},
        {
            "$set": {
                "dex_holders_count": int(count),
                "dex_holders_approximate": bool(approximate),
                "dex_holders_polled_at": _now_iso(),
                "dex_holders_source": source,
                "dex_holders_error": None,
            },
        },
        upsert=True,
    )


async def _persist_error(error: str) -> None:
    await db.vault_state.update_one(
        {"_id": VAULT_DOC_ID},
        {
            "$set": {
                "dex_holders_polled_at": _now_iso(),
                "dex_holders_error": error[:500],
            },
        },
        upsert=True,
    )


# =====================================================================
# Public API
# =====================================================================
async def poll_holders_once() -> Dict[str, Any]:
    """Run the source-resolution chain once and persist the result.

    Returns a small diagnostic dict that the scheduler logs. Designed
    to be invoked by an APScheduler job at ``POLL_INTERVAL_SECONDS``.

    Never raises — every failure path persists an error string and
    returns a structured dict so the scheduler's job-error machinery
    stays quiet.
    """
    doc = await db.vault_state.find_one({"_id": VAULT_DOC_ID})
    if not doc:
        # Nothing to poll yet (pre-mint state).
        return {"skipped": True, "reason": "no_vault_state"}
    mint = (doc.get("dex_token_address") or "").strip()
    if not mint:
        return {"skipped": True, "reason": "no_mint"}

    # ---- Source 1: Helius ----
    api_key = await get_helius_api_key()
    if api_key:
        res = await _fetch_via_helius(mint, api_key)
        if res["ok"]:
            await _persist_success(
                count=res["count"],
                approximate=res["approximate"],
                source="helius",
            )
            logger.info(
                "[holders] helius ok mint=%s… count=%d approximate=%s",
                mint[:6],
                res["count"],
                res["approximate"],
            )
            return {
                "ok": True,
                "source": "helius",
                "count": res["count"],
                "approximate": res["approximate"],
            }
        # Source 1 failed — log + try fallback (no exception bubble).
        logger.warning(
            "[holders] helius failed: %s — trying next source",
            res.get("error"),
        )
    else:
        logger.info(
            "[holders] HELIUS_API_KEY not set — skipping helius source"
        )

    # ---- Source 2: DexScreener (placeholder for future provider) ----
    res2 = await _fetch_via_dexscreener(mint)
    if res2["ok"]:
        await _persist_success(
            count=res2["count"],
            approximate=res2["approximate"],
            source="dexscreener",
        )
        return {
            "ok": True,
            "source": "dexscreener",
            "count": res2["count"],
        }

    # ---- All sources exhausted ----
    err = res2.get("error") or "no source resolved"
    await _persist_error(err)
    logger.info("[holders] no source resolved a count: %s", err)
    return {"ok": False, "error": err}


# =====================================================================
# Optional helper — manual base64 amount decode
# =====================================================================
# Kept here for future use if we ever switch from Helius DAS to a raw
# `getProgramAccounts` call (which returns a base64-encoded SPL token
# account layout). The `amount` is stored at offset 64 as a little-
# endian u64. Current pipeline doesn't need this — Helius DAS already
# gives us the integer amount — but ripping it out later is easier
# than re-deriving it.
def _decode_amount_from_b64(b64: str) -> int:
    raw = base64.b64decode(b64)
    if len(raw) < 8:
        return 0
    return struct.unpack("<Q", raw[:8])[0]
