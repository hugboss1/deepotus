"""Classified vault seal status logic.

The classified vault (= real $DEEPOTUS vault) MUST stay sealed until the token
is actually live on-chain. This module computes the sealed/live status from
the vault_state document, with an optional admin override for QA/testing.

Auto-rule (when override == None):
    sealed = True  IF (helius_demo_mode OR no mint set OR dex_mode != 'helius')
    sealed = False otherwise

Override (admin-only, stored in vault_state.classified_vault_sealed_override):
    None  → use auto-rule
    True  → force SEALED (vault locked, even if mint live)
    False → force LIVE (vault open, even if demo mode — for staff QA)

Public exposure:
    GET /api/vault/classified-status → { sealed, mint_live, launch_eta }
    Used by TerminalPopup to switch into "sealed" phase narrative.

Defense in depth:
    /api/access-card/request and /api/access-card/verify both call
    raise_if_sealed() to return 403 VAULT_SEALED even on direct API hits.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException

VAULT_DOC_ID = "protocol_delta_sigma"


def compute_sealed_status(vs: dict) -> dict:
    """Compute the canonical sealed/live status from a vault_state document.

    Returns a dict safe for public exposure (no override field leaked).
    """
    override = vs.get("classified_vault_sealed_override")
    if isinstance(override, bool):
        sealed = override
        source = "override"
    else:
        mint_set = bool((vs.get("dex_token_address") or "").strip())
        is_demo = bool(vs.get("helius_demo_mode"))
        is_helius_mode = vs.get("dex_mode") == "helius"
        sealed = is_demo or (not mint_set) or (not is_helius_mode)
        source = "auto"
    launch_eta = vs.get("launch_eta") or os.environ.get("DEEPOTUS_LAUNCH_ISO")
    return {
        "sealed": sealed,
        "mint_live": not sealed,
        "launch_eta": launch_eta,
        "source": source,  # "auto" | "override"
    }


def admin_status(vs: dict) -> dict:
    """Same as compute_sealed_status but also exposes the override raw value
    for the admin UI (so it can render a 3-state toggle: Auto / Sealed / Live).
    """
    pub = compute_sealed_status(vs)
    pub["override"] = vs.get("classified_vault_sealed_override")  # None | True | False
    pub["mint"] = (vs.get("dex_token_address") or None)
    pub["helius_demo_mode"] = bool(vs.get("helius_demo_mode"))
    pub["dex_mode"] = vs.get("dex_mode")
    return pub


async def get_sealed_status(db) -> dict:
    """Async helper that loads vault_state and returns the public status."""
    vs = await db.vault_state.find_one({"_id": VAULT_DOC_ID}) or {}
    return compute_sealed_status(vs)


async def is_currently_sealed(db) -> bool:
    """Convenience boolean."""
    return (await get_sealed_status(db))["sealed"]


async def raise_if_sealed(db, *, action: str = "access") -> None:
    """Raise 403 VAULT_SEALED with a Deep-State-flavoured message.

    Call this at the top of access_card endpoints to enforce the rule
    server-side (defense in depth: even if frontend is bypassed).
    """
    if await is_currently_sealed(db):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "VAULT_SEALED",
                "message": (
                    "Transmission denied. The classified vault is sealed until "
                    "$DEEPOTUS genesis. Subscribe to the Genesis broadcast to be "
                    "notified when accreditations re-open."
                ),
                "action": action,
            },
        )


async def set_override(db, override: Optional[bool]) -> dict:
    """Persist or clear the admin override. Returns the new admin status."""
    if override is None:
        await db.vault_state.update_one(
            {"_id": VAULT_DOC_ID},
            {"$unset": {"classified_vault_sealed_override": ""}},
            upsert=True,
        )
    else:
        await db.vault_state.update_one(
            {"_id": VAULT_DOC_ID},
            {"$set": {"classified_vault_sealed_override": bool(override)}},
            upsert=True,
        )
    vs = await db.vault_state.find_one({"_id": VAULT_DOC_ID}) or {}
    return admin_status(vs)
