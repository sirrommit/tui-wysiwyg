# Progress Bar Widget

Display a programmatically-driven progress indicator during a long operation.
The caller drives progress by calling `set_progress()` inside a `with` block;
an optional Cancel button lets the user abort.

---

## Shell Layout

```
|=== <bold>Title</> ===|
|{2R $message$           }|
|------------------------|
|{2R $bar$               }|
|------------------------|
|{1R $buttons$           }|   ← omitted when cancellable=False
|========================|
```

| Region | Interaction | Description |
|--------|-------------|-------------|
| `message` | `ListView` | Status text updated by the caller via `set_progress()`. |
| `bar` | `_BarInteraction` | Draws `[████████░░░░] 55%` scaled to region width. |
| `buttons` | `MenuReturn` | `{"Cancel": None}` — omitted when `cancellable=False`. |

Height is auto-detected:
- **9 rows** when `cancellable=True`  (1+2+1+2+1+1+1)
- **7 rows** when `cancellable=False` (1+2+1+2+1)

---

## Import

```python
from tui_wysiwyg.widgets.progress import Progress
```

---

## Constructor

```python
Progress(
    title: str = "Progress",
    total: int = 100,
    cancellable: bool = True,
    width: int = 50,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"Progress"` | Text shown in the border title (rendered bold). |
| `total` | `int` | `100` | Total number of steps; used to compute the fill fraction. |
| `cancellable` | `bool` | `True` | If `True`, a Cancel button is shown. Check `handle.cancelled` after each `set_progress()`. |
| `width` | `int` | `50` | Width of the popup in characters (including border walls). |

---

## `show()` method — context manager

```python
with Progress(...).show(parent_shell=None, row=None, col=None) as prog:
    prog.set_progress(n, "Status text")
    if prog.cancelled:
        break
```

`show()` is a context manager, not a plain method. The popup is displayed on
`__enter__` and the parent shell is restored on `__exit__`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_shell` | `Shell \| None` | If provided, the parent's display is restored when the popup closes. |
| `row`, `col` | `int \| None` | Override automatic centering. |

**Yields:** a `_ProgressHandle` with:

| Attribute / Method | Description |
|--------------------|-------------|
| `set_progress(current, message="")` | Update the bar to `current` steps and display `message`. Also polls for Cancel. |
| `cancelled` | `True` if the user pressed Cancel or Escape. |

**Returns:** `None` always (progress completed or cancelled — check `handle.cancelled`).

---

## Usage

### Basic cancellable progress

```python
from tui_wysiwyg.widgets.progress import Progress

def process_items(sh, items):
    with Progress(title="Processing…", total=len(items)).show(sh) as prog:
        for i, item in enumerate(items, 1):
            do_work(item)
            prog.set_progress(i, f"Item {i} of {len(items)}")
            if prog.cancelled:
                break
```

### Non-cancellable (runs to completion)

```python
with Progress(title="Importing", total=100, cancellable=False).show(sh) as prog:
    for i in range(1, 101):
        import_row(i)
        prog.set_progress(i, f"Row {i}")
```

### Multi-phase operation

```python
phases = [("Fetching", 30), ("Processing", 50), ("Saving", 20)]
total = sum(n for _, n in phases)
done  = 0

with Progress(title="Multi-step task", total=total).show(sh) as prog:
    for label, steps in phases:
        for _ in range(steps):
            do_step()
            done += 1
            prog.set_progress(done, label)
            if prog.cancelled:
                break
        if prog.cancelled:
            break
```

---

## Bar rendering

The bar scales to the available region width:

```
[████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  30%
```

- `█` — filled portion (scaled from `current / total`)
- `░` — unfilled portion
- 7 characters are reserved for `[`, `]`, ` `, and the 3-digit percentage + `%`

---

## Implementation Notes

`Progress` does **not** use `Shell.run_modal()`. Because `run_modal()` blocks
until a keypress, it cannot be driven programmatically from the same thread.
Instead, `show()` resolves the layout, does an initial `full_render()`, and
then hands control back to the caller (the `with` block).

`set_progress()` updates the interaction state, marks regions dirty via
`shell.update()`, then immediately renders those dirty regions directly
(bypassing the key-driven render loop). It also calls `term.inkey(timeout=0)`
to non-blockingly poll for Cancel.

The popup must be shown from within a parent shell's event-loop context
(e.g., inside a `MenuFunction` callback), so the terminal is already in
`cbreak` / `hidden_cursor` mode.

---

## Example in `example.py`

The demo in `example.py` (option **14. Progress Bar Widget**) shows three
scenarios: a cancellable 20-step bar, a non-cancellable 15-step bar, and a
3-phase multi-step bar. Each scenario uses `time.sleep()` between steps to
simulate work.
