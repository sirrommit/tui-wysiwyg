"""File Picker widget — browse the filesystem to select a file or directory.

Shell layout
------------

    |=== <bold>Title</> ===================|
    |{2R $path$             }|{14 2R $filter$}|
    |-----------------------------------------|
    |{30% 14R $tree$        }|{14R $files$   }|
    |-----------------------------------------|
    |{1R  $buttons$                          }|
    |=========================================|

- ``$path$``    — TextBox showing the current directory or selected file path.
                  The user can edit it directly.
- ``$filter$``  — TextBox (14 chars wide) holding a glob pattern (default ``*``).
                  Changes live-filter ``$files$``.
- ``$tree$``    — MenuFunction: directories under the active directory.
                  Selecting a dir navigates into it.
- ``$files$``   — MenuFunction: files and subdirs in the active directory,
                  filtered by ``$filter$``.  Selecting a file updates ``$path$``;
                  selecting a subdir navigates into it.
- ``$buttons$`` — ``_SubmittingMenu("path")``: Open returns ``shell.get("path")``;
                  Cancel returns ``None``.

Height is auto-detected: **21 rows** (1+2+1+14+1+1+1).

Usage
-----

    from tui_wysiwyg.widgets.file_picker import FilePicker

    def choose_file(sh):
        path = FilePicker(start_dir="/home/user").show(parent_shell=sh)
        if path is not None:
            open_file(path)
"""

import os
import fnmatch

from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import TextBox
from tui_wysiwyg.interactions.menu import MenuFunction
from tui_wysiwyg.widgets._utils import _SubmittingMenu


def _shell_def(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===================|\n"
        "|{2R $path$             }|{14 2R $filter$}|\n"
        "|-----------------------------------------|\n"
        "|{30% 14R $tree$        }|{14R $files$   }|\n"
        "|-----------------------------------------|\n"
        "|{1R  $buttons$                           }|\n"
        "|=========================================|\n"
    )


def _list_dir(path):
    """Return (dirs, files) for *path*, sorted case-insensitively.
    Returns ([], []) on PermissionError."""
    try:
        entries = sorted(os.scandir(path), key=lambda e: e.name.lower())
    except (PermissionError, OSError):
        return [], []
    dirs  = [e for e in entries if e.is_dir()  and not e.name.startswith(".")]
    files = [e for e in entries if e.is_file() and not e.name.startswith(".")]
    return dirs, files


def _apply_filter(files, pattern):
    """Return only the entries whose names match *pattern* (fnmatch glob)."""
    if not pattern or pattern == "*":
        return files
    matched = set(fnmatch.filter([e.name for e in files], pattern))
    return [e for e in files if e.name in matched]


class FilePicker:
    """Browse the filesystem and select a file or directory.

    Parameters
    ----------
    start_dir : str | None
        Initial directory.  Defaults to ``os.getcwd()``.
    title : str
        Text displayed in the popup border (rendered bold).
    dirs_only : bool
        If ``True``, only directories are shown in the files panel (files are
        hidden).  Useful for directory-picker mode.
    filter : str
        Initial glob pattern for the filter bar (default ``"*"``).
    width : int
        Width of the popup in characters (including border walls).
        Height is always auto-detected from the row declarations.

    Returns
    -------
    Absolute path string on Open, ``None`` on Cancel / Escape / Ctrl+Q.
    """

    def __init__(
        self,
        start_dir=None,
        title: str = "Select File",
        dirs_only: bool = False,
        filter: str = "*",
        width: int = 70,
    ):
        self.start_dir = os.path.abspath(start_dir) if start_dir else os.getcwd()
        self.title = title
        self.dirs_only = dirs_only
        self.filter = filter
        self.width = width

    def show(self, parent_shell=None, **run_modal_kwargs):
        """Display the file picker popup.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is restored when the popup
            closes.  Pass the ``sh`` argument from a ``MenuFunction`` callback.
        **run_modal_kwargs
            Forwarded to ``Shell.run_modal()``.

        Returns
        -------
        Absolute path string on Open, ``None`` on Cancel / Escape / Ctrl+Q.
        """
        term = parent_shell.terminal if parent_shell is not None else None
        popup = Shell(_shell_def(self.title), _terminal=term)

        # Mutable shared state — using a dict so closures can mutate it.
        state = {"active_dir": self.start_dir}

        # ------------------------------------------------------------------
        # Internal helpers
        # ------------------------------------------------------------------

        def _rebuild_tree(sh):
            """Replace $tree$ with a fresh MenuFunction for the active dir."""
            was_focused = (sh.focus == "tree")
            items = {}

            # Navigate-up entry (unless already at filesystem root)
            parent = os.path.dirname(state["active_dir"])
            if parent != state["active_dir"]:
                def _go_up(s, p=parent):
                    _navigate(s, p)
                items[".."] = _go_up

            dirs, _ = _list_dir(state["active_dir"])
            for d in dirs:
                def _enter(s, p=d.path):
                    _navigate(s, p)
                items[f"\u25b6 {d.name}/"] = _enter

            sh.unassign("tree")
            sh.assign("tree", MenuFunction(items or {"(empty)": lambda s: None}))
            if was_focused:
                sh.set_focus("tree")

        def _rebuild_files(sh):
            """Replace $files$ with a fresh MenuFunction for the active dir."""
            was_focused = (sh.focus == "files")
            pattern = sh.get("filter") or "*"
            dirs, files = _list_dir(state["active_dir"])

            if self.dirs_only:
                files = []
            else:
                files = _apply_filter(files, pattern)

            items = {}
            for d in dirs:
                def _enter(s, p=d.path):
                    _navigate(s, p)
                items[f"\u25b6 {d.name}/"] = _enter
            for f in files:
                def _pick(s, p=f.path):
                    s.update("path", p)
                items[f.name] = _pick

            sh.unassign("files")
            sh.assign("files", MenuFunction(items or {"(empty)": lambda s: None}))
            if was_focused:
                sh.set_focus("files")

        def _navigate(sh, path):
            """Navigate to *path*: update state, path bar, tree, and files."""
            state["active_dir"] = path
            sh.update("path", path)
            _rebuild_tree(sh)
            _rebuild_files(sh)

        # ------------------------------------------------------------------
        # Initial assignments
        # ------------------------------------------------------------------

        popup.assign("path",   TextBox(initial=state["active_dir"], wrap="extend"))
        popup.assign("filter", TextBox(initial=self.filter, wrap="extend"))

        # Initial tree
        tree_items = {}
        parent = os.path.dirname(state["active_dir"])
        if parent != state["active_dir"]:
            def _up(s, p=parent):
                _navigate(s, p)
            tree_items[".."] = _up

        init_dirs, init_files = _list_dir(state["active_dir"])
        for d in init_dirs:
            def _enter_tree(s, p=d.path):
                _navigate(s, p)
            tree_items[f"\u25b6 {d.name}/"] = _enter_tree

        popup.assign("tree", MenuFunction(tree_items or {"(empty)": lambda s: None}))

        # Initial files
        if self.dirs_only:
            show_files = []
        else:
            show_files = _apply_filter(init_files, self.filter)

        file_items = {}
        for d in init_dirs:
            def _enter_files(s, p=d.path):
                _navigate(s, p)
            file_items[f"\u25b6 {d.name}/"] = _enter_files
        for f in show_files:
            def _pick_file(s, p=f.path):
                s.update("path", p)
            file_items[f.name] = _pick_file

        popup.assign("files",   MenuFunction(file_items or {"(empty)": lambda s: None}))
        popup.assign("buttons", _SubmittingMenu("path"))

        # Live filter: rebuild $files$ whenever the filter text changes.
        popup.on_change("filter", lambda _: _rebuild_files(popup))

        # Path field: live navigation — when the user types a valid directory
        # or file path, update tree/files without overwriting the path box.
        def _on_path_change(value):
            stripped = value.strip()
            if os.path.isdir(stripped) and stripped != state["active_dir"]:
                state["active_dir"] = stripped
                _rebuild_tree(popup)
                _rebuild_files(popup)
            elif os.path.isfile(stripped):
                parent = os.path.dirname(stripped)
                if parent != state["active_dir"]:
                    state["active_dir"] = parent
                    _rebuild_tree(popup)
                    _rebuild_files(popup)

        popup.on_change("path", _on_path_change)

        return popup.run_modal(
            width=self.width,
            parent_shell=parent_shell,
            **run_modal_kwargs,
        )
