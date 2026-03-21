# Public API Reference

## Installation

```bash
pip install tui-wysiwyg
```

## Quick Start

```python
from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import MenuReturn

SHELL = """
|=100%= My App =|
|{ 12R $menu$ }|
|===============|
"""

shell = Shell(SHELL)
shell.assign("menu", MenuReturn({"Option A": "a", "Option B": "b"}))
result = shell.run()
print(result)  # "a" or "b"
```

---

## `Shell`

The top-level object. Parses the shell definition, holds interaction assignments, and owns the event loop.

```python
class Shell(definition: str)
```

### Constructor

| Parameter | Type | Description |
|-----------|------|-------------|
| `definition` | `str` | The shell definition string (see `SHELL_SYNTAX.md`) |

Raises `ShellSyntaxError` if the definition is malformed.

The terminal size is read at construction time to resolve any `%`-based widths and heights. If `%` values are present, the layout will reflow automatically on terminal resize during `run()`.

---

### `Shell.assign(name, interaction)`

Assign an interaction method to a named region.

```python
def assign(name: str, interaction: Interaction) -> None
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Region name as declared in the shell definition (without `$`) |
| `interaction` | `Interaction` | Any interaction instance (see `INTERACTIONS.md`) |

Raises `RegionNotFoundError` if `name` does not exist in the shell definition.
Raises `ValueError` if the region already has an assigned interaction (call `Shell.unassign` first).

Regions without an assigned interaction are rendered as static display areas and cannot receive focus.

---

### `Shell.run()`

Start the TUI, enter the event loop, and block until the TUI exits.

```python
def run() -> Any
```

**Returns:** The return value determined by a `MenuReturn` or `MenuHybrid` selection, or `None` if the user exits via `Ctrl+Q`.

**Behavior:**
1. Saves terminal state.
2. Enters alternate screen mode.
3. Performs an initial full render.
4. Enters the event loop: reads keypresses, dispatches to the focused region, re-renders dirty regions.
5. On exit (return value selected or `Ctrl+Q`): restores terminal state, leaves alternate screen.

Raises `KeyboardInterrupt` if the user presses `Ctrl+C`.

---

### `Shell.get(name)`

Get the current value of a named region.

```python
def get(name: str) -> Any
```

Returns the value as defined by the region's interaction type (see `INTERACTIONS.md` for per-type return values). Returns `None` for regions with no assigned interaction or for regions whose interaction has not yet produced a value.

Raises `RegionNotFoundError` if `name` does not exist.

---

### `Shell.update(name, value)`

Programmatically set a region's value and re-render it.

```python
def update(name: str, value: Any) -> None
```

- Validates that `value` is appropriate for the region's interaction type.
- Fires any `on_change` callbacks registered on `name`.
- Re-renders the region immediately (or marks it dirty if called outside the event loop).

Raises `RegionNotFoundError` if `name` does not exist.
Raises `ValueError` if `value` is not compatible with the assigned interaction type.

---

### `Shell.on_change(name, callback)`

Register a callback to fire when a region's value changes.

```python
def on_change(name: str, callback: Callable[[Any], None]) -> ChangeHandle
```

Returns a `ChangeHandle` with a `.remove()` method to deregister the callback.

See `INTER_REGION.md` for full details and examples.

---

### `Shell.bind(source, target, transform=None)`

Convenience method: when `source` changes, update `target` with the (optionally transformed) new value.

```python
def bind(
    source: str,
    target: str,
    transform: Callable[[Any], Any] | None = None,
) -> ChangeHandle
```

Returns a `ChangeHandle` with a `.remove()` method.

See `INTER_REGION.md` for full details and examples.

---

### `Shell.unassign(name)`

Remove the interaction assigned to a region, returning it to a static display area.

```python
def unassign(name: str) -> Interaction | None
```

Returns the removed interaction, or `None` if no interaction was assigned.
Raises `RegionNotFoundError` if `name` does not exist.

---

### `Shell.terminal`

The underlying `blessed.Terminal` instance. Available for use inside `Function` interaction handlers that need to render custom content directly.

```python
@property
def terminal(self) -> blessed.Terminal
```

---

### `Shell.focus`

The name of the currently focused region, or `None` if no region has focus.

```python
@property
def focus(self) -> str | None
```

---

### `Shell.set_focus(name)`

Move focus to a named region programmatically.

```python
def set_focus(name: str) -> None
```

Raises `RegionNotFoundError` if `name` does not exist.
Raises `ValueError` if the region has no assigned interaction (static regions cannot receive focus).

---

## Interaction Classes

All interaction classes live in `tui_wysiwyg.interactions`. See `INTERACTIONS.md` for full behavioral documentation.

```python
from tui_wysiwyg.interactions import (
    MenuFunction,
    MenuReturn,
    MenuHybrid,
    TextBox,
    ListView,
    SubList,
    CheckBox,
    Function,
    FormInput,
)
```

### Common Base: `Interaction`

All interaction classes inherit from `Interaction` (abstract base class in `tui_wysiwyg.interactions.base`). The base class is not part of the public API and should not be instantiated directly.

---

## Exceptions

```python
from tui_wysiwyg.exceptions import (
    ShellSyntaxError,        # Malformed shell definition string
    RegionNotFoundError,     # Named region does not exist in the shell
    CircularUpdateError,     # on_change callbacks form a cycle
)
```

### `ShellSyntaxError`

Raised during `Shell.__init__()` when the shell definition string is malformed.

```
tui_wysiwyg.exceptions.ShellSyntaxError: duplicate region name 'menu' at line 4
```

Includes a `.line` attribute (1-based line number) and `.message` attribute.

### `RegionNotFoundError`

Raised by `assign`, `get`, `update`, `on_change`, `bind`, `unassign`, and `set_focus` when the given name does not match any region in the shell definition.

```
tui_wysiwyg.exceptions.RegionNotFoundError: no region named 'typo' in this shell
```

### `CircularUpdateError`

Raised when `on_change` callbacks form a dependency cycle.

```
tui_wysiwyg.exceptions.CircularUpdateError: circular update detected: 'a' -> 'b' -> 'a'
```

---

## `Region` (Data Class)

Passed to `Function` interaction handlers. Provides read-only geometry information.

```python
@dataclass(frozen=True)
class Region:
    name: str          # Region name
    row: int           # Top row in terminal coordinates (0-based)
    col: int           # Left column in terminal coordinates (0-based)
    width: int         # Width in characters
    height: int        # Height in rows
```

---

## `ChangeHandle`

Returned by `Shell.on_change()` and `Shell.bind()`.

```python
class ChangeHandle:
    def remove(self) -> None:
        """Deregister the callback."""
```

---

## Module Layout

```
tui_wysiwyg/
├── __init__.py                  # exports: Shell
├── shell.py
├── parser.py
├── layout.py                    # exports: LayoutModel, Region
├── renderer.py
├── events.py
├── observer.py                  # exports: ChangeHandle
├── exceptions.py                # exports: ShellSyntaxError, RegionNotFoundError, CircularUpdateError
└── interactions/
    ├── __init__.py              # exports all interaction classes
    ├── base.py                  # Interaction ABC (not public)
    ├── menu.py                  # MenuFunction, MenuReturn, MenuHybrid
    ├── textbox.py               # TextBox
    ├── list_view.py             # ListView, SubList
    ├── checkbox.py              # CheckBox
    ├── function.py              # Function
    └── form.py                  # FormInput
```
