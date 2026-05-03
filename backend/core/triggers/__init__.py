"""Trigger registry for the Propaganda Engine.

Each trigger is a small detector module that produces a *fire intent*
(``TriggerResult``) — either from real market data (Helius webhook) or
from a manual admin button (``Manual Fire``).

The registry pattern lets us discover and validate triggers at startup,
seed Mongo with their config rows, and route Manual Fire calls to the
right detector by ``key``.
"""

from __future__ import annotations

from .base import (
    KNOWN_TRIGGERS,
    Trigger,
    TriggerCtx,
    TriggerResult,
    register_trigger,
)
from . import (  # noqa: F401  — side-effect imports register triggers
    founder_buy,
    jeet_dip,
    kol_mention,
    mc_milestone,
    mint,
    pumpswap_migration,
    whale_buy,
)

__all__ = [
    "KNOWN_TRIGGERS",
    "Trigger",
    "TriggerCtx",
    "TriggerResult",
    "register_trigger",
]
