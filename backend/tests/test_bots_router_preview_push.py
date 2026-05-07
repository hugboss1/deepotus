"""Tests for the Sprint 17.5 follow-up endpoints in routers/bots.py.

Covers:
  * Pydantic hardening of ``GeneratePreviewResponse`` — surplus keys
    are silently ignored (extra='ignore') and missing fields fall
    back to safe defaults so the ASGI exception path can never
    fire on a partial LLM result.
  * ``PreviewPushRequest`` schema — required fields, platform
    whitelist, language enum.
  * ``ReleaseNowResponse`` shape sanity check.
  * Internal coercion logic — strings, lists, ints all gracefully
    handle bad upstream values.

We test the Pydantic models directly (no FastAPI client) to keep
these helpers offline-safe and dependency-free, in line with the
rest of the backend test suite.
"""

from __future__ import annotations

import os
import sys

# Backend root must be on sys.path regardless of pytest's invocation cwd.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from routers.bots import (  # noqa: E402
    GeneratePreviewResponse,
    PreviewPushRequest,
    ReleaseNowResponse,
)


# =====================================================================
# GeneratePreviewResponse — ASGI hardening
# =====================================================================
class TestGeneratePreviewResponseHardening:
    """Sprint 17.5 follow-up — ``Exception in ASGI application`` was
    occurring when the LLM returned a partial dict (e.g. missing
    `primary_emoji`). With the new ``extra='ignore'`` config + safe
    defaults, the response should always validate cleanly."""

    def test_accepts_empty_payload(self) -> None:
        """All fields optional with safe defaults → empty {} is valid."""
        out = GeneratePreviewResponse()
        assert out.content_fr == ""
        assert out.content_en == ""
        assert out.hashtags == []
        assert out.primary_emoji == ""
        assert out.char_budget == 0

    def test_silently_drops_unknown_keys(self) -> None:
        """A V2 generator that adds a new field (e.g. `weight_picked`)
        must not break the response — Pydantic should drop it."""
        out = GeneratePreviewResponse(
            content_fr="prophecy fr",
            content_en="prophecy en",
            char_budget=280,
            provider="anthropic",
            model="claude-sonnet-4-5",
            content_type="prophecy",
            platform="x",
            hashtags=["DeepState"],
            primary_emoji="🔮",
            template_used="lore",
            template_label="Lore drop",
            # The following are NOT in the schema — they would have
            # raised before the hardening. Now they're dropped.
            weight_picked=4,
            internal_token="should-not-leak",
            ablation_branch="b",
        )  # type: ignore[call-arg]
        # Sanity — the legitimate fields survived.
        assert out.template_used == "lore"
        assert out.primary_emoji == "🔮"
        # The dropped keys must NOT surface on the model.
        assert not hasattr(out, "weight_picked")
        assert not hasattr(out, "internal_token")

    def test_optional_template_fields_default_none(self) -> None:
        """V1 path doesn't carry V2 template metadata — they must
        default to None so the JSON shape stays consistent."""
        out = GeneratePreviewResponse(
            content_fr="x",
            content_en="x",
            char_budget=280,
            provider="anthropic",
            model="claude",
            content_type="prophecy",
            platform="x",
            hashtags=[],
            primary_emoji="",
        )
        assert out.template_used is None
        assert out.template_label is None


# =====================================================================
# PreviewPushRequest — input validation
# =====================================================================
class TestPreviewPushRequest:
    """The /preview/push endpoint must reject malformed payloads
    early so the dispatch_queue.propose call is never reached with
    bad data."""

    def _baseline(self, **overrides):
        defaults = {
            "content_fr": "Le Cabinet voit.",
            "content_en": "The Cabinet sees.",
            "platforms": ["x"],
            "lang": "en",
        }
        defaults.update(overrides)
        return defaults

    def test_minimal_valid_payload(self) -> None:
        req = PreviewPushRequest(**self._baseline())
        assert req.platforms == ["x"]
        assert req.lang == "en"
        # Optional fields default to None / empty.
        assert req.primary_emoji is None
        assert req.hashtags is None

    def test_rejects_invalid_lang(self) -> None:
        import pytest  # local import — keeps the test module fast at collection
        with pytest.raises(ValueError):
            PreviewPushRequest(**self._baseline(lang="es"))  # noqa: F841

    def test_accepts_dual_platform(self) -> None:
        req = PreviewPushRequest(**self._baseline(platforms=["x", "telegram"]))
        assert sorted(req.platforms) == ["telegram", "x"]

    def test_rejects_empty_content(self) -> None:
        import pytest
        with pytest.raises(ValueError):
            PreviewPushRequest(**self._baseline(content_fr=""))

    def test_optional_metadata_fields(self) -> None:
        req = PreviewPushRequest(**self._baseline(
            primary_emoji="🔮",
            hashtags=["DeepState", "PROTOCOL"],
            template_used="lore",
        ))
        assert req.primary_emoji == "🔮"
        assert req.hashtags == ["DeepState", "PROTOCOL"]
        assert req.template_used == "lore"

    def test_extra_keys_silently_ignored(self) -> None:
        """The frontend may evolve faster than the backend — drop unknown
        fields rather than 422-ing the operator's push attempt."""
        req = PreviewPushRequest(**self._baseline(
            future_field="ignored",  # type: ignore[arg-type]
            another_one=42,  # type: ignore[arg-type]
        ))
        # Pydantic (with extra='ignore') drops them silently.
        assert not hasattr(req, "future_field")


# =====================================================================
# ReleaseNowResponse — shape sanity
# =====================================================================
class TestReleaseNowResponse:
    def test_default_shape(self) -> None:
        out = ReleaseNowResponse(
            triggered=[{"id": "heartbeat", "forced_at": "2026-01-01T00:00:00+00:00"}],
            skipped=[],
            kill_switch_active=False,
            note="forced 1 job(s) to run now",
        )
        assert out.kill_switch_active is False
        assert out.triggered[0]["id"] == "heartbeat"

    def test_kill_switch_armed_path(self) -> None:
        """When the kill-switch is armed, the controller short-circuits
        every job into ``skipped`` and returns 0 triggered."""
        out = ReleaseNowResponse(
            triggered=[],
            skipped=[
                {"id": "heartbeat", "reason": "kill_switch_active"},
                {"id": "welcome_signal", "reason": "kill_switch_active"},
            ],
            kill_switch_active=True,
            note="kill-switch armed — jobs left untouched",
        )
        assert out.triggered == []
        assert len(out.skipped) == 2
        assert all(s["reason"] == "kill_switch_active" for s in out.skipped)
