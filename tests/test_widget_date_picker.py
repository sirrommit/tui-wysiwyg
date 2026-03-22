"""Tests for the DatePicker widget.

Focus order in the DatePicker shell: nav → calendar → buttons.
Tests must Tab to the intended region before pressing action keys.
"""

import io
import sys
import datetime
import pytest
from tui_wysiwyg.testing import MockTerminal, make_key
from tui_wysiwyg.widgets.date_picker import DatePicker, _prev_month, _next_month, _clamp_day


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

class _FakeParent:
    def __init__(self, term):
        self.terminal = term
        self._renderer = None


def run_picker(keys, initial=None, width=30):
    term = MockTerminal(width=80, height=24)
    term.feed_keys(keys)
    parent = _FakeParent(term)
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        return DatePicker(initial=initial, width=width).show(parent_shell=parent)
    finally:
        sys.stdout = old


def _tab_to_calendar():
    """One Tab moves focus from nav → calendar."""
    return [make_key('\t')]


def _tab_to_buttons():
    """Two Tabs move focus from nav → calendar → buttons."""
    return [make_key('\t'), make_key('\t')]


# ---------------------------------------------------------------------------
# Date utility function tests (no I/O)
# ---------------------------------------------------------------------------

class TestDateHelpers:
    def test_prev_month_january(self):
        d = datetime.date(2025, 1, 15)
        assert _prev_month(d) == datetime.date(2024, 12, 1)

    def test_prev_month_mid_year(self):
        assert _prev_month(datetime.date(2025, 6, 1)) == datetime.date(2025, 5, 1)

    def test_next_month_december(self):
        assert _next_month(datetime.date(2025, 12, 1)) == datetime.date(2026, 1, 1)

    def test_next_month_mid_year(self):
        assert _next_month(datetime.date(2025, 6, 1)) == datetime.date(2025, 7, 1)

    def test_clamp_day_within_month(self):
        # March 31 → April: clamp to 30
        assert _clamp_day(datetime.date(2025, 3, 31), 2025, 4) == datetime.date(2025, 4, 30)

    def test_clamp_day_no_clamp_needed(self):
        assert _clamp_day(datetime.date(2025, 3, 15), 2025, 4) == datetime.date(2025, 4, 15)

    def test_clamp_day_feb_leap_year(self):
        # Jan 31 → Feb 2024 (leap): clamp to 29
        assert _clamp_day(datetime.date(2024, 1, 31), 2024, 2) == datetime.date(2024, 2, 29)


# ---------------------------------------------------------------------------
# DatePicker widget interaction tests
# ---------------------------------------------------------------------------

class TestDatePicker:
    def test_enter_on_calendar_returns_initial_date(self):
        """Tab to calendar, Enter confirms the cursor date."""
        initial = datetime.date(2025, 6, 15)
        result = run_picker(_tab_to_calendar() + [make_key('KEY_ENTER')], initial=initial)
        assert result == initial

    def test_escape_returns_none(self):
        result = run_picker([make_key(chr(27))])
        assert result is None

    def test_ctrlq_returns_none(self):
        result = run_picker([make_key(chr(17))])
        assert result is None

    def test_right_arrow_advances_one_day(self):
        initial = datetime.date(2025, 6, 15)
        keys = _tab_to_calendar() + [make_key('KEY_RIGHT'), make_key('KEY_ENTER')]
        assert run_picker(keys, initial=initial) == datetime.date(2025, 6, 16)

    def test_left_arrow_retreats_one_day(self):
        initial = datetime.date(2025, 6, 15)
        keys = _tab_to_calendar() + [make_key('KEY_LEFT'), make_key('KEY_ENTER')]
        assert run_picker(keys, initial=initial) == datetime.date(2025, 6, 14)

    def test_down_arrow_advances_one_week(self):
        initial = datetime.date(2025, 6, 1)
        keys = _tab_to_calendar() + [make_key('KEY_DOWN'), make_key('KEY_ENTER')]
        assert run_picker(keys, initial=initial) == datetime.date(2025, 6, 8)

    def test_up_arrow_retreats_one_week(self):
        initial = datetime.date(2025, 6, 15)
        keys = _tab_to_calendar() + [make_key('KEY_UP'), make_key('KEY_ENTER')]
        assert run_picker(keys, initial=initial) == datetime.date(2025, 6, 8)

    def test_cursor_crosses_month_boundary(self):
        """Advancing past month end wraps into the next month."""
        initial = datetime.date(2025, 6, 29)
        # +4 days: Jun 30, Jul 1, Jul 2, Jul 3
        keys = _tab_to_calendar() + [make_key('KEY_RIGHT')] * 4 + [make_key('KEY_ENTER')]
        assert run_picker(keys, initial=initial) == datetime.date(2025, 7, 3)

    def test_ok_button_returns_cursor_date(self):
        """Tab × 2 → buttons → OK → returns cursor date."""
        initial = datetime.date(2025, 6, 15)
        keys = _tab_to_buttons() + [make_key('KEY_ENTER')]
        assert run_picker(keys, initial=initial) == initial

    def test_cancel_button_returns_none(self):
        """Tab × 2 → buttons → Down → Cancel → returns None."""
        initial = datetime.date(2025, 6, 15)
        keys = _tab_to_buttons() + [make_key('KEY_DOWN'), make_key('KEY_ENTER')]
        assert run_picker(keys, initial=initial) is None

    def test_result_is_datetime_date(self):
        keys = _tab_to_calendar() + [make_key('KEY_ENTER')]
        result = run_picker(keys)
        assert isinstance(result, datetime.date)
