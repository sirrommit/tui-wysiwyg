import pytest
from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import MenuReturn, MenuFunction, TextBox, CheckBox
from tui_wysiwyg.exceptions import RegionNotFoundError, CircularUpdateError
from tui_wysiwyg.testing import MockTerminal


SIMPLE_SHELL = """
|=====|
|{12R $menu$ }|
|=====|
"""

TWO_REGION_SHELL = """
|=====|
|{12R $left$ }|{12R $right$ }|
|=====|
"""


@pytest.fixture
def mock_term():
    return MockTerminal(width=80, height=24)


@pytest.fixture
def shell(mock_term):
    return Shell(SIMPLE_SHELL, _terminal=mock_term)


@pytest.fixture
def two_region_shell(mock_term):
    return Shell(TWO_REGION_SHELL, _terminal=mock_term)


class TestShellAssign:
    def test_assign_interaction(self, shell):
        m = MenuReturn({'A': 1, 'B': 2})
        shell.assign('menu', m)
        # Should not raise

    def test_assign_nonexistent_region_raises(self, shell):
        m = MenuReturn({'A': 1})
        with pytest.raises(RegionNotFoundError):
            shell.assign('nonexistent', m)

    def test_assign_twice_raises(self, shell):
        m1 = MenuReturn({'A': 1})
        m2 = MenuReturn({'B': 2})
        shell.assign('menu', m1)
        with pytest.raises(ValueError):
            shell.assign('menu', m2)

    def test_assign_sets_shell_reference(self, shell):
        m = MenuReturn({'A': 1})
        shell.assign('menu', m)
        assert m._shell is shell


class TestShellUnassign:
    def test_unassign_returns_interaction(self, shell):
        m = MenuReturn({'A': 1})
        shell.assign('menu', m)
        result = shell.unassign('menu')
        assert result is m

    def test_unassign_nonexistent_returns_none(self, shell):
        result = shell.unassign('menu')
        assert result is None

    def test_unassign_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.unassign('ghost')

    def test_unassign_allows_reassign(self, shell):
        m1 = MenuReturn({'A': 1})
        m2 = MenuReturn({'B': 2})
        shell.assign('menu', m1)
        shell.unassign('menu')
        shell.assign('menu', m2)  # Should not raise


class TestShellGet:
    def test_get_value_after_assign(self, shell):
        m = MenuReturn({'A': 1, 'B': 2})
        shell.assign('menu', m)
        val = shell.get('menu')
        assert val == 'A'  # First item selected by default

    def test_get_unassigned_region_returns_none(self, shell):
        val = shell.get('menu')
        assert val is None

    def test_get_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.get('ghost')


class TestShellUpdate:
    def test_update_changes_value(self, shell):
        m = MenuReturn({'A': 1, 'B': 2})
        shell.assign('menu', m)
        shell.update('menu', 'B')
        assert shell.get('menu') == 'B'

    def test_update_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.update('ghost', 'value')

    def test_update_unassigned_region_silent(self, shell):
        # No interaction assigned - update should silently do nothing
        shell.update('menu', 'value')


class TestShellOnChange:
    def test_on_change_fires_callback(self, shell):
        m = TextBox()
        shell.assign('menu', m)
        received = []
        shell.on_change('menu', lambda v: received.append(v))
        shell.update('menu', 'hello')
        assert received == ['hello']

    def test_on_change_returns_handle(self, shell):
        shell.assign('menu', MenuReturn({'A': 1}))
        handle = shell.on_change('menu', lambda v: None)
        assert hasattr(handle, 'remove')

    def test_on_change_handle_remove(self, shell):
        m = TextBox()
        shell.assign('menu', m)
        received = []
        handle = shell.on_change('menu', lambda v: received.append(v))
        handle.remove()
        shell.update('menu', 'test')
        assert received == []

    def test_on_change_nonexistent_region_raises(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.on_change('ghost', lambda v: None)


class TestShellBind:
    def test_bind_propagates_value(self, two_region_shell):
        sh = two_region_shell
        left = TextBox()
        right = TextBox()
        sh.assign('left', left)
        sh.assign('right', right)
        sh.bind('left', 'right')
        sh.update('left', 'hello')
        assert sh.get('right') == 'hello'

    def test_bind_with_transform(self, two_region_shell):
        sh = two_region_shell
        left = TextBox()
        right = TextBox()
        sh.assign('left', left)
        sh.assign('right', right)
        sh.bind('left', 'right', transform=lambda v: v.upper())
        sh.update('left', 'hello')
        assert sh.get('right') == 'HELLO'

    def test_bind_nonexistent_source_raises(self, two_region_shell):
        with pytest.raises(RegionNotFoundError):
            two_region_shell.bind('ghost', 'left')

    def test_bind_nonexistent_target_raises(self, two_region_shell):
        with pytest.raises(RegionNotFoundError):
            two_region_shell.bind('left', 'ghost')

    def test_circular_bind_raises(self, two_region_shell):
        sh = two_region_shell
        left = TextBox()
        right = TextBox()
        sh.assign('left', left)
        sh.assign('right', right)
        sh.bind('left', 'right')
        sh.bind('right', 'left')
        with pytest.raises(CircularUpdateError):
            sh.update('left', 'test')


class TestShellFocus:
    def test_set_focus(self, two_region_shell):
        sh = two_region_shell
        sh.assign('left', MenuReturn({'A': 1}))
        sh.assign('right', MenuReturn({'B': 2}))
        sh.set_focus('right')
        assert sh.focus == 'right'

    def test_set_focus_nonexistent_raises(self, two_region_shell):
        with pytest.raises(RegionNotFoundError):
            two_region_shell.set_focus('ghost')

    def test_set_focus_unassigned_raises(self, two_region_shell):
        with pytest.raises(ValueError):
            two_region_shell.set_focus('left')

    def test_focus_property_initially_none(self, shell):
        assert shell.focus is None


class TestShellProperties:
    def test_terminal_property(self, shell, mock_term):
        assert shell.terminal is mock_term

    def test_focus_property(self, shell):
        assert shell.focus is None


class TestShellRegionNotFound:
    def test_all_methods_raise_on_bad_name(self, shell):
        with pytest.raises(RegionNotFoundError):
            shell.assign('bad', MenuReturn({'A': 1}))
        with pytest.raises(RegionNotFoundError):
            shell.unassign('bad')
        with pytest.raises(RegionNotFoundError):
            shell.get('bad')
        with pytest.raises(RegionNotFoundError):
            shell.update('bad', 'val')
        with pytest.raises(RegionNotFoundError):
            shell.on_change('bad', lambda v: None)
        with pytest.raises(RegionNotFoundError):
            shell.set_focus('bad')
