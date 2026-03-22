# Recursive Split-Tree Refactor Plan — COMPLETED

> All four phases were implemented and 213 tests pass. This document is retained for historical reference. The authoritative description of the architecture is now in `ARCHITECTURE.md` and `SHELL_SYNTAX.md`.


## Goal

Replace the hardcoded 3-level layout model (outer HSplit → VSplit → per-column panels) with
a fully recursive split-detection algorithm. The parser will discover structure bottom-up:
search for a full horizontal split first, then a full vertical split, then recurse on each
half. This gives infinite depth automatically and removes all assumptions about split direction.

---

## Phase 1 — New data model (`layout.py`)

### Step 1.1 — Define three recursive node types

- `HSplit(top, bottom, border: BorderRow)` — horizontal split; `top`/`bottom` are child nodes;
  `border` is the `BorderRow` drawn between them (may be `None` if no border line present)
- `VSplit(left, right, divider: str)` — vertical split; `divider` is `'single'` (`|`) or
  `'double'` (`#`)
- `Panel(name, heading, width, is_pct, pct, row_count, row_count_is_pct, row_pct, num_rows_def)`
  — leaf node; absorbs the responsibilities of both the old `ColumnDef` and old `Panel`

Keep `Region`, `BorderRow`, and `PartialBorder` unchanged.

### Step 1.2 — Change `LayoutModel`

Replace `items: list` with `root: LayoutNode | None` (plus `has_percentage`).

### Step 1.3 — Rewrite `LayoutModel.resolve()`

Implement as a recursive helper `_resolve_node(node, row, col, width, height) -> list[Region]`:

- **`HSplit`**: compute top height from top child → resolve top, skip 1 row for border,
  resolve bottom with remaining height
- **`VSplit`**: compute left width from left child's spec → resolve left starting at `col`,
  resolve right starting at `col + left_width + 1`
- **`Panel`**: emit `Region` if named; return consumed (width, height)

`_resolve_col_widths` and `_resolve_panel_heights` can be folded into `_resolve_node` or kept
as private helpers.

---

## Phase 2 — Recursive parser (`parser.py`)

### Step 2.1 — Strip outer `|` before recursing

At the top level, strip the leading and trailing `|` from every non-empty line. All internal
parsing works on "inner" strings throughout the recursion.

### Step 2.2 — `find_full_hsplit(lines) -> int | None`

Scan for the first row index where:
- `line.strip()[0] in ('=', '-')`  AND
- `'{' not in line`

Returns the index, or `None`.

### Step 2.3 — `find_full_vsplit(lines) -> tuple[int, str] | None`

Find the first character position `P` where **all column rows** have `|` or `#` at `P`.
Full border rows (no `{`) are skipped — they contribute fill chars, not dividers.
Returns `(P, char)` or `None`.

### Step 2.4 — `split_vertical(lines, pos) -> (list[str], list[str])`

- Left block: `[line[:pos] for line in lines]`
- Right block: `[line[pos+1:] for line in lines]`

Border rows in the sub-blocks may gain trailing filler from the split; strip as needed.

### Step 2.5 — `parse_leaf(lines, seen_names) -> Panel`

Scan all lines for:
- `$name$` — region name
- `__heading__` — heading text
- Width spec at start of first block: `N%` (percentage) or `N` (fixed chars)
- Row count: `NR` or `N%R`

Returns a `Panel` with extracted values (and increments `seen_names`).

### Step 2.6 — `_parse_block(lines, seen_names) -> LayoutNode`

```
i = find_full_hsplit(lines)
if i is not None:
    border = parse_border_row(lines[i])
    top    = _parse_block(lines[:i],    seen_names) if lines[:i]    else None
    bottom = _parse_block(lines[i+1:],  seen_names) if lines[i+1:] else None
    return HSplit(top=top, border=border, bottom=bottom)

result = find_full_vsplit(lines)
if result is not None:
    pos, char = result
    left_lines, right_lines = split_vertical(lines, pos)
    return VSplit(
        left=_parse_block(left_lines, seen_names),
        right=_parse_block(right_lines, seen_names),
        divider='double' if char == '#' else 'single',
    )

return parse_leaf(lines, seen_names)
```

### Step 2.7 — Update `Parser.parse()`

Strip outer `|`, call `_parse_block()`, wrap result in
`LayoutModel(root=..., has_percentage=...)`.

---

## Phase 3 — Renderer (`renderer.py`)

### Step 3.1 — Replace flat `items` loop with recursive walk

`full_render()` calls `_render_node(node, row, col, width, height, ...)` recursively.

### Step 3.2 — `HSplit` rendering

Draw the border row at the correct absolute row (between top and bottom halves); recurse on
`top` and `bottom` with appropriate row offsets and heights.

### Step 3.3 — `VSplit` rendering

Draw the vertical divider character (`│` or `║`) for the full height of the node; recurse on
`left` and `right` with appropriate column offsets and widths.

### Step 3.4 — `Panel` rendering

Look up the region by name; call `render_region()` or `_render_empty_region()` as now.

### Step 3.5 — Partial borders disappear as a special case

What was previously a "partial border" is now a full `HSplit` border within a sub-block
after vertical splitting. It gets drawn as a normal border at its correct row — no separate
overlay pass needed.

---

## Phase 4 — Tests

### Step 4.1 — `test_layout.py`

- Replace `ColumnDef`/`VSplit(columns=...)` with `HSplit`/`VSplit(left, right)`/`Panel`
- Rewrite `TestResolveColWidths` → test width computation on `Panel` nodes
- Rewrite `TestResolvePanelHeights` → test height computation on `Panel` nodes
- Update `TestLayoutModelResolve` for new `resolve()` behaviour

### Step 4.2 — `test_parser.py`

- Access `model.root` instead of `model.items`
- Navigate the tree (e.g., `model.root.bottom.left` for the left panel of the first section)
- `test_parse_partial_border_creates_two_panels` becomes: verify the left sub-tree contains
  an `HSplit` with two `Panel` children

### Step 4.3 — `test_renderer.py`

- Pass `model.root` tree to renderer
- Remove all references to `VSplit(columns=...)`

### Step 4.4 — `test_style.py`

- One line: `model.items` → `model.root`

---

## Implementation order

1. **Phase 1** — data model (defines contracts; tests break until Phase 2 completes)
2. **Phase 2** — parser (make `test_parser.py` pass)
3. **Phase 3** — renderer (make `test_renderer.py` pass)
4. **Phase 4** — update all four test files incrementally as each phase completes

---

## Key design notes

- **Partial borders are handled automatically.** After a vertical split, what was a
  partial border row (`----|{...}|----`) becomes a full border row (`----`) in the
  left sub-block, and a column row in the right sub-block. No special-case logic needed.
- **Width lives in `Panel` (left child of `VSplit`).** The left child declares its width
  spec; the right child fills the remainder.
- **Height lives in `Panel` (top child of `HSplit`).** The top child declares its row
  count; the bottom child fills the remainder (or has its own count).
- **Empty blocks** (nothing above the first border or below the last) produce `None`
  children in `HSplit`; `resolve()` treats `None` as zero height.
