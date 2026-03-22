"""Tests for Shell.run_modal() — modal popup shells."""
import pytest
from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import MenuReturn
from tui_wysiwyg.testing import MockTerminal, make_key
from tui_wysiwyg.renderer import Renderer


POPUP_DEF = """\
|=== Confirm? ===|
|{$choice$       }|
|================|
"""

PARENT_DEF = """\
|=====|
|{8R $menu$ }|
|=====|
"""


@pytest.fixture
def term():
    return MockTerminal(width=80, height=24)


@pytest.fixture
def parent(term):
    s = Shell(PARENT_DEF, _terminal=term)
    s.assign("menu", MenuReturn({"A": 1, "B": 2}))
    return s


def _popup(term):
    p = Shell(POPUP_DEF, _terminal=term)
    p.assign("choice", MenuReturn({"Yes": True, "No": False}))
    return p


class TestRunModal:
    def test_run_modal_method_exists(self, term):
        popup = _popup(term)
        assert callable(getattr(popup, "run_modal", None))

    def test_run_modal_returns_value_on_selection(self, term):
        popup = _popup(term)
        term.feed_keys(["KEY_ENTER"])   # select "Yes" (first item → True)
        result = popup.run_modal(row=5, col=10, width=20, height=4)
        assert result is True

    def test_run_modal_returns_none_on_escape(self, term):
        popup = _popup(term)
        term.feed_keys(["\x1b"])
        result = popup.run_modal(row=5, col=10, width=20, height=4)
        assert result is None

    def test_run_modal_returns_none_on_ctrl_q(self, term):
        popup = _popup(term)
        term.feed_keys([chr(17)])
        result = popup.run_modal(row=5, col=10, width=20, height=4)
        assert result is None

    def test_run_modal_regions_within_modal_bounds(self, term):
        popup = _popup(term)
        row, col, width, height = 5, 10, 20, 4
        popup._resolve_layout(width=width, height=height,
                              offset_row=row, offset_col=col)
        for region in popup._regions.values():
            assert region.row >= row
            assert region.col >= col + 1
            assert region.col + region.width <= col + width
            assert region.row + region.height <= row + height

    def test_run_modal_does_not_enter_fullscreen(self, term):
        entered = []
        _orig = term.fullscreen

        class _TrackingCtx:
            def __enter__(self_cm):
                entered.append(True)
                return self_cm
            def __exit__(self_cm, *a):
                pass

        term.fullscreen = lambda: _TrackingCtx()
        popup = _popup(term)
        term.feed_keys(["\x1b"])
        popup.run_modal(row=5, col=10, width=20, height=4)
        term.fullscreen = _orig
        assert entered == [], "run_modal must not enter fullscreen()"

    def test_run_modal_restores_parent(self, term, parent, capsys):
        # Give the parent a live renderer (as if run() had set it up).
        parent._renderer = Renderer(term)

        popup = _popup(term)
        term.feed_keys(["\x1b"])
        popup.run_modal(row=5, col=10, width=20, height=4, parent_shell=parent)

        out = capsys.readouterr().out
        # After dismiss, parent full_render fires term.clear ('\x1b[2J')
        assert "\x1b[2J" in out

    def test_run_modal_second_item_returns_false(self, term):
        popup = _popup(term)
        term.feed_keys(["KEY_DOWN", "KEY_ENTER"])   # move to "No" → False
        result = popup.run_modal(row=5, col=10, width=20, height=4)
        assert result is False
