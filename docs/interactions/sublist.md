# sublist

**Class:** `SubList`

Like `ListView`, but list items may themselves be lists, creating nested indented sublists.

## Constructor

```python
SubList(
    items: list[str | list],
    bullet: str | Literal["1", "A", "a", "I", "i"] = "*",
    indent: int = 2,
)
```

`items` is a recursive structure: each element is either a string or a list of the same structure.

```python
SubList([
    "Top level item",
    ["Nested item 1", "Nested item 2",
        ["Doubly nested"]],
    "Another top level",
])
```

## Behavior

- Each nesting level is indented by `indent` spaces.
- Each nesting level uses the same `bullet` style; numeric/alphabetic counters reset at each new level.
- Otherwise identical to `ListView`.

## Value

`Shell.get(name)` returns the current items structure.
