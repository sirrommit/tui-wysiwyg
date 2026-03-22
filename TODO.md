# Implementation TODO

Items are ordered by priority. Complete each group before moving to the next.

---

## P1 — Correctness Bugs

### 1. Scrollable menu interactions

- [x] Introduce `_ScrollableList` base class in `tui_wysiwyg/interactions/`
  - Fields: `_active_index`, `_scroll_offset`
  - Methods: `_clamp_scroll()` (adjusts offset so active item stays in viewport), viewport-slice render helper
  - Optional: `▲`/`▼` overflow indicators on first/last visible row when list is clipped
- [x] Refactor `MenuFunction` to extend `_ScrollableList`
- [x] Refactor `MenuReturn` to extend `_ScrollableList`
- [x] Refactor `MenuHybrid` to extend `_ScrollableList`
- [x] Refactor `CheckBox` to extend `_ScrollableList`
- [x] Add unit tests: navigate active index past viewport height, assert scroll offset advances and active row remains visible (`MenuFunction`, `MenuReturn`, `CheckBox`)
- [ ] Add widget test: `ListSelect` with more items than region height (single and multi mode)
- [ ] Add widget test: `FilePicker` directory with more entries than the files panel height

### 2. Terminal IXON settings not restored after `Shell.run()`

- [x] In `shell.py`, capture `old_attrs = termios.tcgetattr(fd)` before mutating
- [x] Wrap the event loop in a `try/finally` that calls `termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)`
- [x] Add test: mock `tcgetattr`/`tcsetattr`, run `Shell.run()` with immediate exit, assert restore is called
- [x] Add test: verify restore happens on `Ctrl+Q` exit path

### 3. `FormInput` boolean default parsing silently inverts intent

- [ ] In `form.py` `_coerce()`, replace `return bool(value)` for bool fields with strict parsing:
  - Accept `True`/`False` (Python bool) directly
  - Accept `"true"`/`"false"` (case-insensitive strings)
  - Raise `ValueError` for any other input
- [ ] Add test: `FormInput({'f': {'type': 'bool', ..., 'default': 'False'}})` raises `ValueError`
- [ ] Add test: `FormInput({'f': {'type': 'bool', ..., 'default': 'true'}})` → value is `True`
- [ ] Add test: `FormInput({'f': {'type': 'bool', ..., 'default': False}})` → value is `False`

### 4. Widget test coverage (currently 0%)

- [ ] `tests/test_widget_confirm.py` — exit values (Yes/No), Escape/Ctrl+Q returns `None`, parent display restored
- [ ] `tests/test_widget_alert.py` — OK returns `True`, Escape returns `None`
- [ ] `tests/test_widget_input_prompt.py` — typed value returned on OK, Cancel returns `None`, initial text pre-populated
- [ ] `tests/test_widget_list_select.py` — single mode selection, multi mode selection, Cancel returns `None`
- [ ] `tests/test_widget_file_picker.py` — filter narrows file list, `dirs_only` hides files, navigation into subdirectory, Cancel returns `None`
- [ ] `tests/test_widget_date_picker.py` — month navigation, date selection returns `datetime.date`, Cancel returns `None`
- [ ] `tests/test_widget_progress.py` — `set_progress()` updates state, cancel via Escape sets `cancelled=True`, context manager restores parent display on exit

---

## P2 — Doc Corrections

### 5. Correct documentation to match implementation

- [ ] `docs/api.md` — rewrite `Shell.update()` section: describe as thin delegation to `set_value()`, validation is interaction-specific, redraw is lazy (dirty flag, not immediate)
- [ ] `docs/inter-region.md` — same `Shell.update()` correction
- [ ] `docs/interactions/index.md` — replace "highlighted border" with "row-level highlighting within the region (reverse video on active row or `>` prefix)"
- [ ] `docs/interactions/form-input.md` — remove cursor description; correct validation docs to describe submit-time validation (not nav-time); remove claim that invalid numeric input blocks navigation
- [ ] `docs/widgets/index.md` — update `InputPrompt` internals to reference `_SubmittingMenu`; update `ListSelect` buttons description to reference `_SubmittingMenu` in multi mode

### 6. `FilePicker` editable path field drives browsing state

- [ ] In `file_picker.py`, add observer on `path` field changes
- [ ] On Tab or Enter within the path field: if value is an existing directory, call `_set_dir()` to navigate; if existing file, navigate to parent and populate path
- [ ] If path does not exist, update a status message region (or leave silently until status region support is added)
- [ ] Add test: typing a directory path and pressing Tab updates tree/files panel
- [ ] Add test: typing a file path and pressing Tab selects it and shows parent directory
- [ ] Update `docs/widgets/file-picker.md` to describe Tab/Enter trigger for path-driven navigation

---

## P2 — README and Positioning

### 7. Rework README top section

- [ ] Replace the current opening with a crisp DSL differentiator story: shell layout string → interaction assignment → working UI
- [ ] Show a side-by-side (or before/after) of the raw shell definition string and the rendered terminal output

### 8. Add screenshot or GIF to README

- [ ] Capture a terminal screenshot or `asciinema` recording of `example.py` showing at least one widget (Confirm, FilePicker, or DatePicker)
- [ ] Link it from the README and `docs/index.md`

---

## Next — New Features

### 9. Structured validation/status region support

- [ ] Design a `StatusBar` or `ValidationMessage` interaction type (inline, within popup, not global)
- [ ] Add standard error/success/info styling
- [ ] Wire into `FormInput` and `FilePicker` path validation
- [ ] Document in `docs/interactions/`

### 10. Framework comparison table

- [ ] Add a comparison section to `docs/index.md` or README
- [ ] Table columns: Library, Layout style, Sync/Async, Testability, Ceremony
- [ ] Entries: tui_wysiwyg, Textual, prompt_toolkit, urwid

---

## Later — Background Task Support

### 11. Async-safe update queue

- [ ] Design an internal event queue API processed inside the main event loop
- [ ] Document thread-safety contract
- [ ] Add opt-in background update mechanism (does not change default synchronous behavior)
- [ ] Add tests for concurrent updates
