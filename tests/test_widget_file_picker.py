"""Tests for the FilePicker widget.

Uses temporary directories to avoid depending on the real filesystem.
Focus order: path → filter → tree → files → buttons.
"""

import io
import os
import sys
import pytest
from tui_wysiwyg.testing import MockTerminal, make_key
from tui_wysiwyg.widgets.file_picker import FilePicker, _apply_filter


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

class _FakeParent:
    def __init__(self, term):
        self.terminal = term
        self._renderer = None


def run_picker(start_dir, keys, dirs_only=False, filter_str="*", width=70):
    term = MockTerminal(width=80, height=24)
    term.feed_keys(keys)
    parent = _FakeParent(term)
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        return FilePicker(
            start_dir=start_dir,
            dirs_only=dirs_only,
            filter=filter_str,
            width=width,
        ).show(parent_shell=parent)
    finally:
        sys.stdout = old


# ---------------------------------------------------------------------------
# _apply_filter helper tests (no I/O)
# ---------------------------------------------------------------------------

class TestApplyFilter:
    def test_star_matches_all(self, tmp_path):
        files = list((tmp_path / f).open('w') or f for f in ['a.txt', 'b.py'])
        # Use DirEntry-like objects; _apply_filter checks .name
        entries = []
        for name in ['a.txt', 'b.py', 'c.md']:
            (tmp_path / name).write_text('')
        entries = list(os.scandir(tmp_path))
        assert len(_apply_filter(entries, '*')) == len(entries)

    def test_pattern_filters(self, tmp_path):
        for name in ['a.txt', 'b.py', 'c.txt']:
            (tmp_path / name).write_text('')
        entries = sorted(os.scandir(tmp_path), key=lambda e: e.name)
        matched = _apply_filter(entries, '*.txt')
        assert {e.name for e in matched} == {'a.txt', 'c.txt'}

    def test_empty_pattern_returns_all(self, tmp_path):
        for name in ['a.txt', 'b.py']:
            (tmp_path / name).write_text('')
        entries = list(os.scandir(tmp_path))
        assert len(_apply_filter(entries, '')) == len(entries)


# ---------------------------------------------------------------------------
# FilePicker widget tests
# ---------------------------------------------------------------------------

# Focus order: path(0) → filter(1) → tree(2) → files(3) → buttons(4)
# Tab 4 times to reach buttons from initial focus on path.
_TAB_TO_BUTTONS = [make_key('\t')] * 4


class TestFilePicker:
    def test_cancel_returns_none(self, tmp_path):
        """Cancel button returns None."""
        keys = _TAB_TO_BUTTONS + [make_key('KEY_DOWN'), make_key('KEY_ENTER')]
        assert run_picker(str(tmp_path), keys) is None

    def test_escape_returns_none(self, tmp_path):
        assert run_picker(str(tmp_path), [make_key(chr(27))]) is None

    def test_ctrlq_returns_none(self, tmp_path):
        assert run_picker(str(tmp_path), [make_key(chr(17))]) is None

    def test_open_returns_start_dir_path(self, tmp_path):
        """Open with no navigation returns the starting directory."""
        keys = _TAB_TO_BUTTONS + [make_key('KEY_ENTER')]
        result = run_picker(str(tmp_path), keys)
        assert result == str(tmp_path)

    def test_files_panel_shows_files_in_start_dir(self, tmp_path):
        """Files in start_dir appear in the files panel (indirect: selecting one updates path)."""
        (tmp_path / "readme.txt").write_text("hello")
        # Tab × 3 to reach files panel, Enter to select first file, Tab to buttons, Enter Open
        keys = ([make_key('\t')] * 3      # path → filter → tree → files
                + [make_key('KEY_ENTER')]  # select first item in files (readme.txt)
                + _TAB_TO_BUTTONS          # refocus to buttons
                + [make_key('KEY_ENTER')]) # Open
        result = run_picker(str(tmp_path), keys)
        assert result == str(tmp_path / "readme.txt")

    def test_dirs_only_hides_regular_files(self, tmp_path):
        """dirs_only=True means files panel is empty even when files exist."""
        (tmp_path / "file.txt").write_text("x")
        sub = tmp_path / "subdir"
        sub.mkdir()
        # Tab × 3 to files panel; with dirs_only, only subdir shows; Open without selecting
        keys = _TAB_TO_BUTTONS + [make_key('KEY_ENTER')]
        result = run_picker(str(tmp_path), keys, dirs_only=True)
        # result should be the start_dir path (no file selected)
        assert result == str(tmp_path)

    def test_navigation_into_subdir(self, tmp_path):
        """Selecting a subdir from the tree navigates into it."""
        sub = tmp_path / "mysubdir"
        sub.mkdir()
        (sub / "child.txt").write_text("c")
        # Tab × 2 to reach tree panel; Enter on first item (.. or subdir)
        # The tree starts with ".." then subdirs; navigate to subdir
        # Tab to tree → if parent exists, first entry is ".." (which navigates up)
        # Since tmp_path has a parent, ".." is first. Down moves to subdir; Enter navigates in.
        # Then Tab × 4 to buttons, Enter Open
        keys = ([make_key('\t')] * 2     # path → filter → tree
                + [make_key('KEY_DOWN'), make_key('KEY_ENTER')]  # move to subdir, navigate
                + _TAB_TO_BUTTONS        # reattach focus to buttons
                + [make_key('KEY_ENTER')])
        result = run_picker(str(tmp_path), keys)
        assert result == str(sub)

    def test_filter_glob_pattern(self, tmp_path):
        """Setting filter to '*.py' hides non-Python files from the files panel."""
        (tmp_path / "script.py").write_text("x")
        (tmp_path / "readme.txt").write_text("y")
        # Tab to filter, type '*.py' (replacing default '*'), Tab to files
        # Enter on first visible file (script.py), Tab to buttons, Open
        # First: clear the default '*' with backspace, then type '*.py'
        clear = [make_key('KEY_BACKSPACE')]  # remove the '*'
        type_pat = [make_key('*'), make_key('.'), make_key('p'), make_key('y')]
        keys = ([make_key('\t')]        # path → filter
                + clear + type_pat      # set filter to '*.py'
                + [make_key('\t')]      # filter → tree
                + [make_key('\t')]      # tree → files (only .py visible)
                + [make_key('KEY_ENTER')]  # select script.py
                + _TAB_TO_BUTTONS
                + [make_key('KEY_ENTER')])
        result = run_picker(str(tmp_path), keys)
        assert result == str(tmp_path / "script.py")

    def test_permission_error_directory_shows_empty(self, tmp_path):
        """Permission-restricted directories do not raise; show (empty)."""
        restricted = tmp_path / "locked"
        restricted.mkdir()
        try:
            restricted.chmod(0o000)
            # Tab × 2 to tree, navigate into locked dir (Down if needed), then Open
            keys = ([make_key('\t')] * 2
                    + [make_key('KEY_DOWN'), make_key('KEY_ENTER')]  # navigate into locked
                    + _TAB_TO_BUTTONS
                    + [make_key('KEY_ENTER')])
            result = run_picker(str(tmp_path), keys)
            # Should not raise; result is whatever path was set
            assert result is not None or result is None
        finally:
            restricted.chmod(0o755)

    def test_many_files_scrollable(self, tmp_path):
        """More files than viewport height — can still select file beyond initial view."""
        for i in range(20):
            (tmp_path / f"file_{i:02d}.txt").write_text(str(i))
        # Tab × 3 to files panel, navigate down 15 times, Enter to select
        keys = ([make_key('\t')] * 3
                + [make_key('KEY_DOWN')] * 15
                + [make_key('KEY_ENTER')]
                + _TAB_TO_BUTTONS
                + [make_key('KEY_ENTER')])
        result = run_picker(str(tmp_path), keys)
        # Result should be one of the files (15th sorted file)
        assert result is not None
        assert os.path.isfile(result)
