"""T-Zero — the moment $DEEPOTUS becomes live on the bonding curve.

We trust the admin's ``vault_state.dex_mode`` and ``dex_token_address``
as the source of truth: when both are populated for the *first* time we
consider the mint live. In Manual Fire mode the trigger always succeeds.
"""

from __future__ import annotations

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger


def _detect(ctx: TriggerCtx) -> TriggerResult:
    if ctx.manual:
        return TriggerResult(
            fired=True,
            payload={
                "buy_link": ctx.payload_override.get("buy_link", ""),
                "mint": ctx.payload_override.get("mint", ""),
            },
            idempotency_key="manual:mint",
        )
    market = ctx.market or {}
    mint = (market.get("dex_token_address") or "").strip()
    dex_mode = (market.get("dex_mode") or "").strip().lower()
    if not mint or dex_mode not in ("helius", "raydium", "pumpfun", "live"):
        return TriggerResult(fired=False, reason="mint_not_live")
    # Idempotency: collapse repeated detections for the same mint.
    return TriggerResult(
        fired=True,
        payload={"buy_link": market.get("buy_link", ""), "mint": mint},
        idempotency_key=f"mint:{mint}",
    )


MINT = register_trigger(
    Trigger(
        key="mint",
        label="T-Zero — Initial Mint",
        description=(
            "Fires once when the $DEEPOTUS contract goes live on Pump.fun. "
            "Posts the buy link to X and Telegram with a 10–30 s humanized delay."
        ),
        default_policy="approval",
        default_cooldown_minutes=720,  # 12h — once per launch is plenty
        detect=_detect,
    )
)
