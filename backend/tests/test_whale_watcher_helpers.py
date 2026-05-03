"""Unit tests for pure helpers in ``core.whale_watcher``.

Sprint 22.5 (Task E) — widen pytest backend coverage beyond the existing
``cadence_engine`` suite. Focus: the tier classifier, privacy truncator
and amount bucketer. These functions are dependency-free (no DB, no
network) so the tests stay deterministic and fast (<100ms total).
"""

from __future__ import annotations

import pytest

from core.whale_watcher import (
    THRESHOLD_SOL,
    TIER_T2_LOWER,
    TIER_T3_LOWER,
    _bucket,
    _truncate,
    tier_for,
)


# ---------------------------------------------------------------------
# tier_for
# ---------------------------------------------------------------------


class TestTierFor:
    """``tier_for`` maps a SOL amount to T1/T2/T3 or None (sub-threshold)."""

    def test_returns_none_below_threshold(self) -> None:
        assert tier_for(0) is None
        assert tier_for(1.99) is None
        assert tier_for(THRESHOLD_SOL - 0.01) is None

    def test_returns_t1_at_threshold(self) -> None:
        # The threshold is inclusive for T1.
        assert tier_for(THRESHOLD_SOL) == "T1"
        assert tier_for(10.0) == "T1"
        assert tier_for(TIER_T2_LOWER - 0.01) == "T1"

    def test_returns_t2_in_mid_band(self) -> None:
        assert tier_for(TIER_T2_LOWER) == "T2"
        assert tier_for(25.0) == "T2"
        assert tier_for(TIER_T3_LOWER - 0.01) == "T2"

    def test_returns_t3_in_high_band(self) -> None:
        assert tier_for(TIER_T3_LOWER) == "T3"
        assert tier_for(100.0) == "T3"
        assert tier_for(999.99) == "T3"

    def test_handles_string_input(self) -> None:
        # The real dispatch path can receive JSON strings; the helper
        # coerces them defensively.
        assert tier_for("12.3") == "T1"
        assert tier_for("75") == "T3"

    def test_returns_none_on_invalid_input(self) -> None:
        assert tier_for(None) is None  # type: ignore[arg-type]
        assert tier_for("not-a-number") is None
        assert tier_for("") is None


# ---------------------------------------------------------------------
# _truncate — privacy helper for Solana wallet addresses
# ---------------------------------------------------------------------


class TestTruncate:
    """Public feeds should never reveal full buyer wallets."""

    def test_empty_inputs(self) -> None:
        assert _truncate(None) == ""
        assert _truncate("") == ""

    def test_short_addresses_passthrough(self) -> None:
        # Under 9 chars the truncation would be longer than the source
        # itself, so we return it as-is.
        assert _truncate("abc") == "abc"
        assert _truncate("12345678") == "12345678"

    def test_full_address_gets_ellipsis(self) -> None:
        pubkey = "7gXkHxJzwy5o3m6aR4VcJ9qpMnLtNgPe2uFdHs8W"
        truncated = _truncate(pubkey)
        assert truncated == "7gXk…ds8W"[:4] + "…" + pubkey[-4:]
        # Sanity: preserves exactly first-4 + "…" + last-4.
        assert truncated.startswith(pubkey[:4])
        assert truncated.endswith(pubkey[-4:])
        assert "…" in truncated


# ---------------------------------------------------------------------
# _bucket — coarsened amount for public-facing narration
# ---------------------------------------------------------------------


class TestBucket:
    """The public narration must not leak the exact buy size."""

    def test_sub_ten_keeps_one_decimal(self) -> None:
        # Under 10 SOL we keep 0.1 granularity so micro-buys still show
        # a meaningful signal without exposing the exact value.
        assert _bucket(5.0) == 5.0
        assert _bucket(7.83) == pytest.approx(7.8, abs=1e-9)
        assert _bucket(0.05) == pytest.approx(0.1, abs=1e-9)

    def test_ten_to_fifty_rounds_to_five(self) -> None:
        assert _bucket(12) == 10
        assert _bucket(13) == 15
        assert _bucket(47) == 45

    def test_fifty_to_two_hundred_rounds_to_ten(self) -> None:
        assert _bucket(55) == 60
        assert _bucket(123) == 120
        assert _bucket(199) == 200

    def test_over_two_hundred_rounds_to_fifty(self) -> None:
        # Python's banker's rounding makes `round(4.5) == 4`, so 225 → 200
        # by design; we pick values that don't land on a `.5` midpoint.
        assert _bucket(226) == 250
        assert _bucket(480) == 500
        assert _bucket(1050) == 1050

    def test_handles_invalid_input_gracefully(self) -> None:
        # A non-numeric input must NOT crash the narration pipeline —
        # it should degrade to 0 and the upstream caller will drop it.
        assert _bucket(None) == 0.0  # type: ignore[arg-type]
        assert _bucket("not-a-number") == 0.0  # type: ignore[arg-type]
