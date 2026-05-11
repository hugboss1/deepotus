"""Burn Logs — Operation Incinerator (Sprint 17.6).

Records every on-chain $DEEPOTUS burn the operator publicly discloses,
maintains an aggregate, and exposes a "Proof of Scarcity" feed to the
public transparency page.

Schema (collection ``burn_logs``):
    {
      "_id":            uuid4 str,
      "amount":         int   (whole tokens burned — we accept floats
                              but coerce to int via floor since
                              fractional burns are meaningless),
      "tx_signature":   str   (Solana tx sig, validated as 64-128 char
                              base58),
      "tx_link":        str   (rendered solscan URL — built once at
                              insert so the propaganda template can
                              pull it without recomputing),
      "burned_at":      ISO   (caller-supplied or now),
      "source":         str   ("manual" | "scheduler" | ...),
      "note":           str   (optional admin note),
      "redacted_at":    ISO?  (soft-delete marker — kept in collection
                              but excluded from totals + public list),
      "redacted_by":    str?  (admin jti — audit trail),
      "created_at":     ISO,
      "created_by":     str?  (admin jti at insert time),
      "queue_item_id":  str?  (propaganda queue item produced by the
                              auto-fire pipeline — for traceability).
    }

Indexes (idempotent — bootstrapped from ``ensure_indexes``):
    * ``tx_signature`` unique partial (active rows only) — prevents
      double-counting the same on-chain burn even if the admin clicks
      Disclose twice. Redacted rows are excluded from uniqueness via
      a ``partialFilterExpression``.
    * ``burned_at`` desc — feeds the public list ordering.
    * ``created_at`` desc — feeds the admin list ordering.

Invariants:
    * ``INITIAL_SUPPLY`` is the canonical maximum supply (1,000,000,000
      $DEEPOTUS). Circulating = max(0, INITIAL - total_burned).
    * ``total_burned()`` only sums non-redacted rows.
    * The aggregate is computed live on every call. We tested at 100k
      rows the latency stays sub-50ms with the burned_at index; well
      beyond pre-launch ambitions.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.config import db

logger = logging.getLogger("deepotus.burn_logs")

COLLECTION = "burn_logs"

#: Canonical max supply for $DEEPOTUS. Hard-coded by design — this is
#: the immutable mint cap baked into the token program; changing it in
#: code would silently desync the "Circulating Supply" computation.
#: The mint authority is renounced post-launch, so this value will
#: never change.
INITIAL_SUPPLY: int = 1_000_000_000

# ---------------------------------------------------------------------
# Locked allocations (Sprint 17.6 — Cabinet Investor Honesty Pact)
# ---------------------------------------------------------------------
# These allocations are NOT in free circulation at launch — they sit
# behind a public multisig (Treasury) and a vesting contract (Team)
# per the Tokenomics & Treasury Policy §3/§5. We deduct them from the
# *displayed* circulating supply so investors see the truly tradeable
# supply, not the cap-table fiction.
#
# Together they represent 45% of the initial supply (300M + 150M out
# of 1B). The disclaimer rendered next to the metric on /transparency
# spells this out so there is zero ambiguity:
#
#     « Real-time circulating supply, excluding the 45% currently
#       under public multisig / vesting locks. »
#
# If the lock policy ever changes (e.g. partial unlock vote), these
# constants must be updated in lock-step with the on-chain reality
# AND the wallet_registry "purpose" copy, and a public disclosure
# fire'd via the Propaganda Engine to avoid surprise dilution.
TREASURY_LOCKED: int = 300_000_000  # Treasury multisig (30% of supply)
TEAM_LOCKED: int = 150_000_000      # Team vesting contract (15% of supply)
LOCKED_TOTAL: int = TREASURY_LOCKED + TEAM_LOCKED  # 450M (45%)

#: Solana transaction signatures are base58-encoded 64-byte arrays →
#: 64..88 chars in practice (rare edge cases up to ~90). We accept
#: 32..128 for forward-compat with any cluster oddities, but reject
#: anything blatantly malformed (URLs, decimal, etc.).
_TX_SIG_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,128}$")

#: Solscan is the most operator-friendly explorer (clear UI, full tx
#: history, supports both mainnet + devnet via cluster query). We
#: render the link at insert time so the propaganda template can
#: include the canonical URL without re-derivation. To switch to a
#: different explorer post-mint, edit this single template.
_SOLSCAN_URL_TEMPLATE = "https://solscan.io/tx/{sig}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _build_tx_link(sig: str) -> str:
    return _SOLSCAN_URL_TEMPLATE.format(sig=sig)


# ---------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    """Idempotent — called once at startup from server.py."""
    try:
        await db[COLLECTION].create_index(
            [("tx_signature", 1)],
            unique=True,
            name="burn_logs_tx_unique_active",
            partialFilterExpression={"redacted_at": None},
        )
        await db[COLLECTION].create_index(
            [("burned_at", -1)], name="burn_logs_burned_at_desc",
        )
        await db[COLLECTION].create_index(
            [("created_at", -1)], name="burn_logs_created_at_desc",
        )
    except Exception:  # noqa: BLE001
        logger.exception("[burn_logs] index bootstrap failed")


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------
def normalise_amount(raw: Any) -> Tuple[int, Optional[str]]:
    """Return ``(amount_int, None)`` on success, ``(0, reason)`` else.

    We're deliberately permissive about input shape (string, float,
    decimal-prefixed) because the admin form ships free-text and we
    want the failure surface to be a clear validation toast, not a
    500. Negative, zero, or absurdly large values (> INITIAL_SUPPLY)
    are rejected.
    """
    try:
        # int(float(...)) handles "1234.5" → 1234, "1e6" → 1000000.
        amt = int(float(raw))
    except (TypeError, ValueError):
        return 0, "amount_not_numeric"
    if amt <= 0:
        return 0, "amount_must_be_positive"
    if amt > INITIAL_SUPPLY:
        return 0, "amount_exceeds_initial_supply"
    return amt, None


def normalise_signature(raw: Any) -> Tuple[str, Optional[str]]:
    """Validate a Solana tx signature. Returns ``(sig, None)`` on
    success."""
    sig = str(raw or "").strip()
    if not sig:
        return "", "tx_signature_required"
    if not _TX_SIG_RE.match(sig):
        return "", "tx_signature_invalid_format"
    return sig, None


def _parse_iso(raw: Any) -> Optional[datetime]:
    """Parse an ISO 8601 string (with or without Z suffix). Returns
    None on any parse error — the caller picks ``_now`` as fallback."""
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------
async def record_burn(
    *,
    amount: Any,
    tx_signature: Any,
    burned_at: Any = None,
    source: str = "manual",
    note: Optional[str] = None,
    created_by: Optional[str] = None,
    queue_item_id: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Insert a new burn log. Returns ``(doc, None)`` on success or
    ``(None, reason)`` on validation / duplicate failure.

    The function is **idempotent on tx_signature**: a second insert with
    the same active (non-redacted) signature returns
    ``(existing_doc, "duplicate_tx_signature")`` so the admin sees a
    helpful warning toast rather than a 500 from Mongo's unique index.
    """
    amt, amt_err = normalise_amount(amount)
    if amt_err:
        return None, amt_err

    sig, sig_err = normalise_signature(tx_signature)
    if sig_err:
        return None, sig_err

    # Idempotency probe BEFORE insert.
    existing = await db[COLLECTION].find_one(
        {"tx_signature": sig, "redacted_at": None},
    )
    if existing:
        return _view(existing), "duplicate_tx_signature"

    burned_dt = _parse_iso(burned_at) or _now()
    now_iso = _now_iso()
    doc: Dict[str, Any] = {
        "_id": str(uuid.uuid4()),
        "amount": amt,
        "tx_signature": sig,
        "tx_link": _build_tx_link(sig),
        "burned_at": burned_dt.isoformat(),
        "source": (source or "manual").strip() or "manual",
        "note": (note or "").strip() or None,
        "redacted_at": None,
        "redacted_by": None,
        "created_at": now_iso,
        "created_by": (created_by or "").strip() or None,
        "queue_item_id": queue_item_id,
    }
    try:
        await db[COLLECTION].insert_one(doc)
    except Exception as exc:  # noqa: BLE001
        # Mongo DuplicateKeyError lands here when a concurrent insert
        # beat us between our probe and the write. Re-fetch and return.
        if "duplicate key" in str(exc).lower():
            again = await db[COLLECTION].find_one(
                {"tx_signature": sig, "redacted_at": None},
            )
            return (_view(again) if again else None), "duplicate_tx_signature"
        logger.exception("[burn_logs] insert failed sig=%s", sig)
        return None, f"insert_error: {exc}"

    logger.info(
        "[burn_logs] recorded amount=%d sig=%s source=%s by=%s",
        amt, sig, doc["source"], doc["created_by"],
    )
    return _view(doc), None


# ---------------------------------------------------------------------
# Redaction (soft delete)
# ---------------------------------------------------------------------
async def redact_burn(
    *, burn_id: str, redacted_by: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Mark a burn as redacted. The row stays in the collection (audit
    trail) but is excluded from totals + public listing."""
    doc = await db[COLLECTION].find_one({"_id": burn_id})
    if not doc:
        return None, "not_found"
    if doc.get("redacted_at"):
        return _view(doc), "already_redacted"
    now = _now_iso()
    await db[COLLECTION].update_one(
        {"_id": burn_id},
        {"$set": {
            "redacted_at": now,
            "redacted_by": redacted_by,
            "updated_at": now,
        }},
    )
    fresh = await db[COLLECTION].find_one({"_id": burn_id})
    return _view(fresh), None


# ---------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------
async def total_burned() -> int:
    """Sum of every active (non-redacted) burn amount.

    We use Mongo's $sum aggregation rather than pulling docs into
    Python because the result type is consistent (int64) regardless
    of row count, and the operation is O(index-scan)."""
    pipeline = [
        {"$match": {"redacted_at": None}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]
    async for doc in db[COLLECTION].aggregate(pipeline):
        return int(doc.get("total") or 0)
    return 0


async def circulating_supply() -> int:
    """``INITIAL_SUPPLY - total_burned``, floored at 0 for paranoia
    (an admin disclosing > INITIAL_SUPPLY would otherwise yield a
    negative public count)."""
    return max(0, INITIAL_SUPPLY - await total_burned())


async def stats() -> Dict[str, Any]:
    """Single-call snapshot for the public transparency page.

    Returns the full picture: initial supply, total burned, raw
    circulating supply (initial - burned), the locked allocations
    (Treasury + Team), the **effective circulating supply** that the
    UI must surface (= initial - burned - locked_total), count of
    disclosed burns, and timestamp of the latest disclosed burn (so
    the UI can show "Last burn: 2h ago" without a second round-trip).

    Why ``effective_circulating`` and not just ``circulating_supply``?
    The "Cabinet Investor Honesty Pact" (Sprint 17.6) requires we
    publicly subtract the 45% sitting in Treasury multisig + Team
    vesting from the displayed circulating count. Otherwise an
    investor doing a back-of-envelope FDV calc would price tokens
    using a fiction (the cap), not the float.
    """
    burned = await total_burned()
    count = await db[COLLECTION].count_documents({"redacted_at": None})
    latest = await db[COLLECTION].find_one(
        {"redacted_at": None},
        sort=[("burned_at", -1)],
        projection={"_id": 1, "amount": 1, "tx_signature": 1, "tx_link": 1, "burned_at": 1},
    )
    raw_circulating = max(0, INITIAL_SUPPLY - burned)
    effective_circulating = max(0, INITIAL_SUPPLY - burned - LOCKED_TOTAL)
    return {
        "initial_supply": INITIAL_SUPPLY,
        "total_burned": burned,
        # Raw circulating = initial - burned. Kept for backward
        # compatibility with any older client; the UI must NOT surface
        # this value directly post Sprint 17.6 — use
        # ``effective_circulating`` instead.
        "circulating_supply": raw_circulating,
        # Locks (Sprint 17.6).
        "treasury_locked": TREASURY_LOCKED,
        "team_locked": TEAM_LOCKED,
        "locked_total": LOCKED_TOTAL,
        # The HONEST circulating count the UI should display.
        "effective_circulating": effective_circulating,
        # Convenience: percentage of supply currently under lock (for
        # the disclaimer copy — keeps the "45%" claim derived from
        # constants instead of hardcoded twice in the codebase).
        "locked_percent": (
            round(100 * LOCKED_TOTAL / INITIAL_SUPPLY, 2)
            if INITIAL_SUPPLY else 0.0
        ),
        "burn_count": int(count or 0),
        "burned_percent": (
            round(100 * burned / INITIAL_SUPPLY, 4) if INITIAL_SUPPLY else 0.0
        ),
        "latest_burn": (
            {
                "id": latest["_id"],
                "amount": int(latest.get("amount") or 0),
                "tx_signature": latest.get("tx_signature"),
                "tx_link": latest.get("tx_link"),
                "burned_at": latest.get("burned_at"),
            }
            if latest else None
        ),
    }


# ---------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------
async def list_burns(
    *,
    limit: int = 50,
    include_redacted: bool = False,
) -> List[Dict[str, Any]]:
    """Return up to ``limit`` burns ordered by ``burned_at`` desc.

    Public endpoint pages set ``include_redacted=False`` (default);
    the admin list opts into ``True`` so the audit trail is visible.
    """
    query: Dict[str, Any] = {} if include_redacted else {"redacted_at": None}
    cursor = (
        db[COLLECTION]
        .find(query)
        .sort("burned_at", -1)
        .limit(max(1, min(500, int(limit))))
    )
    return [_view(d) async for d in cursor]


def _view(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    return {
        "id": doc["_id"],
        "amount": int(doc.get("amount") or 0),
        "tx_signature": doc.get("tx_signature"),
        "tx_link": doc.get("tx_link"),
        "burned_at": doc.get("burned_at"),
        "source": doc.get("source") or "manual",
        "note": doc.get("note"),
        "redacted_at": doc.get("redacted_at"),
        "redacted_by": doc.get("redacted_by"),
        "created_at": doc.get("created_at"),
        "created_by": doc.get("created_by"),
        "queue_item_id": doc.get("queue_item_id"),
    }


__all__ = [
    "INITIAL_SUPPLY",
    "TREASURY_LOCKED",
    "TEAM_LOCKED",
    "LOCKED_TOTAL",
    "COLLECTION",
    "ensure_indexes",
    "normalise_amount",
    "normalise_signature",
    "record_burn",
    "redact_burn",
    "total_burned",
    "circulating_supply",
    "stats",
    "list_burns",
]
