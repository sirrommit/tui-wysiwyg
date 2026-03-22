# tui-wysiwyg

A Python library for building rich terminal user interfaces from a WYSIWYG layout definition language.

You describe the visual structure of a TUI screen as a formatted string, assign interaction behaviors to named regions, and call `shell.run()`. The library handles rendering, keyboard input, focus management, and inter-region communication.

```
|=100%========== <bold;color=cyan>My App</> ===========|
|{30%  12R  $menu$   }|{  12R  $info$  }|
|=======================================|
```

```python
from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import MenuReturn, ListView

shell = Shell(LAYOUT)
shell.assign("menu", MenuReturn({"Home": "home", "About": "about", "Quit": None}))
shell.assign("info", ListView(["Select an option from the menu."]))
shell.bind("menu", "info", transform=lambda label: PAGES[label])
result = shell.run()
```

---

## Installation

```bash
pip install tui-wysiwyg
```

**Requirements:** Python 3.10+, Linux or macOS. The `blessed` library is installed automatically.

---

## Quick Start

```python
from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import MenuReturn

LAYOUT = """
|=100%=== Choose an option ===|
|{ 8R  $choice$               }|
|=============================|
"""

shell = Shell(LAYOUT)
shell.assign("choice", MenuReturn({
    "Continue": "continue",
    "Settings": "settings",
    "Quit":     None,
}))

result = shell.run()
print(f"Selected: {result}")
```

Run it: `python3 myapp.py`

Use **↑ / ↓** to navigate, **Enter** to select, **Ctrl+Q** to quit.

---

## Shell Definition Language

The shell definition string is a multi-line ASCII diagram that describes the layout of your TUI. It must be surrounded by `|` borders on every line.

### Structure

Every line is either a **border row** or a **column row**.

```
|=100%====== Application Title ======|      ← double border row (title centered)
|{30%  8R  $sidebar$  }|{  8R  $main$  }|   ← column row (two columns)
|{                     }|{              }|   ← filler row (ignored by parser)
|-------------------------------------|      ← single border row (divider)
|{100%  4R  $status$                  }|    ← column row (one full-width column)
|=====================================|      ← double border row (footer)
```

### C-Style Comments

Shell definition strings support `/* ... */` comments. Comments are stripped before parsing and never appear in the rendered TUI. Use them to annotate complex layouts without affecting the output. Multi-line comments are supported.

```python
LAYOUT = """
/* Main application layout — three-column design.                    */
/* Left: navigation menu.  Center: content.  Right: detail panel.   */
|=100%========================= <bold>My App</> =======================|
|{25%  12R  $nav$    }|{50%  12R  $content$ }|{  12R  $detail$  }|
|{                   }|{                    }|{                 }|
|====================================================================|
|{100%  2R  $status$                                                 }| /* status bar */
|====================================================================|
"""
```

### Style Tags

Border row titles (and heading text) can contain style tags to apply colors and text attributes. Style tags degrade gracefully: if a terminal doesn't support an attribute, that attribute is silently skipped and the plain text is still displayed.

**Tag format:**

```
<attr[=value][;attr[=value]...]>text</>
```

The closing tag `</>` resets all styles. A named closing tag like `</bold>` works identically to `</>`.

**Text styles:**

| Tag | Effect |
|-----|--------|
| `<bold>` | Bold / bright |
| `<dim>` | Dim / faint |
| `<italic>` | Italic |
| `<underline>` or `<ul>` | Underline |
| `<blink>` or `<flash>` | Blinking |
| `<reverse>` or `<invert>` | Reverse video (swap fg/bg) |
| `<standout>` | Standout (often same as reverse) |
| `<strike>` or `<strikethrough>` | Strikethrough |
| `<normal>` or `<reset>` | Explicit reset |

**Color attributes:**

Foreground: `color=`, `fg=`, `foreground=`, `fg-color=`, `text-color=`

Background: `bg=`, `background=`, `bg-color=`, `bgcolor=`, `background-color=`

**Named colors:**

| Value | Meaning |
|-------|---------|
| `black`, `red`, `green`, `yellow` | Standard 16-colour foreground/background |
| `blue`, `magenta`, `cyan`, `white` | Standard 16-colour foreground/background |
| `bright_black`, `bright_red`, … | Bright variants (prefix `bright_`) |
| `gray` / `grey` | Alias for `bright_black` |
| `purple` | Alias for `magenta` |
| `pink` | Alias for `bright_magenta` |
| `orange` | Alias for `yellow` (closest 16-colour match) |
| `lime` | Alias for `bright_green` |
| `teal` | Alias for `cyan` |
| `navy` | Alias for `blue` |
| `maroon` | Alias for `red` |
| `0`–`255` | 256-colour index |

**Multiple attributes** are separated by `;`:

```python
LAYOUT = """
|=== <bold;color=cyan>Welcome</> ===|
|=== <color=white;bg=blue>Status</> ===|
|=== <bold;underline;color=bright_yellow>Alert!</> ===|
|{ 8R $menu$ }|
|======================|
"""
```

**Rendering styled text in regions:**

Style tags only apply to border titles out of the box. To draw styled text inside a region (e.g. in a `Function` handler), use `render_styled()`:

```python
from tui_wysiwyg.style import render_styled, styled_plain_text, styled_visual_len

# Inside a Function handler:
def my_handler(shell, region, key):
    term = shell.terminal
    line = render_styled("<bold;color=red>Error:</> something went wrong", term)
    print(term.move(region.row, region.col) + line)
```

`render_styled(text, term, max_len=None)` returns a string containing terminal escape sequences. `max_len` truncates based on visible character count (not escape sequence length).

---

### Border Rows

| Syntax | Renders as |
|--------|-----------|
| `\|====\|` | Double horizontal line (═══) |
| `\|----\|` | Single horizontal line (───) |
| `\|=== Title ===\|` | Double line with centered title |
| `\|--- Section ---\|` | Single line with centered title |
| `\|=== <bold>Title</> ===\|` | Double line with styled title |

### Column Blocks

Each `{...}` block defines a column:

```
{50%  12R  $region_name$  }
 ^^^  ^^^   ^^^^^^^^^^^
 │    │     └── Names this region (required to be interactive)
 │    └──── Height: 12 rows tall (or 50%R for percentage of terminal height)
 └───────── Width: 50% of terminal width (or 25 for 25 chars, or blank to fill remaining)
```

| Width format | Meaning |
|-------------|---------|
| `{50%` | 50% of terminal width |
| `{25` | 25 character columns |
| `{` | Fill remaining width (at most one per row) |

| Height format | Meaning |
|--------------|---------|
| `12R` | 12 terminal rows |
| `50%R` | 50% of terminal height |

**Note:** Percentage widths/heights reflow automatically on terminal resize. Fixed sizes do not.

### Multiple Columns

Separate column blocks with `|` (single line) or `#` (double line):

```
|{30%  10R  $left$  }|{  10R  $right$  }|
|{25%  10R  $a$     }#{  10R  $b$      }|
```

### Named Regions

A region name (`$name$`) marks a column as interactive — it can be assigned an interaction and receive keyboard focus. Names use only lowercase letters, digits, and underscores.

Column blocks without a `$name$` are static display areas (headings, decorative borders, etc.).

### Text Formatting

`__text__` renders as underlined text (falls back to plain text if the terminal doesn't support underline):

```
|{ __Heading__  }|
|{ $content$    }|
```

### Filler Rows

Column rows with neither a `$name$` nor a row-count marker are **filler rows** — they are valid syntax, ignored by the parser, and exist only to make the layout string look like the actual TUI:

```
|{  12R  $menu$  }|   ← content row (has name and row count)
|{                }|   ← filler row (ignored)
|{                }|   ← filler row (ignored)
```

### Complete Example

```python
LAYOUT = """
|=100%========================= My Application ============================|
|{25%     __Navigation__      }|{50%    __Content__    }|{  __Info__      }|
|{12R     $nav$               }|{24R    $content$      }|{24R  $detail$   }|
|{                            }|{                      }|{                }|
|==============================|{                      }|=================|
|{25%     __Status__          }|{                      }|{  __Tags__      }|
|{4R      $status$            }|{                      }|{4R   $tags$     }|
|=========================================================================|
"""
```

---

## Interaction Types

All interaction types live in `tui_wysiwyg.interactions`.

```python
from tui_wysiwyg.interactions import (
    MenuFunction, MenuReturn, MenuHybrid,
    TextBox, ListView, SubList,
    CheckBox, Function, FormInput,
)
```

### Global Keyboard Shortcuts

| Key | Effect |
|-----|--------|
| `Tab` | Move focus to next region |
| `Shift+Tab` | Move focus to previous region |
| `↑` / `↓` | Navigate within menus, checkboxes, forms |
| `k` / `j` | Vim-style ↑ / ↓ in menu and checkbox regions |
| `Enter` | Activate selected item; confirm |
| `Space` | Toggle checkbox; toggle bool/cycle choices in forms |
| `Ctrl+Q` | Exit TUI, `Shell.run()` returns `None` |
| `Ctrl+C` | Raise `KeyboardInterrupt` |

---

### MenuReturn

Displays a scrollable list of labeled options. Selecting an item causes `Shell.run()` to return the associated value.

```python
MenuReturn(items: dict[str, Any])
```

```python
shell.assign("menu", MenuReturn({
    "New File":  "new",
    "Open File": "open",
    "Save":      "save",
    "Quit":      None,
}))
result = shell.run()  # returns "new", "open", "save", or None
```

- `↑` / `↓` or `k` / `j` move the highlight.
- `Enter` triggers the return.
- `Shell.get(name)` returns the label of the currently highlighted item.

---

### MenuFunction

Displays a list of labeled options. Selecting an item calls an associated function.

```python
MenuFunction(items: dict[str, Callable[[Shell], None]])
```

```python
def show_help(shell):
    shell.update("info", ["Help text goes here.", "Press Tab to switch regions."])

def new_file(shell):
    shell.update("content", TextBox())
    shell.update("status", ListView(["Editing new file..."]))

shell.assign("menu", MenuFunction({
    "New File": new_file,
    "Help":     show_help,
}))
```

- Each callback receives the `Shell` instance as its argument.
- The callback runs synchronously; the event loop pauses until it returns.
- Use `shell.update()` inside the callback to modify other regions.
- `Shell.get(name)` returns the label of the last activated item.

---

### MenuHybrid

Combines `MenuFunction` and `MenuReturn`. Each item either calls a function or returns a value.

```python
MenuHybrid(items: dict[str, Callable[[Shell], None] | Any])
```

```python
shell.assign("main_menu", MenuHybrid({
    "Settings":  open_settings,   # callable → runs function, stays in TUI
    "Help":      open_help,        # callable → runs function, stays in TUI
    "Quit":      None,             # non-callable → Shell.run() returns None
}))
```

If the item's value is callable, it behaves like `MenuFunction`. Otherwise it behaves like `MenuReturn`.

---

### TextBox

A free-form text entry area with configurable wrapping.

```python
TextBox(
    initial: str = "",
    wrap: Literal["word", "anywhere", "extend"] = "word",
    readonly: bool = False,
)
```

| `wrap` | Behavior |
|--------|---------|
| `"word"` | Wraps at word boundaries (default) |
| `"anywhere"` | Wraps at the column edge, mid-word if necessary |
| `"extend"` | Lines can extend beyond width; viewport scrolls horizontally |

```python
shell.assign("notes", TextBox(initial="Enter your notes here.", wrap="word"))
shell.assign("preview", TextBox(readonly=True))
```

Standard editing keys work: printable characters insert at cursor, `Backspace` / `Delete` remove, arrow keys move cursor, `Home` / `End` jump to line start/end.

`Shell.get(name)` returns the current text as a string, preserving newlines.

---

### ListView

Displays a static or dynamically updated list of strings. Not interactive — does not accept keyboard input.

```python
ListView(
    items: list[str],
    bullet: str | Literal["1", "A", "a", "I", "i"] = "*",
)
```

| `bullet` | Rendered prefix |
|----------|----------------|
| `"*"` (default) | `* item` |
| `"-"` | `- item` |
| Any single character | `X item` |
| `"1"` | `1. item`, `2. item`, … |
| `"A"` | `A. item`, `B. item`, … |
| `"a"` | `a. item`, `b. item`, … |
| `"I"` | `I. item`, `II. item`, … |
| `"i"` | `i. item`, `ii. item`, … |

```python
shell.assign("log", ListView([], bullet="-"))
shell.assign("steps", ListView(["Install deps", "Run migrations", "Start server"], bullet="1"))
```

Use `shell.update("log", new_list)` to replace the list contents at runtime.

`Shell.get(name)` returns the current list of items.

---

### SubList

Like `ListView`, but list items can themselves be lists, creating an indented nested structure.

```python
SubList(
    items: list[str | list],
    bullet: str | Literal["1", "A", "a", "I", "i"] = "*",
)
```

```python
shell.assign("tree", SubList([
    "Fruits",
    ["Apple", "Banana", "Cherry"],
    "Vegetables",
    ["Carrot", "Broccoli"],
]))
```

Renders as:
```
* Fruits
  * Apple
  * Banana
  * Cherry
* Vegetables
  * Carrot
  * Broccoli
```

Nesting is unlimited — sublists can contain further sublists.

---

### CheckBox

Displays a list of toggleable items.

```python
CheckBox(
    items: dict[str, bool],
    mode: Literal["multi", "single"] = "multi",
)
```

| `mode` | Symbol | Behavior |
|--------|--------|---------|
| `"multi"` | `[X]` / `[ ]` | Any number of items can be checked |
| `"single"` | `(●)` / `( )` | At most one item checked; selecting another auto-deselects |

```python
# Multi-select (checkboxes)
shell.assign("features", CheckBox({
    "Dark mode":       True,
    "Auto-save":       False,
    "Spell check":     True,
    "Line numbers":    False,
}, mode="multi"))

# Single-select (radio buttons)
shell.assign("theme", CheckBox({
    "Light": False,
    "Dark":  True,
    "Auto":  False,
}, mode="single"))
```

- `↑` / `↓` or `k` / `j` move the highlight.
- `Space` or `Enter` toggles the highlighted item.

`Shell.get(name)` returns `dict[str, bool]`.

---

### Function

Delegates all rendering and input handling to a user-provided callable. Use this when none of the built-in types fit.

```python
Function(handler: Callable[[Shell, Region, key | None], None])
```

```python
def my_handler(shell, region, key):
    term = shell.terminal
    if key is None:
        # Initial render
        print(term.move(region.row, region.col) + "Hello from Function!")
    elif str(key) == 'r':
        # User pressed 'r' — do something
        print(term.move(region.row, region.col) + "Refreshed!")

shell.assign("custom", Function(my_handler))
```

- `handler(shell, region, key=None)` is called once on initial render and on every keypress while the region is focused.
- `region` provides `.row`, `.col`, `.width`, `.height` (0-based terminal coordinates).
- Use `shell.terminal` (a `blessed.Terminal`) to write output directly.
- Maintain state by closing over a mutable object or using a class with `__call__`.

`Shell.get(name)` returns `None` unless your handler calls `shell.update(name, value)`.

---

### FormInput

A structured multi-field data entry form.

```python
FormInput(fields: dict[str, dict])
```

Each field is a variable name mapped to a field definition dict:

| Key | Required | Description |
|-----|----------|-------------|
| `"type"` | Yes | `"str"`, `"int"`, `"float"`, `"bool"`, or `"choices"` |
| `"descriptor"` | Yes | Human-readable label shown next to the field |
| `"default"` | No | Pre-filled value |
| `"required"` | No | If `True`, field must be non-empty to submit |
| `"placeholder"` | No | Hint text shown when field is empty (str/int/float only) |
| `"validator"` | No | `Callable[[Any], bool \| str]` — return `True` to accept, or an error string |
| `"options"` | For `choices` | List of valid choices (required for `choices` type) |

```python
shell.assign("registration", FormInput({
    "username": {
        "type":        "str",
        "descriptor":  "Username",
        "required":    True,
        "placeholder": "e.g. alice",
        "validator":   lambda v: True if v.isalnum() else "Letters and digits only",
    },
    "age": {
        "type":        "int",
        "descriptor":  "Age",
        "default":     18,
        "validator":   lambda v: True if v >= 0 else "Must be non-negative",
    },
    "score": {
        "type":        "float",
        "descriptor":  "Score",
        "placeholder": "0.0 – 100.0",
    },
    "active": {
        "type":        "bool",
        "descriptor":  "Active",
        "default":     True,
    },
    "role": {
        "type":        "choices",
        "descriptor":  "Role",
        "options":     ["Admin", "Editor", "Viewer"],
        "default":     "Viewer",
    },
}))
result = shell.run()
# result = {"username": "alice", "age": 25, "score": 98.5, "active": True, "role": "Admin"}
```

**Editing by type:**

| Type | Keys |
|------|------|
| `str` | Standard text entry |
| `int` | Digits and leading `-` only |
| `float` | Digits, single `.`, and leading `-` only |
| `bool` | `Space`, `Enter`, `←`, `→` toggle True/False |
| `choices` | `Space`, `←`, `→` cycle through options |

Navigating away from a numeric field validates the entered value. Submitting validates all fields (required check + validators). Invalid fields are highlighted and a first-error focus is applied.

`Shell.run()` returns the result `dict` when the user activates `[ Submit ]`.

---

## Inter-Region Communication

Regions communicate through an observer pattern.

### `shell.on_change(name, callback)`

Register a function to call when a region's value changes:

```python
def update_detail(selected_label):
    shell.update("detail", DETAIL_MAP.get(selected_label, []))

shell.on_change("menu", update_detail)
```

Returns a `ChangeHandle` — call `.remove()` to deregister:

```python
handle = shell.on_change("menu", my_callback)
# ... later ...
handle.remove()
```

### `shell.bind(source, target, transform=None)`

Convenience method — when `source` changes, update `target`:

```python
# Direct binding — source value flows directly to target
shell.bind("search_box", "results")

# Transform binding — apply a function first
DETAIL_MAP = {
    "Users":  ["Alice", "Bob", "Carol"],
    "Groups": ["Admin", "Editor", "Viewer"],
}
shell.bind("nav", "content", transform=lambda label: DETAIL_MAP.get(label, []))
```

Also returns a `ChangeHandle`.

### Chained updates

Callbacks may themselves call `shell.update()`, creating chains. `CircularUpdateError` is raised if a cycle is detected.

---

## Shell API Reference

### `Shell(definition)`

Parse the shell definition and prepare the layout.

```python
shell = Shell("""
|=100%=|
|{ 10R $menu$ }|
|=============|
""")
```

Raises `ShellSyntaxError` if the definition is malformed.

---

### `shell.assign(name, interaction)`

Assign an interaction to a named region.

```python
shell.assign("menu", MenuReturn({"A": 1, "B": 2}))
```

Raises `RegionNotFoundError` if the region doesn't exist.
Raises `ValueError` if the region already has an interaction (call `unassign` first).

---

### `shell.run() -> Any`

Enter the event loop and block until the TUI exits.

Returns the value chosen by a `MenuReturn`/`MenuHybrid` selection or a `FormInput` submission, or `None` if the user presses `Ctrl+Q`.

---

### `shell.run_modal(row=None, col=None, width=None, height=None, parent_shell=None) -> Any`

Run this Shell as a modal popup overlaid on top of an already-running TUI. Must be called from inside a `MenuFunction` callback (or any context where the terminal is already in fullscreen/cbreak mode).

```python
def open_confirm(sh):
    popup = Shell(CONFIRM_LAYOUT)
    popup.assign("buttons", MenuReturn({"OK": True, "Cancel": False}))
    result = popup.run_modal(width=40, parent_shell=sh)
    if result:
        do_something()

shell.assign("menu", MenuFunction({"Delete": open_confirm}))
```

- `width` / `height` — if omitted, auto-detected from the layout's fixed-size declarations; falls back to 60% of the terminal dimension.
- `row` / `col` — if omitted, the popup is centered on the screen.
- `parent_shell` — if provided, the parent's display is restored when the popup closes.
- Escape or `Ctrl+Q` dismiss the popup and return `None`.

---

### `shell.get(name) -> Any`

Get the current value of a named region (see each interaction type for what "value" means).

---

### `shell.update(name, value)`

Programmatically set a region's value and re-render it.

```python
shell.update("status", ["Ready"])
shell.update("notes", "Hello world")
shell.update("flags", {"Dark mode": True, "Auto-save": False})
```

Fires `on_change` callbacks. Can be called from within a `MenuFunction` callback or a `Function` handler.

---

### `shell.unassign(name) -> Interaction | None`

Remove a region's interaction, returning it to a static display area.

---

### `shell.set_focus(name)`

Move focus to a region programmatically.

---

### `shell.focus` (property)

Name of the currently focused region, or `None`.

---

### `shell.terminal` (property)

The underlying `blessed.Terminal` instance. Use inside `Function` handlers to write directly to the terminal.

---

## Pre-built Widgets

`tui_wysiwyg.widgets` provides seven ready-made popup dialogs built on `Shell.run_modal()`. Each widget exposes a `show(parent_shell=None, **kwargs)` method that constructs the Shell, assigns interactions, and returns the user's selection.

```python
from tui_wysiwyg.widgets import (
    Confirm, Alert, InputPrompt, ListSelect,
    FilePicker, DatePicker, Progress,
)
```

All widgets are designed to be called from inside a `MenuFunction` callback where the terminal is already in fullscreen mode.

### Confirm

Yes/No (or any labelled button) confirmation dialog.

```python
result = Confirm(
    title="Delete item?",
    message_lines=["This cannot be undone.", ""],
    buttons={"Yes": True, "No": False},
    width=40,
).show(parent_shell=sh)
# returns True, False, or None (Escape)
```

### Alert

Informational popup with a single OK button.

```python
Alert(title="Error", message_lines=["File not found."]).show(parent_shell=sh)
```

### InputPrompt

Single-line text entry popup.

```python
name = InputPrompt(
    title="Rename",
    prompt_lines=["Enter new name:"],
    initial="old_name",
).show(parent_shell=sh)
# returns str or None
```

### ListSelect

Pick one item (single mode) or many items (multi mode) from a scrollable list.

```python
# Single selection — exits immediately on pick
choice = ListSelect(title="Choose", items=["Alpha", "Beta", "Gamma"]).show(sh)

# Multi selection — returns {label: bool} on OK
selected = ListSelect(title="Pick features", items={"Dark mode": True, "Auto-save": False}, multi=True).show(sh)
```

### FilePicker

Browse the filesystem to select a file or directory.

```python
path = FilePicker(
    start_dir="/home/user/projects",
    title="Open file",
    filter="*.py",
).show(parent_shell=sh)
# returns absolute path str or None
```

### DatePicker

Monthly calendar popup for selecting a date.

```python
import datetime
date = DatePicker(
    initial=datetime.date.today(),
    title="Choose date",
).show(parent_shell=sh)
# returns datetime.date or None
```

### Progress

Programmatically-driven progress bar. Used as a context manager — call `set_progress()` from inside the `with` block.

```python
with Progress(title="Processing…", total=len(items)).show(parent_shell=sh) as prog:
    for i, item in enumerate(items, 1):
        process(item)
        prog.set_progress(i, f"Item {i}/{len(items)}")
        if prog.cancelled:
            break
```

See [`docs/widgets/`](docs/widgets/) for full documentation on each widget.

---

## Exceptions

```python
from tui_wysiwyg.exceptions import ShellSyntaxError, RegionNotFoundError, CircularUpdateError
```

| Exception | When raised |
|-----------|-------------|
| `ShellSyntaxError` | Malformed shell definition string |
| `RegionNotFoundError` | Named region does not exist |
| `CircularUpdateError` | `on_change` callbacks form a dependency cycle |

`ShellSyntaxError` has `.line` (1-based line number) and `.message` attributes.

---

## Testing

`tui-wysiwyg` ships a `MockTerminal` for headless testing:

```python
from tui_wysiwyg.testing import MockTerminal
```

```python
# conftest.py
import pytest
from tui_wysiwyg import Shell
from tui_wysiwyg.testing import MockTerminal

@pytest.fixture
def terminal():
    return MockTerminal(width=80, height=24)

@pytest.fixture
def shell(terminal):
    def factory(definition: str) -> Shell:
        return Shell(definition, _terminal=terminal)
    return factory
```

```python
def test_menu_return(shell, terminal):
    s = shell("""
    |=100%=|
    |{ 5R $menu$ }|
    |=============|
    """)
    s.assign("menu", MenuReturn({"A": 1, "B": 2, "C": 3}))

    terminal.feed_keys(["KEY_DOWN", "KEY_ENTER"])
    result = s.run()

    assert result == 2
```

`MockTerminal` API:

| Method | Description |
|--------|-------------|
| `feed_keys(keys)` | Queue keypresses by blessed name (e.g. `"KEY_DOWN"`, `"KEY_ENTER"`) or single characters |
| `get_buffer_text()` | Return all output written, stripped of control sequences |
| `get_rendered_lines()` | Return current virtual screen as a list of strings |
| `reset()` | Clear output buffer and key queue |

---

## Package Layout

```
tui_wysiwyg/
├── __init__.py              # exports: Shell
├── shell.py                 # Shell class
├── parser.py                # Shell definition parser
├── layout.py                # LayoutModel, Region
├── renderer.py              # Terminal rendering
├── events.py                # Keyboard input
├── observer.py              # ChangeHandle, Observer
├── style.py                 # Style tag parsing, render_styled(), strip_comments()
├── exceptions.py            # ShellSyntaxError, RegionNotFoundError, CircularUpdateError
├── testing.py               # MockTerminal
├── interactions/
│   ├── __init__.py          # exports all interaction classes
│   ├── base.py              # Interaction ABC
│   ├── menu.py              # MenuFunction, MenuReturn, MenuHybrid
│   ├── textbox.py           # TextBox
│   ├── list_view.py         # ListView, SubList
│   ├── checkbox.py          # CheckBox
│   ├── function.py          # Function
│   └── form.py              # FormInput
└── widgets/
    ├── __init__.py          # exports all widget classes
    ├── confirm.py           # Confirm
    ├── alert.py             # Alert
    ├── input_prompt.py      # InputPrompt
    ├── list_select.py       # ListSelect
    ├── file_picker.py       # FilePicker
    ├── date_picker.py       # DatePicker
    └── progress.py          # Progress
```

## Documentation

Full documentation lives in [`docs/`](docs/):

| Path | Contents |
|------|----------|
| [`docs/index.md`](docs/index.md) | Documentation index |
| [`docs/api.md`](docs/api.md) | Full Shell API reference |
| [`docs/architecture.md`](docs/architecture.md) | Internal design and data flow |
| [`docs/shell-syntax.md`](docs/shell-syntax.md) | Complete shell definition language spec |
| [`docs/inter-region.md`](docs/inter-region.md) | Observer pattern and inter-region communication |
| [`docs/testing.md`](docs/testing.md) | Testing strategy and MockTerminal |
| [`docs/interactions/`](docs/interactions/) | One page per interaction type |
| [`docs/widgets/`](docs/widgets/) | One page per pre-built widget |
