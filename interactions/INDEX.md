# Interaction Types Index

Each named region in a shell definition can be assigned exactly one interaction method. The interaction method controls how the region is rendered and how the user interacts with it.

Interactions are assigned via `Shell.assign(name, interaction)`. See `API.md` for the full assignment API.

---

## Available Types

| Type | Class | Description | File |
|------|-------|-------------|------|
| menu-function | `MenuFunction` | List of options; each calls a function on selection | [menu_function.md](menu_function.md) |
| menu-return | `MenuReturn` | List of options; selection exits the TUI with a return value | [menu_return.md](menu_return.md) |
| menu-hybrid | `MenuHybrid` | List of options; each item either calls a function or returns a value | [menu_hybrid.md](menu_hybrid.md) |
| textbox | `TextBox` | Free-form text entry with wrapping and scroll | [textbox.md](textbox.md) |
| list | `ListView` | Static/dynamic bulleted or numbered list (display only) | [list.md](list.md) |
| sublist | `SubList` | Nested bulleted or numbered list (display only) | [sublist.md](sublist.md) |
| checkbox | `CheckBox` | Toggleable list of items; multi-select or single-select | [checkbox.md](checkbox.md) |
| function | `Function` | Custom interaction — full control delegated to a callable | [function.md](function.md) |
| form-input | `FormInput` | Structured data-entry form returning a dict of typed values | [form_input.md](form_input.md) |

---

## Common Behavior

All interactive regions share these behaviors:

- **Focus indicator:** The currently focused region has a highlighted border (or, if the terminal does not support it, a `>` marker on the active line).
- **Value:** Every interaction type has a current value accessible via `Shell.get(name)`.
- **Update:** A region's value can be set programmatically via `Shell.update(name, value)`, which re-renders that region only.
- **Change notification:** When a region's value changes (by user input or `Shell.update`), any registered `on_change` callbacks fire. See `INTER_REGION.md`.

---

## Keyboard Navigation Summary

| Key | Effect |
|-----|--------|
| `Tab` | Move focus to next region (reading order) |
| `Shift+Tab` | Move focus to previous region |
| `↑` / `↓` | Navigate within menu / checkbox / form regions |
| `k` / `j` | Vim-style equivalents for `↑` / `↓` in menu and checkbox regions |
| `Enter` | Activate selected item; advance to next form field |
| `Space` | Toggle checkbox item; toggle bool / cycle choices in FormInput |
| `←` / `→` | Toggle bool / cycle choices in FormInput |
| `Ctrl+C` | Raise `KeyboardInterrupt` and exit |
| `Ctrl+Q` | Exit the TUI, `Shell.run()` returns `None` |

---

## Adding a New Interaction Type

1. Create a new file in this directory named `<type_name>.md`.
2. Add a row to the **Available Types** table above.
3. Add the class to the `from tui_wysiwyg.interactions import (...)` block in `API.md`.
4. Add the source file to the module layout in `API.md`.
