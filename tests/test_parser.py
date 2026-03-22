import pytest
from tui_wysiwyg.parser import Parser
from tui_wysiwyg.exceptions import ShellSyntaxError
from tui_wysiwyg.layout import LayoutModel, BorderRow, HSplit, VSplit, Panel


SIMPLE_SHELL = """
|=== My App ===|
|{50% $left$ }|{$right$ }|
|=============|
"""

SINGLE_COL_SHELL = """
|===============|
|{12R $menu$ }|
|===============|
"""

PCT_SHELL = """
|=100%=== Title ===|
|{25%  $side$ }|{  $main$ }|
|==================|
"""


# ---------------------------------------------------------------------------
# Tree traversal helpers
# ---------------------------------------------------------------------------

def collect_nodes(node, cls):
    """Collect all nodes of a given type in the tree (depth-first)."""
    if node is None:
        return []
    result = [node] if isinstance(node, cls) else []
    if isinstance(node, HSplit):
        result += collect_nodes(node.top, cls)
        result += collect_nodes(node.bottom, cls)
    elif isinstance(node, VSplit):
        result += collect_nodes(node.left, cls)
        result += collect_nodes(node.right, cls)
    return result


def collect_panels(node):
    return collect_nodes(node, Panel)


def collect_borders(node):
    """Return HSplit nodes that have a non-None border."""
    return [n for n in collect_nodes(node, HSplit) if n.border is not None]


def collect_vsplits(node):
    return collect_nodes(node, VSplit)


class TestParserValid:
    def test_parse_simple_shell(self):
        model = Parser().parse(SIMPLE_SHELL)
        assert isinstance(model, LayoutModel)

    def test_parse_yields_border_rows(self):
        model = Parser().parse(SIMPLE_SHELL)
        borders = collect_borders(model.root)
        assert len(borders) == 2

    def test_parse_yields_vsplits(self):
        model = Parser().parse(SIMPLE_SHELL)
        vsplits = collect_vsplits(model.root)
        assert len(vsplits) == 1

    def test_parse_extracts_region_names(self):
        model = Parser().parse(SIMPLE_SHELL)
        names = [p.name for p in collect_panels(model.root) if p.name]
        assert 'left' in names
        assert 'right' in names

    def test_parse_extracts_percentage_widths(self):
        model = Parser().parse(PCT_SHELL)
        assert model.has_percentage is True
        vsplit = collect_vsplits(model.root)[0]
        assert vsplit.left.is_pct is True
        assert vsplit.left.pct == 25.0

    def test_parse_fill_column(self):
        model = Parser().parse(PCT_SHELL)
        vsplit = collect_vsplits(model.root)[0]
        right = vsplit.right
        assert right.width is None
        assert right.is_pct is False

    def test_parse_row_count(self):
        model = Parser().parse(SINGLE_COL_SHELL)
        panels = collect_panels(model.root)
        named = [p for p in panels if p.name == 'menu']
        assert named[0].row_count == 12

    def test_parse_border_title(self):
        model = Parser().parse(SIMPLE_SHELL)
        borders = collect_borders(model.root)
        titles = [b.border.title for b in borders]
        assert 'My App' in titles

    def test_parse_border_style_double(self):
        model = Parser().parse(SIMPLE_SHELL)
        borders = collect_borders(model.root)
        assert any(b.border.style == 'double' for b in borders)

    def test_parse_border_style_single(self):
        shell = """
|=====|
|{$x$}|
|-----|
"""
        model = Parser().parse(shell)
        borders = collect_borders(model.root)
        single_borders = [b for b in borders if b.border.style == 'single']
        assert len(single_borders) == 1

    def test_parse_heading_text(self):
        shell = """
|=====|
|{__My Heading__ $region$}|
|=====|
"""
        model = Parser().parse(shell)
        panels = collect_panels(model.root)
        headed = [p for p in panels if p.heading == 'My Heading']
        assert len(headed) == 1

    def test_parse_empty_definition(self):
        model = Parser().parse("")
        assert model.root is None

    def test_parse_no_has_percentage(self):
        model = Parser().parse(SINGLE_COL_SHELL)
        assert model.has_percentage is False

    def test_parse_filler_rows_ignored(self):
        shell = """
|=====|
|{12R $menu$ }|
|{           }|
|{           }|
|=====|
"""
        model = Parser().parse(shell)
        panels = collect_panels(model.root)
        named = [p for p in panels if p.name == 'menu']
        assert named[0].row_count == 12

    def test_parse_example_shell(self):
        """The example.shell file must parse without errors and yield all 6 regions."""
        import os
        example_path = os.path.join(os.path.dirname(__file__), '..', 'example.shell')
        with open(example_path) as f:
            content = f.read()
        model = Parser().parse(content)
        regions = model.resolve(120, 40)
        names = {r.name for r in regions}
        assert 'sidemenu' in names
        assert 'mainmenu' in names
        assert 'info1' in names
        assert 'textbox' in names
        assert 'checkbox' in names
        assert 'text_response' in names

    def test_parse_partial_border_creates_two_panels(self):
        """A partial border in a column produces two Panel children in an HSplit."""
        shell = """\
|=====|
|{25% 6R $top$ }|{6R $right$ }|
|-----          |{            }|
|{25% 6R $bot$ }|{            }|
|=====|
"""
        model = Parser().parse(shell)
        # The left branch of the VSplit should be an HSplit with two Panel children
        vsplits = collect_vsplits(model.root)
        assert len(vsplits) >= 1
        vsplit = vsplits[0]
        left = vsplit.left
        assert isinstance(left, HSplit)
        assert isinstance(left.top, Panel)
        assert isinstance(left.bottom, Panel)
        assert left.top.name == 'top'
        assert left.bottom.name == 'bot'
        # Right child is a single Panel
        assert isinstance(vsplit.right, Panel)
        assert vsplit.right.name == 'right'


class TestParserErrors:
    def test_duplicate_region_name(self):
        shell = """
|=====|
|{$menu$}|
|{$menu$}|
|=====|
"""
        with pytest.raises(ShellSyntaxError) as exc_info:
            Parser().parse(shell)
        assert 'duplicate region name' in str(exc_info.value).lower()

    def test_missing_outer_border_left(self):
        shell = "no border here|"
        with pytest.raises(ShellSyntaxError) as exc_info:
            Parser().parse(shell)
        assert 'outer border' in str(exc_info.value).lower()

    def test_missing_outer_border_right(self):
        shell = "|no border here"
        with pytest.raises(ShellSyntaxError) as exc_info:
            Parser().parse(shell)
        assert 'outer border' in str(exc_info.value).lower()

    def test_syntax_error_has_line_number(self):
        shell = """
|=====|
|{$region$}|
|{$region$}|
|=====|
"""
        with pytest.raises(ShellSyntaxError) as exc_info:
            Parser().parse(shell)
        assert exc_info.value.line is not None

    def test_syntax_error_message_attribute(self):
        shell = "not valid"
        with pytest.raises(ShellSyntaxError) as exc_info:
            Parser().parse(shell)
        assert exc_info.value.message is not None
