# Confirm Widget

A centered modal popup that asks the user to confirm an action.  The caller
supplies a title, a message, and a button dictionary; the widget handles all
shell construction, interaction wiring, and modal display.

---

## Shell Layout

```
|=== <bold>Title</> ===|
|{2R $message$         }|
|----------------------|
|{2R $buttons$         }|
|======================|
```

| Region | Interaction | Description |
|--------|-------------|-------------|
| `message` | `ListView` (display-only) | Message text — up to 2 rows visible |
| `buttons` | `MenuReturn` | Caller-supplied button dict; selecting a label returns its value |

Height is always auto-detected from the `2R` declarations: **7 rows**
(1 title + 2 message + 1 divider + 2 buttons + 1 bottom border).

---

## Import

```python
from tui_wysiwyg.widgets.confirm import Confirm
```

---

## Constructor

```python
Confirm(
    title: str = "Confirm",
    message_lines: list[str] = [],
    buttons: dict = {"OK": True, "Cancel": False},
    width: int = 40,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"Confirm"` | Text shown in the border title (rendered bold). |
| `message_lines` | `list[str]` | `[]` | Lines of message text. The region shows 2 rows. |
| `buttons` | `dict` | `{"OK": True, "Cancel": False}` | Mapping of button label → return value. |
| `width` | `int` | `40` | Width of the popup in characters (including border walls). |

---

## `show()` method

```python
result = Confirm(...).show(parent_shell=None, **run_modal_kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_shell` | `Shell \| None` | If provided, the parent's display is fully restored when the popup closes. Pass the `sh` argument received inside a `MenuFunction` callback. |
| `**run_modal_kwargs` | | Forwarded to `Shell.run_modal()`. Use `row`/`col` to override auto-centering. |

**Returns:** The value associated with the chosen button label, or `None` if the
user presses Escape or Ctrl+Q.

---

## Usage

### Basic Yes / No confirmation

```python
from tui_wysiwyg.widgets.confirm import Confirm

def delete_item(sh):
    result = Confirm(
        title="Delete item?",
        message_lines=["This cannot be undone.", ""],
        buttons={"Yes": True, "No": False},
    ).show(parent_shell=sh)

    if result is True:
        # proceed with deletion
        ...
    elif result is False:
        # cancelled
        ...
    else:
        # Escape / Ctrl+Q — treat same as cancel
        ...
```

### Custom button labels and values

```python
result = Confirm(
    title="Overwrite?",
    message_lines=["output.txt already exists.", "Overwrite it?"],
    buttons={"Overwrite": "overwrite", "Keep existing": "keep", "Abort": None},
    width=44,
).show(parent_shell=sh)
```

### Override positioning

By default the popup is centered on screen.  Pass `row` / `col` to place it
at a specific position:

```python
result = Confirm(
    title="Confirm",
    message_lines=["Are you sure?"],
).show(parent_shell=sh, row=5, col=10)
```

---

## Notes

- Call `show()` from inside a `MenuFunction` callback while the parent
  `Shell.run()` is already executing.  The parent's terminal context
  (alternate screen, cbreak mode) must already be active.
- The `message` region shows 2 rows.  If you pass more than 2 lines the
  extra lines are scrollable but not visible without interaction — keep
  messages concise or increase the width to allow wrapping.
- Button labels are displayed in the order they appear in the `buttons`
  dict.  The first button has focus on open.
- Escape and Ctrl+Q both dismiss the popup without selecting a button and
  return `None`.

---

## Example in `example.py`

The demo in `example.py` (option **8. Confirm Widget**) shows three
scenarios — Delete file, Overwrite file, and Quit without saving — each
customising the title, message, button labels, and optional width to suit
the action being confirmed.
