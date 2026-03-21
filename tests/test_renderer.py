import pytest
import io
import sys
from tui_wysiwyg.testing import MockTerminal
from tui_wysiwyg.renderer import Renderer
from tui_wysiwyg.layout import Region, RowGroup, BorderRow, ColumnSpec
from tui_wysiwyg.parser import Parser
from tui_wysiwyg.interactions import MenuReturn, TextBox


@pytest.fixture
def term():
    return MockTerminal(width=80, height=24)


@pytest.fixture
def renderer(term):
    return Renderer(term)


class TestRendererDrawBorder:
    def test_draw_double_border(self, renderer, capsys):
        renderer.draw_border(0, 80, 'double')
        out = capsys.readouterr().out
        assert '═' in out

    def test_draw_single_border(self, renderer, capsys):
        renderer.draw_border(0, 80, 'single')
        out = capsys.readouterr().out
        assert '─' in out

    def test_draw_border_with_title(self, renderer, capsys):
        renderer.draw_border(0, 80, 'double', title='My App')
        out = capsys.readouterr().out
        assert 'My App' in out

    def test_draw_border_correct_width(self, renderer, capsys):
        renderer.draw_border(0, 40, 'double')
        out = capsys.readouterr().out
        assert '═' in out

    def test_draw_double_border_corners_no_context(self, renderer, capsys):
        # With no adjacent row groups, the left/right chars are still fill chars
        renderer.draw_border(0, 40, 'double')
        out = capsys.readouterr().out
        assert '═' in out

    def test_draw_double_border_with_below_context(self, renderer, capsys):
        # A border at the top of the layout: next row group produces T-junction chars
        next_div = {0: 'single', 39: 'single', 20: 'single'}
        renderer.draw_border(0, 40, 'double', next_dividers=next_div)
        out = capsys.readouterr().out
        # Top-left corner for double-h, single-v below
        assert '╒' in out or '╔' in out
        # Column T-junction
        assert '╤' in out

    def test_draw_single_border_corners(self, renderer, capsys):
        prev_div = {0: 'single', 79: 'single'}
        renderer.draw_border(5, 80, 'single',
                              prev_dividers=prev_div, next_dividers=None)
        out = capsys.readouterr().out
        assert '└' in out   # bottom-left, single
        assert '┘' in out   # bottom-right, single


class TestRendererRenderRegion:
    def test_render_region_calls_interaction_render(self, renderer, term):
        region = Region(name='test', row=0, col=0, width=20, height=5)
        called = []

        class MockInteraction:
            def render(self, r, t, focused=False):
                called.append((r, t, focused))

        renderer.render_region(region, MockInteraction(), term, focused=True)
        assert len(called) == 1
        assert called[0][2] is True

    def test_render_region_unfocused(self, renderer, term):
        region = Region(name='test', row=0, col=0, width=20, height=5)
        called = []

        class MockInteraction:
            def render(self, r, t, focused=False):
                called.append(focused)

        renderer.render_region(region, MockInteraction(), term, focused=False)
        assert called[0] is False


class TestRendererFullRender:
    def test_full_render_with_menu(self, renderer, term, capsys):
        shell_def = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell_def)
        regions_list = model.resolve(80, 24)
        regions = {r.name: r for r in regions_list}
        interaction = MenuReturn({'A': 1, 'B': 2})
        interactions = {'menu': interaction}

        renderer.full_render(model, regions, interactions, 'menu', 80, 24)
        out = capsys.readouterr().out
        # Should have output something
        assert len(out) > 0

    def test_full_render_writes_border(self, renderer, term, capsys):
        shell_def = """
|=== Title ===|
|{12R $menu$ }|
|=============|
"""
        model = Parser().parse(shell_def)
        regions_list = model.resolve(80, 24)
        regions = {r.name: r for r in regions_list}
        interactions = {}

        renderer.full_render(model, regions, interactions, None, 80, 24)
        out = capsys.readouterr().out
        assert 'Title' in out


class TestMockTerminal:
    def test_width_height(self):
        term = MockTerminal(width=100, height=30)
        assert term.width == 100
        assert term.height == 30

    def test_move_returns_string(self):
        term = MockTerminal()
        result = term.move(5, 10)
        assert isinstance(result, str)
        assert '5' in result
        assert '10' in result

    def test_feed_keys_and_inkey(self):
        term = MockTerminal()
        from tui_wysiwyg.testing import make_key
        term.feed_keys(['a', 'b'])
        k1 = term.inkey()
        k2 = term.inkey()
        assert str(k1) == 'a'
        assert str(k2) == 'b'

    def test_inkey_empty_queue_returns_falsy(self):
        term = MockTerminal()
        k = term.inkey()
        assert not k

    def test_fullscreen_context_manager(self):
        term = MockTerminal()
        with term.fullscreen():
            pass  # Should not raise

    def test_cbreak_context_manager(self):
        term = MockTerminal()
        with term.cbreak():
            pass

    def test_hidden_cursor_context_manager(self):
        term = MockTerminal()
        with term.hidden_cursor():
            pass

    def test_reset_clears_buffer(self):
        term = MockTerminal()
        term.buffer.append('some text')
        term.reset()
        assert term.buffer == []

    def test_feed_key_sequence(self):
        from tui_wysiwyg.testing import make_key
        term = MockTerminal()
        term.feed_keys(['KEY_UP'])
        k = term.inkey()
        assert k.is_sequence is True
        assert k.name == 'KEY_UP'
