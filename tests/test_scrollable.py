"""Tests for _ScrollableList scroll behaviour in menu and checkbox interactions."""

import io
import sys
import pytest
from tui_wysiwyg.testing import MockTerminal, make_key
from tui_wysiwyg.interactions import MenuFunction, MenuReturn, MenuHybrid, CheckBox
from tui_wysiwyg.layout import Region


@pytest.fixture
def term():
    return MockTerminal(width=80, height=24)


def small_region(height):
    """Region that shows only *height* rows at a time."""
    return Region(name='test', row=0, col=0, width=40, height=height)


def make_labels(n):
    """Return a dict with n labelled items suitable for MenuReturn."""
    return {f'Item {i}': i for i in range(n)}


# ---------------------------------------------------------------------------
# Helper: force a render so _last_height is set
# ---------------------------------------------------------------------------

def prime(interaction, height):
    """Render into a small region so _last_height is stored."""
    buf = io.StringIO()
    region = small_region(height)
    old, sys.stdout = sys.stdout, buf
    try:
        interaction.render(region, MockTerminal(width=80, height=24), focused=False)
    finally:
        sys.stdout = old
    return interaction


# ---------------------------------------------------------------------------
# MenuReturn scrolling
# ---------------------------------------------------------------------------

class TestMenuReturnScroll:
    def test_scroll_offset_advances_when_active_passes_viewport(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)              # viewport = 3 rows
        for _ in range(4):       # move down 4 times
            m.handle_key(make_key('KEY_DOWN'))
        # active = 4, viewport height = 3 → offset must be at least 2
        assert m._scroll_offset >= 2
        assert m._active_index - m._scroll_offset < 3

    def test_active_always_within_viewport(self):
        m = MenuReturn(make_labels(20))
        prime(m, 5)
        for _ in range(19):
            m.handle_key(make_key('KEY_DOWN'))
        assert m._active_index == 19
        assert m._scroll_offset <= 19
        assert m._active_index - m._scroll_offset < 5

    def test_scroll_offset_decreases_when_scrolling_up(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)
        for _ in range(9):       # go to bottom
            m.handle_key(make_key('KEY_DOWN'))
        for _ in range(9):       # go back to top
            m.handle_key(make_key('KEY_UP'))
        assert m._active_index == 0
        assert m._scroll_offset == 0

    def test_scroll_offset_zero_for_short_list(self):
        m = MenuReturn(make_labels(3))
        prime(m, 5)              # viewport larger than list
        m.handle_key(make_key('KEY_DOWN'))
        m.handle_key(make_key('KEY_DOWN'))
        assert m._scroll_offset == 0

    def test_j_k_navigation_scrolls(self):
        m = MenuReturn(make_labels(10))
        prime(m, 3)
        for _ in range(5):
            m.handle_key(make_key('j'))
        assert m._active_index == 5
        assert m._active_index - m._scroll_offset < 3
        for _ in range(5):
            m.handle_key(make_key('k'))
        assert m._active_index == 0
        assert m._scroll_offset == 0


# ---------------------------------------------------------------------------
# MenuFunction scrolling
# ---------------------------------------------------------------------------

class TestMenuFunctionScroll:
    def test_scroll_offset_advances(self):
        calls = []
        items = {f'Action {i}': (lambda i=i: calls.append(i)) for i in range(10)}
        m = MenuFunction(items)
        prime(m, 3)
        for _ in range(6):
            m.handle_key(make_key('KEY_DOWN'))
        assert m._active_index == 6
        assert m._active_index - m._scroll_offset < 3

    def test_scroll_stays_zero_for_small_list(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        prime(m, 5)
        m.handle_key(make_key('KEY_DOWN'))
        assert m._scroll_offset == 0


# ---------------------------------------------------------------------------
# MenuHybrid scrolling
# ---------------------------------------------------------------------------

class TestMenuHybridScroll:
    def test_scroll_offset_advances(self):
        items = {f'Item {i}': i for i in range(10)}
        m = MenuHybrid(items)
        prime(m, 4)
        for _ in range(8):
            m.handle_key(make_key('KEY_DOWN'))
        assert m._active_index == 8
        assert m._active_index - m._scroll_offset < 4


# ---------------------------------------------------------------------------
# CheckBox scrolling
# ---------------------------------------------------------------------------

class TestCheckBoxScroll:
    def test_scroll_offset_advances(self):
        items = {f'Option {i}': False for i in range(10)}
        c = CheckBox(items)
        prime(c, 3)
        for _ in range(6):
            c.handle_key(make_key('KEY_DOWN'))
        assert c._active_index == 6
        assert c._active_index - c._scroll_offset < 3

    def test_toggle_out_of_viewport_does_not_crash(self):
        """Toggling an item that is off-screen should not raise."""
        items = {f'Opt {i}': False for i in range(10)}
        c = CheckBox(items)
        prime(c, 3)
        for _ in range(7):
            c.handle_key(make_key('KEY_DOWN'))
        changed, val = c.handle_key(make_key('KEY_ENTER'))
        assert changed is True
        assert val[f'Opt {c._active_index}'] is True

    def test_scroll_up_restores_offset_to_zero(self):
        items = {f'O{i}': False for i in range(8)}
        c = CheckBox(items)
        prime(c, 3)
        for _ in range(7):
            c.handle_key(make_key('KEY_DOWN'))
        for _ in range(7):
            c.handle_key(make_key('KEY_UP'))
        assert c._active_index == 0
        assert c._scroll_offset == 0


# ---------------------------------------------------------------------------
# Render output — active item is inside the rendered lines
# ---------------------------------------------------------------------------

class TestScrollRender:
    def test_active_item_rendered_after_scroll(self):
        m = MenuReturn(make_labels(10))
        region = small_region(3)
        buf = io.StringIO()
        # Navigate to item 5
        prime(m, 3)
        for _ in range(5):
            m.handle_key(make_key('KEY_DOWN'))
        # Render and check that 'Item 5' appears in output
        old, sys.stdout = sys.stdout, buf
        try:
            m.render(region, MockTerminal(width=80, height=24), focused=True)
        finally:
            sys.stdout = old
        assert 'Item 5' in buf.getvalue()

    def test_first_item_not_rendered_after_scroll(self):
        m = MenuReturn(make_labels(10))
        region = small_region(3)
        buf = io.StringIO()
        prime(m, 3)
        for _ in range(5):
            m.handle_key(make_key('KEY_DOWN'))
        old, sys.stdout = sys.stdout, buf
        try:
            m.render(region, MockTerminal(width=80, height=24), focused=False)
        finally:
            sys.stdout = old
        assert 'Item 0' not in buf.getvalue()
