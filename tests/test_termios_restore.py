"""Tests that Shell.run() restores terminal IXON settings on all exit paths."""

import sys
import types
import pytest
from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import MenuReturn
from tui_wysiwyg.testing import MockTerminal, make_key


# ---------------------------------------------------------------------------
# Minimal blessed-context mock so Shell.run() can execute without a real TTY
# ---------------------------------------------------------------------------

class _FakeContext:
    def __enter__(self):
        return self
    def __exit__(self, *a):
        pass


class _TermWithFd(MockTerminal):
    """MockTerminal that exposes a fake _keyboard_fd so the IXON path runs."""

    def __init__(self, keys=None, **kw):
        super().__init__(**kw)
        self._keyboard_fd = 99          # fake fd number
        self._keys = list(keys or [])   # keystroke queue

    # Context managers that blessed.Terminal normally provides
    def fullscreen(self):
        return _FakeContext()

    def cbreak(self):
        return _FakeContext()

    def hidden_cursor(self):
        return _FakeContext()

    def inkey(self, timeout=None):
        if self._keys:
            return self._keys.pop(0)
        return make_key('\x11')  # Ctrl+Q — causes immediate exit


# ---------------------------------------------------------------------------
# Shared shell definition
# ---------------------------------------------------------------------------

SHELL_DEF = """
|=====|
|{3R $menu$ }|
|=====|
"""


def _make_shell(term):
    sh = Shell(SHELL_DEF, _terminal=term)
    m = MenuReturn({'OK': True, 'Cancel': False})
    sh.assign('menu', m)
    return sh


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTermiosRestore:
    def test_restore_called_after_normal_exit(self, monkeypatch):
        """tcsetattr restore is called when MenuReturn signals exit."""
        term = _TermWithFd(keys=[make_key('KEY_ENTER')], width=80, height=24)

        get_calls = []
        set_calls = []
        fake_attrs = [0b11, 0, 0, 0, 0, 0, []]   # mutable list

        def fake_tcgetattr(fd):
            get_calls.append(fd)
            return list(fake_attrs)

        def fake_tcsetattr(fd, when, attrs):
            set_calls.append((fd, when, attrs))

        fake_termios = types.SimpleNamespace(
            tcgetattr=fake_tcgetattr,
            tcsetattr=fake_tcsetattr,
            TCSANOW=0,
            TCSADRAIN=1,
            IXON=0b10,
        )
        monkeypatch.setattr('tui_wysiwyg.shell._termios', fake_termios)
        monkeypatch.setattr('tui_wysiwyg.shell._HAS_TERMIOS', True)

        sh = _make_shell(term)
        sh.run()

        # tcsetattr called at least twice: once to disable IXON, once to restore
        assert len(set_calls) >= 2
        # The last call must restore the original attrs (IXON bit intact)
        last_fd, last_when, last_attrs = set_calls[-1]
        assert last_fd == 99
        assert last_when == 1           # TCSADRAIN
        assert last_attrs == list(fake_attrs)

    def test_restore_called_after_ctrlq_exit(self, monkeypatch):
        """tcsetattr restore is called when user presses Ctrl+Q."""
        term = _TermWithFd(keys=[make_key('\x11')], width=80, height=24)

        set_calls = []
        fake_attrs = [0b11, 0, 0, 0, 0, 0, []]

        fake_termios = types.SimpleNamespace(
            tcgetattr=lambda fd: list(fake_attrs),
            tcsetattr=lambda fd, when, attrs: set_calls.append((fd, when, attrs)),
            TCSANOW=0,
            TCSADRAIN=1,
            IXON=0b10,
        )
        monkeypatch.setattr('tui_wysiwyg.shell._termios', fake_termios)
        monkeypatch.setattr('tui_wysiwyg.shell._HAS_TERMIOS', True)

        sh = _make_shell(term)
        sh.run()

        assert len(set_calls) >= 2
        last_fd, last_when, last_attrs = set_calls[-1]
        assert last_when == 1           # TCSADRAIN restore
        assert last_attrs == list(fake_attrs)

    def test_restore_called_after_exception(self, monkeypatch):
        """tcsetattr restore is called even when the event loop raises."""
        term = _TermWithFd(width=80, height=24)

        set_calls = []
        fake_attrs = [0b11, 0, 0, 0, 0, 0, []]

        fake_termios = types.SimpleNamespace(
            tcgetattr=lambda fd: list(fake_attrs),
            tcsetattr=lambda fd, when, attrs: set_calls.append((fd, when, attrs)),
            TCSANOW=0,
            TCSADRAIN=1,
            IXON=0b10,
        )
        monkeypatch.setattr('tui_wysiwyg.shell._termios', fake_termios)
        monkeypatch.setattr('tui_wysiwyg.shell._HAS_TERMIOS', True)

        # Patch event_loop.next_key to raise after the first call
        from tui_wysiwyg import events as _ev
        call_count = [0]
        original_next_key = _ev.EventLoop.next_key

        def boom(self):
            call_count[0] += 1
            if call_count[0] > 1:
                raise RuntimeError("simulated crash")
            return make_key('\x00')   # harmless first key

        monkeypatch.setattr(_ev.EventLoop, 'next_key', boom)

        sh = _make_shell(term)
        with pytest.raises(RuntimeError, match="simulated crash"):
            sh.run()

        # Restore must still have been called
        restore_calls = [c for c in set_calls if c[1] == 1]
        assert len(restore_calls) >= 1
        assert restore_calls[-1][2] == list(fake_attrs)

    def test_no_termios_path_does_not_crash(self, monkeypatch):
        """Shell.run() is safe when termios is unavailable."""
        monkeypatch.setattr('tui_wysiwyg.shell._HAS_TERMIOS', False)
        term = _TermWithFd(keys=[make_key('\x11')], width=80, height=24)
        sh = _make_shell(term)
        # Must not raise
        sh.run()
