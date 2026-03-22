"""Tests for the Progress widget.

Tests cover:
- _BarInteraction state management (no I/O)
- _CancelInteraction flag behaviour (no I/O)
- Progress context manager: set_progress() updates state, cancelled flag,
  Escape/Ctrl+Q cancellation via _poll_cancel, non-cancellable mode.
"""

import io
import sys
import pytest
from tui_wysiwyg.testing import MockTerminal, make_key
from tui_wysiwyg.widgets.progress import (
    Progress,
    _BarInteraction,
    _CancelInteraction,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

class _FakeParent:
    def __init__(self, term):
        self.terminal = term
        self._renderer = None


def run_progress(total, keys, cancellable=True, title="Test", width=50):
    """Open a Progress popup, feed *keys* into _poll_cancel via set_progress,
    and return the handle so callers can inspect state."""
    term = MockTerminal(width=80, height=24)
    term.feed_keys(keys)
    parent = _FakeParent(term)
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        with Progress(title=title, total=total, cancellable=cancellable,
                      width=width).show(parent_shell=parent) as handle:
            # One set_progress call: drains one key from the queue via _poll_cancel
            handle.set_progress(1, "step 1")
            return handle
    finally:
        sys.stdout = old


# ---------------------------------------------------------------------------
# _BarInteraction unit tests (no I/O)
# ---------------------------------------------------------------------------

class TestBarInteraction:
    def test_set_value_updates_state(self):
        state = {"current": 0, "total": 100}
        bar = _BarInteraction(state)
        bar.set_value(55)
        assert state["current"] == 55

    def test_get_value_returns_current(self):
        state = {"current": 42, "total": 100}
        bar = _BarInteraction(state)
        assert bar.get_value() == 42

    def test_handle_key_returns_no_change(self):
        state = {"current": 0, "total": 100}
        bar = _BarInteraction(state)
        changed, _ = bar.handle_key(make_key('KEY_DOWN'))
        assert changed is False

    def test_is_not_focusable(self):
        bar = _BarInteraction({"current": 0, "total": 100})
        assert bar.is_focusable is False

    def test_set_value_none_is_ignored(self):
        state = {"current": 7, "total": 100}
        bar = _BarInteraction(state)
        bar.set_value(None)
        assert state["current"] == 7


# ---------------------------------------------------------------------------
# _CancelInteraction unit tests (no I/O)
# ---------------------------------------------------------------------------

class TestCancelInteraction:
    def test_initial_not_cancelled(self):
        state = {"cancelled": False}
        ci = _CancelInteraction(state)
        assert state["cancelled"] is False

    def test_enter_sets_cancelled(self):
        state = {"cancelled": False}
        ci = _CancelInteraction(state)
        ci.handle_key(make_key('KEY_ENTER'))
        assert state["cancelled"] is True

    def test_cancel_interaction_labels(self):
        state = {}
        ci = _CancelInteraction(state)
        assert "Cancel" in ci._labels


# ---------------------------------------------------------------------------
# Progress context manager tests
# ---------------------------------------------------------------------------

class TestProgress:
    def test_set_progress_updates_state(self):
        """set_progress() increments current in state."""
        term = MockTerminal(width=80, height=24)
        parent = _FakeParent(term)
        buf = io.StringIO()
        old, sys.stdout = sys.stdout, buf
        try:
            with Progress(title="T", total=10).show(parent_shell=parent) as h:
                h.set_progress(5, "halfway")
                assert h._state["current"] == 5
        finally:
            sys.stdout = old

    def test_initial_not_cancelled(self):
        """cancelled is False before any keys are fed."""
        term = MockTerminal(width=80, height=24)
        parent = _FakeParent(term)
        buf = io.StringIO()
        old, sys.stdout = sys.stdout, buf
        try:
            with Progress(title="T", total=10).show(parent_shell=parent) as h:
                assert h.cancelled is False
        finally:
            sys.stdout = old

    def test_escape_cancels(self):
        """Feeding Escape before set_progress() triggers cancellation."""
        handle = run_progress(total=10, keys=[make_key(chr(27))])
        assert handle.cancelled is True

    def test_ctrlq_cancels(self):
        """Feeding Ctrl+Q before set_progress() triggers cancellation."""
        handle = run_progress(total=10, keys=[make_key(chr(17))])
        assert handle.cancelled is True

    def test_no_cancel_when_queue_empty(self):
        """Empty key queue → cancelled stays False."""
        handle = run_progress(total=10, keys=[])
        assert handle.cancelled is False

    def test_non_cancellable_has_no_buttons(self):
        """cancellable=False creates the popup without a buttons region."""
        term = MockTerminal(width=80, height=24)
        parent = _FakeParent(term)
        buf = io.StringIO()
        old, sys.stdout = sys.stdout, buf
        try:
            with Progress(title="T", total=10, cancellable=False).show(
                parent_shell=parent
            ) as h:
                assert "buttons" not in h._popup._interactions
        finally:
            sys.stdout = old

    def test_context_manager_exits_cleanly(self):
        """Context manager __exit__ does not raise even after cancellation."""
        term = MockTerminal(width=80, height=24)
        parent = _FakeParent(term)
        buf = io.StringIO()
        old, sys.stdout = sys.stdout, buf
        try:
            with Progress(title="T", total=10).show(parent_shell=parent) as h:
                h.set_progress(3, "a")
                h.set_progress(7, "b")
        finally:
            sys.stdout = old
        # reaching here without exception = pass

    def test_cancelled_property_reflects_state(self):
        """handle.cancelled reads from state dict."""
        term = MockTerminal(width=80, height=24)
        parent = _FakeParent(term)
        buf = io.StringIO()
        old, sys.stdout = sys.stdout, buf
        try:
            with Progress(title="T", total=5).show(parent_shell=parent) as h:
                assert h.cancelled is False
                h._state["cancelled"] = True
                assert h.cancelled is True
        finally:
            sys.stdout = old
