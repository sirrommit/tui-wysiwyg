# checkbox

**Class:** `CheckBox`

Displays a list of toggleable items, each with a checked/unchecked state.

## Constructor

```python
CheckBox(
    items: dict[str, bool],
    mode: Literal["multi", "single"] = "multi",
)
```

| `mode` | Behavior |
|--------|----------|
| `"multi"` | Any number of items can be checked. Renders `[X]` / `[ ]`. |
| `"single"` | At most one item can be checked. Renders `(●)` / `( )`. Selecting an item unchecks the previously selected one. |

## Behavior

- `↑` / `↓` (or `k` / `j`) move the highlight.
- `Space` or `Enter` toggles the highlighted item.
- In `"single"` mode, activating an already-selected item deselects it.

## Value

`Shell.get(name)` returns a `dict[str, bool]` mapping each label to its current checked state.
