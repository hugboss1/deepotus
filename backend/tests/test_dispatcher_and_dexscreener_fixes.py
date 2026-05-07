"""Tests for the Sprint 17.5c critical bug fixes (pre-mint blockers).

Bug 1 — X dispatcher TypeError:
    The home-rolled ``_OAuth1Adapter`` shim broke against httpx because
    it did not implement the full ``httpx.Auth`` contract (specifically,
    requests_oauthlib's OAuth1.__call__ called ``prepare_headers()`` on
    a stub that didn't have the method). We now use
    ``authlib.integrations.httpx_client.OAuth1Auth`` which inherits
    directly from ``httpx.Auth``.

Bug 2 — DexScreener 429 rate-limit:
    POLL_SECONDS bumped 30→60s + exponential backoff schedule.
    On 429 the orchestrator persists ``dex_backoff_until`` and the next
    poll() call short-circuits until the timestamp passes. A successful
    200 resets the streak.

These tests are offline (no real X API or DexScreener calls); we
patch the underlying httpx client with fake transports so we can
observe the auth class type and the response-handling branches.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, patch

# Backend root on sys.path regardless of pytest invocation cwd.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.dispatchers import x as x_dispatcher  # noqa: E402
import dexscreener  # noqa: E402


# =====================================================================
# Bug 1 — X dispatcher uses authlib's httpx-native OAuth1Auth
# =====================================================================
class TestXDispatcherAuthlibSwap:
    """The dispatcher must now hand httpx an ``httpx.Auth`` subclass.

    These tests run the live-mode path (dry_run=False) with a fake
    httpx client and assert that ``auth`` is the authlib class — not
    the dead ``_OAuth1Adapter`` stub. We also assert the dead stub no
    longer exists in the module, preventing a future regression where
    someone reintroduces it.
    """

    def test_dead_oauth1_adapter_is_removed(self) -> None:
        """Dead-code guard — the broken shim must not come back."""
        assert not hasattr(x_dispatcher, "_OAuth1Adapter")
        assert not hasattr(x_dispatcher, "_PreparedRequestStub")

    def test_authlib_oauth1auth_is_imported_in_send(self) -> None:
        """Smoke check — the new live-mode path uses authlib."""
        # Import path must resolve without ImportError so the dispatcher
        # never falls into the ``missing_dep_authlib`` branch.
        from authlib.integrations.httpx_client import OAuth1Auth  # noqa: WPS433
        import httpx
        assert issubclass(OAuth1Auth, httpx.Auth)

    def test_live_post_passes_httpx_auth_subclass(self) -> None:
        """The auth handed to httpx.AsyncClient.post must be an
        ``httpx.Auth`` subclass (concretely ``OAuth1Auth``). This
        is the regression test for the production TypeError."""
        captured: Dict[str, Any] = {}

        class _FakeResp:
            status_code = 201

            def json(self) -> Dict[str, Any]:
                return {"data": {"id": "ok-123", "text": "live tweet"}}

            @property
            def text(self) -> str:
                return ""

        class _FakeClient:
            def __init__(self, *_a: Any, **_kw: Any) -> None:
                pass

            async def __aenter__(self) -> "_FakeClient":
                return self

            async def __aexit__(self, *_a: Any) -> None:
                return None

            async def post(self, _url: str, *, json: Dict[str, Any], auth: Any) -> _FakeResp:  # noqa: A002
                captured["auth_class"] = type(auth)
                captured["body"] = json
                return _FakeResp()

        async def _fake_creds() -> Dict[str, str]:
            return {
                "api_key": "ck",
                "api_secret": "cs",
                "access_token": "at",
                "access_token_secret": "ats",
            }

        import httpx
        from authlib.integrations.httpx_client import OAuth1Auth

        with patch.object(x_dispatcher, "_resolve_x_credentials", _fake_creds), \
             patch("httpx.AsyncClient", _FakeClient):
            result = asyncio.run(x_dispatcher.send(
                {"id": "live-1", "rendered_content": "Prophet speaks. — ΔΣ"},
                dry_run=False,
            ))

        assert result.outcome.value == "sent"
        assert result.platform_message_id == "ok-123"
        # The crucial assertion — auth IS an httpx.Auth subclass.
        assert issubclass(captured["auth_class"], httpx.Auth), (
            f"auth must inherit httpx.Auth; got {captured['auth_class'].__mro__}"
        )
        # And specifically the authlib implementation.
        assert captured["auth_class"] is OAuth1Auth


# =====================================================================
# Bug 2 — DexScreener interval + 429 backoff
# =====================================================================
class TestDexScreenerInterval:
    def test_poll_interval_bumped_to_60_seconds(self) -> None:
        """Sprint 17.5c — explicit floor on the poll cadence."""
        assert dexscreener.POLL_SECONDS == 60


class TestBackoffSchedule:
    """Exponential backoff: each successive 429 doubles roughly, capped
    at 30 minutes. A clean 200 resets the streak."""

    def test_zero_attempt_returns_zero(self) -> None:
        assert dexscreener._backoff_seconds_for(0) == 0

    def test_first_attempt_is_one_minute(self) -> None:
        assert dexscreener._backoff_seconds_for(1) == 60

    def test_schedule_is_monotonically_increasing(self) -> None:
        """Defensive — a future tweak that accidentally orders the
        schedule wrong (e.g. 60, 30, 180...) would silently shorten
        the backoff. Fail loudly if so."""
        prev = -1
        for s in dexscreener._BACKOFF_SCHEDULE_S:
            assert s > prev, f"non-monotonic backoff schedule: {dexscreener._BACKOFF_SCHEDULE_S}"
            prev = s

    def test_capped_at_thirty_minutes(self) -> None:
        # Index 99 → capped at the last entry (30 min).
        assert dexscreener._backoff_seconds_for(99) == dexscreener._BACKOFF_SCHEDULE_S[-1]
        assert dexscreener._BACKOFF_SCHEDULE_S[-1] == 1800


class _FakeAsyncCollection:
    """Lightweight in-memory stand-in for a Motor collection — supports
    just enough surface (find_one + update_one $set merge) for the
    poll() fixtures below."""

    def __init__(self, doc: Optional[Dict[str, Any]] = None) -> None:
        self._doc = dict(doc or {})

    async def find_one(self, _query: Dict[str, Any]) -> Dict[str, Any]:
        return dict(self._doc)

    async def update_one(self, _query: Dict[str, Any], op: Dict[str, Any]) -> None:
        for k, v in (op.get("$set") or {}).items():
            self._doc[k] = v


class _FakeDB:
    def __init__(self, vault_doc: Optional[Dict[str, Any]] = None) -> None:
        self.vault_state = _FakeAsyncCollection(vault_doc)


class TestPollOnceBackoffPath:
    """End-to-end behaviour of the 429 → backoff → skip → reset cycle."""

    def test_429_arms_backoff_and_increments_streak(self) -> None:
        db = _FakeDB({
            "_id": dexscreener.VAULT_DOC_ID,
            "dex_mode": "demo",
            "dex_demo_token_address": "DemoMint",
            "dex_429_streak": 0,
        })

        async def _run() -> Dict[str, Any]:
            with patch.object(
                dexscreener, "_fetch_token_stats",
                AsyncMock(return_value=(None, "rate_limited")),
            ):
                return await dexscreener.dex_poll_once(db, vault_mod=None)

        result = asyncio.run(_run())
        assert result["error"] == "rate_limited"
        assert result["consecutive_429"] == 1
        assert result["wait_seconds"] == 60
        # Persistence side-effect — the doc must now carry the backoff.
        assert db.vault_state._doc["dex_429_streak"] == 1
        assert db.vault_state._doc["dex_backoff_until"] is not None

    def test_active_backoff_short_circuits(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        db = _FakeDB({
            "_id": dexscreener.VAULT_DOC_ID,
            "dex_mode": "demo",
            "dex_demo_token_address": "DemoMint",
            "dex_backoff_until": future,
            "dex_429_streak": 2,
        })

        async def _run() -> Dict[str, Any]:
            # ``_fetch_token_stats`` MUST NOT be called when backoff is
            # active — patch it to raise so a regression would loudly
            # explode this test.
            with patch.object(
                dexscreener, "_fetch_token_stats",
                AsyncMock(side_effect=AssertionError("fetched while backoff active")),
            ):
                return await dexscreener.dex_poll_once(db, vault_mod=None)

        result = asyncio.run(_run())
        assert result["skipped"] is True
        assert result["reason"] == "backoff_active"
        assert result["consecutive_429"] == 2

    def test_successful_200_resets_streak(self) -> None:
        # Past backoff window so the orchestrator proceeds.
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        db = _FakeDB({
            "_id": dexscreener.VAULT_DOC_ID,
            "dex_mode": "demo",
            "dex_demo_token_address": "DemoMint",
            "dex_backoff_until": past,
            "dex_429_streak": 3,
            "dex_last_h24_buys": 0,
            "dex_last_h24_sells": 0,
            "dex_last_h24_volume_usd": 0,
        })

        # Build a synthetic DexScreener pair payload — minimal but
        # enough to satisfy ``_extract_stats``.
        fake_pair = {
            "priceUsd": "0.000123",
            "volume": {"h24": 12345.6},
            "txns": {"h24": {"buys": 100, "sells": 80}},
            "liquidity": {"usd": 50000},
            "pairAddress": "p1",
            "dexId": "raydium",
            "baseToken": {"symbol": "DEMO"},
            "quoteToken": {"symbol": "SOL"},
            "chainId": "solana",
        }

        async def _run() -> Dict[str, Any]:
            # apply_demo_ticks would touch vault_mod — bypass by
            # replacing it with a coroutine that returns 0 ticks.
            from unittest.mock import MagicMock
            vault_mod = MagicMock()
            vault_mod.apply_crack = AsyncMock(return_value=None)
            with patch.object(
                dexscreener, "_fetch_token_stats",
                AsyncMock(return_value=(fake_pair, None)),
            ):
                return await dexscreener.dex_poll_once(db, vault_mod=vault_mod)

        result = asyncio.run(_run())
        # First-seen path → quiet, but the success branch must still
        # reset the streak + clear the backoff.
        assert result.get("error") is None
        assert db.vault_state._doc["dex_429_streak"] == 0
        assert db.vault_state._doc["dex_backoff_until"] is None
