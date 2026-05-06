"""Public Wallet Registry — Sprint Transparency & Trust (pre-mint).

Single source of truth for the five publicly-disclosed wallets behind
the $DEEPOTUS Protocol ΔΣ + the canonical $DEEPOTUS mint address. Used
by the Transparency page (public) and the Admin Panel (operator).

Why a Mongo registry instead of pure env vars?
  * Operators rotate wallets / set locks during the launch window
    without redeploying Render.
  * Each wallet carries an *optional* lock-proof URL (Streamflow,
    Jupiter Lock, …) which is meaningless before launch but mandatory
    post-mint for compliance / MiCA disclosure.
  * The mint address is unknowable until pump.fun confirms — the
    registry lets us flip the site to "mint live" mode in seconds
    without touching code.

Storage shape (collection ``wallet_registry``):

    {
      "_id": "deployer" | "treasury" | "team" | "creator_fees" | "community",
      "address": "<base58 pubkey>",            # may be empty
      "lock_url": "https://streamflow.finance/...",  # may be empty
      "label": "Treasury vault (multi-sig)",   # optional friendly label
      "updated_at": ISODate,
      "updated_by": "<admin_jti>"              # audit trail
    }

The mint address lives in ``vault_state`` under a single canonical key
(``token_mint_address``) so the existing ``vault_state`` plumbing
already handles it via getters/setters — no new collection needed.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import db

logger = logging.getLogger("deepotus.wallet_registry")

WALLET_REGISTRY = "wallet_registry"
VAULT_STATE = "vault_state"
VAULT_STATE_SINGLETON_ID = "vault_state_v1"

# Fixed slot ids — order matters: this is the order the Transparency
# page renders the cards top-to-bottom. Keep this list aligned with the
# i18n keys under ``transparencyPage.wallets.<id>``.
WALLET_SLOTS: List[str] = [
    "deployer",
    "treasury",
    "team",
    "creator_fees",
    "community",
]

# Solana base58 pubkey shape — lifted from clearance_levels._is_valid_solana
# so the contract stays consistent across modules. Empty string is also
# accepted (means "not yet disclosed").
_SOLANA_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

# A lock URL doesn't have a strict schema (each lock provider has its
# own UI), so we accept any https URL. The transparency page just
# renders it as a clickable link, the integrity comes from the operator
# pasting the right URL.
_HTTPS_URL_RE = re.compile(r"^https://[\w./?=&%#:+\-]{8,300}$", re.IGNORECASE)


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------
def _normalise_address(value: Optional[str]) -> str:
    """Trim + validate the pubkey. Empty → empty string. Invalid → raises ValueError."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if not _SOLANA_RE.match(s):
        raise ValueError("address must be a base58-encoded Solana pubkey (32–44 chars)")
    return s


def _normalise_lock_url(value: Optional[str]) -> str:
    """Trim + validate the lock proof URL. Empty → empty string. Invalid → raises ValueError."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if not _HTTPS_URL_RE.match(s):
        raise ValueError("lock_url must be an https:// URL (max 300 chars)")
    return s


def _normalise_label(value: Optional[str]) -> str:
    """Trim. Cap at 80 chars to keep the UI clean."""
    if value is None:
        return ""
    return str(value).strip()[:80]


# ---------------------------------------------------------------------
# CRUD — wallet slots
# ---------------------------------------------------------------------
async def get_all_wallets() -> List[Dict[str, Any]]:
    """Return every slot in the canonical ``WALLET_SLOTS`` order.

    Missing slots are filled with empty strings so the front-end can
    render a stable 5-row table even on a fresh DB.
    """
    rows = await db[WALLET_REGISTRY].find({}).to_list(length=20)
    by_id: Dict[str, Dict[str, Any]] = {str(r.get("_id")): r for r in rows}
    out: List[Dict[str, Any]] = []
    for slot in WALLET_SLOTS:
        row = by_id.get(slot) or {}
        out.append(
            {
                "id": slot,
                "address": str(row.get("address") or ""),
                "lock_url": str(row.get("lock_url") or ""),
                "label": str(row.get("label") or ""),
                "updated_at": row.get("updated_at"),
            }
        )
    return out


async def upsert_wallet(
    slot: str,
    *,
    address: Optional[str] = None,
    lock_url: Optional[str] = None,
    label: Optional[str] = None,
    actor_jti: Optional[str] = None,
) -> Dict[str, Any]:
    """Update one wallet slot. Pass ``None`` to leave a field unchanged.

    Empty string ``""`` is *not* the same as ``None`` — passing
    ``address=""`` clears the slot, while ``address=None`` leaves it
    untouched. This distinction matters for the admin UI: the operator
    explicitly wipes a field by sending an empty string.
    """
    if slot not in WALLET_SLOTS:
        raise ValueError(
            f"unknown wallet slot {slot!r}; expected one of {WALLET_SLOTS}",
        )

    update: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if actor_jti:
        update["updated_by"] = actor_jti
    if address is not None:
        update["address"] = _normalise_address(address)
    if lock_url is not None:
        update["lock_url"] = _normalise_lock_url(lock_url)
    if label is not None:
        update["label"] = _normalise_label(label)

    await db[WALLET_REGISTRY].update_one(
        {"_id": slot},
        {"$set": update, "$setOnInsert": {"_id": slot}},
        upsert=True,
    )
    fresh = await db[WALLET_REGISTRY].find_one({"_id": slot}) or {}
    return {
        "id": slot,
        "address": str(fresh.get("address") or ""),
        "lock_url": str(fresh.get("lock_url") or ""),
        "label": str(fresh.get("label") or ""),
        "updated_at": fresh.get("updated_at"),
    }


# ---------------------------------------------------------------------
# CRUD — token mint address (lives in vault_state)
# ---------------------------------------------------------------------
async def get_mint_address() -> str:
    """Return the canonical $DEEPOTUS mint address, or ``""`` if unset."""
    row = await db[VAULT_STATE].find_one({"_id": VAULT_STATE_SINGLETON_ID}) or {}
    return str(row.get("token_mint_address") or "")


async def set_mint_address(
    address: Optional[str],
    *,
    actor_jti: Optional[str] = None,
) -> str:
    """Set / clear the mint address. Returns the persisted value."""
    normalised = _normalise_address(address)
    update: Dict[str, Any] = {
        "token_mint_address": normalised,
        "token_mint_address_updated_at": datetime.now(timezone.utc),
    }
    if actor_jti:
        update["token_mint_address_updated_by"] = actor_jti
    await db[VAULT_STATE].update_one(
        {"_id": VAULT_STATE_SINGLETON_ID},
        {"$set": update},
        upsert=True,
    )
    return normalised


# ---------------------------------------------------------------------
# Public read API — what the Transparency page actually consumes
# ---------------------------------------------------------------------
async def public_snapshot() -> Dict[str, Any]:
    """Single, public, no-secret snapshot for the /transparency page.

    Returns a dict with:
      * ``wallets``     — list of {id, address, lock_url, label}
      * ``mint_address`` — string (empty until launch)
      * ``mint_live``    — bool, ``True`` iff mint_address is non-empty
      * ``rugcheck_url`` — derived RugCheck deeplink (empty pre-mint)
    """
    wallets = await get_all_wallets()
    mint = await get_mint_address()
    return {
        "wallets": [
            {
                "id": w["id"],
                "address": w["address"],
                "lock_url": w["lock_url"],
                "label": w["label"],
            }
            for w in wallets
        ],
        "mint_address": mint,
        "mint_live": bool(mint),
        "rugcheck_url": f"https://rugcheck.xyz/tokens/{mint}" if mint else "",
    }


# ---------------------------------------------------------------------
# Index bootstrap
# ---------------------------------------------------------------------
async def ensure_indexes() -> None:
    """No secondary indexes needed — slot ids are the natural ``_id``.
    We keep the function so the bootstrap surface in ``server.py``
    stays uniform across modules.
    """
    return None
