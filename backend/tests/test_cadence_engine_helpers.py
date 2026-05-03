"""Unit tests for the pure helpers in ``core.cadence_engine``.

Sprint 21 — these helpers were extracted from the orchestrator
functions during the cyclomatic-complexity refactor. They have zero
I/O, so we test them with simple synchronous assertions and no Mongo
mocks. Run with::

    pytest backend/tests/test_cadence_engine_helpers.py -v
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

# Allow ``import core.cadence_engine`` from the test file.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Some env vars are required by the imports of the engine module (db
# connection at import time). Tests don't actually hit the DB, but we
# need the imports to succeed.
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "deepotus_test_unit")

from core.cadence_engine import (  # noqa: E402
    _crossed_milestone,
    _iter_due_slots,
    format_mc_label,
    is_in_quiet_hours,
    parse_hhmm,
    pick_archetype,
)


# =====================================================================
# parse_hhmm
# =====================================================================
def test_parse_hhmm_valid():
    assert parse_hhmm("00:00") == (0, 0)
    assert parse_hhmm("08:30") == (8, 30)
    assert parse_hhmm("23:59") == (23, 59)


def test_parse_hhmm_invalid():
    assert parse_hhmm("") is None
    assert parse_hhmm("8:30") is None        # too short
    assert parse_hhmm("24:00") is None       # hour out of range
    assert parse_hhmm("12:60") is None       # minute out of range
    assert parse_hhmm("12-30") is None       # bad separator
    assert parse_hhmm("ab:cd") is None       # not numeric


# =====================================================================
# is_in_quiet_hours
# =====================================================================
def _t(h: int, m: int = 0) -> datetime:
    return datetime(2026, 5, 3, h, m, tzinfo=timezone.utc)


def test_quiet_hours_disabled_when_flag_off():
    qh = {"enabled": False, "start_utc": "23:00", "end_utc": "06:00"}
    assert is_in_quiet_hours(_t(23, 30), qh) is False


def test_quiet_hours_same_day_window():
    qh = {"enabled": True, "start_utc": "13:00", "end_utc": "14:00"}
    assert is_in_quiet_hours(_t(12, 59), qh) is False
    assert is_in_quiet_hours(_t(13, 0), qh) is True
    assert is_in_quiet_hours(_t(13, 30), qh) is True
    assert is_in_quiet_hours(_t(14, 0), qh) is False  # end is exclusive
    assert is_in_quiet_hours(_t(14, 30), qh) is False


def test_quiet_hours_wrap_past_midnight():
    qh = {"enabled": True, "start_utc": "23:00", "end_utc": "06:00"}
    assert is_in_quiet_hours(_t(22, 30), qh) is False
    assert is_in_quiet_hours(_t(23, 0), qh) is True
    assert is_in_quiet_hours(_t(2, 0), qh) is True
    assert is_in_quiet_hours(_t(5, 59), qh) is True
    assert is_in_quiet_hours(_t(6, 0), qh) is False


def test_quiet_hours_zero_length_means_disabled():
    qh = {"enabled": True, "start_utc": "08:00", "end_utc": "08:00"}
    assert is_in_quiet_hours(_t(8, 0), qh) is False
    assert is_in_quiet_hours(_t(15, 0), qh) is False


def test_quiet_hours_malformed_inputs_treated_as_disabled():
    assert is_in_quiet_hours(
        _t(2, 0), {"enabled": True, "start_utc": "abc", "end_utc": "06:00"},
    ) is False
    assert is_in_quiet_hours(
        _t(2, 0), {"enabled": True, "start_utc": "23:00", "end_utc": ""},
    ) is False


# =====================================================================
# pick_archetype
# =====================================================================
def test_pick_archetype_respects_allowed_list():
    chosen = pick_archetype(["lore"])
    assert chosen == "lore"


def test_pick_archetype_falls_back_to_full_set_on_empty_allowed():
    chosen = pick_archetype([])
    assert chosen in {"lore", "satire_news", "stats", "prophecy", "meme_visual"}


def test_pick_archetype_falls_back_to_full_set_on_typoed_allowed():
    chosen = pick_archetype(["definitely-not-a-template"])
    assert chosen in {"lore", "satire_news", "stats", "prophecy", "meme_visual"}


def test_pick_archetype_respects_subset_when_some_typoed():
    chosen = pick_archetype(["prophecy", "garbage"])
    assert chosen == "prophecy"


# =====================================================================
# _iter_due_slots
# =====================================================================
def test_iter_due_slots_yields_when_match_and_not_dedup():
    daily = {
        "x": {"enabled": True, "post_times_utc": ["08:30"], "archetypes": ["lore"]},
        "telegram": {"enabled": False},
    }
    out = list(_iter_due_slots(daily, {"x": {}, "telegram": {}}, "08:30", "2026-05-03"))
    assert len(out) == 1
    assert out[0][0] == "x"
    assert out[0][1] == "lore"


def test_iter_due_slots_skips_disabled_platform():
    daily = {
        "x": {"enabled": False, "post_times_utc": ["08:30"]},
        "telegram": {"enabled": True, "post_times_utc": ["08:30"], "archetypes": ["stats"]},
    }
    out = list(_iter_due_slots(daily, {"x": {}, "telegram": {}}, "08:30", "2026-05-03"))
    assert len(out) == 1
    assert out[0][0] == "telegram"


def test_iter_due_slots_skips_when_minute_does_not_match():
    daily = {
        "x": {"enabled": True, "post_times_utc": ["08:30"]},
        "telegram": {"enabled": True, "post_times_utc": ["20:00"]},
    }
    out = list(_iter_due_slots(daily, {"x": {}, "telegram": {}}, "12:00", "2026-05-03"))
    assert out == []


def test_iter_due_slots_skips_when_already_fired_today():
    daily = {
        "x": {"enabled": True, "post_times_utc": ["08:30"]},
        "telegram": {"enabled": False},
    }
    fired = {"x": {"08:30": "2026-05-03"}, "telegram": {}}
    out = list(_iter_due_slots(daily, fired, "08:30", "2026-05-03"))
    assert out == []


def test_iter_due_slots_fires_again_on_new_day():
    daily = {
        "x": {"enabled": True, "post_times_utc": ["08:30"]},
        "telegram": {"enabled": False},
    }
    fired = {"x": {"08:30": "2026-05-02"}, "telegram": {}}
    out = list(_iter_due_slots(daily, fired, "08:30", "2026-05-03"))
    assert len(out) == 1
    assert out[0][0] == "x"


# =====================================================================
# _crossed_milestone
# =====================================================================
def test_crossed_milestone_returns_top_unfired():
    assert _crossed_milestone(750, [100, 500, 1000], set()) == 500
    assert _crossed_milestone(1500, [100, 500, 1000], set()) == 1000


def test_crossed_milestone_returns_none_when_below_lowest():
    assert _crossed_milestone(50, [100, 500, 1000], set()) is None


def test_crossed_milestone_returns_none_when_current_is_none():
    assert _crossed_milestone(None, [100, 500, 1000], set()) is None


def test_crossed_milestone_skips_already_fired():
    # 500 was already announced — only 100 is truly unfired.
    assert _crossed_milestone(750, [100, 500, 1000], {500}) == 100


def test_crossed_milestone_returns_none_when_all_fired():
    assert _crossed_milestone(750, [100, 500], {100, 500}) is None


def test_crossed_milestone_filters_zero_and_negative_targets():
    # Zero / negative tiers must be silently dropped.
    assert _crossed_milestone(50, [0, -1, 100], set()) is None
    assert _crossed_milestone(150, [0, -1, 100], set()) == 100


# =====================================================================
# format_mc_label
# =====================================================================
def test_format_mc_label_dollars_below_1k():
    assert format_mc_label(0) == "$0"
    assert format_mc_label(999) == "$999"


def test_format_mc_label_thousands():
    assert format_mc_label(1000) == "$1k"
    assert format_mc_label(50000) == "$50k"
    assert format_mc_label(999_999) == "$999k"


def test_format_mc_label_millions():
    assert format_mc_label(1_000_000) == "$1M"
    assert format_mc_label(2_500_000) == "$2.5M"
    assert format_mc_label(10_000_000) == "$10M"
