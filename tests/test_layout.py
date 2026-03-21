import pytest
from tui_wysiwyg.layout import (
    LayoutModel, Region, RowGroup, BorderRow, ColumnSpec,
    _resolve_widths, _resolve_height
)
from tui_wysiwyg.parser import Parser


def make_col_spec(
    width=None,
    is_percentage=False,
    pct=None,
    row_count=None,
    row_count_is_pct=False,
    row_pct=None,
    region_name=None,
    heading_text=None,
    double_divider_right=False,
):
    return ColumnSpec(
        width=width,
        is_percentage=is_percentage,
        pct=pct,
        row_count=row_count,
        row_count_is_pct=row_count_is_pct,
        row_pct=row_pct,
        region_name=region_name,
        heading_text=heading_text,
        double_divider_right=double_divider_right,
    )


class TestResolveWidths:
    def test_single_fill_column(self):
        # One fill column in 80-char terminal: 80 - 2 borders = 78
        cols = [make_col_spec(width=None, is_percentage=False)]
        result = _resolve_widths(cols, 80)
        assert result == [78]

    def test_two_equal_pct_columns(self):
        # Two 50% columns in 80-char terminal
        # available = 80 - 2 - 1 divider = 77
        cols = [
            make_col_spec(is_percentage=True, pct=50.0),
            make_col_spec(is_percentage=True, pct=50.0),
        ]
        result = _resolve_widths(cols, 80)
        assert result[0] == 38  # int(77 * 0.5) = 38
        assert result[1] == 38

    def test_fixed_and_fill(self):
        # One 25-char column and one fill column
        # available = 80 - 2 - 1 = 77
        cols = [
            make_col_spec(width=25),
            make_col_spec(width=None),
        ]
        result = _resolve_widths(cols, 80)
        assert result[0] == 25
        assert result[1] == 52  # 77 - 25 = 52

    def test_percentage_and_fill(self):
        # 25% and fill in 80-char terminal
        # available = 80 - 2 - 1 = 77
        cols = [
            make_col_spec(is_percentage=True, pct=25.0),
            make_col_spec(width=None),
        ]
        result = _resolve_widths(cols, 80)
        pct_width = int(77 * 0.25)  # 19
        assert result[0] == pct_width
        assert result[1] == 77 - pct_width

    def test_three_columns(self):
        # Three equal 25-char columns: available = 80 - 2 - 2 dividers = 76
        cols = [
            make_col_spec(width=25),
            make_col_spec(width=25),
            make_col_spec(width=None),
        ]
        result = _resolve_widths(cols, 80)
        assert result[0] == 25
        assert result[1] == 25
        assert result[2] == 76 - 50  # 26


class TestResolveHeight:
    def test_explicit_row_count(self):
        col = make_col_spec(row_count=12)
        rg = RowGroup(columns=[col], num_text_rows=3, border_top=None, border_bottom=None)
        assert _resolve_height(rg, 24) == 12

    def test_percentage_row_count(self):
        col = make_col_spec(row_count=50, row_count_is_pct=True, row_pct=50.0)
        rg = RowGroup(columns=[col], num_text_rows=1, border_top=None, border_bottom=None)
        # 50% of 24 = 12
        assert _resolve_height(rg, 24) == 12

    def test_fallback_to_num_text_rows(self):
        col = make_col_spec()  # No row count
        rg = RowGroup(columns=[col], num_text_rows=5, border_top=None, border_bottom=None)
        assert _resolve_height(rg, 24) == 5

    def test_fallback_minimum_one(self):
        col = make_col_spec()  # No row count
        rg = RowGroup(columns=[col], num_text_rows=0, border_top=None, border_bottom=None)
        assert _resolve_height(rg, 24) == 1


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
        # Menu starts at row 1 (after border row at 0)
        assert regions[0].row == 1

    def test_resolve_region_col_position(self):
        shell = """
|=====|
|{12R $menu$ }|
|=====|
"""
        model = Parser().parse(shell)
        regions = model.resolve(80, 24)
        # Col should be 1 (after left outer border)
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
        # available = 80 - 2 - 1 = 77; 25% of 77 = 19
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
