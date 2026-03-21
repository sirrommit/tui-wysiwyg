import pytest
from tui_wysiwyg.observer import Observer, ChangeHandle
from tui_wysiwyg.exceptions import CircularUpdateError


class TestObserver:
    def test_register_returns_change_handle(self):
        obs = Observer()
        handle = obs.register('x', lambda v, u=None: None)
        assert isinstance(handle, ChangeHandle)

    def test_notify_calls_callback(self):
        obs = Observer()
        received = []
        obs.register('x', lambda v, u=None: received.append(v))
        obs.notify('x', 42)
        assert received == [42]

    def test_notify_calls_multiple_callbacks(self):
        obs = Observer()
        calls = []
        obs.register('x', lambda v, u=None: calls.append(('cb1', v)))
        obs.register('x', lambda v, u=None: calls.append(('cb2', v)))
        obs.notify('x', 'hello')
        assert len(calls) == 2
        assert ('cb1', 'hello') in calls
        assert ('cb2', 'hello') in calls

    def test_notify_different_names_isolated(self):
        obs = Observer()
        received_x = []
        received_y = []
        obs.register('x', lambda v, u=None: received_x.append(v))
        obs.register('y', lambda v, u=None: received_y.append(v))
        obs.notify('x', 1)
        assert received_x == [1]
        assert received_y == []

    def test_remove_deregisters_callback(self):
        obs = Observer()
        received = []
        handle = obs.register('x', lambda v, u=None: received.append(v))
        handle.remove()
        obs.notify('x', 99)
        assert received == []

    def test_remove_only_removes_specific_callback(self):
        obs = Observer()
        calls = []
        handle1 = obs.register('x', lambda v, u=None: calls.append(('cb1', v)))
        obs.register('x', lambda v, u=None: calls.append(('cb2', v)))
        handle1.remove()
        obs.notify('x', 'test')
        assert len(calls) == 1
        assert calls[0][0] == 'cb2'

    def test_notify_unregistered_name_no_error(self):
        obs = Observer()
        # Notifying a name with no callbacks should not raise
        obs.notify('unknown', 42)

    def test_circular_update_detection(self):
        obs = Observer()

        def cb_a(value, updating=None):
            obs.notify('b', value, updating)

        def cb_b(value, updating=None):
            obs.notify('a', value, updating)

        obs.register('a', cb_a)
        obs.register('b', cb_b)

        with pytest.raises(CircularUpdateError):
            obs.notify('a', 1)

    def test_no_false_circular_detection(self):
        """a -> b is fine if b doesn't come back to a."""
        obs = Observer()
        results = []

        def cb_a(value, updating=None):
            obs.notify('b', value * 2, updating)

        def cb_b(value, updating=None):
            results.append(value)

        obs.register('a', cb_a)
        obs.register('b', cb_b)

        obs.notify('a', 5)
        assert results == [10]

    def test_multiple_removes_safe(self):
        """Calling remove() twice should not raise."""
        obs = Observer()
        handle = obs.register('x', lambda v, u=None: None)
        handle.remove()
        handle.remove()  # Should not raise


class TestBindViaObserver:
    """Test observer used in a bind-like pattern."""

    def test_chain_update(self):
        obs = Observer()
        values = {}

        def on_source_change(value, updating=None):
            values['target'] = value * 2
            obs.notify('target', values['target'], updating)

        obs.register('source', on_source_change)
        obs.notify('source', 5)
        assert values['target'] == 10
