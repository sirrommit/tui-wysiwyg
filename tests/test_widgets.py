"""Widget tests — covers Confirm, Alert, InputPrompt, ListSelect exit values.

Progress, FilePicker, and DatePicker tests are in dedicated files.
All tests run headlessly using MockTerminal with a pre-loaded key queue.
"""

import io
import sys
import pytest
from tui_wysiwyg.testing import MockTerminal, make_key
from tui_wysiwyg.widgets import Confirm, Alert, InputPrompt, ListSelect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeParent:
    """Minimal parent-shell stand-in that supplies a MockTerminal."""

    def __init__(self, term: MockTerminal):
        self.terminal = term
        self._renderer = None   # disables the restore-parent-display path


def run_widget(widget, keys, width=40):
    """Feed *keys* into a MockTerminal and call widget.show()."""
    term = MockTerminal(width=80, height=24)
    term.feed_keys(keys)
    parent = _FakeParent(term)

    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        return widget.show(parent_shell=parent)
    finally:
        sys.stdout = old


# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------

class TestConfirm:
    def test_ok_returns_true_by_default(self):
        """First item in default buttons is OK → True."""
        result = run_widget(
            Confirm(title="Test", message_lines=["Are you sure?"]),
            [make_key('KEY_ENTER')],   # focus on buttons, first item = OK
        )
        assert result is True

    def test_cancel_returns_false(self):
        result = run_widget(
            Confirm(title="Test", message_lines=[], buttons={"Yes": True, "No": False}),
            [make_key('KEY_DOWN'), make_key('KEY_ENTER')],  # move to No, select
        )
        assert result is False

    def test_escape_returns_none(self):
        result = run_widget(
            Confirm(title="Test", message_lines=[]),
            [make_key(chr(27))],
        )
        assert result is None

    def test_ctrlq_returns_none(self):
        result = run_widget(
            Confirm(title="Test", message_lines=[]),
            [make_key(chr(17))],
        )
        assert result is None

    def test_custom_buttons_return_values(self):
        result = run_widget(
            Confirm(title="Delete?", message_lines=[], buttons={"Delete": "deleted", "Keep": "kept"}),
            [make_key('KEY_ENTER')],
        )
        assert result == "deleted"

    def test_second_custom_button(self):
        result = run_widget(
            Confirm(title="Delete?", message_lines=[], buttons={"Delete": "deleted", "Keep": "kept"}),
            [make_key('KEY_DOWN'), make_key('KEY_ENTER')],
        )
        assert result == "kept"


# ---------------------------------------------------------------------------
# Alert
# ---------------------------------------------------------------------------

class TestAlert:
    def test_ok_returns_true(self):
        result = run_widget(
            Alert(title="Info", message_lines=["Done."]),
            [make_key('KEY_ENTER')],
        )
        assert result is True

    def test_escape_returns_none(self):
        result = run_widget(
            Alert(title="Info", message_lines=[]),
            [make_key(chr(27))],
        )
        assert result is None

    def test_ctrlq_returns_none(self):
        result = run_widget(
            Alert(title="Info", message_lines=[]),
            [make_key(chr(17))],
        )
        assert result is None


# ---------------------------------------------------------------------------
# InputPrompt
# ---------------------------------------------------------------------------

class TestInputPrompt:
    def _ok_keys(self, chars):
        """Type chars, then Tab to buttons, then Enter on OK."""
        return [make_key(c) for c in chars] + [make_key('\t'), make_key('KEY_ENTER')]

    def test_typed_value_returned_on_ok(self):
        result = run_widget(
            InputPrompt(title="Name", prompt_lines=["Enter name:"]),
            self._ok_keys(['h', 'i']),
            width=50,
        )
        assert result == "hi"

    def test_initial_text_pre_filled(self):
        """OK with no extra typing returns the pre-filled initial value."""
        result = run_widget(
            InputPrompt(title="Edit", initial="hello"),
            [make_key('\t'), make_key('KEY_ENTER')],
            width=50,
        )
        assert result == "hello"

    def test_cancel_returns_none(self):
        result = run_widget(
            InputPrompt(title="Name", prompt_lines=[]),
            [make_key('\t'), make_key('KEY_DOWN'), make_key('KEY_ENTER')],
            width=50,
        )
        assert result is None

    def test_escape_returns_none(self):
        result = run_widget(
            InputPrompt(title="Name", prompt_lines=[]),
            [make_key(chr(27))],
            width=50,
        )
        assert result is None

    def test_empty_input_returns_empty_string(self):
        result = run_widget(
            InputPrompt(title="Name", prompt_lines=[]),
            [make_key('\t'), make_key('KEY_ENTER')],
            width=50,
        )
        assert result == ""


# ---------------------------------------------------------------------------
# ListSelect — single mode
# ---------------------------------------------------------------------------

class TestListSelectSingle:
    def test_first_item_selected_by_enter(self):
        result = run_widget(
            ListSelect(title="Pick", items=["Red", "Green", "Blue"]),
            [make_key('KEY_ENTER')],
        )
        assert result == "Red"

    def test_navigate_then_select(self):
        result = run_widget(
            ListSelect(title="Pick", items=["Red", "Green", "Blue"]),
            [make_key('KEY_DOWN'), make_key('KEY_ENTER')],
        )
        assert result == "Green"

    def test_dict_items_return_mapped_values(self):
        result = run_widget(
            ListSelect(title="Pick", items={"Red": "#f00", "Green": "#0f0"}),
            [make_key('KEY_DOWN'), make_key('KEY_ENTER')],
        )
        assert result == "#0f0"

    def test_escape_returns_none(self):
        result = run_widget(
            ListSelect(title="Pick", items=["A", "B"]),
            [make_key(chr(27))],
        )
        assert result is None

    def test_long_list_selection_after_scroll(self):
        """Select item beyond viewport height (10 rows) — scroll must work."""
        items = [f"Item {i}" for i in range(20)]
        keys = [make_key('KEY_DOWN')] * 15 + [make_key('KEY_ENTER')]
        result = run_widget(ListSelect(title="Pick", items=items), keys)
        assert result == "Item 15"


# ---------------------------------------------------------------------------
# ListSelect — multi mode
# ---------------------------------------------------------------------------

class TestListSelectMulti:
    def _submit(self):
        """Tab to buttons (OK), press Enter."""
        return [make_key('\t'), make_key('KEY_ENTER')]

    def test_initial_state_all_unchecked(self):
        result = run_widget(
            ListSelect(title="Pick", items=["A", "B", "C"], multi=True),
            self._submit(),
        )
        assert result == {"A": False, "B": False, "C": False}

    def test_check_first_item_then_ok(self):
        keys = [make_key(' ')] + self._submit()  # space toggles first item
        result = run_widget(
            ListSelect(title="Pick", items=["A", "B", "C"], multi=True),
            keys,
        )
        assert result["A"] is True
        assert result["B"] is False

    def test_initial_checked_state_preserved(self):
        result = run_widget(
            ListSelect(title="Pick", items={"A": True, "B": False}, multi=True),
            self._submit(),
        )
        assert result["A"] is True
        assert result["B"] is False

    def test_cancel_returns_none(self):
        keys = [make_key('\t'), make_key('KEY_DOWN'), make_key('KEY_ENTER')]
        result = run_widget(
            ListSelect(title="Pick", items=["A", "B"], multi=True),
            keys,
        )
        assert result is None

    def test_escape_returns_none(self):
        result = run_widget(
            ListSelect(title="Pick", items=["A", "B"], multi=True),
            [make_key(chr(27))],
        )
        assert result is None

    def test_long_list_multi_scroll(self):
        """Navigate past viewport in multi mode — checkbox must still toggle."""
        items = {f"Opt {i}": False for i in range(15)}
        # Go down 12, toggle, then submit
        keys = ([make_key('KEY_DOWN')] * 12
                + [make_key(' ')]       # toggle item 12
                + [make_key('\t'), make_key('KEY_ENTER')])
        result = run_widget(
            ListSelect(title="Pick", items=items, multi=True),
            keys,
        )
        assert result["Opt 12"] is True
        assert result["Opt 0"] is False
