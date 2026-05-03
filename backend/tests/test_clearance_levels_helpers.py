"""Unit tests for pure helpers in ``core.clearance_levels``.

Sprint 22.5 (Task E) — cover the level ladder, email/wallet
normalisation and the Solana pubkey structural validation. These are
the gatekeeper functions behind the Proof-of-Intelligence airdrop flow
so any regression here has real user-facing impact.
"""

from __future__ import annotations

import pytest

from core.clearance_levels import (
    _compute_level,
    _is_valid_solana,
    _normalise_addr,
    _normalise_email,
)


# ---------------------------------------------------------------------
# _compute_level — derives the current level from the ledger row
# ---------------------------------------------------------------------


class TestComputeLevel:
    """The level ladder is the contract with the airdrop allocator."""

    def test_empty_doc_returns_zero(self) -> None:
        assert _compute_level({}) == 0

    def test_level_1_only(self) -> None:
        doc = {"level_1_achieved_at": "2026-05-01T00:00:00Z"}
        assert _compute_level(doc) == 1

    def test_level_1_and_2(self) -> None:
        doc = {
            "level_1_achieved_at": "2026-05-01T00:00:00Z",
            "level_2_achieved_at": "2026-05-02T00:00:00Z",
        }
        assert _compute_level(doc) == 2

    def test_level_3_via_explicit_timestamp(self) -> None:
        doc = {
            "level_1_achieved_at": "2026-05-01T00:00:00Z",
            "level_2_achieved_at": "2026-05-02T00:00:00Z",
            "level_3_achieved_at": "2026-05-03T00:00:00Z",
        }
        assert _compute_level(doc) == 3

    def test_level_3_via_solved_riddle_alone(self) -> None:
        # Sprint 14.1 bootstrapping rule: a solved riddle alone promotes
        # to L3 so the operator can demo the flow without TG/X checks.
        doc = {"riddles_solved": ["ENIGME_01"]}
        assert _compute_level(doc) == 3

    def test_multiple_riddles_still_level_3(self) -> None:
        # Any non-empty list bumps to L3; counting them is the allocator's
        # concern, not the ladder's.
        doc = {"riddles_solved": ["R1", "R2", "R3"]}
        assert _compute_level(doc) == 3

    def test_empty_riddles_list_does_not_promote(self) -> None:
        doc = {"riddles_solved": []}
        assert _compute_level(doc) == 0

    def test_none_riddles_field_does_not_promote(self) -> None:
        doc = {"riddles_solved": None}
        assert _compute_level(doc) == 0


# ---------------------------------------------------------------------
# _normalise_email — case + whitespace normalisation for PK equality
# ---------------------------------------------------------------------


class TestNormaliseEmail:
    def test_lowercases(self) -> None:
        assert _normalise_email("Agent@DeepotuS.XYZ") == "agent@deepotus.xyz"

    def test_trims_whitespace(self) -> None:
        assert _normalise_email("  foo@bar.com  ") == "foo@bar.com"

    def test_handles_empty_and_none(self) -> None:
        assert _normalise_email("") == ""
        assert _normalise_email(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# _is_valid_solana — cheap structural check on pubkey shape
# ---------------------------------------------------------------------


class TestIsValidSolana:
    """Full signature verification is out of scope here — we only reject
    obvious garbage so the admin CSV doesn't get polluted."""

    def test_accepts_canonical_pubkey(self) -> None:
        # Any address within the 32–44 base58 range passes.
        assert _is_valid_solana("7gXkHxJzwy5o3m6aR4VcJ9qpMnLtNgPe2uFdHs8W") is True  # 40 chars
        # 43-char address — the regex allows 32–44.
        assert _is_valid_solana("So11111111111111111111111111111111111111112") is True
        # 32-char (minimum) address.
        assert _is_valid_solana("A" * 32) is True
        assert _is_valid_solana("a" * 32) is True

    def test_rejects_too_short_or_too_long(self) -> None:
        assert _is_valid_solana("A" * 31) is False
        assert _is_valid_solana("A" * 45) is False
        assert _is_valid_solana("") is False

    def test_rejects_forbidden_characters(self) -> None:
        # Base58 bans 0, O, I, l — they're visually ambiguous.
        for forbidden in ("0", "O", "I", "l"):
            addr = forbidden * 32
            assert _is_valid_solana(addr) is False, f"{forbidden!r} must be rejected"

    def test_rejects_none(self) -> None:
        assert _is_valid_solana(None) is False  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# _normalise_addr — trims + validates; raises on bad shape
# ---------------------------------------------------------------------


class TestNormaliseAddr:
    def test_returns_none_for_empty(self) -> None:
        assert _normalise_addr(None) is None
        assert _normalise_addr("") is None

    def test_trims_whitespace_then_validates(self) -> None:
        good = "So11111111111111111111111111111111111111112"
        assert _normalise_addr(f"  {good}  ") == good

    def test_raises_on_invalid_shape(self) -> None:
        with pytest.raises(ValueError):
            _normalise_addr("obviously-not-a-pubkey-0000")
        with pytest.raises(ValueError):
            _normalise_addr("X" * 5)
