# List Select Widget

Lets the user pick one item (**single mode**) or many items (**multi mode**)
from a scrollable list.  In single mode the popup exits immediately on
selection; in multi mode checkboxes are shown and an OK/Cancel row appears.

---

## Shell Layouts

### Single mode (no buttons row)

```
|=== <bold>Title</> ===|
|{2R  $prompt$         }|
|----------------------|
|{10R $items$          }|
|======================|
```

Height auto-detected: **14 rows** (1+2+1+10+1 — no buttons row, no divider).

### Multi mode (with buttons row)

```
|=== <bold>Title</> ===|
|{2R  $prompt$         }|
|----------------------|
|{10R $items$          }|
|----------------------|
|{1R  $buttons$        }|
|======================|
```

Height auto-detected: **16 rows** (1+2+1+10+1+1+1).

| Region | Interaction | Description |
|--------|-------------|-------------|
| `prompt` | `ListView` (display-only) | Descriptive text — 2 rows visible |
| `items` | `MenuReturn` (single) or `CheckBox` (multi) | The selectable list — 10 rows visible, scrollable |
| `buttons` | `_SubmittingMenu` (multi only) | OK captures the checkbox dict; Cancel returns `None` |

---

## Import

```python
from tui_wysiwyg.widgets.list_select import ListSelect
```

---

## Constructor

```python
ListSelect(
    title: str = "Select",
    prompt_lines: list[str] = [],
    items: list[str] | dict = [],
    multi: bool = False,
    width: int = 40,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str` | `"Select"` | Text shown in the border title (rendered bold). |
| `prompt_lines` | `list[str]` | `[]` | Descriptive text above the list. Up to 2 rows visible. |
| `items` | `list \| dict` | `[]` | Items to display. See table below. |
| `multi` | `bool` | `False` | `False` = single selection; `True` = multi-selection with checkboxes. |
| `width` | `int` | `40` | Width of the popup in characters (including border walls). |

### `items` parameter

| Mode | Type | Behaviour |
|------|------|-----------|
| Single | `list[str]` | Each label maps to itself as the return value |
| Single | `dict[str, Any]` | Each label maps to its dict value as the return value |
| Multi | `list[str]` | All checkboxes start unchecked |
| Multi | `dict[str, bool]` | Each label starts checked/unchecked per its value |

---

## `show()` method

```python
result = ListSelect(...).show(parent_shell=None, **run_modal_kwargs)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `parent_shell` | `Shell \| None` | If provided, the parent's display is restored when the popup closes. |
| `**run_modal_kwargs` | | Forwarded to `Shell.run_modal()`. Use `row`/`col` to override centering. |

**Returns:**
- **Single mode:** the value mapped to the selected label (string for lists,
  dict value for dicts), or `None` on Escape / Ctrl+Q.
- **Multi mode:** `dict[str, bool]` of all items and their checked states on
  OK, `None` on Cancel / Escape / Ctrl+Q.

---

## Usage

### Single selection from a list

```python
from tui_wysiwyg.widgets.list_select import ListSelect

def pick_theme(sh):
    theme = ListSelect(
        title="Choose theme",
        prompt_lines=["Select a colour theme:"],
        items=["Dark", "Light", "High Contrast", "Solarized"],
    ).show(parent_shell=sh)

    if theme is not None:
        apply_theme(theme)  # theme is the string, e.g. "Dark"
```

### Single selection from a dict (custom return values)

```python
priority = ListSelect(
    title="Set priority",
    items={"Low": 1, "Medium": 2, "High": 3, "Critical": 4},
).show(parent_shell=sh)
# priority is 1, 2, 3, or 4
```

### Multi-selection from a list

```python
toppings = ListSelect(
    title="Choose toppings",
    prompt_lines=["Select all that apply:"],
    items=["Cheese", "Tomato", "Basil", "Olives", "Mushrooms"],
    multi=True,
).show(parent_shell=sh)

if toppings is not None:
    chosen = [t for t, checked in toppings.items() if checked]
```

### Multi-selection with pre-checked items

```python
features = ListSelect(
    title="Features",
    prompt_lines=["Enable or disable features:"],
    items={
        "Auto-save":    True,
        "Spell-check":  True,
        "Line numbers": False,
        "Word-wrap":    False,
    },
    multi=True,
    width=44,
).show(parent_shell=sh)
```

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Up / Down (or k / j) | Move highlight |
| Enter | Single: select and exit · Multi: toggle checkbox |
| Space | Multi: toggle checkbox |
| Tab | Multi: move focus to buttons |
| Ctrl+Q / Escape | Dismiss, return `None` |

---

## Example in `example.py`

The demo in `example.py` (option **11. List Select Widget**) shows four
scenarios: single list, single dict (priority values), multi list, and
multi dict with pre-checked items.
