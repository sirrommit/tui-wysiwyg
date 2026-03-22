# Input Prompt Widget

Asks the user to type a single line of text.  The caller supplies a title,
optional prompt text, and an optional pre-filled initial value.  The widget
blocks until the user submits (OK) or cancels.

---

## Shell Layout

```
|=== <bold>Title</> ===|
|{2R $prompt$          }|
|----------------------|
|{2R $entry$           }|
|----------------------|
|{1R $buttons$         }|
|======================|
```

| Region | Interaction | Description |
|--------|-------------|-------------|
| `prompt` | `ListView` (display-only) | Descriptive text — up to 2 rows visible |
| `entry` | `TextBox(wrap='extend')` | The text entry box — single line that scrolls if text exceeds width |
| `buttons` | `_SubmittingMenu` (internal) | OK reads the entry and signals exit; Cancel signals exit with `None` |

Height is always auto-detected from the row declarations: **9 rows**
(1 title + 2 prompt + 1 divider + 2 entry + 1 divider + 1 buttons + 1 border).

---

## Import

```python
from tui_wysiwyg.widgets.input_prompt import InputPrompt
```

---

## Constructor

```python
InputPrompt(
    title: str = "Input",
    prompt_lines: list[str] = [],
    initial: str = "",
    width: int = 50,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"Input"` | Text shown in the border title (rendered bold). |
| `prompt_lines` | `list[str]` | `[]` | Descriptive text above the entry box. Up to 2 rows visible. |
| `initial` | `str` | `""` | Pre-filled text in the entry box. Cursor is placed at the end. |
| `width` | `int` | `50` | Width of the popup in characters (including border walls). |

---

## `show()` method

```python
result = InputPrompt(...).show(parent_shell=None, **run_modal_kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_shell` | `Shell \| None` | If provided, the parent's display is restored when the popup closes. |
| `**run_modal_kwargs` | | Forwarded to `Shell.run_modal()`. Use `row`/`col` to override auto-centering. |

**Returns:** The typed string on OK, `None` on Cancel / Escape / Ctrl+Q.

---

## Usage

### Simple text input

```python
from tui_wysiwyg.widgets.input_prompt import InputPrompt

def rename_item(sh):
    new_name = InputPrompt(
        title="Rename",
        prompt_lines=["Enter a new name for the item:"],
        initial="old_name",
    ).show(parent_shell=sh)

    if new_name is not None:
        # user submitted text (may be empty string "")
        do_rename(new_name)
    # else: cancelled or dismissed
```

### With validation loop

```python
def get_username(sh):
    while True:
        name = InputPrompt(
            title="Create account",
            prompt_lines=["Username (letters and digits only):"],
        ).show(parent_shell=sh)

        if name is None:
            return None   # cancelled

        if name.isalnum():
            return name

        Alert(
            title="Invalid username",
            message_lines=[f"'{name}' contains invalid characters."],
        ).show(parent_shell=sh)
```

### Pre-filled value

```python
result = InputPrompt(
    title="Edit URL",
    prompt_lines=["Modify the URL below:"],
    initial="https://example.com",
    width=60,
).show(parent_shell=sh)
```

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Any printable key | Insert character at cursor |
| Backspace | Delete character before cursor |
| Delete / Del | Delete character after cursor |
| Left / Right | Move cursor |
| Home / End | Jump to start / end of text |
| Tab | Move focus from entry → buttons |
| Shift+Tab | Move focus back |
| Enter (on OK button) | Submit and return text |
| Enter (on Cancel button) | Cancel and return `None` |
| Escape / Ctrl+Q | Dismiss, return `None` |

> **Note:** Pressing Enter while focused on the *entry* box inserts a
> literal newline in extend mode.  Tab to the OK button and press Enter
> there to submit.  This preserves the entry box for potential multi-line
> use in future widget variants.

---

## Implementation Note

`buttons` uses a private `_SubmittingMenu` subclass of `MenuFunction`.  When
OK is selected it reads `shell.get("entry")` and overrides `signal_return()`
to return `(True, text)`, which causes `run_modal()` to exit with that value.
Cancel sets the exit value to `None`.  No library changes are required —
this is self-contained in the widget module.

---

## Example in `example.py`

The demo in `example.py` (option **10. Input Prompt Widget**) shows three
scenarios: renaming an item, editing a URL (pre-filled), and entering a
search query with the result echoed back.
