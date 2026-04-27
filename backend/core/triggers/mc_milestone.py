"""Market-cap milestone trigger.

Fires when the live MC crosses one of the configured tiers (default:
10k / 25k / 50k / 100k USD). We persist the highest tier already
announced in the trigger's metadata so the engine never re-announces
the same threshold twice — even if the market chops below and back above.
"""

from __future__ import annotations

from typing import List

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger

DEFAULT_TIERS_USD: List[int] = [10_000, 25_000, 50_000, 100_000]


def _detect(ctx: TriggerCtx) -> TriggerResult:
    if ctx.manual:
        tier = int(ctx.payload_override.get("mc_tier") or 25_000)
        return TriggerResult(
            fired=True,
            payload={
                "mc": tier,
                "mc_label": _format_mc(tier),
                "buy_link": ctx.payload_override.get("buy_link", ""),
            },
            idempotency_key=f"manual:mc:{tier}",
        )

    market = ctx.market or {}
    mc = float(market.get("market_cap_usd") or 0)
    last_announced = int(market.get("last_milestone_usd") or 0)
    tiers = list(market.get("milestone_tiers") or DEFAULT_TIERS_USD)
    # Pick the *highest* tier strictly below current MC, that is *above* the
    # last one we already announced. Anything else means we already shipped
    # this milestone.
    candidate = max(
        (t for t in tiers if t <= mc and t > last_announced),
        default=None,
    )
    if candidate is None:
        return TriggerResult(fired=False, reason="no_new_milestone")
    return TriggerResult(
        fired=True,
        payload={
            "mc": int(candidate),
            "mc_label": _format_mc(int(candidate)),
            "buy_link": market.get("buy_link", ""),
        },
        idempotency_key=f"mc:{candidate}",
    )


def _format_mc(amount: int) -> str:
    """Human-friendly $25k / $1.5M label."""
    if amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M".replace(".0M", "M")
    if amount >= 1_000:
        return f"${amount//1000}k"
    return f"${amount}"


MC_MILESTONE = register_trigger(
    Trigger(
        key="mc_milestone",
        label="Market Cap Milestone",
        description=(
            "Fires when the USD market cap crosses one of the configured tiers "
            "(default: 10k / 25k / 50k / 100k). Cooldown ensures one announcement "
            "per tier even if Helius re-emits."
        ),
        default_policy="auto",  # milestones are 'cold' triggers — fine to auto-send
        default_cooldown_minutes=10,
        detect=_detect,
        metadata_defaults={"tiers_usd": DEFAULT_TIERS_USD, "last_announced_usd": 0},
    )
)
