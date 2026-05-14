"""Pure-helper unit tests for Sprint 19+ — Giveaway Extraction.

DB-free + network-free coverage of the deterministic bits in
``core.giveaway`` and ``core.triggers.giveaway_extraction``. Live
endpoint behaviour (mongo + helius + propaganda fire) is exercised
through the testing_agent + the manual smoke we did during the
implementation.
"""

from __future__ import annotations

import os
import sys

# Ensure backend root is importable regardless of pytest's invocation cwd.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import giveaway  # noqa: E402
from core.templates_repo import DEFAULT_TEMPLATES  # noqa: E402
from core.triggers import giveaway_extraction as giv_trigger  # noqa: E402
from core.triggers.base import TriggerCtx  # noqa: E402


# Real-world-looking Solana base58 signature template.
VALID_BLOCKHASH = "5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfWX3hRyBxJvY7uA8n"
VALID_WALLET = "5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfWX3hRyBxJ"


# =====================================================================
# Constants — Cabinet contract
# =====================================================================
class TestGiveawayConstants:
    def test_default_winners_count_is_two(self) -> None:
        # If this fails, the public /giveaway page is out of sync with
        # the backend — change BOTH lib/missions.ts and giveaway.py.
        assert giveaway.DEFAULT_WINNERS_COUNT == 2

    def test_default_min_holding_usd(self) -> None:
        assert giveaway.DEFAULT_MIN_HOLDING_USD == 30.0


# =====================================================================
# Mint + handle + wallet validators
# =====================================================================
class TestValidators:
    def test_is_valid_mint_accepts_real_mint(self) -> None:
        assert giveaway._is_valid_mint("So11111111111111111111111111111111111111112")

    def test_is_valid_mint_rejects_empty(self) -> None:
        assert not giveaway._is_valid_mint("")
        assert not giveaway._is_valid_mint(None)
        assert not giveaway._is_valid_mint("   ")

    def test_is_valid_mint_rejects_too_short(self) -> None:
        assert not giveaway._is_valid_mint("ABC123")

    def test_normalise_handle_strips_at(self) -> None:
        assert giveaway._normalise_handle("@agent_007") == "agent_007"

    def test_normalise_handle_rejects_too_long(self) -> None:
        # Twitter caps at 15 chars; we honour the same.
        assert giveaway._normalise_handle("a" * 16) is None

    def test_normalise_handle_rejects_special_chars(self) -> None:
        assert giveaway._normalise_handle("hello world") is None
        assert giveaway._normalise_handle("hello-world") is None

    def test_short_wallet_truncation(self) -> None:
        s = giveaway._short_wallet("5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfW")
        assert s.startswith("5VfY") and s.endswith("Cs1KfW".replace("Cs1KfW", "1KfW"))

    def test_short_wallet_handles_none(self) -> None:
        assert giveaway._short_wallet(None) == "—"

    def test_short_wallet_handles_already_short(self) -> None:
        assert giveaway._short_wallet("abc") == "abc"


# =====================================================================
# Provably fair RNG — DETERMINISM is the contract
# =====================================================================
class TestProvablyFairRNG:
    """The whole point of the seed-from-blockhash dance is that anyone
    can re-run the math and confirm the same winners. These tests
    pin that contract so a future refactor can't silently break it."""

    BASE_INPUTS = {
        "blockhash": VALID_BLOCKHASH,
        "slot": 123_456_789,
        "sorted_handles": ["alice", "bob", "carol", "dave"],
        "draw_date_iso": "2026-05-20T18:00:00Z",
    }

    def test_seed_is_deterministic(self) -> None:
        s1, fp1 = giveaway.derive_rng_seed(**self.BASE_INPUTS)  # type: ignore[arg-type]
        s2, fp2 = giveaway.derive_rng_seed(**self.BASE_INPUTS)  # type: ignore[arg-type]
        assert s1 == s2
        assert fp1 == fp2

    def test_seed_changes_when_blockhash_changes(self) -> None:
        a, _ = giveaway.derive_rng_seed(**self.BASE_INPUTS)  # type: ignore[arg-type]
        inputs = {**self.BASE_INPUTS, "blockhash": VALID_BLOCKHASH[:-1] + "Z"}
        b, _ = giveaway.derive_rng_seed(**inputs)  # type: ignore[arg-type]
        assert a != b

    def test_seed_changes_when_handles_reorder(self) -> None:
        """Handles MUST be passed sorted so the seed is order-invariant
        at the call site — but if the caller forgets to sort, the seed
        should change (defensive)."""
        a, _ = giveaway.derive_rng_seed(**self.BASE_INPUTS)  # type: ignore[arg-type]
        inputs = {**self.BASE_INPUTS, "sorted_handles": ["dave", "carol", "bob", "alice"]}
        b, _ = giveaway.derive_rng_seed(**inputs)  # type: ignore[arg-type]
        assert a != b

    def test_seed_changes_when_draw_date_changes(self) -> None:
        a, _ = giveaway.derive_rng_seed(**self.BASE_INPUTS)  # type: ignore[arg-type]
        inputs = {**self.BASE_INPUTS, "draw_date_iso": "2099-01-01T00:00:00Z"}
        b, _ = giveaway.derive_rng_seed(**inputs)  # type: ignore[arg-type]
        assert a != b

    def test_fingerprint_is_64_hex_chars(self) -> None:
        _, fp = giveaway.derive_rng_seed(**self.BASE_INPUTS)  # type: ignore[arg-type]
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)


class TestPickWinners:
    POOL = [
        {"x_handle": f"agent_{i:02d}", "wallet": f"w{i}"} for i in range(10)
    ]

    def test_pick_count_zero_returns_empty(self) -> None:
        assert giveaway.pick_winners_deterministic(pool=self.POOL, count=0, seed_int=42) == []

    def test_pick_count_greater_than_pool_caps_at_pool_size(self) -> None:
        # We never want to crash when count > len(pool); the function
        # must gracefully return everyone.
        out = giveaway.pick_winners_deterministic(pool=self.POOL, count=99, seed_int=42)
        assert len(out) == len(self.POOL)

    def test_pick_is_deterministic_for_same_seed(self) -> None:
        a = giveaway.pick_winners_deterministic(pool=self.POOL, count=2, seed_int=12345)
        b = giveaway.pick_winners_deterministic(pool=self.POOL, count=2, seed_int=12345)
        assert [r["x_handle"] for r in a] == [r["x_handle"] for r in b]

    def test_pick_changes_with_seed(self) -> None:
        a = giveaway.pick_winners_deterministic(pool=self.POOL, count=2, seed_int=12345)
        b = giveaway.pick_winners_deterministic(pool=self.POOL, count=2, seed_int=99999)
        # With a pool of 10 and 2 picks the odds of collision are
        # 1/45 — pin the specific seeds to keep this test stable.
        assert [r["x_handle"] for r in a] != [r["x_handle"] for r in b]

    def test_pick_returns_unique_winners(self) -> None:
        out = giveaway.pick_winners_deterministic(pool=self.POOL, count=5, seed_int=7)
        handles = [r["x_handle"] for r in out]
        assert len(handles) == len(set(handles))


# =====================================================================
# Trigger detection
# =====================================================================
class TestGiveawayTrigger:
    def _ctx(self, manual: bool = True, **payload):  # type: ignore[no-untyped-def]
        return TriggerCtx(
            trigger_key="giveaway_extraction",
            manual=manual,
            payload_override=payload,
        )

    def _valid_payload(self) -> dict:
        return {
            "snapshot_id": "abc-123-def",
            "winners_formatted": "@alice, @bob",
            "winners_count": 2,
            "pool_sol": 5,
            "per_winner_sol": 2.5,
            "draw_date_iso": "2026-05-20T18:00:00Z",
            "seed_fingerprint": "deadbeef" * 8,
        }

    def test_fires_with_valid_payload(self) -> None:
        ctx = self._ctx(**self._valid_payload())
        res = giv_trigger._detect(ctx)
        assert res.fired is True
        assert res.payload["snapshot_id_short"] == "abc-123-"
        assert res.payload["seed_fingerprint_short"] == "deadbeefdead"
        assert res.idempotency_key == "giveaway:abc-123-def"

    def test_refuses_non_manual(self) -> None:
        ctx = self._ctx(manual=False, **self._valid_payload())
        res = giv_trigger._detect(ctx)
        assert res.fired is False
        assert res.reason == "manual_only"

    def test_refuses_zero_winners(self) -> None:
        p = self._valid_payload(); p["winners_count"] = 0
        res = giv_trigger._detect(self._ctx(**p))
        assert res.fired is False

    def test_refuses_empty_winners_formatted(self) -> None:
        p = self._valid_payload(); p["winners_formatted"] = ""
        res = giv_trigger._detect(self._ctx(**p))
        assert res.fired is False

    def test_refuses_zero_pool(self) -> None:
        p = self._valid_payload(); p["pool_sol"] = 0
        res = giv_trigger._detect(self._ctx(**p))
        assert res.fired is False


# =====================================================================
# Templates contract
# =====================================================================
class TestGiveawayTemplates:
    def setup_method(self) -> None:
        self.tpls = [t for t in DEFAULT_TEMPLATES if t["trigger_key"] == "giveaway_extraction"]

    def test_four_templates_seeded(self) -> None:
        assert len(self.tpls) == 4

    def test_languages_balanced(self) -> None:
        langs = [t["language"] for t in self.tpls]
        assert langs.count("en") == 2
        assert langs.count("fr") == 2

    def test_every_template_uses_winners_formatted(self) -> None:
        for t in self.tpls:
            assert "{winners_formatted}" in t["content"], (
                f"Template missing {{winners_formatted}}: {t['content'][:60]!r}"
            )


# =====================================================================
# Winners-formatting helper
# =====================================================================
class TestFormatWinners:
    def test_renders_handles_with_at(self) -> None:
        out = giveaway.format_winners_for_template([
            {"x_handle": "alice"}, {"x_handle": "bob"},
        ])
        assert out == "@alice, @bob"

    def test_returns_empty_string_when_no_winners(self) -> None:
        assert giveaway.format_winners_for_template([]) == ""

    def test_truncates_with_plus_n_more_when_long(self) -> None:
        winners = [{"x_handle": f"agent_{i}"} for i in range(8)]
        out = giveaway.format_winners_for_template(winners, max_render=3)
        assert out.endswith("+5 more")
        assert "@agent_0" in out
        assert "@agent_7" not in out
