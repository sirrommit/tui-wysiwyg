# Testing Strategy

## Framework

**[`pytest`](https://docs.pytest.org/)** is the test framework. All tests live in `tests/`.

```bash
pip install pytest pytest-cov
pytest
pytest --cov=tui_wysiwyg --cov-report=term-missing
```

---

## Test Categories

### 1. Parser Tests (`tests/test_parser.py`)

Unit tests for the shell definition language parser. No terminal required.

- Valid shell definitions parse to the expected `LayoutModel` with a recursive `HSplit`/`VSplit`/`Panel` tree rooted at `model.root`.
- Tree structure verified by depth-first traversal helpers (`collect_panels`, `collect_borders`, `collect_vsplits`).
- All `ShellSyntaxError` cases are triggered by the appropriate malformed input.
- Width calculation (fixed, percentage, remainder) via `Panel.width`/`Panel.pct`.
- Row-count extraction via `Panel.row_count`.
- Region name extraction and deduplication check.
- Filler rows are correctly ignored.
- Partial border layouts parse to an `HSplit` within one branch of a `VSplit`.

### 2. Layout Tests (`tests/test_layout.py`)

Unit tests for the recursive layout model and geometry helpers.

- `_declared_width(node, available, pct_base)`: fill column, fixed-width column, percentage column, `HSplit` delegation, `VSplit` takes all available.
- `_declared_height(node, available)`: explicit row count, percentage row count, fallback to `num_rows_def`, minimum 1, `HSplit` sums children (+1 for border), `VSplit` takes max child.
- `LayoutModel.resolve()`: region coordinate calculation given known terminal size, percentage → character conversion, row/column position, named-only regions returned, frozen `Region` objects.

### 3. Interaction Tests (`tests/test_interactions.py`)

Unit tests for each interaction type, using the `MockTerminal` (see below).

For each interaction type, test:
- Initial render output matches expected content.
- Correct keys advance/modify state.
- `get_value()` returns the expected value after state changes.
- `set_value()` updates state and marks the region dirty.
- Edge cases: empty item list, single item, overflow content.

### 4. Observer Tests (`tests/test_observer.py`)

Unit tests for the observer/callback system.

- `on_change` callback fires when value changes.
- Multiple callbacks on same region all fire.
- `ChangeHandle.remove()` stops future callbacks.
- `bind()` with and without `transform`.
- `CircularUpdateError` is raised on cyclic updates.
- Callback order is preserved.

### 5. Shell Integration Tests (`tests/test_shell.py`)

Integration tests for the full `Shell` object, using `MockTerminal` and simulated keypresses.

- `assign` / `unassign` work correctly.
- `get` / `update` work correctly.
- `set_focus` moves focus correctly.
- `RegionNotFoundError` raised for unknown region names.
- `run()` returns correct value on `MenuReturn` selection.
- `run()` returns `None` on `Ctrl+Q`.
- Full wiring scenario: sidemenu selection updates info region.

### 6. Renderer Tests (`tests/test_renderer.py`)

Tests that the renderer writes the expected character sequences to the terminal buffer, using `MockTerminal`.

- Border rows render with correct box-drawing characters (double and single styles).
- Border intersection characters are correct when dividers meet a border row.
- `draw_border` with `start_col`/`end_col` renders partial-width borders at the correct position.
- `full_render` with `Parser`→`model.resolve()` tree writes border and content output.
- Partial border layouts render without error.

---

## `MockTerminal`

The `MockTerminal` provides a fake terminal for headless testing. It is defined in `tests/conftest.py` and available as a `pytest` fixture.

### What it replaces

`MockTerminal` replaces the real `blessed.Terminal` object. It:

- Has a configurable `width` and `height` (default 80×24).
- Records all output written to it in an internal buffer.
- Provides a `feed_keys(keys)` method to inject synthetic keypresses.
- Implements all `blessed.Terminal` methods used by `tui_wysiwyg` (position, color, reverse video, etc.) as no-ops or capture methods.
- Does **not** interact with a real TTY.

### Fixture

```python
# tests/conftest.py
import pytest
from tui_wysiwyg.testing import MockTerminal

@pytest.fixture
def terminal():
    return MockTerminal(width=80, height=24)

@pytest.fixture
def shell(terminal):
    """Returns a factory: shell_factory(definition) -> Shell using MockTerminal."""
    from tui_wysiwyg import Shell
    def factory(definition: str) -> Shell:
        return Shell(definition, _terminal=terminal)
    return factory
```

`Shell` accepts an optional `_terminal` parameter (not part of the public API) that substitutes a mock for the real `blessed.Terminal`. This seam is for testing only.

### Usage

```python
def test_menu_return_selection(shell, terminal):
    SHELL = """
    |=100%= Test =|
    |{ 5R $menu$ }|
    |=============|
    """
    s = shell(SHELL)
    s.assign("menu", MenuReturn({"A": 1, "B": 2, "C": 3}))

    terminal.feed_keys(["KEY_DOWN", "KEY_ENTER"])
    result = s.run()

    assert result == 2
```

```python
def test_bind_updates_region(shell, terminal):
    SHELL = """
    |=100%=|
    |{ 5R $src$ }|{ 5R $dst$ }|
    |======|
    """
    s = shell(SHELL)
    s.assign("src", MenuReturn({"X": "x", "Y": "y"}))
    s.assign("dst", ListView([]))
    s.bind("src", "dst", transform=lambda v: [v.upper()])

    terminal.feed_keys(["KEY_ENTER"])  # select "X"
    s.run()

    assert s.get("dst") == ["X"]
```

### `MockTerminal` API

```python
class MockTerminal:
    width: int
    height: int
    buffer: list[str]          # all output written, in order

    def feed_keys(self, keys: list[str]) -> None:
        """Queue synthetic keypresses. Key names match blessed's KEY_* constants."""

    def get_buffer_text(self) -> str:
        """Return buffer contents joined as a single string (strips control sequences)."""

    def get_rendered_lines(self) -> list[str]:
        """Return the current virtual screen state as a list of strings, one per row."""

    def reset(self) -> None:
        """Clear buffer and key queue."""
```

`MockTerminal` lives in `tui_wysiwyg.testing` so it can be imported by downstream code that wants to test TUI integrations:

```python
from tui_wysiwyg.testing import MockTerminal
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=tui_wysiwyg --cov-report=term-missing

# Specific file
pytest tests/test_parser.py

# Specific test
pytest tests/test_interactions.py::test_menu_return_selection

# Verbose
pytest -v
```

---

## CI Considerations

- Tests must pass with no real TTY attached (all tests use `MockTerminal`).
- `pytest` is the only test dependency; `blessed` is a runtime dependency.
- Suggested minimum coverage target: 90% line coverage on `tui_wysiwyg/`.
