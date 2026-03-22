# Date Picker Widget

Browse a monthly calendar and select a date.

---

## Shell Layout

```
|=== <bold>Title</> ===|
|{2R $nav$               }|
|------------------------|
|{8R $calendar$          }|
|------------------------|
|{1R $buttons$           }|
|========================|
```

| Region | Interaction | Description |
|--------|-------------|-------------|
| `nav` | `_NavBar` (custom) | Renders centred month/year label (row 0) and `< Prev` / `Next >` hints (row 1). Left/Right arrows change the displayed month. |
| `calendar` | `_CalendarInteraction` (custom) | Draws weekday header row + up to 6 date rows (Su Mo Tu We Th Fr Sa). Arrow keys move the highlighted cursor date. Enter confirms. |
| `buttons` | `_SubmittingMenu` | OK returns the cursor date; Cancel returns `None`. |

Height is auto-detected: **14 rows** (1+2+1+8+1+1+1).

---

## Import

```python
from tui_wysiwyg.widgets.date_picker import DatePicker
```

---

## Constructor

```python
DatePicker(
    initial: datetime.date | None = None,
    title: str = "Select Date",
    width: int = 30,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `initial` | `datetime.date \| None` | `datetime.date.today()` | Date to highlight on open. |
| `title` | `str` | `"Select Date"` | Text shown in the border title (rendered bold). |
| `width` | `int` | `30` | Width of the popup in characters (including border walls). Must be at least 23 to fit the weekday header. |

---

## `show()` method

```python
date = DatePicker(...).show(parent_shell=None, **run_modal_kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_shell` | `Shell \| None` | If provided, the parent's display is restored when the popup closes. |
| `**run_modal_kwargs` | | Forwarded to `Shell.run_modal()`. Use `row`/`col` to override auto-centering. |

**Returns:** `datetime.date` on OK or Enter, `None` on Cancel / Escape / Ctrl+Q.

---

## Usage

### Basic usage — pick a date starting from today

```python
import datetime
from tui_wysiwyg.widgets.date_picker import DatePicker

def schedule(sh):
    d = DatePicker(title="Choose Date").show(parent_shell=sh)
    if d is not None:
        print(f"Scheduled for {d.isoformat()}")
```

### Open at a specific date

```python
initial = datetime.date(2026, 6, 15)
d = DatePicker(initial=initial, title="Select start date").show(parent_shell=sh)
```

### Calculate days from today

```python
d = DatePicker(title="Set Deadline").show(parent_shell=sh)
if d is not None:
    days = (d - datetime.date.today()).days
    print(f"Deadline in {days} days")
```

---

## Navigation

| Key | Action |
|-----|--------|
| Left / Right | Move cursor by one day (in `$calendar$`) or change month (in `$nav$`) |
| Up / Down | Move cursor by one week (in `$calendar$`) or change month (in `$nav$`) |
| Enter | Confirm selected date (exits the picker) |
| Tab / Shift+Tab | Cycle focus between `nav`, `calendar`, `buttons` |
| OK button | Confirm selected date |
| Cancel button | Dismiss, return `None` |
| Escape / Ctrl+Q | Dismiss, return `None` |

When the cursor moves past the last day of a month, the calendar automatically advances to the next month (or retreats to the previous month).

---

## Date rendering

| Date | Appearance |
|------|------------|
| Cursor date | `bold + reverse` |
| Today's date | `bold` |
| Other dates | plain text |
| Padding cells (day 0) | blank |

---

## Implementation Notes

`$nav$` and `$calendar$` share a mutable `state` dict:

```python
state = {"month": _first_of(initial), "cursor": initial}
```

- `_NavBar` reads and writes `state["month"]`; when the month changes it calls
  `shell.update("calendar", None)` to force a calendar redraw.
- `_CalendarInteraction` reads and writes `state["cursor"]`; when the cursor
  crosses a month boundary it also updates `state["month"]` and calls
  `shell.update("nav", None)` to refresh the nav label.

`_CalendarInteraction.signal_return()` returns `(True, cursor)` when Enter is
pressed, allowing `run_modal()` to exit with the selected date even without
pressing the OK button.

The `_SubmittingMenu("calendar")` OK button reads `shell.get("calendar")`,
which returns `state["cursor"]` via `get_value()`.

---

## Example in `example.py`

The demo in `example.py` (option **13. Date Picker Widget**) shows three
scenarios: pick any date from today, open at a preset date (June 2026), and
set a deadline with days-until calculation displayed in the result bar.
