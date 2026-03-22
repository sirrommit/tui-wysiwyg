# Alert Widget

An informational or warning popup with a single OK button.  Use it to
surface errors, warnings, or status messages that the user must acknowledge
before continuing.

---

## Shell Layout

```
|=== <bold>Title</> ===|
|{3R $message$         }|
|----------------------|
|{1R $ok$              }|
|======================|
```

| Region | Interaction | Description |
|--------|-------------|-------------|
| `message` | `ListView` (display-only) | Message text — up to 3 rows visible |
| `ok` | `MenuReturn` | Single `{"OK": True}` button |

Height is always auto-detected from the row declarations: **7 rows**
(1 title + 3 message + 1 divider + 1 ok + 1 bottom border).

---

## Import

```python
from tui_wysiwyg.widgets.alert import Alert
```

---

## Constructor

```python
Alert(
    title: str = "Alert",
    message_lines: list[str] = [],
    width: int = 40,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"Alert"` | Text shown in the border title (rendered bold). |
| `message_lines` | `list[str]` | `[]` | Lines of message text. The region shows 3 rows. |
| `width` | `int` | `40` | Width of the popup in characters (including border walls). |

---

## `show()` method

```python
Alert(...).show(parent_shell=None, **run_modal_kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_shell` | `Shell \| None` | If provided, the parent's display is restored when the popup closes. |
| `**run_modal_kwargs` | | Forwarded to `Shell.run_modal()`. Use `row`/`col` to override auto-centering. |

**Returns:** `True` when OK is pressed, `None` on Escape / Ctrl+Q.

The return value is rarely needed — Alert is typically called for its side
effect (blocking until the user reads the message).

---

## Usage

### Simple error message

```python
from tui_wysiwyg.widgets.alert import Alert

def save_file(sh):
    try:
        _do_save()
    except PermissionError:
        Alert(
            title="Save failed",
            message_lines=["Permission denied.", "Check file permissions."],
        ).show(parent_shell=sh)
```

### Warning with longer message

```python
Alert(
    title="Warning",
    message_lines=[
        "The configuration file is missing.",
        "Default settings will be used.",
        "Changes will not be persisted.",
    ],
    width=48,
).show(parent_shell=sh)
```

### Override positioning

```python
Alert(
    title="Note",
    message_lines=["Operation complete."],
).show(parent_shell=sh, row=3, col=5)
```

---

## Notes

- The `message` region shows 3 rows.  Extra lines are not visible but the
  region is scrollable; keep messages to 3 lines or fewer for best UX.
- Unlike `Confirm`, there is no cancel path — the only way to dismiss is OK,
  Escape, or Ctrl+Q (all of which unblock the caller).
- Call `show()` from inside a `MenuFunction` callback while the parent
  `Shell.run()` is active.

---

## Example in `example.py`

The demo in `example.py` (option **9. Alert Widget**) shows three alert
scenarios — an error, a warning, and an informational notice — each using a
different title and message.
