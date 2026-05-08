"""Pure-helper unit tests for Sprint 17.5 — Cabinet Expansion.

Covers the deterministic, network-free helpers in:
  * ``core.welcome_signal`` — render_message, settings hydration
  * ``core.prophet_interaction`` — _ensure_signed, _enforce_handle_prefix,
    _build_seed
  * ``core.dispatchers.x`` — reply-mode body shape (we don't make HTTP
    calls; we patch the httpx client to capture the outgoing payload)

These tests run offline and require zero credentials, so they're safe
to gate on every CI run. Live-API behaviour is exercised separately by
the manual ``fire(manual=True, dry_run=True)`` smoke path.

Async helpers are driven via ``asyncio.run`` to stay consistent with
the rest of the backend test suite (no pytest-asyncio dep).
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict
from unittest.mock import patch

import pytest  # noqa: F401  (kept for future skip/parametrize hooks)

# Ensure backend root is importable regardless of pytest's invocation cwd.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import welcome_signal  # noqa: E402
from core import prophet_interaction as pi  # noqa: E402
from core.dispatchers import x as x_dispatcher  # noqa: E402


# =====================================================================
# welcome_signal.render_message
# =====================================================================
class TestWelcomeSignalRender:
    """The Welcome Signal copy is deterministic on purpose — these tests
    pin the format so a future tweak doesn't accidentally drop the
    Cabinet voice."""

    def test_renders_basic_thread_with_handles(self) -> None:
        msg = welcome_signal.render_message(["alice", "bob", "carol"])
        assert "The Cabinet grows." in msg
        assert "@alice @bob @carol" in msg
        assert "PROTOCOL ΔΣ" in msg
        assert "LEVEL 02" in msg

    def test_strips_leading_at_sign(self) -> None:
        """Some agents will paste their @handle, others won't — the
        renderer must canonicalise either way."""
        msg = welcome_signal.render_message(["@alice", "bob", "@carol"])
        assert "@@alice" not in msg
        assert "@alice @bob @carol" in msg

    def test_drops_blank_handles(self) -> None:
        msg = welcome_signal.render_message(["alice", "", "  ", "bob"])
        assert "@alice @bob" in msg
        # Sanity: no double-spaces from the dropped entries.
        assert "  " not in msg.split("Agents ")[1].split(" identified")[0]

    def test_returns_empty_when_no_handles(self) -> None:
        assert welcome_signal.render_message([]) == ""


# =====================================================================
# prophet_interaction signature + addressing helpers
# =====================================================================
class TestEnsureSigned:
    """The ΔΣ signature is the Prophet's brand mark — every reply MUST
    carry it, even if the LLM strips it during a rewrite."""

    def test_appends_signature_when_missing(self) -> None:
        out = pi._ensure_signed("Stay the course, the chart whispers.")
        assert out.endswith("— ΔΣ")

    def test_keeps_existing_signature_intact(self) -> None:
        original = "Some prophecy.\n— ΔΣ"
        out = pi._ensure_signed(original)
        assert out == original

    def test_recognises_em_dash_variants(self) -> None:
        # Any of —, –, - immediately before ΔΣ counts as already signed.
        for dash in ["—", "–", "-"]:
            out = pi._ensure_signed(f"prophecy {dash} ΔΣ")
            # Must not duplicate the signature.
            assert out.count("ΔΣ") == 1

    def test_blank_input_returns_blank(self) -> None:
        assert pi._ensure_signed("") == ""
        assert pi._ensure_signed("   ") == ""


class TestEnforceHandlePrefix:
    def test_prepends_when_missing(self) -> None:
        out = pi._enforce_handle_prefix("hello", "alice")
        assert out.startswith("@alice ")

    def test_idempotent_when_present(self) -> None:
        out = pi._enforce_handle_prefix("@Alice the Cabinet sees you", "alice")
        # Case-insensitive recognition — we don't double-prepend.
        assert out.lower().count("@alice") == 1

    def test_strips_caller_at_sign(self) -> None:
        # Defensive: if someone passes ``@alice`` we don't get @@alice.
        out = pi._enforce_handle_prefix("hello", "@alice")
        assert "@@" not in out
        assert out.startswith("@alice ")


class TestBuildSeed:
    def test_includes_handle_and_excerpt(self) -> None:
        seed = pi._build_seed("alice", "the chart looks bullish today")
        assert "@alice" in seed
        assert "the chart looks bullish today" in seed
        assert "PROTOCOL ΔΣ" in seed
        assert "240 chars" in seed  # contract reminder for the LLM

    def test_truncates_long_source(self) -> None:
        long_source = "x" * 500
        seed = pi._build_seed("bob", long_source)
        # The excerpt portion must be capped at 200 chars.
        assert seed.count("x") <= 210


# =====================================================================
# dispatchers.x — reply body shape
# =====================================================================
class TestDispatcherReplyMode:
    """The Prophet Interaction Bot relies on
    ``meta.reply_to_tweet_id`` being plumbed into the X v2 ``reply``
    sub-object. These tests patch the httpx client so we can observe
    the outgoing body without ever reaching the network."""

    def test_dry_run_carries_reply_target(self) -> None:
        """Dry-run path must still log the reply-target (we use this
        in the admin's ``Fire now (dry run)`` smoke button)."""
        item: Dict[str, Any] = {
            "id": "t1",
            "rendered_content": "@alice prophecy — ΔΣ",
            "meta": {"reply_to_tweet_id": "12345"},
        }
        result = asyncio.run(x_dispatcher.send(item, dry_run=True))
        assert result.outcome.value == "sent"
        assert result.dry_run is True

    def test_live_post_includes_reply_field(self) -> None:
        """When dry_run=False, the dispatcher must put the tweet_id in
        ``body['reply']['in_reply_to_tweet_id']`` per X API v2 spec.

        Sprint 17.5f — the dispatcher now uses manual oauthlib signing
        and ``httpx.post(content=bytes, headers=signed_headers)`` so we
        capture ``content`` (raw JSON bytes) and decode it to assert
        the body structure."""
        import json as _json
        captured: Dict[str, Any] = {}

        class _FakeResp:
            status_code = 201

            def json(self) -> Dict[str, Any]:
                return {"data": {"id": "999", "text": "reply ok"}}

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

            async def post(  # noqa: A002
                self, _url: str, *,
                content: bytes,
                headers: Dict[str, str],
            ) -> _FakeResp:
                captured["raw_content"] = content
                captured["body"] = _json.loads(content.decode("utf-8"))
                captured["headers"] = dict(headers)
                return _FakeResp()

        # The dispatcher's _verify_creds reads from the cabinet vault; we
        # short-circuit it to return a complete OAuth1 tuple so the live
        # path is reachable in the test.
        async def _fake_creds() -> Dict[str, str]:
            return {
                "api_key": "ck",
                "api_secret": "cs",
                "access_token": "at",
                "access_token_secret": "ats",
            }

        with patch.object(x_dispatcher, "_resolve_x_credentials", _fake_creds), \
             patch("httpx.AsyncClient", _FakeClient):
            result = asyncio.run(x_dispatcher.send(
                {
                    "id": "t2",
                    "rendered_content": "@bob the chart whispers — ΔΣ",
                    "meta": {"reply_to_tweet_id": "tweet-42"},
                },
                dry_run=False,
            ))

        assert result.outcome.value == "sent"
        # The crucial check: body MUST contain the text + reply structure.
        assert captured["body"]["text"].endswith("— ΔΣ")
        assert captured["body"]["reply"] == {"in_reply_to_tweet_id": "tweet-42"}
        # Content-Type header is application/json (not form-urlencoded —
        # that was the root cause of the production 400).
        assert "application/json" in captured["headers"]["Content-Type"]
        # OAuth1 Authorization header is computed by oauthlib.
        assert captured["headers"]["Authorization"].startswith("OAuth ")

    def test_no_reply_field_when_meta_absent(self) -> None:
        """Default behaviour — without ``meta.reply_to_tweet_id`` we
        post a regular tweet (no ``reply`` key in the body)."""
        import json as _json
        captured: Dict[str, Any] = {}

        class _FakeResp:
            status_code = 201

            def json(self) -> Dict[str, Any]:
                return {"data": {"id": "999", "text": "ok"}}

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

            async def post(  # noqa: A002
                self, _url: str, *,
                content: bytes,
                headers: Dict[str, str],
            ) -> _FakeResp:
                captured["body"] = _json.loads(content.decode("utf-8"))
                captured["headers"] = dict(headers)
                return _FakeResp()

        async def _fake_creds() -> Dict[str, str]:
            return {
                "api_key": "ck",
                "api_secret": "cs",
                "access_token": "at",
                "access_token_secret": "ats",
            }

        with patch.object(x_dispatcher, "_resolve_x_credentials", _fake_creds), \
             patch("httpx.AsyncClient", _FakeClient):
            asyncio.run(x_dispatcher.send(
                {"id": "t3", "rendered_content": "regular post"},
                dry_run=False,
            ))

        assert "reply" not in captured["body"]
        assert captured["body"]["text"] == "regular post"


# =====================================================================
# Sprint 17.5d/e — Structured 400 error parsing
# =====================================================================
class TestX400ErrorParsing:
    """The dispatcher must classify common X 400 reasons into specific
    error codes so the queue UI can render an actionable hint instead
    of the opaque ``http_400``."""

    def _run_with_400_body(self, body_dict: Dict[str, Any], *, status: int = 400) -> Any:
        """Run send() with a fake httpx client that returns ``body_dict``
        as the response JSON + raw text. Returns the DispatchResult.

        Sprint 17.5f — updated for the new manual-signing path: the
        fake client's ``post`` now accepts ``content=`` + ``headers=``
        instead of ``json=`` + ``auth=``."""
        import json as _json

        body_text = _json.dumps(body_dict)

        class _FakeResp:
            def __init__(self) -> None:
                self.status_code = status
                self.text = body_text

            def json(self) -> Dict[str, Any]:
                return body_dict

        class _FakeClient:
            def __init__(self, *_a: Any, **_kw: Any) -> None:
                pass

            async def __aenter__(self) -> "_FakeClient":
                return self

            async def __aexit__(self, *_a: Any) -> None:
                return None

            async def post(  # noqa: A002, ARG002
                self, _url: str, *,
                content: bytes,
                headers: Dict[str, str],
            ) -> _FakeResp:
                return _FakeResp()

        async def _fake_creds() -> Dict[str, str]:
            return {
                "api_key": "ck", "api_secret": "cs",
                "access_token": "at", "access_token_secret": "ats",
            }

        with patch.object(x_dispatcher, "_resolve_x_credentials", _fake_creds), \
             patch("httpx.AsyncClient", _FakeClient):
            return asyncio.run(x_dispatcher.send(
                {"id": "t-400", "rendered_content": "test"},
                dry_run=False,
            ))

    def test_duplicate_content_detected_via_type_url(self) -> None:
        """X v2 standard 'duplicate-rules' type URL."""
        result = self._run_with_400_body({
            "title": "Forbidden",
            "type": "https://api.twitter.com/2/problems/duplicate-rules",
            "detail": "You are not permitted to create a duplicate Tweet.",
        })
        assert result.error == "x_duplicate_content"
        # Snippet must surface X's own detail message.
        assert "duplicate" in (result.response_snippet or "").lower()

    def test_duplicate_content_detected_via_detail_text(self) -> None:
        """Defensive — even if X's type URL changes, detail text wins."""
        result = self._run_with_400_body({
            "title": "Forbidden",
            "type": "https://api.twitter.com/2/problems/some-future-type",
            "detail": "Status is a duplicate.",
        })
        assert result.error == "x_duplicate_content"

    def test_text_too_long_detected(self) -> None:
        result = self._run_with_400_body({
            "errors": [{
                "message": "Tweet needs to be a bit shorter.",
                "code": 186,
            }],
            "detail": "Your Tweet is too long.",
        })
        assert result.error == "x_text_too_long"

    def test_invalid_payload_falls_through(self) -> None:
        result = self._run_with_400_body({
            "title": "Invalid Request",
            "errors": [{"message": "Field 'text' is required."}],
            "detail": "One or more parameters to your request was invalid.",
        })
        assert result.error == "x_invalid_payload"
        assert "invalid" in (result.response_snippet or "").lower()

    def test_unknown_400_keeps_generic_code_but_surfaces_detail(self) -> None:
        """A 400 we can't classify must still pass through the snippet."""
        result = self._run_with_400_body({
            "title": "Some New Reason",
            "detail": "Some never-seen-before failure.",
        })
        assert result.error == "http_400"
        # Detail must be surfaced in response_snippet.
        assert "never-seen" in (result.response_snippet or "")

    def test_5xx_marked_transient(self) -> None:
        """5xx are transient — the worker should retry."""
        result = self._run_with_400_body(
            {"title": "Service Unavailable", "detail": "Try again."},
            status=503,
        )
        assert result.error == "http_503"
        assert result.transient_failure is True
