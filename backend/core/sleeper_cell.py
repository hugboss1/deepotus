"""Sleeper Cell mode — Sprint 14.1.

A global pre-launch toggle the operator flips ON before the token is
minted and OFF the moment the contract goes live on Pump.fun. When ON:

  * the landing page hides every ``buy_link`` / direct purchase CTA,
  * the Propaganda Engine's mint / whale / pumpswap triggers are blocked
    (the market simply isn't live yet — no point shouting about it),
  * only the Proof-of-Intelligence terminal stays fully accessible —
    that's the only legitimate entry point for pre-launch agents.

We keep the implementation intentionally tiny: a singleton document in
``infiltration_settings`` with an ``active`` boolean + a short custom
message the operator can tailor (“The vault sealed. Complete your
Proof of Intelligence first.”).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.config import db

logger = logging.getLogger("deepotus.infiltration.sleeper")

SETTINGS_ID = "sleeper_cell"

DEFAULT_DOC: Dict[str, Any] = {
    "_id": SETTINGS_ID,
    "active": True,  # we start ON — pre-mint by default.
    "message_fr": (
        "MODE DORMANT ACTIF. Le coffre est scellé. Complétez la Preuve "
        "d'Intelligence pour obtenir votre accréditation."
    ),
    "message_en": (
        "SLEEPER CELL ENGAGED. The vault is sealed. Complete the Proof of "
        "Intelligence to earn your clearance."
    ),
    "activated_at": datetime.now(timezone.utc).isoformat(),
    "deactivated_at": None,
    "blocked_triggers": ["mint", "whale_buy", "mc_milestone", "pumpswap_migration"],
    "version": 1,
}


async def get_state() -> Dict[str, Any]:
    doc = await db.infiltration_settings.find_one({"_id": SETTINGS_ID})
    if not doc:
        await db.infiltration_settings.insert_one(DEFAULT_DOC)
        doc = DEFAULT_DOC
    return {k: v for k, v in doc.items() if k != "_id"}


async def set_state(
    *,
    active: Optional[bool] = None,
    message_fr: Optional[str] = None,
    message_en: Optional[str] = None,
    blocked_triggers: Optional[list] = None,
    by_jti: Optional[str] = None,
) -> Dict[str, Any]:
    patch: Dict[str, Any] = {}
    now = datetime.now(timezone.utc).isoformat()
    if active is not None:
        patch["active"] = bool(active)
        if active:
            patch["activated_at"] = now
            patch["deactivated_at"] = None
        else:
            patch["deactivated_at"] = now
    if message_fr is not None:
        patch["message_fr"] = (message_fr or "").strip()[:500]
    if message_en is not None:
        patch["message_en"] = (message_en or "").strip()[:500]
    if blocked_triggers is not None:
        patch["blocked_triggers"] = [str(x).strip() for x in blocked_triggers if str(x).strip()]
    if patch:
        patch["last_changed_by_jti"] = by_jti
        await db.infiltration_settings.update_one(
            {"_id": SETTINGS_ID},
            {"$set": patch, "$inc": {"version": 1}},
            upsert=True,
        )
        if active is not None:
            logger.warning(
                "[sleeper_cell] mode %s (by_jti=%s)",
                "ACTIVATED" if active else "DEACTIVATED", by_jti,
            )
    return await get_state()


async def is_trigger_blocked(trigger_key: str) -> bool:
    """Called by the Propaganda Engine before firing a market trigger.

    When the sleeper cell is ON, market triggers (mint, whale, etc.)
    produce no queue item so we never leak a buy link while the vault
    is still sealed. The ``jeet_dip`` trigger is NOT in the block list
    by default — you won’t have a dip on a token that's not live yet.
    """
    state = await get_state()
    if not state.get("active"):
        return False
    return trigger_key in (state.get("blocked_triggers") or [])
