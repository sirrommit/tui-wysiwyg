# form-input

**Class:** `FormInput`

A structured data-entry form. Displays a list of labeled fields, each with a type, optional default, and optional constraints. When the user completes the form and activates the Submit entry, returns a dictionary of variable names to their typed values.

## Constructor

```python
FormInput(fields: dict[str, dict])
```

`fields` maps variable names (used as keys in the returned dict) to field definition dictionaries.

## Field Definition

Each field definition is a dictionary. All keys are optional except `type` and `descriptor`.

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `type` | `str` | Yes | One of `"str"`, `"int"`, `"float"`, `"bool"`, `"choices"` |
| `descriptor` | `str` | Yes | Human-readable label shown next to the field |
| `default` | Any | No | Pre-filled value. Must match the field's `type`. |
| `required` | `bool` | No | If `True`, the field must be non-empty to submit. Default: `False`. |
| `placeholder` | `str` | No | Hint text shown when the field is empty. Shown in a dimmed style. Applies to `str`, `int`, and `float` types only. |
| `validator` | `Callable[[Any], bool \| str]` | No | Called with the parsed value when the user leaves the field. Return `True` to accept, or a non-empty string as an error message to reject. |
| `options` | `list[Any]` | For `choices` | The list of valid choices. Required when `type` is `"choices"`. Raises `ValueError` at construction if absent for a `choices` field. |

## Example

```python
FormInput({
    "username": {
        "type": "str",
        "descriptor": "Username",
        "required": True,
        "placeholder": "e.g. alice",
        "validator": lambda v: True if v.isalnum() else "Only letters and digits allowed",
    },
    "age": {
        "type": "int",
        "descriptor": "Age",
        "default": 18,
        "validator": lambda v: True if v >= 0 else "Age must be non-negative",
    },
    "score": {
        "type": "float",
        "descriptor": "Score",
        "required": False,
        "placeholder": "0.0–100.0",
    },
    "active": {
        "type": "bool",
        "descriptor": "Active",
        "default": True,
    },
    "role": {
        "type": "choices",
        "descriptor": "Role",
        "options": ["Admin", "Editor", "Viewer"],
        "default": "Viewer",
    },
})
```

## Rendering

Fields are rendered in insertion order, one per row:

```
  Username     : [alice             ]
  Age          : [25                ]
  Score        : [                  ]   ← placeholder shown dimmed: 0.0–100.0
  Active       : < Yes >
  Role         : < Viewer          >
  ──────────────────────────────────
  [ Submit ]
```

- The separator line and `[ Submit ]` entry appear at the bottom of the field list.
- The focused row is highlighted (reverse video or `>` prefix fallback).
- For `str`, `int`, and `float` fields: the value area is an inline single-line text input; there is no blinking cursor — the focused row is shown in reverse video like any other active row.
- For `bool` fields: the current value is shown as `< Yes >` or `< No >`.
- For `choices` fields: the current selection is shown as `< Option >`.
- If a field has a validation error, the error message is shown on the line below the field in a dimmed or distinct style:

```
  Age          : [abc               ]
                  ! Must be a whole number
```

- If content overflows the region height, the field list scrolls; the Submit entry is always visible at the bottom.

## Field Types and Editing

| Type | Editing behavior |
|------|-----------------|
| `"str"` | Standard text entry. All printable characters accepted. |
| `"int"` | Text entry. Only digits and a leading `-` accepted (non-digit keypresses are silently ignored). |
| `"float"` | Text entry. Only digits, a single `.`, and a leading `-` accepted. |
| `"bool"` | Not a text field. `Space`, `Enter`, `←`, or `→` toggles between `True` and `False`. |
| `"choices"` | Not a text field. `←` / `→` or `Space` cycles through `options`. |

## Validation

All validation runs at **submit time** only — navigation between fields never
triggers validation.  The user can freely move focus away from a field
regardless of whether its current value is valid.

When the user activates `[ Submit ]`, the following checks run for each
field in order:

1. **Type parse:** For `int` and `float`, the entered string is parsed.
   If it cannot be parsed (e.g. `"abc"` for an `int`), an error is recorded.
2. **`validator`:** If provided, called with the parsed value. If it returns
   a string, that string is recorded as an error.
3. **`required`:** If `True` and the field is empty (or the parsed value is
   falsy), an error is recorded.

## Submit Behavior

When the user activates `[ Submit ]` (navigates to it and presses `Enter`):

1. All field validations are re-run (type parse + `validator` + `required`).
2. If any field has an error, all errors are shown simultaneously and focus moves to the first field with an error. The form does not close.
3. If all fields are valid, `Shell.run()` returns the result dictionary (see **Value** below).

## Value

`Shell.get(name)` returns a `dict[str, Any]` mapping each variable name to its current (possibly unparsed or partial) value.

On submission, `Shell.run()` returns a `dict[str, Any]` where:

- `"str"` fields → `str`
- `"int"` fields → `int`
- `"float"` fields → `float`
- `"bool"` fields → `bool`
- `"choices"` fields → the selected element from `options` (preserving its original type)
- Empty non-required fields → `None`

## Construction Errors

Raised immediately at `FormInput(...)` construction time, before the TUI starts:

| Error | Condition |
|-------|-----------|
| `ValueError: field 'x' missing required key 'type'` | A field definition omits `type` |
| `ValueError: field 'x' missing required key 'descriptor'` | A field definition omits `descriptor` |
| `ValueError: field 'x' type 'choices' requires 'options'` | A `choices` field has no `options` list |
| `ValueError: field 'x' default value does not match type` | `default` cannot be coerced to the declared `type` |
| `ValueError: field 'x' options must be a non-empty list` | `options` is empty |
