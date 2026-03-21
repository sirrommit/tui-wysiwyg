# Shell Definition Language Specification

A "shell" is a multi-line string that defines the visual structure of a TUI screen. It describes a grid of regions using ASCII box-drawing characters and special syntax markers.

---

## Minimal Example

```
|=100%==== My App ====|
|{50%  $left$  }|{  $right$  }|
|=====================|
```

---

## Full Example

See `example.shell` for a complete multi-region layout.

---

## Top-Level Structure

Every shell definition is a series of **rows**. Each row is a line in the string. Rows fall into three categories:

| Row Type | Description |
|----------|-------------|
| **Border row** | A horizontal rule spanning the full width (`====` or `----`) |
| **Column row** | A line containing one or more `{ }` column blocks |
| **Filler row** | A column row that contains no `$name$` markers and no row-count marker — used for human readability only, ignored by the parser |

---

## Outer Border

The entire layout is wrapped in `|` characters on the left and right edges. The outer border is required on every row.

```
|...|
```

---

## Horizontal Rules

Horizontal rules span the full terminal width between the outer `|` borders.

| Syntax | Rendered as |
|--------|------------|
| `====` (one or more `=`) | Double horizontal line |
| `----` (one or more `-`) | Single horizontal line |

Rules may contain title text between the `=` or `-` characters:

```
|==== My Application ====|
|---- Section Title ------|
```

Text in a rule is centered in the available width.

---

## Vertical Dividers

Vertical dividers separate columns within a row.

| Character | Rendered as |
|-----------|------------|
| `\|` | Single vertical line |
| `#` | Double vertical line |

Vertical dividers span the full height of the tallest column in their row group.

---

## Column Blocks

A column block defines a rectangular region of the screen.

```
{width  content  }
```

- Opens with `{`, closes with `}`.
- The `{` and `}` characters are **not rendered** in the TUI unless escaped (see Escaping).
- Multiple column blocks on the same line create side-by-side columns.
- Columns in a row are separated by vertical dividers (`|` or `#`).

### Column Width

Width is specified immediately after `{` with no space:

| Format | Meaning |
|--------|---------|
| `{50%` | 50% of terminal width |
| `{25` | 25 character columns wide |
| `{` (no spec) | Fills remaining available width |

At most one column per row may omit the width; it receives all remaining space after fixed/percentage columns are calculated.

**Percentage widths:** When any column in a shell uses `%` widths, the layout reflows on terminal resize. If all widths are fixed character counts, resize events are ignored.

**Width calculation rules:**
1. Sum all fixed-character-width columns.
2. Calculate percentage columns relative to terminal width.
3. The remainder (if any unspecified column exists) fills the gap.
4. If column widths sum to more than terminal width, a `ShellSyntaxError` is raised at parse time (for fixed widths) or at render time (for percentage widths that overflow).

---

## Row Count Marker

A row count marker defines how many terminal rows a column block occupies.

```
{25%  12R  $region_name$  }
```

| Format | Meaning |
|--------|---------|
| `12R` | 12 terminal rows tall |
| `50%R` | 50% of terminal height |

**Rules:**
- The row count marker must appear in the **first content row** of the column block (the row immediately following the header row, if any).
- All columns in a row group must agree on height — conflicting row count markers raise a `ShellSyntaxError`.
- If no row count marker is provided, the column block height is determined by the number of content rows in the shell definition (filler rows included in the count). At least one row count marker per row group is recommended.
- Percentage row heights trigger reflow on terminal resize.

---

## Named Regions

A named region marks a column block as interactive — it can be assigned an interaction method.

```
$region_name$
```

- Names consist of lowercase letters, digits, and underscores: `[a-z0-9_]+`
- Names must be unique within a shell definition. Duplicate names raise `ShellSyntaxError`.
- A named region may appear anywhere inside a column block's content area.
- Column blocks without a `$name$` are static display areas (headings, borders, etc.).

---

## Text Formatting

| Syntax | Effect |
|--------|--------|
| `__text__` | Underlined text (falls back to plain text if terminal does not support underline) |

Text formatting may appear anywhere in a column block's content, including header rows.

---

## Filler Rows

Filler rows are column rows that contain neither a `$name$` nor a row count marker. They are valid shell syntax and are ignored by the parser — their only purpose is to make the shell definition visually readable as a diagram.

```
|{  $menu$  }|{  $info$  }|   ← content row (has $name$)
|{          }|{          }|   ← filler row (ignored)
|{          }|{          }|   ← filler row (ignored)
```

---

## Escaping

To render a literal `{`, `}`, `$`, `#`, `__`, `----`, or `====` as text content, prefix the character with `\`:

| Escape | Output |
|--------|--------|
| `\{` | `{` |
| `\}` | `}` |
| `\$` | `$` |
| `\#` | `#` |
| `\__text__` | `__text__` (no underline) |

---

## Complete Grammar (Informal)

```
shell        ::= row+
row          ::= border_row | column_row
border_row   ::= "|" ("=" | "-")+ [text ("=" | "-")+] "|" NEWLINE
column_row   ::= "|" col_block (divider col_block)* "|" NEWLINE
col_block    ::= "{" [width] content "}"
width        ::= INTEGER "%" | INTEGER   (no space before content)
content      ::= (row_count | name | formatted_text | filler_text)*
row_count    ::= INTEGER "R" | INTEGER "%" "R"
name         ::= "$" [a-z0-9_]+ "$"
formatted    ::= "__" text "__"
divider      ::= "|" | "#"
```

---

## Parser Behavior

The parser processes the shell definition string as follows:

1. Split on newlines.
2. Strip each line. Empty lines are ignored.
3. Validate that each line begins and ends with `|`.
4. Classify each line as a border row or column row.
5. Group consecutive column rows between border rows into **row groups**.
6. Within each row group, parse column blocks and extract widths, row counts, and region names.
7. Validate: no duplicate names, no width overflow (fixed widths only), at least one row count per group (warning if missing).
8. Return a `LayoutModel`.

---

## Error Reference

| Error | Condition |
|-------|-----------|
| `ShellSyntaxError: missing outer border` | A row does not begin or end with `\|` |
| `ShellSyntaxError: duplicate region name 'x'` | `$x$` appears more than once |
| `ShellSyntaxError: conflicting row heights` | Two columns in a row group specify different row counts |
| `ShellSyntaxError: width overflow` | Fixed-width columns sum to more than specified total |
| `ShellSyntaxError: invalid width specifier` | Width is not a positive integer or valid percentage |
| `ShellSyntaxError: invalid region name` | Region name contains characters outside `[a-z0-9_]` |
