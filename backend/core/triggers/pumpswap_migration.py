"""Trigger 5 — PumpSwap ascension.

Fires once when the bonding curve hits 100 % and the LP migrates to
PumpSwap. We trust the ``vault_state.dex_mode`` field as the source of
truth: the value flips from ``pumpfun`` (or ``helius``) to ``pumpswap``
the moment the migration is detected by our Helius webhook handler.

Idempotency: keyed by the mint address — a single token never migrates
twice, so this guards against any retry storm during the cutover.
"""

from __future__ import annotations

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger


def _detect(ctx: TriggerCtx) -> TriggerResult:
    if ctx.manual:
        return TriggerResult(
            fired=True,
            payload={
                "pumpswap_link": ctx.payload_override.get("pumpswap_link", ""),
                "mint": ctx.payload_override.get("mint", ""),
            },
            idempotency_key="manual:pumpswap",
        )

    market = ctx.market or {}
    mint = (market.get("dex_token_address") or "").strip()
    dex_mode = (market.get("dex_mode") or "").strip().lower()
    if not mint:
        return TriggerResult(fired=False, reason="no_mint")
    if dex_mode != "pumpswap":
        return TriggerResult(fired=False, reason=f"dex_mode_is_{dex_mode or 'unset'}")
    return TriggerResult(
        fired=True,
        payload={
            "pumpswap_link": market.get("pumpswap_link", ""),
            "mint": mint,
        },
        idempotency_key=f"pumpswap:{mint}",
    )


PUMPSWAP_MIGRATION = register_trigger(
    Trigger(
        key="pumpswap_migration",
        label="PumpSwap Ascension",
        description=(
            "Fires once when the bonding curve completes (100 %) and the LP "
            "migrates to PumpSwap. Posts the new chart link — idempotent on mint."
        ),
        default_policy="approval",
        default_cooldown_minutes=720,  # one announcement per launch lifetime
        detect=_detect,
    )
)
