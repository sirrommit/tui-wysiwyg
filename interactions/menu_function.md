# menu-function

**Class:** `MenuFunction`

Displays a list of labeled options. When the user selects an option, the associated function is called.

## Constructor

```python
MenuFunction(items: dict[str, Callable[[Shell], None]])
```

`items` maps display labels to callables. Each callable receives the `Shell` instance as its only argument.

## Behavior

- Renders each key in `items` as a selectable line, in insertion order.
- The active (highlighted) line uses **reverse video** if the terminal supports it; otherwise renders as `> label`.
- `↑` / `↓` (or `k` / `j`) move the highlight.
- `Enter` calls `items[selected_label](shell)`, then re-renders the region.
- The callable runs synchronously. The event loop is paused until the callable returns.

## Value

`Shell.get(name)` returns the label of the most recently activated item, or `None` if no item has been activated yet.

## Notes

- The callable is responsible for any side effects (e.g., updating other regions via `shell.update()`).
- There is no "return value" from the callable — use `shell.update()` to communicate results back to the TUI.
