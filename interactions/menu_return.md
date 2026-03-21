# menu-return

**Class:** `MenuReturn`

Displays a list of labeled options. When the user selects an option, `Shell.run()` returns that option's associated value.

## Constructor

```python
MenuReturn(items: dict[str, Any])
```

`items` maps display labels to return values of any type.

## Behavior

- Renders and navigates identically to `MenuFunction`.
- `Enter` on a highlighted item causes `Shell.run()` to return `items[selected_label]`.
- The TUI exits cleanly (terminal restored) before returning.

## Value

`Shell.get(name)` returns the label of the currently highlighted item (not yet selected), or `None` before first interaction.
