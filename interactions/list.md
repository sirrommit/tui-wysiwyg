# list

**Class:** `ListView`

Displays a static or dynamic bulleted/numbered list. Not interactive — does not accept user input.

## Constructor

```python
ListView(
    items: list[str],
    bullet: str | Literal["1", "A", "a", "I", "i"] = "*",
)
```

| `bullet` value | Rendered prefix |
|----------------|----------------|
| Any single character (e.g. `"*"`, `"-"`, `"•"`) | `* item` |
| `"1"` | `1. item`, `2. item`, … |
| `"A"` | `A. item`, `B. item`, … |
| `"a"` | `a. item`, `b. item`, … |
| `"I"` | `I. item`, `II. item`, … |
| `"i"` | `i. item`, `ii. item`, … |

## Behavior

- Renders items in order, one per line.
- If items overflow the region height, a scroll indicator is shown (view is not user-scrollable; use `Shell.update` to replace items).
- Long items wrap according to the region width.

## Value

`Shell.get(name)` returns the current list of items as a `list[str]`.
