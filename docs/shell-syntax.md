# Shell Definition Language Specification

A "shell" is a multi-line string that defines the visual structure of a TUI screen. It describes a grid of regions using ASCII box-drawing characters and special syntax markers.

---

## Minimal Example

```
|=100%==== <bold>My App</> ====|
|{50%  $left$  }|{  $right$  }|
|=============================|
```

---

## Full Example

See `example.shell` for a complete multi-region layout.

---

## C-Style Comments

Shell definition strings support `/* ... */` block comments. Comments are stripped before any parsing occurs and never appear in the rendered TUI. Newlines inside a comment are preserved so that the line numbering of the remaining content is not disrupted.

```
/* Three-column layout — nav | content | detail.                  */
/* Left column is fixed 25 chars; others split remaining space.   */
|=100%========================= My App ===========================|
|{25  12R  $nav$     }|{50%  12R  $content$ }|{  12R  $detail$ }|
|{                   }|{                    }|{                 }| /* filler */
|================================================================|
|{100%  2R  $status$                                             }|
|================================================================|
```

Multi-line comments are allowed:

```
/*
 * Status bar appears at the bottom.
 * Height is fixed at 2 rows.
 */
|{100%  2R  $status$ }|
```

Comments may appear between rows, at the end of a row, or on their own line. They may **not** appear inside a `{ }` column block or inside a border row's fill characters in a way that disrupts the `=`/`-` pattern — place them before or after the `|...|` line instead.

---

## Top-Level Structure

Every shell definition is a series of **rows**. Each row is a line in the string. Rows fall into three categories:

| Row Type | Description |
|----------|-------------|
| **Border row** | A horizontal rule (`====` or `----`) — may appear at any nesting level, not just at the outermost level |
| **Column row** | A line containing one or more `{ }` column blocks |
| **Filler row** | A column row that contains no `$name$` markers and no row-count marker — used for human readability only, ignored by the parser |

The parser discovers layout structure recursively: it looks for horizontal splits first, then vertical splits, then treats the remaining content as a single region (leaf). This means layouts are not restricted to a fixed number of levels — columns can contain further horizontal or vertical splits to arbitrary depth.

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

Titles may include **style tags** (see [Style Tags](#style-tags) below):

```
|==== <bold;color=cyan>My Application</> ====|
|---- <italic>Section Title</> --------------|
```

Text in a rule is centered based on its **visible** length (style tags are excluded from the width calculation).

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

## Style Tags

Style tags apply colors and text attributes to border row titles. They follow a simple XML-like format and degrade gracefully — if a terminal does not support an attribute, that attribute is silently skipped and the plain text is still displayed.

### Tag Format

```
<attr[=value][;attr[=value]...]>text</>
```

- Opening tag: one or more `attr` or `attr=value` pairs separated by `;`
- Closing tag: `</>` or `</anything>` — the tag name is ignored; all styles reset

Examples:

```
<bold>text</>
<color=red>text</>
<bold;color=red>text</>
<color=white;bg=blue>text</>
<bold;underline;color=bright_yellow>text</>
```

### Text Style Attributes

| Attribute | Aliases | Effect |
|-----------|---------|--------|
| `bold` | — | Bold / bright |
| `dim` | `faint` | Dim / faint |
| `italic` | — | Italic |
| `underline` | `ul`, `underlined`, `underline-text` | Underline |
| `blink` | `flash` | Blinking |
| `reverse` | `invert`, `reverse-video` | Swap foreground and background |
| `standout` | — | Standout (often same as reverse) |
| `strike` | `strikethrough`, `strikeout`, `line-through` | Strikethrough |
| `normal` | `reset` | Explicit reset to default |

### Color Attributes

**Foreground color** — any of these keys:
`color`, `fg`, `foreground`, `fg-color`, `text-color`

**Background color** — any of these keys:
`bg`, `background`, `bg-color`, `bgcolor`, `background-color`

### Named Colors

| Value | Notes |
|-------|-------|
| `black`, `red`, `green`, `yellow` | Standard 16-colour palette |
| `blue`, `magenta`, `cyan`, `white` | Standard 16-colour palette |
| `bright_black`, `bright_red`, … | Bright variants (prefix `bright_`) |
| `gray` / `grey` | Alias → `bright_black` |
| `purple` / `violet` | Alias → `magenta` |
| `pink` | Alias → `bright_magenta` |
| `orange` | Alias → `yellow` (closest 16-colour match) |
| `lime` | Alias → `bright_green` |
| `teal` / `aqua` | Alias → `cyan` |
| `navy` / `indigo` | Alias → `blue` |
| `maroon` | Alias → `red` |
| `silver` / `lightgray` | Alias → `white` |
| `0`–`255` | 256-colour index (`color=196`) |

### Rendering Styled Text Inside Regions

Style tags in the shell definition language only apply to border titles. To render styled text inside a region — for example, in a `Function` handler — use `render_styled()` from `tui_wysiwyg.style`:

```python
from tui_wysiwyg.style import render_styled, styled_plain_text, styled_visual_len

def my_handler(shell, region, key):
    term = shell.terminal
    tagged = "<bold;color=red>Error:</> file not found"
    line = render_styled(tagged, term, max_len=region.width)
    print(term.move(region.row, region.col) + line)
```

| Function | Description |
|----------|-------------|
| `render_styled(text, term, max_len=None)` | Render tagged text with terminal escapes; truncate visible text to `max_len` if given |
| `styled_plain_text(text)` | Strip all style tags and return plain text |
| `styled_visual_len(text)` | Return visible character count (tags excluded) |

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
shell        ::= comment* row+
row          ::= border_row | column_row
border_row   ::= "|" ("=" | "-")+ [title ("=" | "-")+] "|" NEWLINE
title        ::= styled_text                  (plain text or style-tagged text)
column_row   ::= "|" col_block (divider col_block)* "|" NEWLINE
col_block    ::= "{" [width] content "}"
width        ::= INTEGER "%" | INTEGER        (no space before content)
content      ::= (row_count | name | formatted_text | filler_text)*
row_count    ::= INTEGER "R" | INTEGER "%" "R"
name         ::= "$" [a-z0-9_]+ "$"
formatted    ::= "__" text "__"
divider      ::= "|" | "#"
comment      ::= "/*" .* "*/"                 (DOTALL; newlines preserved)
style_tag    ::= "<" attr_list ">" | "</>" | "</" name ">"
attr_list    ::= attr (";" attr)*
attr         ::= NAME ["=" VALUE]
```

---

## Parser Behavior

The parser processes the shell definition string using a recursive algorithm:

1. Strip `/* ... */` comments, preserving the newlines they contained.
2. Split on newlines. Strip each line. Empty lines are ignored.
3. Validate that each line begins and ends with `|`. Strip the outer `|` from every line before recursing.
4. Call `_parse_block(lines)` on the remaining inner content.

### `_parse_block` (recursive)

```
_parse_block(lines):
    i = find_full_hsplit(lines)   # first border row with no '{' character
    if i is not None:
        return HSplit(
            top    = _parse_block(lines[:i])    if lines[:i]   else None,
            border = parse_border_row(lines[i]),
            bottom = _parse_block(lines[i+1:]) if lines[i+1:] else None,
        )

    pos = find_full_vsplit(lines)  # first column where ALL column rows have '|' or '#'
    if pos is not None:
        left_lines, right_lines = split_vertical(lines, pos)
        return VSplit(
            left    = _parse_block(left_lines),
            right   = _parse_block(right_lines),
            divider = 'double' if char == '#' else 'single',
        )

    return parse_leaf(lines)       # extract Panel: name, width, row_count, etc.
```

**`find_full_hsplit`** returns the index of the first line whose stripped content starts with `=` or `-` and contains no `{`. Border rows that span the full horizontal extent (including inside a sub-block after vertical splitting) are detected this way.

**`find_full_vsplit`** scans all column rows for the first character position that is `|` or `#` in every column row. It ignores full border rows when scanning. The scan tracks brace depth so that `|` characters inside `{...}` blocks are not treated as dividers.

**`split_vertical`** splits each line at its own first outer divider character (tracking brace depth independently per line). This handles inconsistent whitespace padding between columns.

**Partial borders** are handled automatically: after vertical splitting, a row like `-----|{...}|-----` becomes a full border row `-----` in the left sub-block and a column row `{...}` in the right sub-block. No special-case logic is needed.

### Validation

After the recursive parse, the `LayoutModel` is validated for:
- Duplicate region names (raises `ShellSyntaxError`).
- Missing outer `|` borders (raises `ShellSyntaxError`).

Style tags in border row titles are stored as-is and parsed at render time by `render_styled()`. They do not affect parsing or validation.

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
