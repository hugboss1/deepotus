"""Trigger 8 — 'Giveaway Extraction Success' (Sprint 19+).

Fires once the admin has run the May 20 (or future) draw via
``run_extraction(dry_run=False)`` and confirms the announce. Manual-
only — there is no automated firing path.

Required payload fields (validated upstream by the router):
  * ``snapshot_id``        — UUID of the persisted extraction.
  * ``winners_formatted``  — pre-rendered @handle list (Cabinet copy).
  * ``winners_count``      — int, used for "X agents extracted" copy.
  * ``pool_sol``           — float, total distributed pool.
  * ``per_winner_sol``     — float, per-winner share (already rounded).
  * ``draw_date_iso``      — ISO snapshot moment (for the audit link).
  * ``seed_fingerprint``   — sha256 hex (truncated to 12 chars for the
                             tweet); proves the draw is replayable.
"""

from __future__ import annotations

from .base import Trigger, TriggerCtx, TriggerResult, register_trigger


def _detect(ctx: TriggerCtx) -> TriggerResult:
    if not ctx.manual:
        return TriggerResult(fired=False, reason="manual_only")

    p = ctx.payload_override or {}

    snapshot_id = (p.get("snapshot_id") or "").strip()
    if not snapshot_id:
        return TriggerResult(fired=False, reason="snapshot_id required")

    winners_formatted = (p.get("winners_formatted") or "").strip()
    if not winners_formatted:
        return TriggerResult(fired=False, reason="winners_formatted required (none picked)")

    try:
        winners_count = int(p.get("winners_count") or 0)
    except (TypeError, ValueError):
        winners_count = 0
    if winners_count <= 0:
        return TriggerResult(fired=False, reason="winners_count must be > 0")

    try:
        pool_sol = float(p.get("pool_sol") or 0)
    except (TypeError, ValueError):
        pool_sol = 0.0
    if pool_sol <= 0:
        return TriggerResult(fired=False, reason="pool_sol must be > 0")

    try:
        per_winner_sol = float(p.get("per_winner_sol") or (pool_sol / winners_count))
    except (TypeError, ValueError, ZeroDivisionError):
        per_winner_sol = 0.0

    seed_fp = (p.get("seed_fingerprint") or "").strip() or "unaudited"
    seed_short = seed_fp[:12] if seed_fp != "unaudited" else seed_fp
    draw_date_iso = (p.get("draw_date_iso") or "").strip()

    return TriggerResult(
        fired=True,
        payload={
            "snapshot_id": snapshot_id,
            "snapshot_id_short": snapshot_id[:8],
            "winners_formatted": winners_formatted,
            "winners_count": winners_count,
            "pool_sol": pool_sol,
            "pool_sol_pretty": f"{pool_sol:g}",
            "per_winner_sol": per_winner_sol,
            "per_winner_sol_pretty": f"{per_winner_sol:g}",
            "draw_date_iso": draw_date_iso,
            "seed_fingerprint": seed_fp,
            "seed_fingerprint_short": seed_short,
        },
        # One announce per snapshot — same draw cannot be announced twice
        # by accident.
        idempotency_key=f"giveaway:{snapshot_id}",
    )


register_trigger(
    Trigger(
        key="giveaway_extraction",
        label="Giveaway Extraction Success",
        description=(
            "Fired by the admin endpoint POST /api/admin/giveaway/"
            "snapshots/{id}/announce after a public draw has been "
            "extracted. Generates a cynical Cabinet announcement on "
            "X + Telegram citing the winners' @handles. Idempotent "
            "on snapshot_id so a double-click never produces two "
            "announcements for the same draw."
        ),
        default_policy="approval",
        default_cooldown_minutes=0,
        detect=_detect,
        metadata_defaults={},
    )
)
