import pytest
from tui_wysiwyg.layout import (
    LayoutModel, Region, HSplit, VSplit, Panel, BorderRow,
    _declared_width, _declared_height,
)
from tui_wysiwyg.parser import Parser


def make_panel(row_count=None, row_count_is_pct=False, row_pct=None,
               name=None, heading=None, num_rows_def=1,
               width=None, is_pct=False, pct=None):
    return Panel(name=name, heading=heading,
                 width=width, is_pct=is_pct, pct=pct,
                 row_count=row_count, row_count_is_pct=row_count_is_pct,
                 row_pct=row_pct, num_rows_def=num_rows_def)


class TestDeclaredWidth:
    """Tests for _declared_width via Panel nodes."""

    def test_single_fill_column(self):
        p = make_panel(width=None, is_pct=False)
        assert _declared_width(p, 78, 77) == 78

    def test_two_equal_pct_columns(self):
        # pct_base for term_width=80, 2 cols: 78 - 1 = 77
        p = make_panel(is_pct=True, pct=50.0)
        assert _declared_width(p, 77, 77) == 38

    def test_fixed_width(self):
        p = make_panel(width=25)
        assert _declared_width(p, 78, 77) == 25

    def test_percentage_width(self):
        # pct_base=77, 25% → int(77 * 25 / 100) = 19
        p = make_panel(is_pct=True, pct=25.0)
        assert _declared_width(p, 77, 77) == 19

    def test_hsplit_delegates_to_child(self):
        panel = make_panel(width=25)
        node = HSplit(top=panel, bottom=None, border=None)
        assert _declared_width(node, 78, 77) == 25

    def test_vsplit_takes_all_available(self):
        node = VSplit(left=make_panel(), right=make_panel(), divider='single')
        assert _declared_width(node, 78, 77) == 78


class TestDeclaredHeight:
    """Tests for _declared_height via Panel and composite nodes."""

    def test_explicit_row_count(self):
        p = make_panel(row_count=12)
        assert _declared_height(p, 24) == 12

    def test_percentage_row_count(self):
        p = make_panel(row_count=50, row_count_is_pct=True, row_pct=50.0)
        assert _declared_height(p, 24) == 12

    def test_fallback_to_num_rows_def(self):
        p = make_panel(num_rows_def=5)
        assert _declared_height(p, 24) == 5

    def test_fallback_minimum_one(self):
        p = make_panel(num_rows_def=0)
        assert _declared_height(p, 24) == 1

    def test_hsplit_sums_children(self):
        top = make_panel(row_count=10)
        bot = make_panel(row_count=5)
        node = HSplit(top=top, bottom=bot, border=BorderRow('single', None))
        # 10 + 1 (border) + 5 = 16
        assert _declared_height(node, 24) == 16

    def test_vsplit_takes_max_child(self):
        left = make_panel(row_count=10)
        right = make_panel(row_count=5)
        node = VSplit(left=left, right=right, divider='single')
        assert _declared_height(node, 24) == 10


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
