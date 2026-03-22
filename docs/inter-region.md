# Inter-Region Communication

Regions in a shell can respond to changes in other regions. `tui-wysiwyg` uses an **observer pattern** for this: regions emit change events, and registered callbacks respond.

---

## The Problem

Consider a shell with a `$sidemenu$` region and an `$info$` region. When the user changes the selection in `$sidemenu$`, the content of `$info$` should update accordingly. Neither region knows about the other at definition time.

---

## Solution: Observer Pattern

Every region emits a **change event** whenever its value changes — either by user input or by a programmatic `shell.update()` call. Callers register callbacks to respond.

### `Shell.on_change(name, callback)`

Register a callback that fires when region `name`'s value changes.

```python
def on_change(
    name: str,
    callback: Callable[[Any], None],
) -> None
```

- `name`: the region name to observe.
- `callback`: called with the new value when the region changes.
- Multiple callbacks can be registered on the same region; they fire in registration order.

**Example:**

```python
shell = Shell(definition)
shell.assign("sidemenu", MenuReturn({"Alpha": "alpha", "Beta": "beta"}))
shell.assign("info", ListView(["Select an item"]))

def update_info(selected_label):
    info_content = CONTENT_MAP[selected_label]
    shell.update("info", info_content)

shell.on_change("sidemenu", update_info)
shell.run()
```

When the user selects "Alpha" in `$sidemenu$`, `update_info("Alpha")` is called, which pushes new content into `$info$` and re-renders only that region.

---

### `Shell.bind(source, target, transform=None)`

A convenience method for the most common case: one region's value drives another region's content.

```python
def bind(
    source: str,
    target: str,
    transform: Callable[[Any], Any] | None = None,
) -> None
```

- `source`: the region to observe.
- `target`: the region to update.
- `transform`: an optional function that converts the source value into the target's new value. If `None`, the raw source value is passed directly.

**Example — direct binding:**

```python
# When $search$ text changes, pass the same text to $results$
shell.bind("search", "results")
```

**Example — transform binding:**

```python
DETAIL_MAP = {
    "Users": ["Alice", "Bob", "Carol"],
    "Groups": ["Admin", "Editor", "Viewer"],
}

shell.bind(
    "sidemenu",
    "mainlist",
    transform=lambda label: DETAIL_MAP.get(label, []),
)
```

`bind` is exactly equivalent to:

```python
shell.on_change(
    "sidemenu",
    lambda val: shell.update("mainlist", DETAIL_MAP.get(val, [])),
)
```

---

## Removing Callbacks

`on_change` returns a handle that can be used to deregister the callback:

```python
handle = shell.on_change("sidemenu", my_callback)
# ... later ...
handle.remove()
```

`bind` also returns such a handle.

---

## `Shell.update(name, value)`

Programmatically set the value of a region and schedule a redraw.

```python
def update(name: str, value: Any) -> None
```

Thin delegation to `interaction.set_value(value)`:

- Raises `RegionNotFoundError` if `name` is not a known region; silently
  ignores the call if no interaction is assigned to that region yet.
- Calls `set_value()` on the assigned interaction. Validation (if any) is
  interaction-specific — `update()` does not perform a universal type-check.
- Marks the region dirty; the actual redraw happens lazily on the next
  event-loop tick, not immediately.
- Triggers `on_change` callbacks for `name`.
- Can be called from within a `MenuFunction` callback, from a `Function`
  handler, or from any other code that holds a reference to the `Shell`
  instance.

---

## Chained Updates

Callbacks may themselves call `shell.update()`, creating a chain of updates:

```python
shell.on_change("category", lambda cat: shell.update("subcategory", SUBS[cat]))
shell.on_change("subcategory", lambda sub: shell.update("detail", DETAILS[sub]))
```

**Cycle detection:** If a chain of updates creates a cycle (A → B → A → …), `tui-wysiwyg` detects this and raises `CircularUpdateError` after the first re-entry rather than looping forever.

---

## Thread Safety

The observer system is **not thread-safe**. All `shell.update()` calls must occur on the same thread that owns the event loop. Do not call `shell.update()` from a background thread.

If you need background work to update the TUI, collect results in a queue and call `shell.update()` from within a `MenuFunction` callback or a `Function` handler on the next event loop tick.

---

## Full Wiring Example

```python
from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import MenuReturn, ListView, TextBox

SHELL = """
|=100%==== My App ====|
|{30%  12R  $menu$  }|{  12R  $content$  }|
|=====================|
"""

PAGES = {
    "Home":    ["Welcome to the app.", "Use the menu to navigate."],
    "About":   ["tui-wysiwyg demo.", "Version 0.1.0"],
    "Contact": ["Email: user@example.com"],
}

def main():
    shell = Shell(SHELL)
    shell.assign("menu", MenuReturn({k: k for k in PAGES}))
    shell.assign("content", ListView(PAGES["Home"]))

    shell.bind(
        source="menu",
        target="content",
        transform=lambda label: PAGES.get(label, []),
    )

    result = shell.run()
    print(f"User selected: {result}")

if __name__ == "__main__":
    main()
```
