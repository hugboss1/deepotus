"""Trigger 4 — 'whale recognition'.

Fires when a single buy transaction is larger than the configured
threshold (default: 5 SOL). The detector reads two pieces of data from
the market context:

  * ``last_buy.amount_sol`` — size of the most recent ingested swap
  * ``last_buy.tx_signature`` — used as the idempotency key so a single
    chain transaction never produces two announcements.

In manual mode the admin chooses any amount via the UI — the trigger
still respects the threshold (we don't broadcast 'whale alert' for a
0.1 SOL test).
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger

DEFAULT_THRESHOLD_SOL = 5.0


def _resolve_threshold(meta: Dict[str, Any]) -> float:
    try:
        return float(meta.get("threshold_sol") or DEFAULT_THRESHOLD_SOL)
    except (TypeError, ValueError):
        return DEFAULT_THRESHOLD_SOL


def _truncate_addr(addr: str) -> str:
    if not addr or len(addr) < 9:
        return addr or ""
    return f"{addr[:4]}…{addr[-4:]}"


def _detect(ctx: TriggerCtx) -> TriggerResult:
    cfg_meta = (ctx.market or {}).get("trigger_metadata", {}) or {}
    threshold = _resolve_threshold(cfg_meta)

    if ctx.manual:
        amount = float(ctx.payload_override.get("whale_amount") or 7.0)
        if amount < threshold:
            return TriggerResult(
                fired=False,
                reason=f"manual_amount_below_threshold({threshold})",
            )
        # Hash the amount + bucket so we don't fire twice in one minute
        # for the very same input — still flexible enough for testing.
        key = hashlib.sha256(
            f"manual_whale:{amount:.4f}".encode("utf-8"),
        ).hexdigest()[:12]
        return TriggerResult(
            fired=True,
            payload={
                "whale_amount": round(amount, 2),
                "buyer_short": ctx.payload_override.get("buyer_short", "7gXk…2kQ4"),
                "tier": _tier_label(amount),
            },
            idempotency_key=f"manual:whale:{key}",
        )

    last_buy = (ctx.market or {}).get("last_buy") or {}
    amount = float(last_buy.get("amount_sol") or 0)
    if amount < threshold:
        return TriggerResult(fired=False, reason="below_threshold")

    tx_sig = (last_buy.get("tx_signature") or "").strip()
    buyer = (last_buy.get("buyer") or "").strip()
    # Trust the watcher's tier first (it's the same numeric mapping but
    # avoids a recompute mismatch if thresholds ever drift).
    tier = (last_buy.get("tier") or _tier_label(amount))
    return TriggerResult(
        fired=True,
        payload={
            "whale_amount": round(amount, 2),
            "buyer_short": _truncate_addr(buyer),
            "tx_signature": tx_sig,
            "tier": tier,
        },
        idempotency_key=f"whale:{tx_sig or hashlib.sha256(f'{amount}|{buyer}'.encode()).hexdigest()[:12]}",
    )


def _tier_label(amount: float) -> str:
    """Mirror of `core.whale_watcher.tier_for` kept tiny here so the
    trigger module has zero runtime deps on the watcher (avoids a
    circular import — the watcher itself imports propaganda_engine
    which imports the triggers)."""
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        return "T1"
    if amt < 15.0:
        return "T1"
    if amt < 50.0:
        return "T2"
    return "T3"


WHALE_BUY = register_trigger(
    Trigger(
        key="whale_buy",
        label="Whale Recognition (> 5 SOL)",
        description=(
            "Fires when a single buy transaction exceeds the configured "
            "threshold (default 5 SOL). Idempotent on tx_signature so the "
            "same swap never produces two announcements."
        ),
        default_policy="approval",
        default_cooldown_minutes=10,
        detect=_detect,
        metadata_defaults={"threshold_sol": DEFAULT_THRESHOLD_SOL},
    )
)
