# textbox

**Class:** `TextBox`

A free-form text entry area.

## Constructor

```python
TextBox(
    initial: str = "",
    wrap: Literal["word", "anywhere", "extend"] = "word",
    readonly: bool = False,
)
```

| Parameter | Description |
|-----------|-------------|
| `initial` | Pre-filled text content |
| `wrap` | `"word"` wraps on word boundaries; `"anywhere"` wraps at column edge; `"extend"` allows lines to scroll horizontally beyond the region width |
| `readonly` | If `True`, the region displays text but does not accept keyboard input |

## Behavior

- Standard text editing keys: printable characters insert at cursor, `Backspace`/`Delete` remove, arrow keys move cursor.
- `Home` / `End` move to line start/end.
- `Ctrl+Home` / `Ctrl+End` move to document start/end.
- If content exceeds the region height, the view scrolls vertically. A scroll indicator is shown if the terminal is wide enough.
- In `"extend"` mode, lines scroll horizontally; `←` / `→` scroll the viewport.

## Value

`Shell.get(name)` returns the current text content as a string (preserving newlines).
