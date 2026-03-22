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

- [x] In `form.py` `_coerce()`, replace `return bool(value)` for bool fields with strict parsing:
  - Accept `True`/`False` (Python bool) directly
  - Accept `"true"`/`"false"` (case-insensitive strings)
  - Raise `ValueError` for any other input
- [x] Fix `form.py` `__init__` to use `_coerce()` rather than `bool()` when initialising state
- [x] Add test: ambiguous strings (`'1'`, `'yes'`, etc.) raise `ValueError`
- [x] Add test: `'False'`/`'false'`/`'true'` accepted correctly
- [x] Add test: Python `True`/`False` accepted correctly

### 4. Widget test coverage (currently 0%)

- [x] `tests/test_widgets.py` — Confirm, Alert, InputPrompt, ListSelect (single + multi) exit values, Escape/Ctrl+Q, scroll
- [x] `tests/test_widget_file_picker.py` — filter narrows file list, `dirs_only` hides files, navigation into subdirectory, Cancel returns `None`
- [x] `tests/test_widget_date_picker.py` — month navigation, date selection returns `datetime.date`, Cancel returns `None`
- [x] `tests/test_widget_progress.py` — `set_progress()` updates state, cancel via Escape sets `cancelled=True`, context manager restores parent display on exit

---

## P2 — Doc Corrections

### 5. Correct documentation to match implementation

- [x] `docs/api.md` — rewrite `Shell.update()` section: describe as thin delegation to `set_value()`, validation is interaction-specific, redraw is lazy (dirty flag, not immediate)
- [x] `docs/inter-region.md` — same `Shell.update()` correction
- [x] `docs/interactions/index.md` — replace "highlighted border" with "row-level highlighting within the region (reverse video on active row or `>` prefix)"
- [x] `docs/interactions/form-input.md` — remove cursor description; correct validation docs to describe submit-time validation (not nav-time); remove claim that invalid numeric input blocks navigation
- [x] `docs/widgets/index.md` — update `InputPrompt` internals to reference `_SubmittingMenu`; update `ListSelect` buttons description to reference `_SubmittingMenu` in multi mode

### 6. `FilePicker` editable path field drives browsing state

- [x] In `file_picker.py`, add observer on `path` field changes — live navigation updates tree/files without overwriting the path box
- [x] On every keystroke: if value is an existing directory, navigate tree/files; if existing file, navigate to parent and keep file path
- [x] If path does not exist, leave silently (status region support not yet added)
- [x] Add test: typing a directory path navigates tree/files live
- [x] Add test: typing a file path keeps path box; tree/files show parent directory
- [x] Update `docs/widgets/file-picker.md` to describe live path-driven navigation

---

## P2 — README and Positioning

### 7. Rework README top section

- [x] Replace the current opening with a crisp DSL differentiator story: shell layout string → interaction assignment → working UI
- [x] Show a before/after of the raw shell definition string and ASCII-art rendered terminal output

### 8. Add screenshot or GIF to README

- [ ] Capture a terminal screenshot or `asciinema` recording of `example.py` showing at least one widget (Confirm, FilePicker, or DatePicker) — requires interactive terminal session
- [ ] Link it from the README and `docs/index.md`

---

## Next — New Features

### 9. Structured validation/status region support

- [x] Design a `StatusBar` or `ValidationMessage` interaction type (inline, within popup, not global)
- [x] Add standard error/success/info styling
- [x] Wire into `FormInput` and `FilePicker` path validation
- [x] Document in `docs/interactions/`

### 10. Framework comparison table

- [x] Add a comparison section to `docs/index.md` and README
- [x] Table columns: Library, Layout style, Sync/Async, Testability, Ceremony
- [x] Entries: tui_wysiwyg, Textual, prompt_toolkit, urwid

---

## Later — Background Task Support

### 11. Async-safe update queue

- [ ] Design an internal event queue API processed inside the main event loop
- [ ] Document thread-safety contract
- [ ] Add opt-in background update mechanism (does not change default synchronous behavior)
- [ ] Add tests for concurrent updates
