"""Trigger 7 — 'burn disclosure event' (Sprint 17.6).

Fires when the admin publicly discloses an on-chain $DEEPOTUS burn.

This is a **disclosure-driven** trigger, twin in spirit to
``founder_buy``: the burn already happened on-chain; the admin pushes
the proof through ``POST /api/admin/burns/disclose`` and we produce a
cynical Cabinet announcement on X + Telegram. The point is to make
deflation **visible** — a burn that no one sees is a marketing wash.

The trigger is **manual-only**. It cannot fire from a market snapshot
because a burn is a deliberate act, not an observation.

Required payload fields (validated upstream by the router):
  * ``burn_amount``      — whole tokens destroyed (must be > 0)
  * ``tx_signature``     — Solana transaction signature (used as
                           idempotency key — same burn disclosed twice
                           yields one queue item only)

Optional:
  * ``tx_link``          — pre-rendered Solscan URL (we recompute it
                           defensively if missing)
  * ``burn_note``        — free-form 80-char tag (e.g. "Q1 buyback")
  * ``burned_at``        — ISO timestamp; rendered into templates as
                           ``burn_ts``

Derived placeholders (computed here for the templates):
  * ``burn_amount_pretty`` — ``1.5M``, ``250K``, etc.
  * ``burn_pct``           — burn share of INITIAL_SUPPLY, 2 decimals.
  * ``burn_circulating_after`` — effective circulating supply post-burn
                                 (initial - locked - burned).
"""

from __future__ import annotations

import re

from core.burn_logs import INITIAL_SUPPLY, LOCKED_TOTAL

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger

#: Match the same base58 alphabet enforced by ``burn_logs``.
_TX_SIG_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,128}$")

#: Solscan template — re-derived here when the upstream caller didn't
#: include ``tx_link`` in the payload. Keep in lockstep with the one in
#: ``core/burn_logs.py`` so the rendered URL is always consistent.
_SOLSCAN_URL_TEMPLATE = "https://solscan.io/tx/{sig}"


def _fmt_amount(amt: int) -> str:
    """Pretty-print a token amount for tweet copy.

    Examples:
        1_500_000   -> "1.5M"
        250_000     -> "250K"
        7_500       -> "7,500"
    """
    if amt >= 1_000_000_000:
        return f"{amt/1_000_000_000:.2f}B"
    if amt >= 1_000_000:
        return f"{amt/1_000_000:.2f}M"
    if amt >= 1_000:
        return f"{amt/1_000:.1f}K"
    # Below 1k: render with thousands separator (defensive — burns this
    # small are pointless theatre but we don't want to ship "0.001K").
    return f"{amt:,}"


def _detect(ctx: TriggerCtx) -> TriggerResult:
    # Disclosure trigger: ONLY fires in manual mode. We never want a
    # background poller to spuriously announce a burn.
    if not ctx.manual:
        return TriggerResult(fired=False, reason="manual_only")

    payload = ctx.payload_override or {}
    try:
        amount = int(float(payload.get("burn_amount") or 0))
    except (TypeError, ValueError):
        amount = 0
    if amount <= 0:
        return TriggerResult(
            fired=False, reason="burn_amount must be > 0"
        )
    if amount > INITIAL_SUPPLY:
        # Defensive: an admin typo of "10000000000" (10B) would
        # otherwise produce nonsense math downstream.
        return TriggerResult(
            fired=False, reason="burn_amount exceeds initial supply"
        )

    tx_sig = (payload.get("tx_signature") or "").strip()
    if not _TX_SIG_RE.match(tx_sig):
        return TriggerResult(
            fired=False, reason="tx_signature must be a valid Solana sig"
        )

    tx_link = (payload.get("tx_link") or "").strip()
    if not tx_link:
        tx_link = _SOLSCAN_URL_TEMPLATE.format(sig=tx_sig)

    note = (payload.get("burn_note") or "").strip()[:80]
    burned_at = (payload.get("burned_at") or "").strip()

    # Derived metrics for the cynical templates. INITIAL_SUPPLY is
    # guaranteed > 0 (constant); LOCKED_TOTAL is also a constant. We
    # don't reach into the DB here — keep triggers cheap and pure.
    burn_pct = round(100 * amount / INITIAL_SUPPLY, 4)
    burn_circulating_after = max(0, INITIAL_SUPPLY - LOCKED_TOTAL - amount)

    return TriggerResult(
        fired=True,
        payload={
            "burn_amount": amount,
            "burn_amount_pretty": _fmt_amount(amount),
            "tx_signature": tx_sig,
            "tx_link": tx_link,
            "burn_note": note,
            "burn_ts": burned_at,
            "burn_pct": f"{burn_pct:.4f}",
            "burn_circulating_after": burn_circulating_after,
            "burn_circulating_after_pretty": _fmt_amount(burn_circulating_after),
        },
        # Stable idempotency: same tx_signature => same announcement
        # once. burn_logs.record_burn() enforces the same invariant at
        # the DB level (unique partial index).
        idempotency_key=f"burn:{tx_sig}",
    )


register_trigger(
    Trigger(
        key="burn_event",
        label="Burn Disclosure",
        description=(
            "Disclosure-driven trigger fired by the admin endpoint "
            "POST /api/admin/burns/disclose. Generates a cynical "
            "Cabinet-grade transparency announcement on X + Telegram "
            "for every on-chain $DEEPOTUS burn. Idempotent on "
            "tx_signature so a double-click never yields a double "
            "post. Feeds the /transparency 'Proof of Scarcity' "
            "header via the public burn feed."
        ),
        default_policy="approval",
        # No cooldown: a buyback day can legitimately produce several
        # burns. tx_signature idempotency prevents accidental dupes.
        default_cooldown_minutes=0,
        detect=_detect,
        metadata_defaults={},
    )
)
