"""Clearance Levels ledger — Sprint 14.1 (Proof of Intelligence airdrop gate).

Three levels map to the operator's spec:

  * Level 1 (Observer)     — follow @Deepotus_AI + join TG (verified in 14.2)
  * Level 2 (Infiltrator)  — share a Prophecy with #DEEPOTUS (verified in 14.2)
  * Level 3 (Agent)        — solve AT LEAST ONE riddle in the Terminal

In Sprint 14.1 only Level 3 is *verifiable automatically* (through
``riddles.submit_attempt``). Levels 1 & 2 are recordable manually from
the admin dashboard, so the operator can kick off the whitelist now
while Sprint 14.2 wires the X / Telegram checks.

Identity model (choice 1C validated by user):
  * primary key = email (required once the user engages),
  * wallet address OPTIONAL until Level 3, at which point a wallet is
    STRONGLY RECOMMENDED — the admin export excludes Level 3 records
    without a linked wallet.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.infiltration.clearance")

_SOLANA_ADDR_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_valid_solana(addr: str) -> bool:
    """Structural check (base58 alphabet, 32–44 chars). We keep it cheap
    here — full signature-based proof of ownership is Sprint 14.2's job."""
    return bool(addr and _SOLANA_ADDR_RE.match(addr.strip()))


async def ensure_indexes() -> None:
    try:
        await db.clearance_levels.create_index([("email", 1)], unique=True)
        # Use a PARTIAL index rather than a sparse one: sparse only skips
        # documents where the field is ABSENT, not when it is present with
        # value=null. Our row defaults `wallet_address` to null before the
        # user links it, so a sparse index collides on the second insert.
        # The partial filter guarantees only real addresses are indexed.
        await db.clearance_levels.create_index(
            [("wallet_address", 1)],
            unique=True,
            name="wallet_address_unique_when_set",
            partialFilterExpression={
                "wallet_address": {"$exists": True, "$type": "string"},
            },
        )
        await db.clearance_levels.create_index([("level", -1), ("level_achieved_at", 1)])
    except Exception:  # noqa: BLE001
        pass


def _compute_level(doc: Dict[str, Any]) -> int:
    """Derive the current level from the ledger row.

    A level is only awarded when its *prerequisite* is true, so the
    ladder never skips. Level 3 requires at least one solved riddle
    AND Levels 1+2 checks to be ticked — but in 14.1 we relax this for
    bootstrapping: riddle-solved alone promotes to Level 3 so the
    operator can demo the flow pre-launch.
    """
    lvl = 0
    if doc.get("level_1_achieved_at"):
        lvl = 1
    if doc.get("level_2_achieved_at"):
        lvl = 2
    if doc.get("level_3_achieved_at") or (doc.get("riddles_solved") or []):
        lvl = 3
    return lvl


def _normalise_email(email: str) -> str:
    return (email or "").strip().lower()


def _normalise_addr(addr: Optional[str]) -> Optional[str]:
    if not addr:
        return None
    addr = addr.strip()
    if not _is_valid_solana(addr):
        raise ValueError("invalid Solana wallet address")
    return addr


def _view(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    return {
        "id": doc["_id"],
        "email": doc["email"],
        "wallet_address": doc.get("wallet_address"),
        "level": _compute_level(doc),
        "riddles_solved": list(doc.get("riddles_solved") or []),
        "level_1_achieved_at": doc.get("level_1_achieved_at"),
        "level_2_achieved_at": doc.get("level_2_achieved_at"),
        "level_3_achieved_at": doc.get("level_3_achieved_at"),
        "wallet_linked_at": doc.get("wallet_linked_at"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "notes": doc.get("notes"),
        "source": doc.get("source"),
    }


async def _ensure_row(email: str, *, source: str = "terminal") -> Dict[str, Any]:
    email_l = _normalise_email(email)
    if not email_l or "@" not in email_l:
        raise ValueError("valid email required")
    now = _iso()
    doc = await db.clearance_levels.find_one({"email": email_l})
    if doc:
        return doc
    new = {
        "_id": str(uuid.uuid4()),
        "email": email_l,
        # NOTE: `wallet_address` is intentionally omitted here so the unique
        # index (partial, only when present and a string) does not see any
        # row with `null`. It will be $set later by `link_wallet` /
        # `admin_set_wallet`. Same rationale for `level_*_achieved_at`.
        "riddles_solved": [],
        "source": source,
        "created_at": now,
        "updated_at": now,
    }
    await db.clearance_levels.insert_one(new)
    return new


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
async def get_status(email: str) -> Optional[Dict[str, Any]]:
    email_l = _normalise_email(email)
    if not email_l:
        return None
    doc = await db.clearance_levels.find_one({"email": email_l})
    return _view(doc)


async def mark_riddle_solved(
    *, email: str, slug: str, matched_keyword: Optional[str] = None,
) -> Dict[str, Any]:
    """Called by ``core.riddles`` on a correct submission. Idempotent —
    a second submit of the same riddle is a no-op.
    """
    await _ensure_row(email, source="terminal")
    email_l = _normalise_email(email)
    now = _iso()
    res = await db.clearance_levels.find_one_and_update(
        {"email": email_l},
        {
            "$addToSet": {"riddles_solved": slug},
            "$set": {
                "updated_at": now,
                "level_3_achieved_at": now,
            },
            "$push": {
                "events": {
                    "$each": [{"at": now, "type": "riddle_solved",
                               "slug": slug, "matched": matched_keyword}],
                    "$slice": -50,  # keep the last 50 events only
                },
            },
        },
        return_document=True,
    )
    doc = _view(res)
    return {
        "level": (doc or {}).get("level", 0),
        "solved_count": len((doc or {}).get("riddles_solved") or []),
    }


async def link_wallet(*, email: str, wallet_address: str) -> Dict[str, Any]:
    """Attach a Solana wallet to the ledger row. Sprint 14.2 will add
    the signature-verified version; here we store the address so the
    admin snapshot can already export Level 3 → wallet pairs.
    """
    await _ensure_row(email)
    addr = _normalise_addr(wallet_address)
    if addr is None:
        raise ValueError("wallet_address cannot be empty")
    email_l = _normalise_email(email)
    # Enforce 1-to-1: reject if the wallet is already claimed by a different email.
    existing = await db.clearance_levels.find_one({"wallet_address": addr})
    if existing and existing.get("email") != email_l:
        raise ValueError("wallet_address already linked to another agent")
    now = _iso()
    res = await db.clearance_levels.find_one_and_update(
        {"email": email_l},
        {"$set": {"wallet_address": addr, "wallet_linked_at": now,
                  "updated_at": now}},
        return_document=True,
    )
    return _view(res) or {}


# ---------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------
async def list_all(
    *, level: Optional[int] = None, limit: int = 500,
) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {}
    cursor = db.clearance_levels.find(q).sort("updated_at", -1).limit(min(max(limit, 1), 2000))
    rows = [_view(d) async for d in cursor]
    if level is not None:
        rows = [r for r in rows if r and r["level"] == int(level)]
    return rows


async def admin_set_level(
    *, email: str, level: int,
    by_jti: Optional[str] = None, notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Operator override: force-promote (or demote) an agent. Used when
    Levels 1 & 2 are verified manually in 14.1 while 14.2 lags.
    """
    if level not in (0, 1, 2, 3):
        raise ValueError("level must be 0, 1, 2 or 3")
    await _ensure_row(email, source="admin_manual")
    email_l = _normalise_email(email)
    now = _iso()
    patch: Dict[str, Any] = {"updated_at": now}
    # Set the level_X_achieved_at fields in a ladder-consistent way.
    patch["level_1_achieved_at"] = now if level >= 1 else None
    patch["level_2_achieved_at"] = now if level >= 2 else None
    patch["level_3_achieved_at"] = now if level >= 3 else None
    if notes:
        patch["notes"] = str(notes).strip()[:500]
    res = await db.clearance_levels.find_one_and_update(
        {"email": email_l},
        {
            "$set": patch,
            "$push": {
                "events": {
                    "$each": [{"at": now, "type": "admin_level_set",
                               "level": level, "by_jti": by_jti}],
                    "$slice": -50,
                },
            },
        },
        return_document=True,
    )
    return _view(res) or {}


async def admin_set_wallet(
    *, email: str, wallet_address: Optional[str],
    by_jti: Optional[str] = None,
) -> Dict[str, Any]:
    await _ensure_row(email, source="admin_manual")
    email_l = _normalise_email(email)
    addr = _normalise_addr(wallet_address) if wallet_address else None
    now = _iso()
    res = await db.clearance_levels.find_one_and_update(
        {"email": email_l},
        {"$set": {"wallet_address": addr,
                  "wallet_linked_at": now if addr else None,
                  "updated_at": now},
         "$push": {"events": {
             "$each": [{"at": now, "type": "admin_wallet_set",
                        "wallet": addr, "by_jti": by_jti}],
             "$slice": -50,
         }}},
        return_document=True,
    )
    return _view(res) or {}


async def snapshot_level3() -> List[Dict[str, Any]]:
    """Return a pre-airdrop snapshot: Level 3 agents WITH a wallet.

    The admin CSV export filters on this list. Level 3 without a wallet
    are flagged for the operator to chase on Discord/Email.
    """
    all_rows = await list_all(level=3)
    with_wallet = [r for r in all_rows if r and r.get("wallet_address")]
    without_wallet = [r for r in all_rows if r and not r.get("wallet_address")]
    return [
        *with_wallet,
        *[{**r, "_snapshot_status": "no_wallet"} for r in without_wallet],
    ]


async def stats() -> Dict[str, Any]:
    """Aggregate counts for the admin dashboard cards."""
    total = await db.clearance_levels.count_documents({})
    lvl1 = await db.clearance_levels.count_documents({"level_1_achieved_at": {"$ne": None}})
    lvl2 = await db.clearance_levels.count_documents({"level_2_achieved_at": {"$ne": None}})
    lvl3 = await db.clearance_levels.count_documents({"level_3_achieved_at": {"$ne": None}})
    with_wallet = await db.clearance_levels.count_documents({"wallet_address": {"$ne": None}})
    return {
        "total": total,
        "level_1": lvl1,
        "level_2": lvl2,
        "level_3": lvl3,
        "with_wallet": with_wallet,
        "airdrop_eligible": min(lvl3, with_wallet),
    }
