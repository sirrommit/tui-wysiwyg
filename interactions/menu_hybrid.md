# menu-hybrid

**Class:** `MenuHybrid`

Combines `MenuFunction` and `MenuReturn`. Each item maps to either a callable or a return value.

## Constructor

```python
MenuHybrid(items: dict[str, Callable[[Shell], None] | Any])
```

If an item's value is callable, it behaves like `MenuFunction`. Otherwise it behaves like `MenuReturn`.

## Behavior

- Navigation is identical to `MenuFunction` and `MenuReturn`.
- On `Enter`:
  - If `items[label]` is callable: call it with `shell`, then continue the event loop.
  - Otherwise: cause `Shell.run()` to return `items[label]`.

## Value

`Shell.get(name)` returns the currently highlighted label, or `None`.
