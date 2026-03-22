# status-message

**Class:** `StatusMessage`

A display-only region that shows a single-line status or validation message with severity styling. Not focusable; updated programmatically via `Shell.update()`.

## Constructor

```python
StatusMessage()
```

No parameters. The region starts empty (blank).

## Update Values

Pass one of the following to `Shell.update(name, value)`:

| Value | Effect |
|-------|--------|
| `None` or `""` | Clears the region (shows blank) |
| `(style, message)` tuple | Displays `message` with the given `style` |
| Plain `str` | Treated as `("info", str)` |

### Styles

| Style | Prefix | Color |
|-------|--------|-------|
| `"error"` | `✗ ` | Red (falls back to plain text if terminal has no colour) |
| `"success"` | `✓ ` | Green (same fallback) |
| `"info"` | `ℹ ` | Terminal default colour |

## Behavior

- Not focusable — Tab and Shift+Tab skip this region.
- The message is clipped to the region width; no wrapping occurs.
- If the region is taller than one row, extra rows are blanked.
- An unrecognized style string is treated as `"info"`.

## Example

```python
from tui_wysiwyg.interactions import StatusMessage

shell.assign("status", StatusMessage())

shell.update("status", ("error",   "File not found"))
shell.update("status", ("success", "Saved successfully"))
shell.update("status", ("info",    "3 items selected"))
shell.update("status", None)          # clear
```

## Value

`Shell.get("status")` returns:

- `None` when the region is empty
- `(style, message)` tuple when a message is displayed
