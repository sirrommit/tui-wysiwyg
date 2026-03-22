import pytest
import io
import sys
from tui_wysiwyg.testing import MockTerminal, make_key
from tui_wysiwyg.interactions import (
    MenuFunction, MenuReturn, MenuHybrid,
    TextBox, ListView, SubList, CheckBox, Function, FormInput
)
from tui_wysiwyg.layout import Region


@pytest.fixture
def term():
    return MockTerminal(width=80, height=24)


@pytest.fixture
def region():
    return Region(name='test', row=0, col=0, width=40, height=10)


@pytest.fixture
def capture(monkeypatch):
    buf = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buf)
    return buf


class TestMenuReturn:
    def test_initial_value(self):
        m = MenuReturn({'Option A': 'a', 'Option B': 'b'})
        assert m.get_value() == 'Option A'

    def test_navigate_down(self):
        m = MenuReturn({'A': 1, 'B': 2, 'C': 3})
        changed, val = m.handle_key(make_key('KEY_DOWN'))
        assert changed is True
        assert val == 'B'

    def test_navigate_up(self):
        m = MenuReturn({'A': 1, 'B': 2, 'C': 3})
        m.handle_key(make_key('KEY_DOWN'))
        changed, val = m.handle_key(make_key('KEY_UP'))
        assert changed is True
        assert val == 'A'

    def test_navigate_clamp_at_top(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key(make_key('KEY_UP'))
        assert m.get_value() == 'A'

    def test_navigate_clamp_at_bottom(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key(make_key('KEY_DOWN'))
        m.handle_key(make_key('KEY_DOWN'))
        assert m.get_value() == 'B'

    def test_enter_signals_exit(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key(make_key('KEY_ENTER'))
        should_exit, rv = m.signal_return()
        assert should_exit is True
        assert rv == 1

    def test_enter_second_item(self):
        m = MenuReturn({'A': 1, 'B': 2})
        m.handle_key(make_key('KEY_DOWN'))
        m.handle_key(make_key('KEY_ENTER'))
        should_exit, rv = m.signal_return()
        assert should_exit is True
        assert rv == 2

    def test_signal_return_initially_false(self):
        m = MenuReturn({'A': 1})
        should_exit, rv = m.signal_return()
        assert should_exit is False

    def test_set_value(self):
        m = MenuReturn({'A': 1, 'B': 2, 'C': 3})
        m.set_value('C')
        assert m.get_value() == 'C'

    def test_render_does_not_crash(self, term, region, capture):
        m = MenuReturn({'Option A': 'a', 'Option B': 'b'})
        m.render(region, term, focused=True)


class TestMenuFunction:
    def test_initial_value_none(self):
        m = MenuFunction({'Action': lambda s: None})
        assert m.get_value() is None

    def test_navigate_down(self):
        m = MenuFunction({'A': lambda s: None, 'B': lambda s: None})
        m.handle_key(make_key('KEY_DOWN'))
        # Active index should be 1

    def test_enter_calls_function(self):
        called = []
        m = MenuFunction({'Do it': lambda s: called.append(s)})
        m._shell = 'mock_shell'
        m.handle_key(make_key('KEY_ENTER'))
        assert called == ['mock_shell']

    def test_enter_sets_last_activated(self):
        m = MenuFunction({'Action': lambda s: None})
        m.handle_key(make_key('KEY_ENTER'))
        assert m.get_value() == 'Action'

    def test_render_does_not_crash(self, term, region, capture):
        m = MenuFunction({'Option': lambda s: None})
        m.render(region, term, focused=True)


class TestMenuHybrid:
    def test_callable_item_calls_function(self):
        called = []
        m = MenuHybrid({'func': lambda s: called.append(True), 'val': 42})
        m._shell = 'shell'
        m.handle_key(make_key('KEY_ENTER'))
        assert called == [True]
        should_exit, _ = m.signal_return()
        assert should_exit is False

    def test_value_item_signals_exit(self):
        m = MenuHybrid({'func': lambda s: None, 'val': 42})
        m.handle_key(make_key('KEY_DOWN'))
        m.handle_key(make_key('KEY_ENTER'))
        should_exit, rv = m.signal_return()
        assert should_exit is True
        assert rv == 42

    def test_render_does_not_crash(self, term, region, capture):
        m = MenuHybrid({'A': lambda s: None, 'B': 99})
        m.render(region, term, focused=True)


class TestTextBox:
    def test_initial_value(self):
        t = TextBox(initial='hello')
        assert t.get_value() == 'hello'

    def test_type_chars(self):
        t = TextBox()
        t.handle_key(make_key('h'))
        t.handle_key(make_key('i'))
        assert t.get_value() == 'hi'

    def test_backspace(self):
        t = TextBox(initial='hello')
        t.handle_key(make_key('KEY_BACKSPACE'))
        assert t.get_value() == 'hell'

    def test_set_value(self):
        t = TextBox()
        t.set_value('new text')
        assert t.get_value() == 'new text'

    def test_readonly_ignores_keys(self):
        t = TextBox(initial='fixed', readonly=True)
        t.handle_key(make_key('x'))
        assert t.get_value() == 'fixed'

    def test_value_changed_flag(self):
        t = TextBox()
        changed, val = t.handle_key(make_key('a'))
        assert changed is True
        assert val == 'a'

    def test_non_printable_not_added(self):
        t = TextBox()
        t.handle_key(make_key('KEY_UP'))
        assert t.get_value() == ''

    def test_render_does_not_crash(self, term, region, capture):
        t = TextBox(initial='some text')
        t.render(region, term, focused=True)


class TestListView:
    def test_initial_value(self):
        lv = ListView(['apple', 'banana', 'cherry'])
        assert lv.get_value() == ['apple', 'banana', 'cherry']

    def test_handle_key_returns_no_change(self):
        lv = ListView(['a', 'b'])
        changed, val = lv.handle_key(make_key('KEY_DOWN'))
        assert changed is False

    def test_set_value(self):
        lv = ListView(['a'])
        lv.set_value(['x', 'y', 'z'])
        assert lv.get_value() == ['x', 'y', 'z']

    def test_render_does_not_crash(self, term, region, capture):
        lv = ListView(['item 1', 'item 2'])
        lv.render(region, term)

    def test_bullet_numeric(self):
        lv = ListView(['a', 'b', 'c'], bullet='1')
        assert lv._bullet == '1'

    def test_bullet_alpha_upper(self):
        lv = ListView(['a', 'b'], bullet='A')
        assert lv._bullet == 'A'


class TestSubList:
    def test_initial_value(self):
        sl = SubList(['top', ['sub1', 'sub2'], 'end'])
        assert sl.get_value() == ['top', ['sub1', 'sub2'], 'end']

    def test_render_does_not_crash(self, term, region, capture):
        sl = SubList(['item', ['subitem'], 'other'])
        sl.render(region, term)

    def test_handle_key_no_change(self):
        sl = SubList(['a'])
        changed, _ = sl.handle_key(make_key('KEY_DOWN'))
        assert changed is False


class TestCheckBox:
    def test_initial_value(self):
        cb = CheckBox({'a': True, 'b': False, 'c': True})
        assert cb.get_value() == {'a': True, 'b': False, 'c': True}

    def test_toggle_with_space(self):
        cb = CheckBox({'a': False, 'b': False})
        changed, val = cb.handle_key(make_key(' '))
        assert changed is True
        assert val['a'] is True

    def test_navigate_down_then_toggle(self):
        cb = CheckBox({'a': False, 'b': False})
        cb.handle_key(make_key('KEY_DOWN'))
        cb.handle_key(make_key(' '))
        val = cb.get_value()
        assert val['b'] is True
        assert val['a'] is False

    def test_single_mode_deselects_others(self):
        cb = CheckBox({'a': True, 'b': False}, mode='single')
        cb.handle_key(make_key('KEY_DOWN'))
        cb.handle_key(make_key(' '))
        val = cb.get_value()
        assert val['b'] is True
        assert val['a'] is False

    def test_multi_mode_allows_multiple(self):
        cb = CheckBox({'a': True, 'b': False}, mode='multi')
        cb.handle_key(make_key('KEY_DOWN'))
        cb.handle_key(make_key(' '))
        val = cb.get_value()
        assert val['a'] is True
        assert val['b'] is True

    def test_set_value(self):
        cb = CheckBox({'a': False})
        cb.set_value({'a': True})
        assert cb.get_value() == {'a': True}

    def test_render_does_not_crash(self, term, region, capture):
        cb = CheckBox({'opt1': True, 'opt2': False})
        cb.render(region, term, focused=True)


class TestFunction:
    def test_render_calls_handler(self, region, term, capture):
        calls = []
        def handler(shell, reg, key):
            calls.append((shell, reg, key))
        f = Function(handler)
        f.render(region, term)
        assert len(calls) == 1
        assert calls[0][2] is None  # key=None on render

    def test_handle_key_calls_handler(self, region, term, capture):
        calls = []
        def handler(shell, reg, key):
            calls.append(key)
        f = Function(handler)
        f._region = region
        key = make_key('x')
        f.handle_key(key)
        assert key in calls

    def test_initial_value_none(self):
        f = Function(lambda s, r, k: None)
        assert f.get_value() is None

    def test_set_value(self):
        f = Function(lambda s, r, k: None)
        f.set_value(42)
        assert f.get_value() == 42


class TestFormInput:
    def test_construction_valid(self):
        form = FormInput({
            'name': {'type': 'str', 'descriptor': 'Name'},
        })
        assert form is not None

    def test_construction_missing_type_raises(self):
        with pytest.raises(ValueError, match="missing required key 'type'"):
            FormInput({'x': {'descriptor': 'X'}})

    def test_construction_missing_descriptor_raises(self):
        with pytest.raises(ValueError, match="missing required key 'descriptor'"):
            FormInput({'x': {'type': 'str'}})

    def test_construction_choices_missing_options_raises(self):
        with pytest.raises(ValueError, match="requires 'options'"):
            FormInput({'x': {'type': 'choices', 'descriptor': 'X'}})

    def test_construction_choices_empty_options_raises(self):
        with pytest.raises(ValueError, match="non-empty list"):
            FormInput({'x': {'type': 'choices', 'descriptor': 'X', 'options': []}})

    def test_initial_str_value(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name', 'default': 'Alice'}})
        val = form.get_value()
        assert val['name'] == 'Alice'

    def test_initial_bool_value(self):
        form = FormInput({'flag': {'type': 'bool', 'descriptor': 'Flag', 'default': True}})
        val = form.get_value()
        assert val['flag'] is True

    def test_initial_choices_value(self):
        form = FormInput({
            'role': {'type': 'choices', 'descriptor': 'Role',
                     'options': ['Admin', 'User'], 'default': 'User'}
        })
        val = form.get_value()
        assert val['role'] == 'User'

    def test_type_str_character(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        form.handle_key(make_key('a'))
        assert form.get_value()['name'] == 'a'

    def test_type_int_allows_digits(self):
        form = FormInput({'age': {'type': 'int', 'descriptor': 'Age'}})
        form.handle_key(make_key('2'))
        form.handle_key(make_key('5'))
        assert form.get_value()['age'] == '25'

    def test_type_int_rejects_letters(self):
        form = FormInput({'age': {'type': 'int', 'descriptor': 'Age'}})
        form.handle_key(make_key('a'))
        assert form.get_value()['age'] == ''

    def test_bool_toggle_with_space(self):
        form = FormInput({'flag': {'type': 'bool', 'descriptor': 'Flag', 'default': False}})
        form.handle_key(make_key(' '))
        assert form.get_value()['flag'] is True

    # --- bool default parsing ---

    def test_bool_default_ambiguous_string_raises(self):
        """Arbitrary truthy strings like '1', 'yes', 'on' must be rejected."""
        for bad in ('1', '0', 'yes', 'no', 'on', 'off', ''):
            with pytest.raises(ValueError):
                FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': bad}})

    def test_bool_default_false_capital_accepted(self):
        """'False' (capital F) is accepted case-insensitively and maps to False."""
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'False'}})
        assert form.get_value()['f'] is False

    def test_bool_default_true_string_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'true'}})
        assert form.get_value()['f'] is True

    def test_bool_default_false_lower_string_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'false'}})
        assert form.get_value()['f'] is False

    def test_bool_default_true_mixed_case_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': 'True'}})
        assert form.get_value()['f'] is True

    def test_bool_default_python_true_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': True}})
        assert form.get_value()['f'] is True

    def test_bool_default_python_false_accepted(self):
        form = FormInput({'f': {'type': 'bool', 'descriptor': 'F', 'default': False}})
        assert form.get_value()['f'] is False

    def test_choices_cycle_with_space(self):
        form = FormInput({
            'role': {'type': 'choices', 'descriptor': 'Role', 'options': ['A', 'B', 'C']}
        })
        form.handle_key(make_key(' '))
        assert form.get_value()['role'] == 'B'

    def test_navigate_down(self):
        form = FormInput({
            'a': {'type': 'str', 'descriptor': 'A'},
            'b': {'type': 'str', 'descriptor': 'B'},
        })
        form.handle_key(make_key('KEY_DOWN'))
        # Active should be at index 1 now
        assert form._active_index == 1

    def test_submit_valid_form(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        form.handle_key(make_key('h'))
        form.handle_key(make_key('i'))
        # Navigate to submit
        form.handle_key(make_key('KEY_DOWN'))
        form.handle_key(make_key('KEY_ENTER'))
        should_exit, rv = form.signal_return()
        assert should_exit is True
        assert rv['name'] == 'hi'

    def test_submit_required_field_empty(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name', 'required': True}})
        # Navigate to submit
        form.handle_key(make_key('KEY_DOWN'))
        form.handle_key(make_key('KEY_ENTER'))
        should_exit, _ = form.signal_return()
        assert should_exit is False
        # Error should be set
        assert form._field_errors.get('name') is not None

    def test_render_does_not_crash(self, term, region, capture):
        form = FormInput({
            'name': {'type': 'str', 'descriptor': 'Name'},
            'active': {'type': 'bool', 'descriptor': 'Active'},
        })
        form.render(region, term, focused=True)

    def test_set_value(self):
        form = FormInput({'name': {'type': 'str', 'descriptor': 'Name'}})
        form.set_value({'name': 'Bob'})
        assert form.get_value()['name'] == 'Bob'
