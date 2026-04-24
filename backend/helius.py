"""
Helius Solana indexer integration.

Two ingestion paths into the PROTOCOL ΔΣ vault:

    1. WEBHOOK (primary, push-based, recommended)
       Helius dashboard pushes every SWAP transaction involving the $DEEPOTUS
       mint to `POST /api/webhooks/helius`. The router in `routers/webhooks.py`
       calls `ingest_enhanced_transactions()` from this module to dedup, parse,
       and feed each BUY into vault.apply_crack().

    2. POLLING (fallback / cold-start catch-up)
       `poll_recent_swaps(mint, since_signature)` fetches enhanced txns from
       /v0/addresses/{mint}/transactions?type=SWAP and ingests them identically.
       Admin can trigger it on demand; it also runs at boot to catch anything
       missed while the service was down.

Key parsing rules (per Helius enhanced schema):
    - A transaction is a BUY of $DEEPOTUS when the $DEEPOTUS tokenTransfers[]
      destination account belongs to a *user wallet* (i.e. NOT the pool LP).
      Heuristic used here: the pool is the account that appears BOTH as a
      source AND a destination for the SAME mint across a short window (or
      that matches a known pool address configured on vault_state).
    - The token amount received = sum of tokenTransfers[] where mint matches
      our mint and destination is the user.
    - We read tokenStandard, decimals, source, destination from the transfer.

Dedup: each ingested transaction is keyed by its Solana signature in
`helius_ingested` collection, with a 30-day TTL.

See also:
    core/config.py  — HELIUS_API_KEY, HELIUS_WEBHOOK_AUTH
    routers/webhooks.py::helius_webhook — HTTP handler + signature check
    vault.py::apply_crack — the final sink for each BUY
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx

VAULT_DOC_ID = "protocol_delta_sigma"
HELIUS_API_BASE = "https://api.helius.xyz"
HTTP_TIMEOUT = 15.0

# Collection used for dedup
DEDUP_COLLECTION = "helius_ingested"
DEDUP_TTL_SECONDS = 30 * 24 * 3600  # 30 days


# ---------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------
def _token_transfers_for_mint(
    tx: Dict[str, Any], mint: str
) -> List[Dict[str, Any]]:
    """Return only the tokenTransfers entries matching our mint."""
    transfers = tx.get("tokenTransfers") or []
    return [t for t in transfers if (t.get("mint") or "").strip() == mint]


def _identify_pool(
    tx: Dict[str, Any], mint: str, known_pool: Optional[str]
) -> Optional[str]:
    """Best-effort pool detection.

    - If `known_pool` is configured (most reliable), use it verbatim.
    - Otherwise fall back to heuristic: the address that sends OUT $DEEPOTUS
      in a SWAP (the side that pays out the mint to the user) is the pool.
    """
    if known_pool:
        return known_pool.strip()

    transfers = _token_transfers_for_mint(tx, mint)
    # For a BUY, the source account is the pool and the destination is the buyer
    senders = [t.get("fromUserAccount") for t in transfers if t.get("fromUserAccount")]
    # Return the first sender that appears multiple times across transfers
    # (pool LP typically has a stable address) — heuristic only.
    if senders:
        return senders[0]
    return None


def _coerce_token_amount(entry: Dict[str, Any]) -> float:
    """Extract a normalized (decimals-applied) token amount from a swap entry.

    Helius uses two shapes:
        - `tokenAmount` (float, already decimal-normalized)
        - `rawTokenAmount: {tokenAmount, decimals}` (raw integer + decimals)
    """
    raw_obj = entry.get("rawTokenAmount") or {}
    amt = entry.get("tokenAmount") or raw_obj.get("tokenAmount") or 0
    try:
        value = float(amt)
    except (TypeError, ValueError):
        return 0.0

    decimals = 0
    try:
        decimals = int(raw_obj.get("decimals") or 0)
    except (TypeError, ValueError):
        decimals = 0

    if raw_obj and decimals > 0:
        value = value / (10 ** decimals)
    return value


def _scan_swap_entries(
    entries, mint: str, prefer_user_key: str = "userAccount"
) -> Tuple[float, Optional[str]]:
    """Sum token amounts matching `mint` across a list of swap entries.

    Returns (total_amount, first_non_empty_wallet).
    """
    if not entries:
        return 0.0, None

    total = 0.0
    wallet: Optional[str] = None
    for e in entries:
        if not isinstance(e, dict):
            continue
        if (e.get("mint") or "").strip() != mint:
            continue
        total += abs(_coerce_token_amount(e))
        if not wallet:
            wallet = e.get(prefer_user_key) or e.get("account")
    return total, wallet


def _decide_direction(
    out_tokens: float,
    in_tokens: float,
    out_user: Optional[str],
    in_user: Optional[str],
) -> Tuple[str, float, Optional[str]]:
    """Pure decision layer: compare input vs output sums to label a swap."""
    if out_tokens > 0 and in_tokens == 0:
        return "buy", out_tokens, out_user
    if in_tokens > 0 and out_tokens == 0:
        return "sell", in_tokens, in_user
    if out_tokens > in_tokens:
        return "buy", out_tokens - in_tokens, out_user or in_user
    if in_tokens > out_tokens:
        return "sell", in_tokens - out_tokens, in_user or out_user
    return "unknown", 0.0, out_user or in_user


def _classify_swap_via_events(
    tx: Dict[str, Any], mint: str
) -> Tuple[str, float, Optional[str]]:
    """Use Helius `events.swap` (structured) when available — the most reliable path.

    If our mint is in tokenOutputs → user receives it = BUY.
    If it's in tokenInputs → user sends it = SELL.
    No pool knowledge required.
    """
    events = tx.get("events") or {}
    swap = events.get("swap") if isinstance(events, dict) else None
    if not isinstance(swap, dict):
        return "unknown", 0.0, None

    out_tokens, out_user = _scan_swap_entries(swap.get("tokenOutputs"), mint)
    in_tokens, in_user = _scan_swap_entries(swap.get("tokenInputs"), mint)
    return _decide_direction(out_tokens, in_tokens, out_user, in_user)


def _classify_swap_via_transfers(
    tx: Dict[str, Any], mint: str, pool: Optional[str]
) -> Tuple[str, float, Optional[str]]:
    """Fallback parser when `events.swap` is missing.

    Relies on the pool address to tell apart incoming and outgoing transfers.
    Without a pool, this fallback returns `unknown`.
    """
    transfers = _token_transfers_for_mint(tx, mint)
    if not transfers:
        return "unknown", 0.0, None

    total_to_user = 0.0
    total_from_user = 0.0
    user_wallet: Optional[str] = None

    for t in transfers:
        try:
            amount = float(t.get("tokenAmount") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        src = t.get("fromUserAccount") or ""
        dst = t.get("toUserAccount") or ""
        if pool and src == pool:
            total_to_user += amount
            if not user_wallet and dst:
                user_wallet = dst
        elif pool and dst == pool:
            total_from_user += amount
            if not user_wallet and src:
                user_wallet = src

    direction, tokens, wallet = _decide_direction(
        total_to_user, total_from_user, user_wallet, user_wallet
    )
    return direction, tokens, wallet


def _classify_swap(
    tx: Dict[str, Any], mint: str, pool: Optional[str]
) -> Tuple[str, float, Optional[str]]:
    """Return (direction, token_amount, user_wallet).

    Tries `events.swap` first (most reliable, needs no pool info).
    Falls back to tokenTransfers + pool heuristic if events.swap is missing.
    """
    direction, tokens, user = _classify_swap_via_events(tx, mint)
    if direction != "unknown" and tokens > 0:
        return direction, tokens, user
    return _classify_swap_via_transfers(tx, mint, pool)


# ---------------------------------------------------------------------
# Dedup
# ---------------------------------------------------------------------
async def ensure_dedup_index(db) -> None:
    """Create a TTL index so ingested signatures expire after DEDUP_TTL_SECONDS."""
    try:
        await db[DEDUP_COLLECTION].create_index(
            "received_at", expireAfterSeconds=DEDUP_TTL_SECONDS
        )
    except Exception:
        # index may already exist; ignore
        pass


async def already_ingested(db, signature: str) -> bool:
    doc = await db[DEDUP_COLLECTION].find_one({"_id": signature})
    return doc is not None


async def mark_ingested(db, signature: str, meta: Dict[str, Any]) -> None:
    await db[DEDUP_COLLECTION].insert_one(
        {
            "_id": signature,
            "received_at": datetime.now(timezone.utc),
            **meta,
        }
    )


# ---------------------------------------------------------------------
# Main ingestion entrypoint (called by webhook AND polling)
# ---------------------------------------------------------------------
async def ingest_enhanced_transactions(
    db,
    vault_mod,
    transactions: Iterable[Dict[str, Any]],
    mint: str,
    pool: Optional[str] = None,
    source: str = "webhook",
    demo_tokens_per_buy: Optional[int] = None,
) -> Dict[str, int]:
    """Parse + feed each BUY into vault.apply_crack().

    Args:
        db: Mongo database handle
        vault_mod: the `vault` module (imported lazily to avoid cycles)
        transactions: array of Helius enhanced transaction dicts
        mint: the SPL mint we care about (used to filter tokenTransfers)
        pool: optional pool LP address for precise buy/sell detection
        source: "webhook" | "poll_catchup" | etc. — stamped on audit rows
        demo_tokens_per_buy: when set (demo mode, e.g. tracking BONK before
            $DEEPOTUS is deployed), every detected BUY applies exactly this
            many tokens to the vault instead of the real on-chain amount.
            Prevents a single multi-million-token BONK trade from instantly
            cracking the vault.

    Returns diagnostics: {ingested, buys, sells, duplicates, skipped}.
    """
    ingested = 0
    buys = 0
    sells = 0
    duplicates = 0
    skipped = 0

    for tx in transactions:
        signature = tx.get("signature")
        if not signature:
            skipped += 1
            continue

        if await already_ingested(db, signature):
            duplicates += 1
            continue

        direction, tokens, user_wallet = _classify_swap(tx, mint, pool)
        if direction == "unknown" or tokens <= 0:
            skipped += 1
            await mark_ingested(
                db,
                signature,
                {"direction": "unknown", "source": source, "mint": mint},
            )
            continue

        if direction == "buy":
            agent_code = f"SOL-{(user_wallet or 'anon')[:6].upper()}"
            applied_tokens = (
                int(demo_tokens_per_buy)
                if demo_tokens_per_buy and demo_tokens_per_buy > 0
                else int(tokens)
            )
            note_tokens = f"{tokens:.0f}"
            if demo_tokens_per_buy:
                note_tokens = f"{tokens:.0f} raw → {applied_tokens} demo"
            await vault_mod.apply_crack(
                db,
                tokens=applied_tokens,
                kind="purchase",
                agent_code=agent_code,
                note=f"helius {source}: buy sig={signature[:10]}… ({note_tokens} tokens)",
            )
            buys += 1
        else:
            sells += 1

        await mark_ingested(
            db,
            signature,
            {
                "direction": direction,
                "tokens": tokens,
                "user_wallet": user_wallet,
                "source": source,
                "mint": mint,
            },
        )
        ingested += 1

    return {
        "ingested": ingested,
        "buys": buys,
        "sells": sells,
        "duplicates": duplicates,
        "skipped": skipped,
    }


# ---------------------------------------------------------------------
# Polling (catch-up)
# ---------------------------------------------------------------------
async def fetch_recent_swaps(
    api_key: str,
    mint: str,
    limit: int = 50,
    before: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """GET /v0/addresses/{mint}/transactions?api-key=...&type=SWAP&limit=...&before=..."""
    if not api_key:
        logging.warning("[helius] fetch_recent_swaps: no api_key")
        return []
    url = f"{HELIUS_API_BASE}/v0/addresses/{mint}/transactions"
    params = {"api-key": api_key, "type": "SWAP", "limit": int(limit)}
    if before:
        params["before"] = before
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(url, params=params)
            if r.status_code != 200:
                logging.warning(
                    f"[helius] fetch non-200 {r.status_code} body={r.text[:200]}"
                )
                return []
            data = r.json()
            return data if isinstance(data, list) else []
    except Exception:
        logging.exception("[helius] fetch_recent_swaps error")
        return []


async def catch_up_from_helius(
    db,
    vault_mod,
    api_key: str,
    mint: str,
    pool: Optional[str] = None,
    demo_tokens_per_buy: Optional[int] = None,
) -> Dict[str, Any]:
    """On boot or on-demand: pull the last 50 swaps and ingest any not-yet-seen."""
    txs = await fetch_recent_swaps(api_key, mint, limit=50)
    if not txs:
        return {"fetched": 0, "ingested": 0}
    result = await ingest_enhanced_transactions(
        db,
        vault_mod,
        txs,
        mint=mint,
        pool=pool,
        source="poll_catchup",
        demo_tokens_per_buy=demo_tokens_per_buy,
    )
    result["fetched"] = len(txs)
    return result


# ---------------------------------------------------------------------
# Webhook registration helpers (optional; admin-triggered)
# ---------------------------------------------------------------------
async def register_webhook(
    api_key: str,
    webhook_url: str,
    mint: str,
    auth_header: Optional[str] = None,
    transaction_types: Optional[List[str]] = None,
    webhook_type: str = "enhanced",
) -> Dict[str, Any]:
    """POST /v0/webhooks to register our callback URL.

    Call this once after getting your API key. Returns the Helius webhookID,
    which you should persist in vault_state.helius_webhook_id.
    """
    if not api_key:
        raise ValueError("missing api_key")
    tx_types = transaction_types or ["SWAP"]
    body = {
        "webhookURL": webhook_url,
        "transactionTypes": tx_types,
        "accountAddresses": [mint],
        "webhookType": webhook_type,
    }
    if auth_header:
        body["authHeader"] = auth_header

    url = f"{HELIUS_API_BASE}/v0/webhooks?api-key={api_key}"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(url, json=body)
        r.raise_for_status()
        return r.json()


async def list_webhooks(api_key: str) -> List[Dict[str, Any]]:
    if not api_key:
        return []
    url = f"{HELIUS_API_BASE}/v0/webhooks?api-key={api_key}"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.get(url)
        if r.status_code != 200:
            return []
        data = r.json()
        return data if isinstance(data, list) else []


async def delete_webhook(api_key: str, webhook_id: str) -> bool:
    if not api_key or not webhook_id:
        return False
    url = f"{HELIUS_API_BASE}/v0/webhooks/{webhook_id}?api-key={api_key}"
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.delete(url)
        return r.status_code in (200, 204)
