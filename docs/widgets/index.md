# tui-wysiwyg Widget Plan

Each widget is a self-contained Python module in this directory.  The module starts
by defining the shell layout as a human-readable string, then contains the
implementation class that wires up interactions and exposes a clean constructor.

## Usage Pattern

```python
from tui_wysiwyg.widgets.confirm import Confirm

def delete_item(sh):
    result = Confirm(
        title="Delete item?",
        message_lines=["This cannot be undone.", ""],
        buttons={"Yes": True, "No": False},
    ).show(parent_shell=sh)
    if result:
        ...
```

Every widget exposes a `show(parent_shell=None, **run_modal_kwargs)` method that
constructs the Shell, assigns interactions, and calls `run_modal()`.  Width is
always passed explicitly (fill panels have no natural width); height is
auto-detected from explicit `nR` row counts where possible.

---

## Status

| Widget | File | Status |
|--------|------|--------|
| Confirm | `confirm.py` | Complete |
| Alert | `alert.py` | Complete |
| Input Prompt | `input_prompt.py` | Complete |
| List Select | `list_select.py` | Complete |
| File Picker | `file_picker.py` | Complete |
| Date Picker | `date_picker.py` | Complete |
| Progress Bar | `progress.py` | Complete |

---

## 1. Confirm (`confirm.py`)

Replaces and formalises the `CONFIRM_POPUP` pattern from `example.py`.

### Shell

```
|=== <bold>{title}</> ===|
|{2R $message$           }|
|------------------------|
|{2R $buttons$           }|
|========================|
```

### Regions

| Region | Interaction | Description |
|--------|-------------|-------------|
| `message` | `ListView` | Display-only message text (2 rows visible) |
| `buttons` | `MenuReturn` | Caller-supplied button dict, e.g. `{"Yes": True, "No": False}` |

### Sizing

- **Width:** explicit (fill panels have no natural width; default 40)
- **Height:** auto-detected from `2R` declarations — total 7 rows (1+2+1+2+1)

### API

```python
Confirm(
    title: str = "Confirm",
    message_lines: list[str] = [],
    buttons: dict = {"OK": True, "Cancel": False},
    width: int = 40,
)
```

**Returns:** the selected button value, or `None` on Escape / Ctrl+Q.

---

## 2. Alert (`alert.py`)

Informational or warning popup with a single OK button.

### Shell

```
|=== <bold>{title}</> ===|
|{3R $message$           }|
|------------------------|
|{1R $ok$                }|
|========================|
```

### Regions

| Region | Interaction | Description |
|--------|-------------|-------------|
| `message` | `ListView` | Display-only message text (3 rows visible) |
| `ok` | `MenuReturn` | Single entry: `{"OK": True}` |

### Sizing

- **Width:** explicit (default 40)
- **Height:** auto-detected — total 7 rows (1+3+1+1+1)

### API

```python
Alert(
    title: str = "Alert",
    message_lines: list[str] = [],
    width: int = 40,
)
```

**Returns:** `True` when OK is pressed, `None` on Escape / Ctrl+Q.

---

## 3. Input Prompt (`input_prompt.py`)

Asks the user to type a single line of text.

### Shell

```
|=== <bold>{title}</> ===|
|{2R $prompt$            }|
|------------------------|
|{2R $entry$             }|
|------------------------|
|{1R $buttons$           }|
|========================|
```

### Regions

| Region | Interaction | Description |
|--------|-------------|-------------|
| `prompt` | `ListView` | Display-only prompt text |
| `entry` | `TextBox(wrap='extend')` | Single-line text entry |
| `buttons` | `_SubmittingMenu("entry")` | OK reads `shell.get("entry")` and exits; Cancel exits with `None` |

### Sizing

- **Width:** explicit (default 50)
- **Height:** auto-detected — total 9 rows (1+2+1+2+1+1+1)

### API

```python
InputPrompt(
    title: str = "Input",
    prompt_lines: list[str] = [],
    initial: str = "",
    width: int = 50,
)
```

**Returns:** the text string on OK, `None` on Cancel / Escape / Ctrl+Q.

### Notes

- `buttons` is a `_SubmittingMenu("entry")` — an internal `MenuFunction`
  subclass whose OK handler reads `shell.get("entry")`, stores the result,
  and sets `_submitted = True` so `signal_return()` exits the modal.

---

## 4. List Select (`list_select.py`)

Lets the user pick one item (single mode) or many items (multi mode) from a
scrollable list.

### Shell

```
|=== <bold>{title}</> ===|
|{2R  $prompt$           }|
|------------------------|
|{10R $items$            }|
|------------------------|
|{1R  $buttons$          }|
|========================|
```

### Regions

| Region | Interaction | Description |
|--------|-------------|-------------|
| `prompt` | `ListView` | Display-only prompt text |
| `items` | `CheckBox` (multi) or `MenuReturn` (single) | The selectable list |
| `buttons` | `_SubmittingMenu("items")` | OK reads `shell.get("items")` and exits; Cancel exits with `None` — only shown in multi mode |

### Sizing

- **Width:** explicit (default 40)
- **Height:** auto-detected — total 16 rows (1+2+1+10+1+1+1; buttons row omitted in single mode → 14)

### API

```python
ListSelect(
    title: str = "Select",
    prompt_lines: list[str] = [],
    items: list[str] | dict[str, Any] = [],
    multi: bool = False,
    width: int = 40,
)
```

**Returns:**
- `multi=False`: the value of the chosen item (exits immediately on selection)
- `multi=True`: `dict[str, bool]` of checked items on OK, `None` on Cancel

### Notes

- In single mode `items` is a `MenuReturn`; selecting any item immediately exits
  (no OK button needed — the buttons region is omitted from the shell definition).
- In multi mode `items` is a `CheckBox`; `buttons` is a `_SubmittingMenu("items")`
  whose OK handler reads `shell.get("items")` and returns the full checked dict.

---

## 5. File Picker (`file_picker.py`)

Browse the filesystem to select a file or directory.  A combined path/filter bar
sits at the top: the wide left column shows the current directory/filename (editable);
the narrow right column holds the glob filter.  Below that, the left column shows a
navigable directory tree and the right column shows filtered directory contents.

### Shell

```
|=== <bold>{title}</> ===================|
|{2R $path$             }|{14 2R $filter$}|
|-----------------------------------------|
|{30% 14R $tree$        }|{14R $files$   }|
|-----------------------------------------|
|{1R  $buttons$                          }|
|=========================================|
```

### Regions

| Region | Interaction | Description |
|--------|-------------|-------------|
| `path` | `TextBox(wrap='extend')` | Wide left column at top — shows the current directory path; updated when navigating; user can type a path directly. |
| `filter` | `TextBox(wrap='extend')` | Narrow right column (14 chars) at top — glob pattern, default `*`. Live-filters `$files$` on change via `on_change`. |
| `tree` | `MenuFunction` | Left (30%) — directory tree. `▶ dir/` collapsed, `▼ dir/` expanded. Selecting a dir toggles expansion and updates `$files$` and `$path$`. |
| `files` | `MenuFunction` | Right (fill) — files and subdirs in the active directory, filtered by `$filter$` glob. Selecting a file updates `$path$`; selecting a subdir expands it in `$tree$`. |
| `buttons` | `MenuReturn` | `{"Open": "_submit", "Cancel": None}` |

### Sizing

- **Width:** explicit (default 70; tree ~20 chars, divider, files ~47 chars; filter column fixed at 14)
- **Height:** auto-detected — total 21 rows (1+2+1+14+1+1+1)

### API

```python
FilePicker(
    start_dir: str | None = None,   # defaults to os.getcwd()
    title: str = "Select File",
    dirs_only: bool = False,
    filter: str = "*",
    width: int = 70,
)
```

**Returns:** absolute path string on Open, `None` on Cancel / Escape / Ctrl+Q.

### Notes

**Path bar (`$path$`)**
- Initialised to `start_dir` (or `os.getcwd()`).
- Updated by `_set_active_dir(path)` whenever a directory is navigated into.
- Updated to the full file path when a file is selected in `$files$`.
- On Open, the widget returns `shell.get("path")`, allowing the user to type
  a path manually without using the tree/file list at all.

**Filter bar (`$filter$`)**
- Fixed 14-char column; initial value `*`.
- `on_change("filter", _rebuild_files)` live-filters `$files$` as the user types.
- `fnmatch.filter()` is applied to file entries only; directories are always shown.

**Tree behaviour**
- Root node is `start_dir`; a `..` entry at the top navigates up.
- Expansion state is kept in a widget-local `_expanded: set[str]`.
- `MenuFunction` entries rebuilt on each expand/collapse: `" ▼ dirname/"` or `" ▶ dirname/"`.

**Wiring**
- Selecting a directory in either `$tree$` or `$files$` calls the same internal
  `_set_active_dir(path)` helper, which updates `$path$`, `$tree$`, and `$files$`.
- Selecting a file in `$files$` calls `shell.update("path", abs_path)`.

---

## 6. Date Picker (`date_picker.py`)

Presents a monthly calendar for selecting a date.

### Shell

```
|=== <bold>{title}</> ===|
|{2R $nav$               }|
|------------------------|
|{8R $calendar$          }|
|------------------------|
|{1R $buttons$           }|
|========================|
```

### Regions

| Region | Interaction | Description |
|--------|-------------|-------------|
| `nav` | `MenuFunction` | Three entries: `"< Prev"`, `"  Month YYYY  "` (display), `"Next >"`. Prev/Next shift the displayed month; the centre entry does nothing. |
| `calendar` | `Function` | Custom handler draws weekday header row + up to 6 date rows (Su Mo Tu We Th Fr Sa). Arrow keys move the highlighted date; Enter confirms. |
| `buttons` | `MenuReturn` | `{"OK": "_submit", "Cancel": None}` |

### Sizing

- **Width:** explicit (default 30; fits "Su Mo Tu We Th Fr Sa" at 3 chars/cell + borders)
- **Height:** auto-detected — total 14 rows (1+2+1+8+1+1+1)

### API

```python
DatePicker(
    initial: datetime.date | None = None,   # defaults to today
    title: str = "Select Date",
    width: int = 30,
)
```

**Returns:** `datetime.date` on OK, `None` on Cancel / Escape / Ctrl+Q.

### Notes

**`$nav$`**
- Three `MenuFunction` entries share the 2-row region.
- Prev/Next callbacks update a widget-local `_month: datetime.date` (first of month)
  and call `shell.update("nav", ...)` to refresh the centre label, then trigger
  a `$calendar$` redraw via `shell.update("calendar", None)`.

**`$calendar$` Function handler**
- `key=None` (initial render): draws the static weekday header and all date cells.
- `key=KEY_UP/DOWN/LEFT/RIGHT`: moves `_cursor: datetime.date`; marks `$calendar$`
  dirty to redraw.
- `key=Enter`: sets `_selected_date` and signals exit (via a custom `signal_return`
  override).
- Rendering: today's date shown with `reverse`; cursor date with `bold+reverse`;
  dates outside the current month shown dim or omitted.

---

## 7. Progress Bar (`progress.py`)

Displays a progress indicator during a long operation.  Driven programmatically
by the caller; optionally includes a Cancel button.

### Shell

```
|=== <bold>{title}</> ===|
|{2R $message$           }|
|------------------------|
|{2R $bar$               }|
|------------------------|
|{1R $buttons$           }|
|========================|
```

### Regions

| Region | Interaction | Description |
|--------|-------------|-------------|
| `message` | `ListView` | Status text updated by caller via `set_progress()` |
| `bar` | `Function` | Draws `[████████░░░░] 55%`; block characters scaled to region width |
| `buttons` | `MenuReturn` | `{"Cancel": None}`; omitted when `cancellable=False` |

### Sizing

- **Width:** explicit (default 50)
- **Height:** auto-detected — total 9 rows (1+2+1+2+1+1+1)

### API

```python
Progress(
    title: str = "Progress",
    total: int = 100,
    cancellable: bool = True,
    width: int = 50,
)

# Caller interface (called while run_modal() is executing in another thread,
# or between yields in a generator-based usage):
widget.set_progress(current: int, message: str = "")
```

**Returns:** `None` always (cancelled or complete).

### Notes

- `$bar$` `Function` handler reads widget-local `_current` and `_total` to compute
  fill fraction; renders `█` for filled portion and `░` for empty, scaled to
  `region.width - 10` chars (reserving space for `[`, `]`, ` `, percentage text).
- Caller drives progress by calling `widget.set_progress(n)`, which calls
  `shell.update("bar", n)` and `shell.update("message", [msg])` and then
  `sys.stdout.flush()`.
- Thread safety: for generator-based use (caller yields between steps and calls
  `set_progress` synchronously before the next `run_modal` iteration), no threading
  is needed. For true background threads, the caller is responsible for
  synchronisation.
