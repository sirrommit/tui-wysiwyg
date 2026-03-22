# File Picker Widget

Browse the filesystem to select a file or directory.  A path/filter bar sits
at the top; a navigable directory listing fills the main area with a tree on
the left and filtered file list on the right.

---

## Shell Layout

```
|=== <bold>Title</> ===================|
|{2R $path$             }|{14 2R $filter$}|
|-----------------------------------------|
|{30% 14R $tree$        }|{14R $files$   }|
|-----------------------------------------|
|{1R  $buttons$                          }|
|=========================================|
```

| Region | Interaction | Description |
|--------|-------------|-------------|
| `path` | `TextBox(wrap='extend')` | Shows the active dir or selected file path. User can type a path directly. |
| `filter` | `TextBox(wrap='extend')` | 14-char glob filter (e.g. `*.py`). Defaults to `*`. Live-filters `$files$` on change. |
| `tree` | `MenuFunction` | Left 30% — subdirectories of the active dir. `▶ dirname/` entries navigate into that dir. `..` goes up one level. |
| `files` | `MenuFunction` | Right fill — files and subdirs in the active dir, filtered by `$filter$`. Selecting a file updates `$path$`; selecting a subdir navigates into it. |
| `buttons` | `_SubmittingMenu` | Open returns `shell.get("path")`; Cancel returns `None`. |

Height is auto-detected: **21 rows** (1+2+1+14+1+1+1).

---

## Import

```python
from tui_wysiwyg.widgets.file_picker import FilePicker
```

---

## Constructor

```python
FilePicker(
    start_dir: str | None = None,
    title: str = "Select File",
    dirs_only: bool = False,
    filter: str = "*",
    width: int = 70,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_dir` | `str \| None` | `os.getcwd()` | Initial directory to display. |
| `title` | `str` | `"Select File"` | Text shown in the border title (rendered bold). |
| `dirs_only` | `bool` | `False` | If `True`, files are hidden; only directories are shown in `$files$`. |
| `filter` | `str` | `"*"` | Initial glob pattern for the filter bar. |
| `width` | `int` | `70` | Width of the popup in characters (including border walls). |

---

## `show()` method

```python
path = FilePicker(...).show(parent_shell=None, **run_modal_kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_shell` | `Shell \| None` | If provided, the parent's display is restored when the popup closes. |
| `**run_modal_kwargs` | | Forwarded to `Shell.run_modal()`. Use `row`/`col` to override auto-centering. |

**Returns:** Absolute path string on Open, `None` on Cancel / Escape / Ctrl+Q.

---

## Usage

### Pick any file starting in the current directory

```python
from tui_wysiwyg.widgets.file_picker import FilePicker

def open_file(sh):
    path = FilePicker().show(parent_shell=sh)
    if path is not None:
        with open(path) as f:
            content = f.read()
```

### Pick a Python file only

```python
path = FilePicker(
    start_dir="/home/user/projects",
    title="Open Python file",
    filter="*.py",
).show(parent_shell=sh)
```

### Pick a directory

```python
directory = FilePicker(
    title="Choose output directory",
    dirs_only=True,
).show(parent_shell=sh)
```

### Type a path manually

The `$path$` box is an editable TextBox.  The user can navigate with the
tree/files panels, or Tab to `$path$` and type an absolute path directly.

**Live path navigation:** as the user types in `$path$`, the widget checks
whether the current text is a valid filesystem path on every keystroke:

- If the text is an **existing directory**, `$tree$` and `$files$` update
  immediately to show that directory's contents.  The path box continues to
  display what the user typed.
- If the text is an **existing file**, `$tree$` and `$files$` update to show
  the file's parent directory.  The path box keeps the file path.
- If the text does not exist, `$tree$` and `$files$` are unchanged.

Pressing Open returns whatever is in the path box, so manually typed paths
work without any tree navigation.

---

## Navigation

| Key | Action |
|-----|--------|
| Up / Down | Move highlight in tree or files list |
| Enter | Tree: navigate into dir · Files: navigate into dir or select file |
| Tab / Shift+Tab | Cycle focus between `path`, `filter`, `tree`, `files`, `buttons` |
| Escape / Ctrl+Q | Dismiss, return `None` |

- Hidden files (names starting with `.`) are not shown.
- Directories are always visible in `$files$` regardless of the glob filter;
  the filter applies to files only.
- On `PermissionError` (unreadable directory), the panel shows `(empty)`.

---

## Implementation Notes

`$tree$` and `$files$` are rebuilt from scratch on each navigation by
calling `shell.unassign()` then `shell.assign()` with a new `MenuFunction`.
Focus is preserved across rebuilds — if the user was in `$tree$` when they
selected a directory, focus remains in `$tree$` after the rebuild.

The filter TextBox uses `shell.on_change("filter", ...)` so `$files$` updates
live as the user types.

---

## Example in `example.py`

The demo in `example.py` (option **12. File Picker Widget**) shows three
scenarios: pick any file, pick Python files only (pre-filtered), and pick a
directory (`dirs_only=True`).  The selected path is echoed back in the
result bar after each action.
