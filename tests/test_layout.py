import pytest
from tui_wysiwyg.layout import (
    LayoutModel, Region, VSplit, BorderRow, ColumnDef, Panel, PartialBorder,
    _resolve_col_widths, _resolve_panel_heights,
)
from tui_wysiwyg.parser import Parser


def make_panel(row_count=None, row_count_is_pct=False, row_pct=None,
               name=None, heading=None, num_rows_def=1):
    return Panel(name=name, row_count=row_count, row_count_is_pct=row_count_is_pct,
                 row_pct=row_pct, heading=heading, num_rows_def=num_rows_def)


def make_col(width=None, is_percentage=False, pct=None,
             panels=None, partial_borders=None,
             double_divider_right=False):
    return ColumnDef(
        width=width,
        is_percentage=is_percentage,
        pct=pct,
        double_divider_right=double_divider_right,
        panels=panels or [make_panel()],
        partial_borders=partial_borders or [],
    )


class TestResolveColWidths:
    def test_single_fill_column(self):
        cols = [make_col(width=None, is_percentage=False)]
        result = _resolve_col_widths(cols, 80)
        assert result == [78]

    def test_two_equal_pct_columns(self):
        cols = [
            make_col(is_percentage=True, pct=50.0),
            make_col(is_percentage=True, pct=50.0),
        ]
        result = _resolve_col_widths(cols, 80)
        assert result[0] == 38
        assert result[1] == 38

    def test_fixed_and_fill(self):
        cols = [make_col(width=25), make_col(width=None)]
        result = _resolve_col_widths(cols, 80)
        assert result[0] == 25
        assert result[1] == 52

    def test_percentage_and_fill(self):
        cols = [
            make_col(is_percentage=True, pct=25.0),
            make_col(width=None),
        ]
        result = _resolve_col_widths(cols, 80)
        pct_width = int(77 * 0.25)
        assert result[0] == pct_width
        assert result[1] == 77 - pct_width

    def test_three_columns(self):
        cols = [make_col(width=25), make_col(width=25), make_col(width=None)]
        result = _resolve_col_widths(cols, 80)
        assert result[0] == 25
        assert result[1] == 25
        assert result[2] == 76 - 50


class TestResolvePanelHeights:
    def test_explicit_row_count(self):
        col = make_col(panels=[make_panel(row_count=12)])
        result = _resolve_panel_heights(col, 24)
        assert result == [12]

    def test_percentage_row_count(self):
        col = make_col(panels=[make_panel(row_count=50, row_count_is_pct=True, row_pct=50.0)])
        result = _resolve_panel_heights(col, 24)
        assert result == [12]

    def test_fallback_to_num_rows_def(self):
        col = make_col(panels=[make_panel(num_rows_def=5)])
        result = _resolve_panel_heights(col, 24)
        assert result == [5]

    def test_fallback_minimum_one(self):
        col = make_col(panels=[make_panel(num_rows_def=0)])
        result = _resolve_panel_heights(col, 24)
        assert result == [1]

    def test_multiple_panels(self):
        col = make_col(panels=[
            make_panel(row_count=10),
            make_panel(row_count=5),
        ])
        result = _resolve_panel_heights(col, 24)
        assert result == [10, 5]


class TestLayoutModelResolve:
    def test_resolve_simple_shell(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert len(regions) == 1
        assert regions[0].name == 'menu'
        assert regions[0].height == 12

    def test_resolve_two_columns(self):
        shell = """
|=====|
|{50% 12R $left$ }|{12R $right$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        names = {r.name for r in regions}
        assert 'left' in names
        assert 'right' in names

    def test_resolve_border_advances_row(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert regions[0].row == 1

    def test_resolve_region_col_position(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert regions[0].col == 1

    def test_resolve_percentage_width(self):
        shell = """
|=====|
|{25% 12R $side$ }|{ 12R $main$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        side = next(r for r in regions if r.name == 'side')
        assert side.width == 19

    def test_resolve_unnamed_columns_excluded(self):
        shell = """
|=====|
|{12R unnamed_col }|{12R $named$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        assert all(r.name == 'named' for r in regions)
        assert len(regions) == 1

    def test_region_is_frozen(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        with pytest.raises((AttributeError, TypeError)):
            regions[0].name = 'changed'

    def test_resolve_partial_border_split(self):
        """Columns with a partial border produce two separate regions."""
        shell = """\
|=====|
|{25% 12R $top$ }|{12R $right$ }|
|-----           |{             }|
|{25% 12R $bot$ }|{             }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        names = {r.name: r for r in regions}
        assert 'top' in names
        assert 'bot' in names
        assert 'right' in names
        # top and bot should be at different rows
        assert names['top'].row != names['bot'].row
        # right should span from where top is to below bot (height = top + pb + bot)
        assert names['right'].height == names['top'].height + 1 + names['bot'].height

    def test_partial_border_col_height_stretch(self):
        """A column without a partial border stretches to match split column."""
        shell = """\
|=====|
|{25%  8R $a$ }|{ 6R $b$ }|
|---           |{         }|
|{25%  8R $c$ }|{         }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        names = {r.name: r for r in regions}
        # Col 0: 8 + pb + 8 = 17 total height; col 1 stretches to 17
        assert names['b'].height == 17
