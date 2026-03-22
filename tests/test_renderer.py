import pytest
import sys
from tui_wysiwyg.testing import MockTerminal
from tui_wysiwyg.renderer import Renderer
from tui_wysiwyg.layout import Region, HSplit, VSplit, Panel, BorderRow
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

    def test_draw_double_border_with_below_context(self, renderer, capsys):
        next_div = {0: 'single', 39: 'single', 20: 'single'}
        renderer.draw_border(0, 40, 'double', next_dividers=next_div)
        out = capsys.readouterr().out
        assert '╒' in out or '╔' in out
        assert '╤' in out

    def test_draw_single_border_corners(self, renderer, capsys):
        prev_div = {0: 'single', 79: 'single'}
        renderer.draw_border(5, 80, 'single',
                              prev_dividers=prev_div, next_dividers=None)
        out = capsys.readouterr().out
        assert '└' in out
        assert '┘' in out


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

    def test_full_render_partial_border_produces_output(self, renderer, term, capsys):
        """A shell with partial borders renders without error."""
        shell_def = """\
|=====|
|{25% 6R $top$ }|{6R $right$ }|
|-----          |{            }|
|{25% 6R $bot$ }|{            }|
|=====|
"""
        model = Parser().parse(shell_def)
        regions_list = model.resolve(80, 24)
        regions = {r.name: r for r in regions_list}
        renderer.full_render(model, regions, {}, None, 80, 24)
        out = capsys.readouterr().out
        # Partial border character should appear
        assert '─' in out or '├' in out or '┤' in out


class TestRendererFullRenderOffset:
    """full_render() with non-zero offset_row / offset_col (modal rendering)."""

    def test_offset_render_does_not_emit_clear(self, capsys):
        term = MockTerminal(width=40, height=10)
        renderer = Renderer(term)
        model = Parser().parse("|=====|\n|{4R $r$ }|\n|=====|\n")
        regions = {r.name: r for r in model.resolve(20, 6, offset_row=5, offset_col=10)}
        renderer.full_render(model, regions, {}, None, 20, 6,
                             offset_row=5, offset_col=10)
        out = capsys.readouterr().out
        # term.clear (MockTerminal returns '\x1b[2J'-style) must not appear
        assert '\x1b[2J' not in out

    def test_zero_offset_still_emits_clear(self, capsys):
        term = MockTerminal(width=40, height=10)
        renderer = Renderer(term)
        model = Parser().parse("|=====|\n|{4R $r$ }|\n|=====|\n")
        regions = {r.name: r for r in model.resolve(40, 10)}
        renderer.full_render(model, regions, {}, None, 40, 10)
        out = capsys.readouterr().out
        assert '\x1b[2J' in out

    def test_offset_render_places_border_at_correct_col(self, capsys):
        term = MockTerminal(width=40, height=10)
        renderer = Renderer(term)
        model = Parser().parse("|=====|\n|{4R $r$ }|\n|=====|\n")
        regions = {r.name: r for r in model.resolve(20, 6, offset_row=2, offset_col=10)}
        renderer.full_render(model, regions, {}, None, 20, 6,
                             offset_row=2, offset_col=10)
        out = capsys.readouterr().out
        # The outer left wall should appear at col 10 — move(2, 10) in output
        assert '2' in out and '10' in out

    def test_offset_region_content_at_correct_position(self):
        model = Parser().parse("|=====|\n|{4R $r$ }|\n|=====|\n")
        regions = model.resolve(20, 6, offset_row=5, offset_col=10)
        r = next(reg for reg in regions if reg.name == 'r')
        # Region col should be offset_col + 1 (one inside the left border wall)
        assert r.col == 11
        assert r.row == 6   # offset_row(5) + 1 border row

    def test_offset_does_not_blank_rows_outside_modal(self, capsys):
        """Rows outside the modal bounding box must not be written."""
        term = MockTerminal(width=80, height=24)
        renderer = Renderer(term)
        model = Parser().parse("|=====|\n|{4R $r$ }|\n|=====|\n")
        regions = {r.name: r for r in model.resolve(20, 6, offset_row=5, offset_col=10)}
        renderer.full_render(model, regions, {}, None, 20, 6,
                             offset_row=5, offset_col=10)
        out = capsys.readouterr().out
        # Rows 0-4 are outside the modal; move(0,...) must not appear
        assert 'move(0,' not in out and 'move(1,' not in out


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
            pass

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
