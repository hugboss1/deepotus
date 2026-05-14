"""Sprint 19+ — Giveaway Extraction Pipeline.

End-to-end logic for the May 20 (and future) public draws. Splits into
four cleanly-separable concerns so each is testable in isolation:

1. **Eligibility query** — pull every ``clearance_levels`` row that has
   a non-empty ``x_handle``. That's the *whitelisted* pool. We don't
   filter on level here (operator may want to draw on Observer-tier
   too); the Pydantic admin endpoint exposes ``min_level`` if narrower
   eligibility is needed.

2. **On-chain holding check** — for every candidate we resolve a wallet
   address (priority: row.wallet_address → operator's manual override
   map → none). We then RPC into Helius to count the SPL token balance
   for the configured ``$DEEP`` mint, and price it via DexScreener.
   Returns USD value. If the mint isn't deployed yet (pre-launch
   audit mode), the check short-circuits with ``status = "pre_mint"``
   and the candidate is treated as eligible (operator decision).

3. **Provably fair selection** — we derive a deterministic random seed
   from (a) a *recently* observed Solana blockhash captured during the
   extraction run, plus (b) a sha256 of the sorted candidate handles.
   The seed and its inputs are persisted in the snapshot doc so any
   third party can re-run the shuffle and confirm the same winners.
   This is **not** the same guarantee as on-chain VRF, but it is far
   stronger than ``random.choice`` because the operator cannot pick
   the blockhash retro-actively (the seed depends on whatever block
   was current at extraction time, which is timestamped + immutable
   on Solana).

4. **Snapshot persistence** — every extraction (preview or real) writes
   one ``giveaway_snapshots`` row containing the full inputs, the
   eligible pool, the verified pool, the seed math, and the picked
   winners. Snapshots are append-only; redaction is a soft-delete via
   ``cancelled_at`` so the public ``Extraction Success`` propaganda can
   reference an audit URL.

Indexes are idempotent — safe to call ``ensure_indexes`` on every
boot.
"""

from __future__ import annotations

import hashlib
import logging
import random
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from core.config import HELIUS_API_KEY, db

logger = logging.getLogger("deepotus.giveaway")

# =====================================================================
# Configuration constants — single source of truth across the codebase.
# Tune these here, never inline.
# =====================================================================

#: Mongo collection holding immutable extraction snapshots.
COLLECTION: str = "giveaway_snapshots"

#: Default number of winners to draw per extraction. Mirrored in
#: ``frontend/src/lib/missions.ts``'s ``GIVEAWAY.winnersCount`` so the
#: public /giveaway page stays in lockstep. If you change this, update
#: BOTH files in the same commit.
DEFAULT_WINNERS_COUNT: int = 2

#: Minimum USD value of $DEEP a wallet must hold to qualify. Per spec.
DEFAULT_MIN_HOLDING_USD: float = 30.0

#: How recent the Solana blockhash captured at extraction time can be
#: (in seconds) for the RNG seed to be considered "fresh". Defensive
#: only — the RPC call almost always returns the current slot, but if
#: it's older than this we re-fetch.
BLOCKHASH_MAX_AGE_SEC: int = 60

#: Helius mainnet RPC endpoint. Uses the same API key as the webhook
#: ingestion pipeline (``core.config.HELIUS_API_KEY``).
HELIUS_RPC_URL_TEMPLATE: str = "https://mainnet.helius-rpc.com/?api-key={key}"

#: DexScreener token endpoint — used to convert raw token balance into
#: USD value (priceUsd field). Same upstream as ``dexscreener.py``.
DEXSCREENER_TOKEN_URL_TEMPLATE: str = "https://api.dexscreener.com/latest/dex/tokens/{mint}"

#: HTTP timeouts — kept short so a slow external dependency cannot lock
#: an admin request for minutes.
HTTP_TIMEOUT_SEC: float = 8.0

#: Conventional decimals for $DEEP. We always call ``getTokenSupply``
#: to get the real decimals if the mint exists, but we fall back to
#: this constant if the RPC fails (so a transient network glitch
#: doesn't produce wildly wrong USD math).
DEFAULT_TOKEN_DECIMALS: int = 6

_SOLANA_ADDR_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
_X_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")


# =====================================================================
# Utilities
# =====================================================================

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime] = None) -> str:
    return (dt or _now()).isoformat()


def _is_valid_mint(addr: Optional[str]) -> bool:
    if not addr:
        return False
    s = addr.strip()
    if not s:
        return False
    return bool(_SOLANA_ADDR_RE.match(s))


def _normalise_handle(handle: Optional[str]) -> Optional[str]:
    if not handle:
        return None
    s = str(handle).strip().lstrip("@")
    return s if _X_HANDLE_RE.match(s) else None


def _short_wallet(addr: Optional[str]) -> str:
    if not addr:
        return "—"
    return f"{addr[:4]}…{addr[-4:]}" if len(addr) > 10 else addr


async def ensure_indexes() -> None:
    """Mongo indexes — idempotent. Called once at startup."""
    try:
        await db[COLLECTION].create_index([("created_at", -1)])
        await db[COLLECTION].create_index([("draw_date_iso", 1)])
        # Audit hardening: an active (non-cancelled) extraction is
        # unique per draw_date so an operator can't double-fire on the
        # same date by accident.
        await db[COLLECTION].create_index(
            [("draw_date_iso", 1)],
            unique=True,
            name="active_extraction_unique_per_draw",
            partialFilterExpression={
                "cancelled_at": None,
                "kind": "extraction",
            },
        )
    except Exception:
        logger.exception("[giveaway] ensure_indexes failed (non-fatal)")


# =====================================================================
# Eligibility query
# =====================================================================

async def list_eligible_candidates(
    *,
    min_level: int = 0,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Pull whitelisted participants who have a public X handle.

    The handle is the *announcement* identity (we cite winners by
    handle on X + Telegram so they're publicly verifiable). The
    wallet is the *verification* identity (we check on-chain holdings
    against it). Both can be populated separately, hence the loose
    coupling here.

    Returns rows shaped:
        {
            "email":          str,
            "x_handle":       str,    # always present in this list
            "wallet_address": str|null,
            "level":          int,
            "verified_human": bool,   # mirrored from clearance row when present
            "created_at":     str,
        }
    """
    cursor = db.clearance_levels.find(
        {
            "x_handle": {"$exists": True, "$ne": None, "$type": "string"},
            "level": {"$gte": int(min_level)},
        },
        projection={
            "_id": 0,
            "email": 1,
            "x_handle": 1,
            "wallet_address": 1,
            "level": 1,
            "verified_human": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1).limit(max(1, min(limit, 5000)))

    rows = await cursor.to_list(length=None)
    out: List[Dict[str, Any]] = []
    for r in rows:
        handle = _normalise_handle(r.get("x_handle"))
        if not handle:
            continue
        out.append({
            "email": str(r.get("email") or ""),
            "x_handle": handle,
            "wallet_address": r.get("wallet_address") or None,
            "level": int(r.get("level") or 0),
            "verified_human": bool(r.get("verified_human") or False),
            "created_at": _iso(r.get("created_at")) if r.get("created_at") else None,
        })
    return out


# =====================================================================
# Price feed
# =====================================================================

async def get_deep_price_usd(mint_address: str) -> Tuple[Optional[float], Optional[str]]:
    """Return ``(price_usd, error)``.

    ``error`` mirrors the DexScreener taxonomy used elsewhere in the
    codebase ("rate_limited", "no_pairs", "http_<code>", "fetch_error")
    so callers can render a consistent operator message.
    """
    if not _is_valid_mint(mint_address):
        return None, "invalid_mint"
    url = DEXSCREENER_TOKEN_URL_TEMPLATE.format(mint=mint_address)
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SEC) as client:
            r = await client.get(url)
        if r.status_code == 429:
            return None, "rate_limited"
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        data = r.json() or {}
        pairs = data.get("pairs") or []
        if not pairs:
            return None, "no_pairs"
        # Take the most-active Solana pair, identical heuristic to
        # ``dexscreener.py::_fetch_token_stats``.
        sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
        if not sol_pairs:
            return None, "no_solana_pair"
        sol_pairs.sort(
            key=lambda p: int(((p.get("txns") or {}).get("h24") or {}).get("buys") or 0)
            + int(((p.get("txns") or {}).get("h24") or {}).get("sells") or 0),
            reverse=True,
        )
        raw = sol_pairs[0].get("priceUsd")
        try:
            return float(raw), None
        except (TypeError, ValueError):
            return None, "price_not_numeric"
    except httpx.HTTPError:
        return None, "fetch_error"
    except Exception:
        logger.exception("[giveaway] get_deep_price_usd unexpected error")
        return None, "fetch_error"


# =====================================================================
# On-chain holding check
# =====================================================================

async def _solana_rpc(method: str, params: List[Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Thin wrapper around Helius mainnet RPC. Returns ``(result, err)``
    where ``err`` is one of "no_api_key" / "rate_limited" /
    "http_<code>" / "rpc_error" / "fetch_error"."""
    if not HELIUS_API_KEY:
        return None, "no_api_key"
    url = HELIUS_RPC_URL_TEMPLATE.format(key=HELIUS_API_KEY)
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params,
    }
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SEC) as client:
            r = await client.post(url, json=payload)
        if r.status_code == 429:
            return None, "rate_limited"
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        data = r.json() or {}
        if data.get("error"):
            return None, "rpc_error"
        return data.get("result"), None
    except httpx.HTTPError:
        return None, "fetch_error"
    except Exception:
        logger.exception("[giveaway] solana rpc unexpected error")
        return None, "fetch_error"


async def get_holding_tokens(wallet: str, mint: str) -> Tuple[float, Optional[str]]:
    """Return the **whole-token** $DEEP balance for ``wallet`` (i.e.
    already divided by 10**decimals). Returns ``(0.0, error)`` on
    failure — the error code is suitable for surfacing in admin UI.
    """
    if not _SOLANA_ADDR_RE.match(wallet or ""):
        return 0.0, "invalid_wallet"
    if not _is_valid_mint(mint):
        return 0.0, "invalid_mint"

    result, err = await _solana_rpc(
        "getTokenAccountsByOwner",
        [
            wallet,
            {"mint": mint},
            {"encoding": "jsonParsed"},
        ],
    )
    if err:
        return 0.0, err
    if not result:
        return 0.0, None  # legitimate zero balance (no ATA)

    accounts = result.get("value") or []
    if not accounts:
        return 0.0, None
    # Sum across all accounts (rare but possible: split ATAs).
    total: float = 0.0
    for acc in accounts:
        try:
            info = ((acc.get("account") or {}).get("data") or {}).get("parsed", {}).get("info", {})
            token_amount = (info.get("tokenAmount") or {})
            # `uiAmount` is already decimal-adjusted by the RPC; prefer
            # it but fall back to manual computation when it's null
            # (uiAmount is sometimes None on freshly-minted SPLs).
            ui = token_amount.get("uiAmount")
            if ui is None:
                raw = int(token_amount.get("amount") or 0)
                dec = int(token_amount.get("decimals") or DEFAULT_TOKEN_DECIMALS)
                total += raw / (10 ** dec)
            else:
                total += float(ui)
        except Exception:
            logger.warning("[giveaway] failed to parse token account, skipping")
            continue
    return total, None


# =====================================================================
# Provably fair RNG
# =====================================================================

async def fetch_solana_seed() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Capture a freshness anchor — (blockhash, slot, captured_at_iso)
    — to mix into the RNG seed. We use the standard ``getLatestBlockhash``
    RPC; the returned hash changes every ~400ms so an operator can't
    influence it.
    """
    result, err = await _solana_rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
    if err or not result:
        return None, err or "no_result"
    value = result.get("value") or {}
    blockhash = value.get("blockhash")
    slot = (result.get("context") or {}).get("slot")
    if not blockhash or slot is None:
        return None, "malformed_rpc_response"
    return {
        "blockhash": str(blockhash),
        "slot": int(slot),
        "captured_at": _iso(),
    }, None


def derive_rng_seed(
    *,
    blockhash: str,
    slot: int,
    sorted_handles: List[str],
    draw_date_iso: str,
) -> Tuple[int, str]:
    """Derive a deterministic seed from publicly-verifiable inputs.

    Returns ``(seed_int, fingerprint_hex)``. The fingerprint is the
    full sha256 hex digest — kept in the snapshot so a verifier can
    re-derive the same value with the same inputs.

    Math:
        sha256(blockhash || ":" || slot || ":" || draw_date_iso ||
               ":" || "\\n".join(sorted_handles))
        → 64 hex chars → int → seed
    """
    payload = (
        f"{blockhash}:{slot}:{draw_date_iso}:" + "\n".join(sorted_handles)
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest, 16), digest


def pick_winners_deterministic(
    *,
    pool: List[Dict[str, Any]],
    count: int,
    seed_int: int,
) -> List[Dict[str, Any]]:
    """Deterministic shuffle + slice — never network-dependent.

    Note: we use ``random.Random(seed)`` rather than ``secrets`` because
    we WANT determinism here (so a verifier can replay). The seed
    itself is what gives the fairness guarantee, not the algorithm.
    """
    if not pool or count <= 0:
        return []
    rng = random.Random(seed_int)
    indices = list(range(len(pool)))
    rng.shuffle(indices)
    picked_idx = indices[: min(count, len(pool))]
    return [pool[i] for i in picked_idx]


# =====================================================================
# Full extraction pipeline
# =====================================================================

async def run_extraction(
    *,
    draw_date_iso: str,
    token_mint: Optional[str],
    pool_sol: float,
    winners_count: int = DEFAULT_WINNERS_COUNT,
    min_holding_usd: float = DEFAULT_MIN_HOLDING_USD,
    manual_wallets: Optional[Dict[str, str]] = None,
    dry_run: bool = True,
    min_level: int = 0,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full pipeline.

    Args:
        draw_date_iso: ISO timestamp the draw is anchored to. Used in
            the RNG payload and as the idempotency key.
        token_mint: Solana mint address of $DEEP. If falsy/invalid the
            pipeline runs in PRE-MINT mode: holding checks are skipped
            and every candidate with a non-null wallet OR x_handle is
            considered verified.
        pool_sol: Total SOL distributed across all winners (split
            evenly downstream by the propaganda template).
        winners_count: How many winners to pick.
        min_holding_usd: USD threshold each verified wallet must clear.
        manual_wallets: ``{x_handle: wallet_address}`` overrides for
            participants who haven't linked a wallet via the Terminal.
        dry_run: When True, the snapshot is persisted with
            ``kind = "preview"`` and announce can't fire against it.
        min_level: Only consider clearance rows at or above this level.
        created_by: Admin JTI for audit trail.

    Returns a dict shaped roughly:
        {
            "snapshot_id":     str,
            "kind":            "preview" | "extraction",
            "draw_date_iso":   str,
            "pre_mint":        bool,
            "eligible":        int,
            "verified":        int,
            "winners":         [{x_handle, wallet, wallet_short, holding_usd}, ...],
            "pool_sol":        float,
            "per_winner_sol":  float,
            "seed": {
                "blockhash":   str,
                "slot":        int,
                "fingerprint": str,
                "captured_at": str,
            } | null,
            "price_usd":       float | null,
            "errors":          [str, ...],
            "created_at":      str,
        }
    """
    manual = {
        (_normalise_handle(k) or ""): v
        for k, v in (manual_wallets or {}).items()
        if _normalise_handle(k) and _SOLANA_ADDR_RE.match((v or "").strip())
    }
    errors: List[str] = []

    candidates = await list_eligible_candidates(min_level=min_level)
    eligible_count = len(candidates)

    # ---- Price feed (skipped in PRE-MINT) ----
    pre_mint = not _is_valid_mint(token_mint)
    price_usd: Optional[float] = None
    if not pre_mint and token_mint:
        price_usd, price_err = await get_deep_price_usd(token_mint)
        if price_err:
            errors.append(f"price:{price_err}")

    # ---- Holding check per candidate ----
    verified_pool: List[Dict[str, Any]] = []
    detailed: List[Dict[str, Any]] = []
    for cand in candidates:
        handle = cand["x_handle"]
        wallet = cand.get("wallet_address") or manual.get(handle) or None
        check: Dict[str, Any] = {
            "x_handle": handle,
            "email": cand.get("email"),
            "wallet": wallet,
            "wallet_short": _short_wallet(wallet),
            "level": cand.get("level"),
            "status": "pre_mint" if pre_mint else "pending",
            "holding_tokens": 0.0,
            "holding_usd": 0.0,
        }

        if pre_mint:
            # In PRE-MINT mode every candidate is considered verified.
            check["status"] = "pre_mint"
            verified_pool.append(check)
            detailed.append(check)
            continue

        if not wallet:
            check["status"] = "no_wallet"
            detailed.append(check)
            continue

        # token_mint is guaranteed non-falsy here (pre_mint is False).
        assert token_mint is not None
        tokens, err = await get_holding_tokens(wallet, token_mint)
        if err:
            check["status"] = f"rpc_error:{err}"
            errors.append(f"rpc:{handle}:{err}")
            detailed.append(check)
            continue
        check["holding_tokens"] = round(tokens, 6)
        usd = (tokens * price_usd) if (price_usd is not None) else 0.0
        check["holding_usd"] = round(usd, 4)
        if price_usd is None:
            check["status"] = "no_price"
        elif usd >= min_holding_usd:
            check["status"] = "verified"
            verified_pool.append(check)
        else:
            check["status"] = "under_threshold"
        detailed.append(check)

    verified_count = len(verified_pool)

    # ---- Provably fair RNG ----
    seed_info: Optional[Dict[str, Any]] = None
    winners: List[Dict[str, Any]] = []
    if verified_count > 0 and winners_count > 0:
        seed_input, seed_err = await fetch_solana_seed()
        if seed_err or not seed_input:
            errors.append(f"seed:{seed_err or 'unknown'}")
        else:
            sorted_handles = sorted(p["x_handle"] for p in verified_pool)
            seed_int, fingerprint = derive_rng_seed(
                blockhash=seed_input["blockhash"],
                slot=seed_input["slot"],
                sorted_handles=sorted_handles,
                draw_date_iso=draw_date_iso,
            )
            seed_info = {
                "blockhash": seed_input["blockhash"],
                "slot": seed_input["slot"],
                "captured_at": seed_input["captured_at"],
                "fingerprint": fingerprint,
            }
            winners = pick_winners_deterministic(
                pool=verified_pool, count=winners_count, seed_int=seed_int,
            )

    per_winner_sol = (
        round(pool_sol / len(winners), 4) if winners else 0.0
    )

    snapshot_id = str(uuid.uuid4())
    snapshot = {
        "_id": snapshot_id,
        "kind": "preview" if dry_run else "extraction",
        "draw_date_iso": draw_date_iso,
        "token_mint": token_mint or None,
        "pre_mint": pre_mint,
        "pool_sol": float(pool_sol),
        "per_winner_sol": per_winner_sol,
        "winners_count_target": int(winners_count),
        "min_holding_usd": float(min_holding_usd),
        "min_level": int(min_level),
        "eligible_count": eligible_count,
        "verified_count": verified_count,
        "winners": winners,
        "details": detailed,
        "price_usd": price_usd,
        "seed": seed_info,
        "errors": errors,
        "manual_wallets_used": manual,
        "created_at": _now(),
        "created_by": created_by,
        "cancelled_at": None,
        "announced_queue_item_id": None,
    }

    # Persist only when this is a real extraction OR an operator-flagged
    # preview they want to keep. Previews are also persisted because the
    # operator may want a paper trail of "we considered drawing on date X
    # and these were the candidates"; previews are excluded from the
    # unique partial index above so multiple previews coexist freely.
    try:
        await db[COLLECTION].insert_one(snapshot)
    except Exception as exc:
        # Most likely cause: duplicate active extraction on same draw_date.
        if not dry_run and "duplicate key" in str(exc).lower():
            errors.append("duplicate_active_extraction")
            return {
                **_view_snapshot(snapshot),
                "errors": errors,
                "persisted": False,
            }
        logger.exception("[giveaway] snapshot insert failed")
        errors.append("persist_failed")

    return {**_view_snapshot(snapshot), "persisted": True}


def _view_snapshot(snap: Dict[str, Any]) -> Dict[str, Any]:
    """Public-friendly projection of a snapshot doc — flattens the
    Mongo ``_id`` into ``snapshot_id`` and ISO-formats datetimes."""
    return {
        "snapshot_id": str(snap.get("_id") or snap.get("snapshot_id") or ""),
        "kind": snap.get("kind"),
        "draw_date_iso": snap.get("draw_date_iso"),
        "token_mint": snap.get("token_mint"),
        "pre_mint": bool(snap.get("pre_mint")),
        "pool_sol": snap.get("pool_sol"),
        "per_winner_sol": snap.get("per_winner_sol"),
        "winners_count_target": snap.get("winners_count_target"),
        "min_holding_usd": snap.get("min_holding_usd"),
        "min_level": snap.get("min_level"),
        "eligible_count": snap.get("eligible_count"),
        "verified_count": snap.get("verified_count"),
        "winners": snap.get("winners") or [],
        "details": snap.get("details") or [],
        "price_usd": snap.get("price_usd"),
        "seed": snap.get("seed"),
        "errors": snap.get("errors") or [],
        "created_at": _iso(snap.get("created_at")) if isinstance(snap.get("created_at"), datetime) else snap.get("created_at"),
        "created_by": snap.get("created_by"),
        "cancelled_at": _iso(snap.get("cancelled_at")) if isinstance(snap.get("cancelled_at"), datetime) else snap.get("cancelled_at"),
        "announced_queue_item_id": snap.get("announced_queue_item_id"),
    }


async def get_snapshot(snapshot_id: str) -> Optional[Dict[str, Any]]:
    doc = await db[COLLECTION].find_one({"_id": snapshot_id})
    return _view_snapshot(doc) if doc else None


async def list_snapshots(*, limit: int = 50, kind: Optional[str] = None) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    if kind in ("preview", "extraction"):
        q["kind"] = kind
    cursor = db[COLLECTION].find(q).sort("created_at", -1).limit(max(1, min(limit, 200)))
    rows = await cursor.to_list(length=None)
    return [_view_snapshot(r) for r in rows]


async def cancel_snapshot(snapshot_id: str, actor_jti: Optional[str]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Soft-delete a snapshot (clears the unique idx slot)."""
    doc = await db[COLLECTION].find_one({"_id": snapshot_id})
    if not doc:
        return None, "not_found"
    if doc.get("cancelled_at"):
        return _view_snapshot(doc), "already_cancelled"
    await db[COLLECTION].update_one(
        {"_id": snapshot_id},
        {"$set": {"cancelled_at": _now(), "cancelled_by": actor_jti}},
    )
    refreshed = await db[COLLECTION].find_one({"_id": snapshot_id})
    return _view_snapshot(refreshed), None


def format_winners_for_template(
    winners: List[Dict[str, Any]],
    *,
    max_render: int = 5,
) -> str:
    """Render the winners list as a single string suitable for tweet
    interpolation: ``@alice, @bob`` (or comma-joined). Truncates at
    ``max_render`` with a trailing ``+N more`` when needed."""
    if not winners:
        return ""
    handles = [f"@{w['x_handle']}" for w in winners if w.get("x_handle")]
    if len(handles) <= max_render:
        return ", ".join(handles)
    return ", ".join(handles[:max_render]) + f", +{len(handles) - max_render} more"


__all__ = [
    "COLLECTION",
    "DEFAULT_WINNERS_COUNT",
    "DEFAULT_MIN_HOLDING_USD",
    "ensure_indexes",
    "list_eligible_candidates",
    "get_deep_price_usd",
    "get_holding_tokens",
    "fetch_solana_seed",
    "derive_rng_seed",
    "pick_winners_deterministic",
    "run_extraction",
    "get_snapshot",
    "list_snapshots",
    "cancel_snapshot",
    "format_winners_for_template",
]
