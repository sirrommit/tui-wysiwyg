"""Tests for tui_wysiwyg.style — comment stripping and styled text."""
import pytest
from tui_wysiwyg.style import (
    strip_comments,
    parse_styled,
    styled_plain_text,
    styled_visual_len,
    render_styled,
)
from tui_wysiwyg.testing import MockTerminal


# ── strip_comments ──────────────────────────────────────────────────────────

class TestStripComments:
    def test_no_comments(self):
        text = '|=====|\n|{$x$}|\n|=====|'
        assert strip_comments(text) == text

    def test_inline_comment_removed(self):
        text = '|=== Title ===| /* a comment */\n|{$x$}|'
        result = strip_comments(text)
        assert '/*' not in result
        assert '*/' not in result
        assert 'a comment' not in result

    def test_inline_comment_preserves_other_content(self):
        text = '|=== Title ===| /* comment */\n|{$x$}|'
        result = strip_comments(text)
        assert '|=== Title ===|' in result
        assert '|{$x$}|' in result

    def test_multiline_comment_preserves_line_count(self):
        text = '|=====|\n/* line1\nline2\nline3 */\n|{$x$}|\n|=====|'
        result = strip_comments(text)
        # The comment contained 2 newlines; they must be preserved
        assert result.count('\n') == text.count('\n')

    def test_comment_only_line_becomes_empty(self):
        text = '/* just a comment */\n|=====|'
        result = strip_comments(text)
        lines = [l for l in result.split('\n') if l.strip()]
        assert lines == ['|=====|']

    def test_multiple_comments(self):
        text = '/* A */|=====|/* B */\n|{$x$ /* C */ }|'
        result = strip_comments(text)
        assert 'A' not in result
        assert 'B' not in result
        assert 'C' not in result

    def test_comment_inside_shell_def_parsed_correctly(self):
        """Parser should accept a definition with comments."""
        from tui_wysiwyg.parser import Parser
        definition = """
/* main layout */
|=== My App ===|
|{12R $menu$ }| /* menu panel */
|==============|
"""
        model = Parser().parse(definition)
        assert model.root is not None


# ── parse_styled ────────────────────────────────────────────────────────────

class TestParseStyled:
    def test_plain_text_no_tags(self):
        segments = parse_styled('hello world')
        assert len(segments) == 1
        assert segments[0] == ({}, 'hello world')

    def test_bold_tag(self):
        segments = parse_styled('<bold>text</bold>')
        assert len(segments) == 1
        attrs, chunk = segments[0]
        assert attrs.get('bold') is True
        assert chunk == 'text'

    def test_close_slash_resets(self):
        segments = parse_styled('<bold>A</>B')
        assert segments[0] == ({'bold': True}, 'A')
        assert segments[1] == ({}, 'B')

    def test_color_attr(self):
        segments = parse_styled('<color=red>text</>')
        attrs, chunk = segments[0]
        assert attrs.get('color') == 'red'
        assert chunk == 'text'

    def test_multiple_attrs(self):
        segments = parse_styled('<color=red;bg=blue;bold>text</>')
        attrs, _ = segments[0]
        assert attrs.get('color') == 'red'
        assert attrs.get('bg') == 'blue'
        assert attrs.get('bold') is True

    def test_mixed_styled_and_plain(self):
        segments = parse_styled('before <bold>middle</> after')
        assert segments[0] == ({}, 'before ')
        assert segments[1][0].get('bold') is True
        assert segments[1][1] == 'middle'
        assert segments[2] == ({}, ' after')

    def test_adjacent_styled_spans(self):
        segments = parse_styled('<bold>A</><italic>B</>')
        assert len(segments) == 2
        assert segments[0][0].get('bold') is True
        assert segments[1][0].get('italic') is True

    def test_hyphenated_key(self):
        segments = parse_styled('<bg-color=green>text</>')
        attrs, _ = segments[0]
        assert attrs.get('bg-color') == 'green'

    def test_empty_string(self):
        assert parse_styled('') == []

    def test_unclosed_tag_content_still_styled(self):
        segments = parse_styled('<bold>text')
        assert segments[0][0].get('bold') is True
        assert segments[0][1] == 'text'


# ── styled_plain_text / styled_visual_len ──────────────────────────────────

class TestStyledPlainText:
    def test_plain(self):
        assert styled_plain_text('hello') == 'hello'

    def test_strips_tags(self):
        assert styled_plain_text('<bold>hello</bold>') == 'hello'

    def test_strips_multiple_tags(self):
        assert styled_plain_text('<color=red>A</><bold>B</>C') == 'ABC'

    def test_visual_len(self):
        assert styled_visual_len('<bold>hello</bold>') == 5

    def test_visual_len_plain(self):
        assert styled_visual_len('hello world') == 11


# ── render_styled ───────────────────────────────────────────────────────────

class TestRenderStyled:
    @pytest.fixture
    def term(self):
        return MockTerminal()

    def test_plain_text_unchanged(self, term):
        assert render_styled('hello', term) == 'hello'

    def test_bold_adds_escape(self, term):
        result = render_styled('<bold>hello</>', term)
        assert '\x1b[1m' in result
        assert 'hello' in result

    def test_reset_added_after_styled(self, term):
        result = render_styled('<bold>hi</>', term)
        # normal reset must appear after the bold text
        assert result.index('\x1b[0m') > result.index('hi')

    def test_color_red(self, term):
        result = render_styled('<color=red>text</>', term)
        assert '\x1b[31m' in result
        assert 'text' in result

    def test_bg_color_blue(self, term):
        result = render_styled('<bg=blue>text</>', term)
        assert '\x1b[44m' in result

    def test_italic(self, term):
        result = render_styled('<italic>text</>', term)
        assert '\x1b[3m' in result

    def test_underline(self, term):
        result = render_styled('<underline>text</>', term)
        assert '\x1b[4m' in result

    def test_dim(self, term):
        result = render_styled('<dim>text</>', term)
        assert '\x1b[2m' in result

    def test_blink(self, term):
        result = render_styled('<blink>text</>', term)
        assert '\x1b[5m' in result

    def test_reverse(self, term):
        result = render_styled('<reverse>text</>', term)
        assert '\x1b[7m' in result

    def test_strike(self, term):
        result = render_styled('<strike>text</>', term)
        assert '\x1b[9m' in result

    def test_multiple_attrs(self, term):
        result = render_styled('<bold;color=green>text</>', term)
        assert '\x1b[1m' in result
        assert '\x1b[32m' in result
        assert 'text' in result

    def test_color_aliases_gray(self, term):
        result = render_styled('<color=gray>text</>', term)
        assert '\x1b[90m' in result   # bright_black

    def test_color_alias_purple(self, term):
        result = render_styled('<color=purple>text</>', term)
        assert '\x1b[35m' in result   # magenta

    def test_bright_color(self, term):
        result = render_styled('<color=bright_red>text</>', term)
        assert '\x1b[91m' in result

    def test_256_color_foreground(self, term):
        result = render_styled('<color=196>text</>', term)
        assert '196' in result

    def test_256_color_background(self, term):
        result = render_styled('<bg=22>text</>', term)
        assert '22' in result

    def test_max_len_truncates(self, term):
        result = render_styled('<bold>hello world</>', term, max_len=5)
        assert 'hello' in result
        assert 'world' not in result

    def test_unstyled_terminal_fallback(self, term):
        """If terminal returns empty string for an attribute, text still appears."""
        # Patch an attribute to return empty string
        term.__dict__['bold'] = ''
        result = render_styled('<bold>hello</>', term)
        assert 'hello' in result

    def test_no_bleeding_between_spans(self, term):
        """Each styled span is independently reset."""
        result = render_styled('<bold>A</><color=red>B</>', term)
        # There should be a reset between A and the red B
        assert result.count('\x1b[0m') >= 2

    def test_fg_aliases(self, term):
        """Multiple key aliases for foreground color all work."""
        for key in ('fg', 'foreground', 'fg-color', 'text-color'):
            result = render_styled(f'<{key}=red>x</>', term)
            assert '\x1b[31m' in result, f'key {key!r} did not produce red'

    def test_bg_aliases(self, term):
        """Multiple key aliases for background color all work."""
        for key in ('bg', 'background', 'bg-color', 'bgcolor', 'background-color'):
            result = render_styled(f'<{key}=green>x</>', term)
            assert '\x1b[42m' in result, f'key {key!r} did not produce on_green'


# ── integration: styled title in border row ─────────────────────────────────

class TestStyledTitleInBorder:
    def test_styled_title_rendered(self, capsys):
        from tui_wysiwyg.parser import Parser
        from tui_wysiwyg.renderer import Renderer

        term = MockTerminal(width=40, height=10)
        renderer = Renderer(term)
        model = Parser().parse("""
|=== <bold>My App</bold> ===|
|{10R $region$ }|
|============================|
""")
        regions_list = model.resolve(40, 10)
        regions = {r.name: r for r in regions_list}
        renderer.full_render(model, regions, {}, None, 40, 10)
        out = capsys.readouterr().out
        assert 'My App' in out
        assert '\x1b[1m' in out   # bold escape

    def test_unstyled_title_still_works(self, capsys):
        from tui_wysiwyg.parser import Parser
        from tui_wysiwyg.renderer import Renderer

        term = MockTerminal(width=40, height=10)
        renderer = Renderer(term)
        model = Parser().parse("""
|=== Plain Title ===|
|{10R $region$ }|
|====================|
""")
        regions_list = model.resolve(40, 10)
        regions = {r.name: r for r in regions_list}
        renderer.full_render(model, regions, {}, None, 40, 10)
        out = capsys.readouterr().out
        assert 'Plain Title' in out
