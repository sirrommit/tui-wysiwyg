# function

**Class:** `Function`

Delegates all rendering and input handling to a user-provided callable. Use this when none of the built-in interaction types fit.

## Constructor

```python
Function(handler: Callable[[Shell, Region, Keystroke | None], None])
```

The `handler` callable signature:

```python
def my_handler(shell: Shell, region: Region, key: Keystroke | None) -> None:
    ...
```

| Parameter | Description |
|-----------|-------------|
| `shell` | The `Shell` instance (use to call `shell.update()`, etc.) |
| `region` | The `Region` data object (provides `.width`, `.height`, `.row`, `.col`) |
| `key` | The keypress that triggered this call, or `None` on initial render |

## Behavior

- Called once on initial render (`key=None`).
- Called on every keypress while the region has focus.
- The handler is responsible for rendering output into the region's area using `blessed` directly (a `blessed.Terminal` instance is available via `shell.terminal`).
- The handler is responsible for maintaining its own internal state (close over mutable state or use a class with `__call__`).

## Value

`Shell.get(name)` always returns `None` for `Function` interactions unless the handler calls `shell.update(name, value)` explicitly.
