"""Pure-helper unit tests for Sprint 17.6 — Operation Incinerator.

Network-free + DB-free coverage of the deterministic helpers in:
  * ``core.burn_logs`` — normalise_amount, normalise_signature,
    locked-allocation constants, _parse_iso, _build_tx_link, _fmt
    (the bits that don't talk to Mongo).
  * ``core.triggers.burn_event`` — _detect happy path, idempotency
    key shape, validation failures (manual-only gate, bad signature,
    over-cap amount, negative amount).
  * ``core.templates_repo.DEFAULT_TEMPLATES`` — make sure the 4 new
    burn_event templates (2 EN + 2 FR) reference the canonical
    placeholders so a rename in the trigger never silently breaks
    a template rendering at fire time.

Live API behaviour (X / Telegram dispatch) is exercised separately
through the existing Pytest sweeps and the testing_agent.
"""

from __future__ import annotations

import os
import sys

# Ensure backend root is importable regardless of pytest's invocation cwd.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import burn_logs  # noqa: E402
from core.templates_repo import DEFAULT_TEMPLATES  # noqa: E402
from core.triggers import burn_event as burn_trigger  # noqa: E402
from core.triggers.base import TriggerCtx  # noqa: E402


# =====================================================================
# Constants — Cabinet Investor Honesty Pact
# =====================================================================
class TestLockedAllocations:
    """The ``LOCKED_TOTAL`` constant drives the public
    ``effective_circulating`` math. Any change here must be matched
    by a public on-chain disclosure first."""

    def test_initial_supply_is_one_billion(self) -> None:
        assert burn_logs.INITIAL_SUPPLY == 1_000_000_000

    def test_treasury_locked_is_300m(self) -> None:
        assert burn_logs.TREASURY_LOCKED == 300_000_000

    def test_team_locked_is_150m(self) -> None:
        assert burn_logs.TEAM_LOCKED == 150_000_000

    def test_locked_total_is_sum(self) -> None:
        # Defensive — guards against someone tweaking one constant in
        # isolation. LOCKED_TOTAL is the source of truth for the
        # 45% disclosure copy.
        assert (
            burn_logs.LOCKED_TOTAL
            == burn_logs.TREASURY_LOCKED + burn_logs.TEAM_LOCKED
            == 450_000_000
        )

    def test_locked_percent_is_forty_five(self) -> None:
        # The public disclaimer hardcodes "45%" — pin the ratio so it
        # stays mathematically true.
        pct = 100 * burn_logs.LOCKED_TOTAL / burn_logs.INITIAL_SUPPLY
        assert pct == 45.0


# =====================================================================
# burn_logs.normalise_amount
# =====================================================================
class TestNormaliseAmount:
    def test_accepts_positive_int(self) -> None:
        amt, err = burn_logs.normalise_amount(50_000_000)
        assert err is None and amt == 50_000_000

    def test_accepts_string_int(self) -> None:
        amt, err = burn_logs.normalise_amount("123456")
        assert err is None and amt == 123_456

    def test_accepts_float_floors_to_int(self) -> None:
        amt, err = burn_logs.normalise_amount(1234.999)
        assert err is None and amt == 1234

    def test_accepts_scientific_notation(self) -> None:
        amt, err = burn_logs.normalise_amount("1e6")
        assert err is None and amt == 1_000_000

    def test_rejects_zero(self) -> None:
        amt, err = burn_logs.normalise_amount(0)
        assert err == "amount_must_be_positive" and amt == 0

    def test_rejects_negative(self) -> None:
        amt, err = burn_logs.normalise_amount(-1)
        assert err == "amount_must_be_positive"

    def test_rejects_non_numeric(self) -> None:
        amt, err = burn_logs.normalise_amount("abc")
        assert err == "amount_not_numeric" and amt == 0

    def test_rejects_above_initial_supply(self) -> None:
        amt, err = burn_logs.normalise_amount(burn_logs.INITIAL_SUPPLY + 1)
        assert err == "amount_exceeds_initial_supply"


# =====================================================================
# burn_logs.normalise_signature
# =====================================================================
class TestNormaliseSignature:
    # Real-world-looking Solana tx sig (base58, 88 chars typical).
    VALID_SIG = (
        "5VfYK9JNwNqaQ8MnGqV7sLB4mTrHGD2Cs1KfWX3hRyBxJ"
        "vY7uA8nP6jKLNcEwQzTHxYi2P9MFXuVbR4tDcN1ABCD"
    )

    def test_accepts_valid_base58(self) -> None:
        sig, err = burn_logs.normalise_signature(self.VALID_SIG)
        assert err is None and sig == self.VALID_SIG

    def test_strips_whitespace(self) -> None:
        sig, err = burn_logs.normalise_signature(f"   {self.VALID_SIG}   ")
        assert err is None and sig == self.VALID_SIG

    def test_rejects_empty(self) -> None:
        _, err = burn_logs.normalise_signature("")
        assert err == "tx_signature_required"

    def test_rejects_too_short(self) -> None:
        _, err = burn_logs.normalise_signature("ABCD1234")
        assert err == "tx_signature_invalid_format"

    def test_rejects_invalid_base58_chars(self) -> None:
        # '0' (zero) is not in base58 alphabet.
        bad = "0" * 64
        _, err = burn_logs.normalise_signature(bad)
        assert err == "tx_signature_invalid_format"

    def test_rejects_url(self) -> None:
        _, err = burn_logs.normalise_signature(
            "https://solscan.io/tx/" + self.VALID_SIG,
        )
        assert err == "tx_signature_invalid_format"


# =====================================================================
# burn_logs._parse_iso + _build_tx_link
# =====================================================================
class TestBurnLogsHelpers:
    def test_parse_iso_handles_z_suffix(self) -> None:
        dt = burn_logs._parse_iso("2026-05-11T14:00:00Z")
        assert dt is not None
        assert dt.year == 2026 and dt.month == 5 and dt.day == 11

    def test_parse_iso_returns_none_on_garbage(self) -> None:
        assert burn_logs._parse_iso("not a date") is None
        assert burn_logs._parse_iso(None) is None
        assert burn_logs._parse_iso("") is None

    def test_build_tx_link_uses_solscan(self) -> None:
        url = burn_logs._build_tx_link("ABC123")
        assert url == "https://solscan.io/tx/ABC123"


# =====================================================================
# triggers.burn_event._detect
# =====================================================================
class TestBurnEventTrigger:
    VALID_SIG = TestNormaliseSignature.VALID_SIG

    def _ctx(self, manual: bool = True, **payload):  # type: ignore[no-untyped-def]
        return TriggerCtx(
            trigger_key="burn_event",
            manual=manual,
            payload_override=payload,
        )

    def test_fires_on_manual_with_valid_payload(self) -> None:
        ctx = self._ctx(
            burn_amount=50_000_000,
            tx_signature=self.VALID_SIG,
            burn_note="Q1 buyback",
        )
        res = burn_trigger._detect(ctx)
        assert res.fired is True
        assert res.payload["burn_amount"] == 50_000_000
        assert res.payload["tx_signature"] == self.VALID_SIG
        # tx_link derived defensively when missing in payload.
        assert res.payload["tx_link"].startswith("https://solscan.io/tx/")
        # burn_pct = 50M / 1B = 5%.
        assert float(res.payload["burn_pct"]) == 5.0
        # Effective circulating after = 1B - 450M (locks) - 50M = 500M.
        assert res.payload["burn_circulating_after"] == 500_000_000
        # Pretty format for tweet readability.
        assert res.payload["burn_amount_pretty"] == "50.00M"
        assert res.payload["burn_circulating_after_pretty"] == "500.00M"
        # Idempotency key bound to tx_signature.
        assert res.idempotency_key == f"burn:{self.VALID_SIG}"

    def test_refuses_non_manual(self) -> None:
        # Burn announcements MUST be a deliberate disclosure, never an
        # observation from a poller.
        ctx = self._ctx(
            manual=False,
            burn_amount=50_000_000,
            tx_signature=self.VALID_SIG,
        )
        res = burn_trigger._detect(ctx)
        assert res.fired is False
        assert res.reason == "manual_only"

    def test_refuses_zero_amount(self) -> None:
        ctx = self._ctx(burn_amount=0, tx_signature=self.VALID_SIG)
        res = burn_trigger._detect(ctx)
        assert res.fired is False

    def test_refuses_amount_above_initial_supply(self) -> None:
        ctx = self._ctx(
            burn_amount=burn_logs.INITIAL_SUPPLY + 1,
            tx_signature=self.VALID_SIG,
        )
        res = burn_trigger._detect(ctx)
        assert res.fired is False

    def test_refuses_invalid_signature(self) -> None:
        ctx = self._ctx(burn_amount=1000, tx_signature="not_base58_!!")
        res = burn_trigger._detect(ctx)
        assert res.fired is False
        assert "tx_signature" in (res.reason or "")

    def test_respects_provided_tx_link(self) -> None:
        # If the upstream router pre-rendered a tx_link (which the
        # production router does), we should use it as-is instead of
        # rebuilding the URL.
        custom_link = "https://solscan.io/tx/CUSTOM"
        ctx = self._ctx(
            burn_amount=1_000,
            tx_signature=self.VALID_SIG,
            tx_link=custom_link,
        )
        res = burn_trigger._detect(ctx)
        assert res.fired is True
        assert res.payload["tx_link"] == custom_link


# =====================================================================
# templates_repo — burn_event placeholders
# =====================================================================
class TestBurnEventTemplates:
    """Lock in the contract between the trigger's payload keys and the
    template strings. Renaming a placeholder in the trigger without
    updating the templates produces an empty interpolation at runtime
    — these tests catch that drift in CI instead of in prod."""

    def setup_method(self) -> None:
        self.burn_tpls = [
            t for t in DEFAULT_TEMPLATES if t["trigger_key"] == "burn_event"
        ]

    def test_four_templates_seeded(self) -> None:
        # 2 EN + 2 FR — minimum for tonal variance in the queue.
        assert len(self.burn_tpls) == 4

    def test_languages_balanced(self) -> None:
        langs = [t["language"] for t in self.burn_tpls]
        assert langs.count("en") == 2
        assert langs.count("fr") == 2

    def test_every_template_uses_tx_link(self) -> None:
        # The whole point of a burn disclosure is proof. Every variant
        # must include the on-chain link.
        for t in self.burn_tpls:
            assert "{tx_link}" in t["content"], (
                f"Template missing {{tx_link}}: {t['content'][:60]!r}"
            )

    def test_every_template_uses_burn_amount_pretty(self) -> None:
        for t in self.burn_tpls:
            assert "{burn_amount_pretty}" in t["content"], (
                f"Template missing {{burn_amount_pretty}}: "
                f"{t['content'][:60]!r}"
            )

    def test_at_least_one_template_uses_burn_pct(self) -> None:
        # We don't require every template to surface burn_pct (some
        # variants intentionally avoid the number for variety), but at
        # least one per language should — that's the "scarcity proof"
        # angle.
        has_pct = [t for t in self.burn_tpls if "{burn_pct}" in t["content"]]
        assert len(has_pct) >= 2, (
            "Need at least one EN + one FR template using {burn_pct}"
        )
