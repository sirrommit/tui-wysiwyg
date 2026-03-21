import pytest
from tui_wysiwyg.parser import Parser
from tui_wysiwyg.exceptions import ShellSyntaxError
from tui_wysiwyg.layout import LayoutModel, BorderRow, VSplit


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


class TestParserValid:
    def test_parse_simple_shell(self):
        model = Parser().parse(SIMPLE_SHELL)
        assert isinstance(model, LayoutModel)

    def test_parse_yields_border_rows(self):
        model = Parser().parse(SIMPLE_SHELL)
        border_rows = [r for r in model.items if isinstance(r, BorderRow)]
        assert len(border_rows) == 2

    def test_parse_yields_vsplits(self):
        model = Parser().parse(SIMPLE_SHELL)
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        assert len(vsplits) == 1

    def test_parse_extracts_region_names(self):
        model = Parser().parse(SIMPLE_SHELL)
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        names = []
        for vs in vsplits:
            for col in vs.columns:
                for panel in col.panels:
                    if panel.name:
                        names.append(panel.name)
        assert 'left' in names
        assert 'right' in names

    def test_parse_extracts_percentage_widths(self):
        model = Parser().parse(PCT_SHELL)
        assert model.has_percentage is True
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        assert vsplits[0].columns[0].is_percentage is True
        assert vsplits[0].columns[0].pct == 25.0

    def test_parse_fill_column(self):
        model = Parser().parse(PCT_SHELL)
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        col1 = vsplits[0].columns[1]
        assert col1.width is None
        assert col1.is_percentage is False

    def test_parse_row_count(self):
        model = Parser().parse(SINGLE_COL_SHELL)
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        assert vsplits[0].columns[0].panels[0].row_count == 12

    def test_parse_border_title(self):
        model = Parser().parse(SIMPLE_SHELL)
        borders = [r for r in model.items if isinstance(r, BorderRow)]
        assert borders[0].title == 'My App'

    def test_parse_border_style_double(self):
        model = Parser().parse(SIMPLE_SHELL)
        borders = [r for r in model.items if isinstance(r, BorderRow)]
        assert borders[0].style == 'double'

    def test_parse_border_style_single(self):
        shell = """
|=====|
|{$x$}|
|-----|
"""
        model = Parser().parse(shell)
        borders = [r for r in model.items if isinstance(r, BorderRow)]
        single_borders = [b for b in borders if b.style == 'single']
        assert len(single_borders) == 1

    def test_parse_heading_text(self):
        shell = """
|=====|
|{__My Heading__ $region$}|
|=====|
"""
        model = Parser().parse(shell)
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        col = vsplits[0].columns[0]
        assert col.panels[0].heading == 'My Heading'

    def test_parse_empty_definition(self):
        model = Parser().parse("")
        assert model.items == []

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
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        assert vsplits[0].columns[0].panels[0].row_count == 12

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
        """A partial border in a column should produce two panels in that column."""
        shell = """\
|=====|
|{25% 6R $top$ }|{6R $right$ }|
|-----          |{            }|
|{25% 6R $bot$ }|{            }|
|=====|
"""
        model = Parser().parse(shell)
        vsplits = [r for r in model.items if isinstance(r, VSplit)]
        col0 = vsplits[0].columns[0]
        assert len(col0.panels) == 2
        assert len(col0.partial_borders) == 1
        assert col0.panels[0].name == 'top'
        assert col0.panels[1].name == 'bot'
        # Column 1 has no partial border
        col1 = vsplits[0].columns[1]
        assert len(col1.panels) == 1
        assert len(col1.partial_borders) == 0


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
