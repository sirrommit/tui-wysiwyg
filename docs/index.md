# tui-wysiwyg Documentation

A Python library for building rich terminal user interfaces from a WYSIWYG layout definition language.

---

## Core Docs

| Document | Description |
|----------|-------------|
| [overview.md](overview.md) | Project overview, shell API summary, and interaction type list |
| [architecture.md](architecture.md) | Internal design: components, data flow, renderer, modal popups |
| [api.md](api.md) | Full public API reference for the `Shell` class and all exceptions |
| [inter-region.md](inter-region.md) | Observer pattern for inter-region communication (`on_change`, `bind`) |
| [testing.md](testing.md) | Testing strategy, `MockTerminal`, test categories, and CI notes |
| [update.md](update.md) | Historical: recursive split-tree refactor plan (completed) |

---

## Shell Syntax

| Document | Description |
|----------|-------------|
| [shell-syntax.md](shell-syntax.md) | Full shell definition language specification: borders, columns, named regions, style tags, grammar |

---

## Interactions

| Document | Description |
|----------|-------------|
| [interactions/index.md](interactions/index.md) | Index of all interaction types, common behavior, and keyboard navigation |
| [interactions/menu-function.md](interactions/menu-function.md) | `MenuFunction` — list of options, each calls a function |
| [interactions/menu-return.md](interactions/menu-return.md) | `MenuReturn` — list of options, selection returns a value |
| [interactions/menu-hybrid.md](interactions/menu-hybrid.md) | `MenuHybrid` — combines function and return behaviors |
| [interactions/textbox.md](interactions/textbox.md) | `TextBox` — free-form text entry |
| [interactions/list.md](interactions/list.md) | `ListView` — static/dynamic bulleted or numbered list |
| [interactions/sublist.md](interactions/sublist.md) | `SubList` — nested indented list |
| [interactions/checkbox.md](interactions/checkbox.md) | `CheckBox` — toggleable multi- or single-select list |
| [interactions/function.md](interactions/function.md) | `Function` — custom interaction delegated to a callable |
| [interactions/form-input.md](interactions/form-input.md) | `FormInput` — structured data-entry form |

---

## Widgets

Pre-built modal popup widgets built on top of the core library.

| Document | Description |
|----------|-------------|
| [widgets/index.md](widgets/index.md) | Widget overview, usage pattern, and status table |
| [widgets/confirm.md](widgets/confirm.md) | `Confirm` — Yes/No confirmation dialog |
| [widgets/alert.md](widgets/alert.md) | `Alert` — informational popup with OK button |
| [widgets/input-prompt.md](widgets/input-prompt.md) | `InputPrompt` — single-line text input dialog |
| [widgets/list-select.md](widgets/list-select.md) | `ListSelect` — single or multi-select from a scrollable list |
| [widgets/file-picker.md](widgets/file-picker.md) | `FilePicker` — filesystem browser for selecting files or directories |
| [widgets/date-picker.md](widgets/date-picker.md) | `DatePicker` — monthly calendar for selecting a date |
| [widgets/progress.md](widgets/progress.md) | `Progress` — programmatically-driven progress bar |
