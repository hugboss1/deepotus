"""Unit tests for the pure helpers of the organic-engagement modules.

Covers ``core.mention_responder`` (auto-reply to mentions) and
``core.keyword_digest`` (semi-auto Telegram digest). The I/O paths
(Mongo, X API, Telegram) are exercised via the dry-run recette
(``POST /api/admin/engagement/mentions/poll-now?dry_run=true`` and
``/digest/run-now``), not here — same split as the KOL-listener tests.

Recette criteria encoded below:
  * Every rendered reply (mention templates + digest templates) fits
    the X dispatcher's 260-char cap WITH the longest realistic handle,
    and carries the 4 mandatory blocks: $D2EP, the mint CA, the site,
    and the @Deepotus_AI follow CTA.
  * Template rotation yields distinct bodies (X rejects duplicates).
  * The digest hour-gate fires exactly in the configured UTC hours and
    never twice within 3 h.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

# Backend root importable + env prerequisites for core.config.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "deepotus_test")

from core.keyword_digest import (  # noqa: E402
    DEFAULT_RULES,
    build_hit_message,
    build_query,
    render_suggested_reply,
    should_fire,
)
from core.mention_responder import (  # noqa: E402
    DEFAULT_REPLY_TEMPLATES,
    render_reply,
)

_MINT_CA = "AUztiAfSCwDwm5Be5tSDiTmrZPnwATk7837cAFeDpump"
#: X caps handles at 15 chars — worst-case length for budget math.
_LONGEST_HANDLE = "abcdefghijklmno"


# =====================================================================
# Mention Responder — reply rendering
# =====================================================================
class TestMentionReplyTemplates:
    def test_all_defaults_fit_x_budget_with_longest_handle(self) -> None:
        """The dispatcher hard-trims at 260 chars; a trimmed reply would
        amputate the follow CTA, so every default must fit untrimmed."""
        for i in range(len(DEFAULT_REPLY_TEMPLATES)):
            body = render_reply(_LONGEST_HANDLE, DEFAULT_REPLY_TEMPLATES, i)
            assert len(body) <= 260, f"template #{i} overflows: {len(body)} chars"

    def test_all_defaults_carry_mandatory_blocks(self) -> None:
        for i in range(len(DEFAULT_REPLY_TEMPLATES)):
            body = render_reply("someuser", DEFAULT_REPLY_TEMPLATES, i)
            assert "$D2EP" in body
            assert _MINT_CA in body
            assert "deepotus.xyz" in body
            assert "@Deepotus_AI" in body
            assert "NFA" in body

    def test_handle_is_injected_with_at_prefix(self) -> None:
        body = render_reply("Alice_42", DEFAULT_REPLY_TEMPLATES, 0)
        assert body.startswith("@Alice_42")
        body2 = render_reply("@Alice_42", DEFAULT_REPLY_TEMPLATES, 0)
        assert body2.startswith("@Alice_42")
        assert "@@" not in body2

    def test_rotation_yields_distinct_bodies(self) -> None:
        """Same handle, consecutive rotation indexes → different texts,
        otherwise X's duplicate-content check kills reply #2."""
        bodies = {
            render_reply("bob", DEFAULT_REPLY_TEMPLATES, i)
            for i in range(len(DEFAULT_REPLY_TEMPLATES))
        }
        assert len(bodies) == len(DEFAULT_REPLY_TEMPLATES)

    def test_empty_template_list_falls_back_to_defaults(self) -> None:
        body = render_reply("carol", [], 0)
        assert "$D2EP" in body and _MINT_CA in body

    def test_oversized_custom_template_is_trimmed(self) -> None:
        body = render_reply("dave", ["{handle} " + "x" * 400], 0)
        assert len(body) == 260
        assert body.endswith("…")


# =====================================================================
# Keyword Digest — query building
# =====================================================================
class TestBuildQuery:
    def test_appends_noise_filters_and_lang(self) -> None:
        q = build_query('"i need a ticker"', "en")
        assert "-is:retweet" in q
        assert "-is:reply" in q
        assert "lang:en" in q

    def test_parenthesises_top_level_or_queries(self) -> None:
        """``a OR b -is:retweet`` binds the filter to the last operand
        only — the helper must wrap the OR clause first."""
        q = build_query('"need a ticker" OR "gimme a ticker"', "en")
        assert q.startswith('("need a ticker" OR "gimme a ticker")')

    def test_does_not_duplicate_existing_filters(self) -> None:
        q = build_query('chill -is:retweet -is:reply lang:en', "en")
        assert q.count("-is:retweet") == 1
        assert q.count("lang:en") == 1

    def test_no_lang_clause_when_lang_empty(self) -> None:
        q = build_query("chill", "")
        assert "lang:" not in q


# =====================================================================
# Keyword Digest — suggested replies + hit message
# =====================================================================
class TestDigestRendering:
    def test_all_default_rule_templates_fit_budget_and_carry_blocks(self) -> None:
        for rule in DEFAULT_RULES:
            body = render_suggested_reply(rule["template"], _LONGEST_HANDLE)
            assert len(body) <= 260, f"rule {rule['label']!r} overflows"
            assert "$D2EP" in body
            assert _MINT_CA in body
            assert "deepotus.xyz" in body
            assert "@Deepotus_AI" in body

    def test_hit_message_contains_links_and_escaped_excerpt(self) -> None:
        hit = {
            "id": "1811111111111111111",
            "text": "I need a ticker <now> & fast",
            "author_handle": "degen_guy",
            "author_followers": 1234,
        }
        suggested = render_suggested_reply(DEFAULT_RULES[0]["template"], "degen_guy")
        msg = build_hit_message(hit, "i need a ticker", suggested)
        # Direct link to the source tweet.
        assert "https://x.com/degen_guy/status/1811111111111111111" in msg
        # One-tap pre-filled reply intent (urlencoded body).
        assert "https://x.com/intent/tweet?in_reply_to=1811111111111111111" in msg
        assert "%24D2EP" in msg or "$D2EP" in msg
        # HTML-escaped excerpt (raw "<now>" would break parse_mode=HTML).
        assert "<now>" not in msg
        assert "&lt;now&gt;" in msg
        # Copyable block present.
        assert "<pre>" in msg and "</pre>" in msg


# =====================================================================
# Keyword Digest — hour gating
# =====================================================================
class TestShouldFire:
    def _at(self, hour: int) -> datetime:
        return datetime(2026, 7, 19, hour, 5, tzinfo=timezone.utc)

    def test_fires_in_configured_hour_with_no_prior_run(self) -> None:
        assert should_fire(hours_utc=[7, 16], now=self._at(7), last_run_at=None)

    def test_never_fires_outside_configured_hours(self) -> None:
        assert not should_fire(hours_utc=[7, 16], now=self._at(12), last_run_at=None)

    def test_blocks_second_run_in_same_window(self) -> None:
        just_ran = self._at(7).isoformat()
        assert not should_fire(
            hours_utc=[7, 16], now=self._at(7), last_run_at=just_ran,
        )

    def test_fires_again_at_the_next_slot(self) -> None:
        morning = self._at(7).isoformat()
        assert should_fire(hours_utc=[7, 16], now=self._at(16), last_run_at=morning)

    def test_unparseable_last_run_fails_open(self) -> None:
        assert should_fire(hours_utc=[7], now=self._at(7), last_run_at="not-a-date")
