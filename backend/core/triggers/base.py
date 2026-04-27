"""Shared types and registry for the Propaganda Engine triggers.

A *trigger* is a thin policy object that decides:
  1. whether a market event (or a manual fire) should produce a message,
  2. which payload (placeholders) to ship with the templated message,
  3. an idempotency key so we never double-fire on Helius retries.

Dispatch / approval / rate-limiting happens *outside* the trigger — keep
these modules dumb and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

# ---------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------
@dataclass
class TriggerCtx:
    """Context passed to a trigger when it is *fired*.

    Carries everything the detector + template renderer need: live market
    snapshot, the manual-fire flag (so triggers can short-circuit market
    checks during pre-mint testing), and the admin's audit JTI.
    """

    trigger_key: str
    manual: bool = False
    market: Dict[str, Any] = field(default_factory=dict)
    payload_override: Dict[str, Any] = field(default_factory=dict)
    jti: Optional[str] = None
    ip: Optional[str] = None


@dataclass
class TriggerResult:
    """What a trigger produces when it decides to fire.

    ``payload`` populates the template placeholders (e.g. ``{mc}``,
    ``{whale_amount}``, ``{buy_link}``). ``idempotency_key`` is hashed
    into the queue document so Helius retries collapse into a single
    queued message.
    """

    fired: bool
    payload: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None
    reason: Optional[str] = None  # populated when fired=False, for diagnostics


TriggerFn = Callable[[TriggerCtx], TriggerResult]


@dataclass
class Trigger:
    """Static metadata + bound detector function.

    Stored once in process memory; the *runtime* config (enabled flag,
    policy, cooldown overrides) lives in the ``propaganda_triggers``
    Mongo collection so the admin can flip it at will.
    """

    key: str
    label: str
    description: str
    default_policy: str = "approval"   # "auto" | "approval"
    default_cooldown_minutes: int = 15
    detect: Optional[TriggerFn] = None
    metadata_defaults: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------
# Module-level registry — populated by side-effect imports.
# ---------------------------------------------------------------------
KNOWN_TRIGGERS: Dict[str, Trigger] = {}


def register_trigger(t: Trigger) -> Trigger:
    if t.key in KNOWN_TRIGGERS:
        raise RuntimeError(f"Trigger '{t.key}' already registered.")
    KNOWN_TRIGGERS[t.key] = t
    return t
