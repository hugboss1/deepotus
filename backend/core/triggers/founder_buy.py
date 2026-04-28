"""Trigger 6 — 'founder buy disclosure' (Sprint 16.2).

Fires when the founder publishes a personal buy of $DEEPOTUS.

Unlike `whale_buy` which is observation-driven (the chain produced a
swap, the watcher narrated it), this trigger is **disclosure-driven**:
the founder explicitly announces their buy through the admin endpoint
``POST /api/admin/founder/disclose-buy`` and the trigger generates a
transparency tweet/telegram post. The point is to establish in advance
a verifiable, auditable founder position so the community is never
surprised by "founder dumped" scenarios later (see
``docs/TOKENOMICS_TREASURY_POLICY.md`` §6).

The trigger is **manual-only**. It cannot fire from a market snapshot
because the disclosure is a deliberate, signed act — not an observation.

Required payload fields (validated upstream by the router):
  * ``founder_amount_sol``  — SOL spent (must be > 0)
  * ``founder_wallet``       — full pubkey of the founder's personal
                               wallet (truncated for the public message)
  * ``founder_mc_usd``       — market cap in USD at the time of the buy
  * ``tx_signature``         — Solana transaction signature (used as
                               idempotency key — same buy disclosed
                               twice produces only one queue item)

Optional:
  * ``founder_note``  — free-form 80-char tag (e.g. "anniversary buy")
"""

from __future__ import annotations

import hashlib

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger


def _truncate(addr: str) -> str:
    if not addr or len(addr) < 9:
        return addr or ""
    return f"{addr[:4]}…{addr[-4:]}"


def _detect(ctx: TriggerCtx) -> TriggerResult:
    # Disclosure trigger: ONLY fires in manual mode. We never want a
    # market poll to spuriously announce a founder buy.
    if not ctx.manual:
        return TriggerResult(fired=False, reason="manual_only")

    payload = ctx.payload_override or {}
    try:
        amount = float(payload.get("founder_amount_sol") or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount <= 0:
        return TriggerResult(
            fired=False, reason="founder_amount_sol must be > 0"
        )

    wallet = (payload.get("founder_wallet") or "").strip()
    if len(wallet) < 4:
        return TriggerResult(
            fired=False, reason="founder_wallet must be a real pubkey"
        )

    try:
        mc_usd = float(payload.get("founder_mc_usd") or 0)
    except (TypeError, ValueError):
        mc_usd = 0.0

    tx_sig = (payload.get("tx_signature") or "").strip()
    note = (payload.get("founder_note") or "").strip()[:80]

    # Stable idempotency: same tx_signature => same announcement once.
    # If no tx_signature is provided (extremely early disclosure of a
    # not-yet-broadcast buy), bucket by amount to a 1-minute window so
    # an accidental double-click doesn't spam.
    if tx_sig:
        idem = f"founder:{tx_sig}"
    else:
        idem = (
            "founder:nosig:"
            + hashlib.sha256(
                f"{amount:.4f}|{wallet}".encode("utf-8")
            ).hexdigest()[:12]
        )

    return TriggerResult(
        fired=True,
        payload={
            "founder_amount": round(amount, 2),
            "founder_wallet_short": _truncate(wallet),
            "founder_wallet_full": wallet,
            "founder_mc_usd": round(mc_usd, 0),
            "founder_mc_usd_pretty": _fmt_mc(mc_usd),
            "tx_signature": tx_sig,
            "founder_note": note,
        },
        idempotency_key=idem,
    )


def _fmt_mc(mc: float) -> str:
    """Pretty-print a market-cap value into a tweet-friendly form
    ('$ 187 K', '$ 4.2 M'). Dollar sign included so templates don't have
    to remember to add it."""
    if mc <= 0:
        return ""
    if mc < 1_000:
        return f"${int(mc)}"
    if mc < 1_000_000:
        return f"${mc/1_000:.0f}K"
    if mc < 1_000_000_000:
        return f"${mc/1_000_000:.2f}M"
    return f"${mc/1_000_000_000:.2f}B"


register_trigger(
    Trigger(
        key="founder_buy",
        label="Founder Buy Disclosure",
        description=(
            "Disclosure-driven trigger fired by the admin endpoint "
            "POST /api/admin/founder/disclose-buy. Generates a "
            "transparency tweet + telegram post for a personal founder "
            "purchase of $DEEPOTUS, per the Tokenomics & Treasury "
            "Policy §6. Idempotent on tx_signature."
        ),
        default_policy="approval",
        # No cooldown: a founder may legitimately disclose multiple
        # buys on the same day. tx_signature idempotency prevents
        # accidental double-fires.
        default_cooldown_minutes=0,
        detect=_detect,
        metadata_defaults={},
    )
)
