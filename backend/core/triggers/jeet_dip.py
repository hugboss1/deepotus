"""Trigger 2 — the ‘jeet dip’.

Fires when the price drops by ≥ 20 % within 2 minutes. We delegate the
actual rolling-window arithmetic to ``core.market_analytics.detect_dip``
so the trigger module stays a thin policy layer.

Idempotency: bucketing by 2-minute windows means that even if the dip
is still in progress when Helius retries the webhook, we only fire one
message per dip event.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger


def _bucket_key() -> str:
    """Two-minute bucket — collapses repeated detections of the same dip."""
    now = datetime.now(timezone.utc)
    return f"{now.year}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute//2:02d}"


def _detect(ctx: TriggerCtx) -> TriggerResult:
    if ctx.manual:
        return TriggerResult(
            fired=True,
            payload={
                "drop_pct": ctx.payload_override.get("drop_pct", 22),
                "peak_price": ctx.payload_override.get("peak_price", 0),
                "current_price": ctx.payload_override.get("current_price", 0),
            },
            idempotency_key=f"manual:jeet_dip:{_bucket_key()}",
        )

    dip = (ctx.market or {}).get("dip_analysis") or {}
    if not dip.get("detected"):
        return TriggerResult(
            fired=False,
            reason=dip.get("reason") or "no_dip_detected",
        )
    return TriggerResult(
        fired=True,
        payload={
            "drop_pct": dip.get("drop_pct", 0),
            "peak_price": dip.get("peak_price", 0),
            "current_price": dip.get("current_price", 0),
        },
        idempotency_key=f"jeet:{_bucket_key()}",
    )


JEET_DIP = register_trigger(
    Trigger(
        key="jeet_dip",
        label="Jeet Dip (− 20 % / 2 min)",
        description=(
            "Fires when the rolling price drops at least 20 % within 2 min. "
            "Used to launch a 'confidence blast' message and discourage panic-sells."
        ),
        default_policy="approval",   # hot trigger — admin reviews before sending
        default_cooldown_minutes=15,
        detect=_detect,
    )
)
