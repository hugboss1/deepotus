"""Trigger 7 — 'KOL mention listener' (Sprint 16.4).

Fires when a configured KOL X account tweets a mention of $DEEPOTUS.

This is a **manual-only** trigger: the KOL polling worker (or the admin
simulate endpoint) calls ``propaganda_engine.fire("kol_mention", ...)``
with a payload describing the tweet — there is no market-snapshot
detector.

Required payload fields:
  * ``kol_handle``        — X handle (no leading @, e.g. "Ansem")
  * ``kol_tweet_excerpt`` — first 200 chars of the tweet text
  * ``kol_tweet_url``     — full URL to the tweet (optional but recommended)

Idempotency is encoded as ``kol:<handle>:<sha12-of-excerpt>`` so two
distinct mentions from the same handle don't get squashed but a
re-emit of the same one does.
"""

from __future__ import annotations

import hashlib

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger


def _detect(ctx: TriggerCtx) -> TriggerResult:
    if not ctx.manual:
        return TriggerResult(fired=False, reason="manual_only")

    payload = ctx.payload_override or {}
    handle = (payload.get("kol_handle") or "").strip().lstrip("@")
    if len(handle) < 2:
        return TriggerResult(
            fired=False, reason="kol_handle missing or too short"
        )
    excerpt = (payload.get("kol_tweet_excerpt") or "").strip()
    if len(excerpt) < 4:
        return TriggerResult(
            fired=False, reason="kol_tweet_excerpt missing"
        )

    excerpt_hash = hashlib.sha256(
        excerpt.encode("utf-8", errors="ignore")
    ).hexdigest()[:12]
    return TriggerResult(
        fired=True,
        payload={
            "kol_handle": handle,
            "kol_tweet_excerpt": excerpt[:200],
            "kol_tweet_url": (payload.get("kol_tweet_url") or "").strip(),
        },
        idempotency_key=f"kol:{handle}:{excerpt_hash}",
    )


register_trigger(
    Trigger(
        key="kol_mention",
        label="KOL Mention Listener",
        description=(
            "Fires when a configured Solana KOL on X mentions $DEEPOTUS. "
            "Foundation only in Sprint 16.4 — actual polling lands in "
            "Sprint 17 once the X API tier is confirmed. The simulate "
            "endpoint already exercises the full propaganda pipeline."
        ),
        default_policy="approval",
        # No cooldown — multiple distinct KOL mentions per hour is a
        # legitimate viral signal we want to surface.
        default_cooldown_minutes=0,
        detect=_detect,
        metadata_defaults={},
    )
)
