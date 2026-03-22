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
├── parser.py            # Shell definition language → LayoutModel (recursive tree)
├── layout.py            # HSplit, VSplit, Panel, LayoutModel, Region data classes
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
| `LayoutModel` | Immutable recursive tree describing the layout: `HSplit` / `VSplit` / `Panel` nodes rooted at `model.root`. Resolves to flat `Region` list via `resolve(width, height)`. |
| `Renderer` | Translates `LayoutModel` + interaction states into terminal output via `blessed`. Supports partial redraws of individual regions. |
| `Events` | Reads keypresses via `blessed`'s `Terminal.inkey()`. Dispatches to the focused region's interaction handler. |
| `Observer` | Tracks `on_change` callbacks per region name. Called by interactions when their value changes. |
| `Interaction` (base) | Defines the interface all interaction types implement: `render(region)`, `handle_key(key) -> bool`, `get_value()`, `set_value(value)`. |

---

## Recursive Layout Model

The layout is represented as a tree of three node types:

```
LayoutNode = HSplit | VSplit | Panel
```

| Node | Fields | Meaning |
|------|--------|---------|
| `HSplit` | `top: LayoutNode \| None`, `bottom: LayoutNode \| None`, `border: BorderRow \| None` | A horizontal split. `top` sits above `border` sits above `bottom`. Either `top` or `bottom` may be `None`. |
| `VSplit` | `left: LayoutNode`, `right: LayoutNode`, `divider: str` | A vertical split (`'single'` = `│`, `'double'` = `║`). |
| `Panel` | `name`, `heading`, `width`, `is_pct`, `pct`, `row_count`, … | Leaf node — a single rectangular region. If `name` is set the region is interactive. |

`LayoutModel` holds `root: LayoutNode | None` and `has_percentage: bool`. The `resolve(term_width, term_height)` method walks the tree recursively and returns a flat `list[Region]` of named regions with absolute `(row, col, width, height)` coordinates.

### Width and height helpers

Two private helpers are exported for use by the renderer:

- `_declared_width(node, available, pct_base)` — returns the width the node claims, or `available` if the node fills remaining space.
- `_declared_height(node, available)` — returns the height the node claims, or the `num_rows_def` fallback.

**`pct_base`** is the total interior width computed once at the outermost `VSplit` of each horizontal section and passed unchanged through nested `VSplit` nodes. It is reset to `None` at `HSplit` boundaries so each new row of sections has its own `pct_base`.

---

## Data Flow

```
Shell Definition String
        │
        ▼
    Parser  (recursive _parse_block)
        │  strips outer |, recurses: HSplit first → VSplit → Panel leaf
        ▼
   LayoutModel (root: HSplit/VSplit/Panel tree)
        │
        │  resolve(term_width, term_height)
        ▼
   list[Region]  ◄──── Terminal size (for % widths)
        │
        ▼
   Renderer (3 passes)
     Pass 1: outer │ walls for all rows
     Pass 2: _render_structure — recursive dividers & borders
     Pass 3: content regions (interaction.render per region)
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

## Renderer Design

`Renderer.full_render()` uses three sequential passes:

1. **Outer walls** — Prints `│` at column 0 and column `term_width-1` for every terminal row. This draws the left and right outer borders for the entire screen height.

2. **Structure pass** — `_render_structure(node, row, col, width, height, pct_base, left_div, right_div, term_width)` walks the tree recursively:
   - **`VSplit`**: draws the vertical divider character (`│` or `║`) for the full height, then recurses into `left` and `right` sub-trees. Tracks `pct_base` for percentage-width columns.
   - **`HSplit`**: recurses into `top`, draws the border row via `draw_border()`, then recurses into `bottom`. `pct_base` is reset to `None` for both children.
   - **`Panel`**: base case — no structural drawing needed.

3. **Content pass** — Iterates the flat `regions` dict; for each region calls `interaction.render()` (if assigned) or `_render_empty_region()`.

`draw_border()` accepts optional `start_col` / `end_col` parameters so partial-width borders (inside one branch of a `VSplit`) are drawn at the correct absolute columns. Intersection characters at divider positions are computed from `_bottom_face_dividers()` / `_top_face_dividers()` which walk the node tree to find all `VSplit` divider columns visible at a border's top or bottom face.

"Partial borders" (a border that spans only part of the screen width) are no longer a special case — after vertical splitting, what was `---|{...}|---` becomes a full `---` border inside a sub-block. The renderer handles it as an ordinary `HSplit` border.

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

## Modal Popup Shells

A modal shell is a second `Shell` instance that renders as a popup overlay at a fixed position on top of a running parent shell.

### Design constraint

`MenuFunction` callbacks fire synchronously *inside* `Shell.run()`, while the parent's terminal context (alternate screen, cbreak mode, hidden cursor) is already active. The modal must **not** re-enter those context managers — doing so would restore the terminal to normal mode and then re-enter, flickering and losing state.

### How it works

1. **`Shell.run_modal(row, col, width, height, parent_shell=None)`** resolves the modal's layout with absolute offsets:

   ```python
   self._resolve_layout(width=width, height=height, offset_row=row, offset_col=col)
   ```

   `LayoutModel.resolve(width, height, offset_row=row, offset_col=col)` passes the offsets through to `_resolve_node`, which already accepts arbitrary `row`/`col`. All `Region` objects emerge with correct absolute terminal coordinates — no translation needed later.

2. **`Renderer.full_render(…, offset_row=row, offset_col=col)`** draws only within the popup bounding box:
   - `term.clear` is **not** called (it would erase the parent shell).
   - Pass 1: outer `│` walls are drawn at `offset_col` and `offset_col + width − 1` for `height` rows only.
   - Pass 2: `_render_structure` starts at `(row=offset_row, col=offset_col + 1)`.
   - Pass 3: content regions use their pre-computed absolute coordinates unchanged.

3. The modal runs its **own event loop** (same structure as `run()`) reading keys from the same terminal. Escape or Ctrl+Q break the loop and return `None`.

4. On exit, if `parent_shell` is provided, `parent_shell._renderer.full_render(…)` is called at `(0, 0)` — a normal full-screen render that overwrites the popup area and restores the parent display.

### Key insight: `is_full_screen` flag

```python
is_full_screen = (offset_row == 0 and offset_col == 0)
if is_full_screen:
    print(term.clear, ...)
```

This single flag gates all behavior that must differ between a full-screen render and a modal render (clearing, blanking rows below the layout, etc.). All existing call sites pass `offset_row=0, offset_col=0` and are unaffected.

### Typical call site

```python
def confirm_delete(sh):
    popup = Shell(CONFIRM_POPUP, _terminal=sh.terminal)
    popup.assign("msg",    ListView(["Delete item?", ""], bullet=" "))
    popup.assign("choice", MenuReturn({"Yes": True, "No": False}))
    # height auto-detected as 7 (all panels use explicit 2R);
    # row/col auto-centered; only width needs to be explicit (fill panels).
    return popup.run_modal(width=30, parent_shell=sh)
```

`run_modal()` must be called from inside a `MenuFunction` callback (while `Shell.run()` is executing) so the terminal context is already active.

---

## Package Structure

```
tui-wysiwyg/
├── pyproject.toml
├── README.md
├── docs/
│   ├── index.md
│   ├── overview.md
│   ├── architecture.md
│   ├── shell-syntax.md
│   ├── interactions/
│   └── widgets/
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
