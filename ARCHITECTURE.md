# tui-wysiwyg Architecture

## Overview

`tui-wysiwyg` is a Python library for building rich terminal user interfaces from a WYSIWYG layout definition language. Developers describe the visual structure of a screen as a formatted string (the "shell"), assign interaction behaviors to named regions, and call the rendering loop.

## Design Principles

1. **Layout is declarative.** The shell definition string is pure structure — no behavior.
2. **Behavior is assigned, not embedded.** Interaction types are attached to named regions at runtime.
3. **The caller owns the loop.** The library provides `Shell.run()` which the caller explicitly invokes; it does not auto-start.
4. **Regions are independent.** Regions render and update independently — a change to one region does not force a full redraw.
5. **Fail loudly.** Malformed shell definitions or invalid assignments raise exceptions rather than silently degrading.

---

## Rendering Backend: `blessed`

**Decision:** Use the [`blessed`](https://pypi.org/project/blessed/) library as the terminal rendering backend.

**Rationale:**
- Wraps `curses`/`terminfo` cleanly; no direct `curses` boilerplate required.
- Handles terminal capability detection automatically (reverse highlighting, color depth, unicode support).
- Provides `Terminal.inkey()` for non-blocking/timeout key reads, which simplifies the event loop.
- Handles `SIGWINCH` (terminal resize signal) in a straightforward way.
- Has a path to Windows support via `jinxed` (a `blessed`-compatible shim) if needed later, without API changes.
- Actively maintained and widely used.

---

## Component Breakdown

```
tui_wysiwyg/
├── __init__.py          # Public API re-exports
├── shell.py             # Shell class — top-level user-facing object
├── parser.py            # Shell definition language → LayoutModel
├── layout.py            # LayoutModel, Row, Column, Region data classes
├── renderer.py          # Terminal rendering via blessed
├── events.py            # Keyboard input reading and dispatch
├── observer.py          # Observer/callback system for inter-region communication
├── exceptions.py        # ShellSyntaxError, RegionNotFoundError, etc.
└── interactions/
    ├── __init__.py
    ├── base.py          # Interaction abstract base class
    ├── menu.py          # MenuFunction, MenuReturn, MenuHybrid
    ├── textbox.py       # TextBox
    ├── list_view.py     # List, SubList
    ├── checkbox.py      # CheckBox
    └── function.py      # Function (custom interaction)
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `Shell` | Top-level API. Owns the layout, renderer, and event loop. Exposes `assign`, `run`, `get`, `update`, `bind`. |
| `Parser` | Tokenizes and validates the shell definition string. Produces a `LayoutModel`. |
| `LayoutModel` | Immutable data structure describing the grid: rows, columns, region names, and dimensions. |
| `Renderer` | Translates `LayoutModel` + interaction states into terminal output via `blessed`. Supports partial redraws of individual regions. |
| `Events` | Reads keypresses via `blessed`'s `Terminal.inkey()`. Dispatches to the focused region's interaction handler. |
| `Observer` | Tracks `on_change` callbacks per region name. Called by interactions when their value changes. |
| `Interaction` (base) | Defines the interface all interaction types implement: `render(region)`, `handle_key(key) -> bool`, `get_value()`, `set_value(value)`. |

---

## Data Flow

```
Shell Definition String
        │
        ▼
    Parser
        │  produces
        ▼
   LayoutModel  ◄──── Terminal size (for % widths)
        │
        ▼
   Renderer ◄──── Interaction.render() for each named region
        │
        ▼
   Terminal Output

User Keypress
        │
        ▼
   Events.read()
        │
        ▼
   Active Region's Interaction.handle_key()
        │  if value changes:
        ▼
   Observer.notify(region_name, new_value)
        │
        ▼
   Registered callbacks → Shell.update(other_region, new_value)
        │
        ▼
   Renderer.redraw_region(other_region)
```

---

## Terminal Resize Handling

When percentage-based widths or heights are used in the shell definition, the layout must reflow on terminal resize.

- `blessed` surfaces resize events as a `blessed.keyboard.Keystroke` with `code == Terminal.KEY_RESIZE`, or via `SIGWINCH`.
- On resize, `Shell` re-invokes the `Parser` with the new terminal dimensions to produce a new `LayoutModel`.
- The `Renderer` performs a full redraw with the updated layout.
- If only fixed character widths/heights are used, resize events are ignored.

---

## Focus Model

- At any time, exactly one region has **focus**.
- Focus is moved between regions via `Tab` / `Shift+Tab` (or arrow keys at region boundaries, TBD).
- The focused region receives all keypress events.
- The `Renderer` visually distinguishes the focused region (e.g., highlighted border).
- Focus order follows reading order: left-to-right, top-to-bottom through the grid.

---

## Menu-Function Control Flow

When a `MenuFunction` interaction calls a user-provided function:

1. The TUI remains in control of the terminal (alt-screen stays active).
2. The function is called synchronously with the `Shell` instance as an argument: `fn(shell)`.
3. While the function executes, the TUI is paused (no keypresses are read).
4. The function may call `shell.update(name, value)` to modify region state.
5. When the function returns, the TUI re-renders any dirty regions and resumes the event loop.

This keeps the model single-threaded and avoids terminal state complexity.

---

## Package Structure

```
tui-wysiwyg/
├── pyproject.toml
├── README.md
├── OVERVIEW.md
├── ARCHITECTURE.md
├── SHELL_SYNTAX.md
├── INTERACTIONS.md
├── API.md
├── INTER_REGION.md
├── TESTING.md
├── example.shell
├── tests/
│   ├── conftest.py        # MockTerminal fixture
│   ├── test_parser.py
│   ├── test_layout.py
│   ├── test_renderer.py
│   ├── test_interactions.py
│   └── test_shell.py
└── tui_wysiwyg/
    └── ... (as above)
```
