"""Unit tests for pure helpers in ``core.kol_listener``.

Sprint P1 (live polling) — covers the substring matcher only. The I/O
paths (``_resolve_user_id``, ``_fetch_kol_recent_tweets``,
``poll_x_api_once``) depend on MongoDB + httpx so they're exercised via
the integration test harness, not here.
"""

from __future__ import annotations


from core.kol_listener import _match_terms_hit


class TestMatchTermsHit:
    """Case-insensitive substring matching drives the "this tweet
    mentions us" gate in the live poller. False positives are cheap
    (admin just rejects the draft); false negatives silently drop a
    real KOL mention so we prioritise recall over precision."""

    def test_hits_case_insensitively(self) -> None:
        assert _match_terms_hit("Hello $DEEPOTUS fam", ["$DEEPOTUS"]) is True
        assert _match_terms_hit("hello $deepotus fam", ["$DEEPOTUS"]) is True
        assert _match_terms_hit("HELLO $DEEPOTUS FAM", ["$deepotus"]) is True

    def test_any_term_is_a_hit(self) -> None:
        # Multi-term OR semantics — any one term in the list matching
        # the text triggers a hit.
        assert (
            _match_terms_hit(
                "This is about PROTOCOL ΔΣ today",
                ["$DEEPOTUS", "protocol delta sigma", "PROTOCOL ΔΣ"],
            )
            is True
        )
        # Python lowercases "Σ" at end-of-word to final-sigma "ς" (not
        # medial "σ") — so a properly-cased admin term matches itself
        # under lowercasing, which is the contract we rely on.
        assert (
            _match_terms_hit("PROTOCOL ΔΣ drops tomorrow", ["PROTOCOL ΔΣ"])
            is True
        )

    def test_returns_false_when_no_term_matches(self) -> None:
        assert _match_terms_hit("Just random crypto talk", ["$DEEPOTUS"]) is False
        assert _match_terms_hit("BTC to the moon", []) is False

    def test_handles_empty_text_and_terms(self) -> None:
        assert _match_terms_hit("", ["$DEEPOTUS"]) is False
        assert _match_terms_hit(None, ["$DEEPOTUS"]) is False  # type: ignore[arg-type]
        assert _match_terms_hit("anything", None) is False  # type: ignore[arg-type]
        assert _match_terms_hit("anything", []) is False

    def test_strips_whitespace_around_terms(self) -> None:
        # Admin might paste terms with trailing whitespace from a
        # spreadsheet — the matcher should tolerate it.
        assert _match_terms_hit("Hello $DEEPOTUS fam", ["  $DEEPOTUS  "]) is True

    def test_ignores_falsy_term_entries(self) -> None:
        assert _match_terms_hit("Hello $DEEPOTUS", ["", None, "$DEEPOTUS"]) is True  # type: ignore[list-item]
        # Pure-empty/None list → no hit (prevents "" matching everything).
        assert _match_terms_hit("anything at all", ["", None]) is False  # type: ignore[list-item]
