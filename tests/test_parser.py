import pytest
from tui_wysiwyg.parser import Parser
from tui_wysiwyg.exceptions import ShellSyntaxError
from tui_wysiwyg.layout import LayoutModel, BorderRow, RowGroup


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
        parser = Parser()
        model = parser.parse(SIMPLE_SHELL)
        assert isinstance(model, LayoutModel)

    def test_parse_yields_border_rows(self):
        parser = Parser()
        model = parser.parse(SIMPLE_SHELL)
        border_rows = [r for r in model.rows if isinstance(r, BorderRow)]
        assert len(border_rows) == 2

    def test_parse_yields_row_groups(self):
        parser = Parser()
        model = parser.parse(SIMPLE_SHELL)
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        assert len(row_groups) == 1

    def test_parse_extracts_region_names(self):
        parser = Parser()
        model = parser.parse(SIMPLE_SHELL)
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        names = [col.region_name for rg in row_groups for col in rg.columns if col.region_name]
        assert 'left' in names
        assert 'right' in names

    def test_parse_extracts_percentage_widths(self):
        parser = Parser()
        model = parser.parse(PCT_SHELL)
        assert model.has_percentage is True
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        assert row_groups[0].columns[0].is_percentage is True
        assert row_groups[0].columns[0].pct == 25.0

    def test_parse_fill_column(self):
        parser = Parser()
        model = parser.parse(PCT_SHELL)
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        # Second column has no width - should be fill
        assert row_groups[0].columns[1].width is None
        assert row_groups[0].columns[1].is_percentage is False

    def test_parse_row_count(self):
        parser = Parser()
        model = parser.parse(SINGLE_COL_SHELL)
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        assert row_groups[0].columns[0].row_count == 12

    def test_parse_border_title(self):
        parser = Parser()
        model = parser.parse(SIMPLE_SHELL)
        borders = [r for r in model.rows if isinstance(r, BorderRow)]
        assert borders[0].title == 'My App'

    def test_parse_border_style_double(self):
        parser = Parser()
        model = parser.parse(SIMPLE_SHELL)
        borders = [r for r in model.rows if isinstance(r, BorderRow)]
        assert borders[0].style == 'double'

    def test_parse_border_style_single(self):
        shell = """
|=====|
|{$x$}|
|-----|
"""
        parser = Parser()
        model = parser.parse(shell)
        borders = [r for r in model.rows if isinstance(r, BorderRow)]
        single_borders = [b for b in borders if b.style == 'single']
        assert len(single_borders) == 1

    def test_parse_heading_text(self):
        shell = """
|=====|
|{__My Heading__ $region$}|
|=====|
"""
        parser = Parser()
        model = parser.parse(shell)
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        col = row_groups[0].columns[0]
        assert col.heading_text == 'My Heading'

    def test_parse_empty_definition(self):
        parser = Parser()
        model = parser.parse("")
        assert model.rows == []

    def test_parse_no_has_percentage(self):
        parser = Parser()
        model = parser.parse(SINGLE_COL_SHELL)
        assert model.has_percentage is False

    def test_parse_filler_rows_ignored(self):
        shell = """
|=====|
|{12R $menu$ }|
|{           }|
|{           }|
|=====|
"""
        parser = Parser()
        model = parser.parse(shell)
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        # Row count should still be 12 from first content row
        assert row_groups[0].columns[0].row_count == 12

    def test_parse_example_shell(self):
        """Test that the example.shell file parses without errors."""
        import os
        example_path = os.path.join(os.path.dirname(__file__), '..', 'example.shell')
        with open(example_path) as f:
            content = f.read()
        parser = Parser()
        model = parser.parse(content)
        # Should have multiple row groups
        row_groups = [r for r in model.rows if isinstance(r, RowGroup)]
        assert len(row_groups) > 0


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
        # Line number should be set
        assert exc_info.value.line is not None

    def test_syntax_error_message_attribute(self):
        shell = "not valid"
        with pytest.raises(ShellSyntaxError) as exc_info:
            Parser().parse(shell)
        assert exc_info.value.message is not None
