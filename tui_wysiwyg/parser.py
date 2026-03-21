import re
from .layout import LayoutModel, RowGroup, BorderRow, ColumnSpec


class Parser:
    def parse(self, definition: str) -> LayoutModel:
        lines = definition.split('\n')
        # Strip and filter empty lines, but keep track of original line numbers
        processed = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped:
                processed.append((i, stripped))

        if not processed:
            return LayoutModel(rows=[], has_percentage=False)

        rows = []
        has_percentage = False
        seen_names = set()

        # Group consecutive column rows into row groups
        i = 0
        while i < len(processed):
            lineno, line = processed[i]

            # Validate outer border
            if not (line.startswith('|') and line.endswith('|')):
                raise _syntax_error(f"missing outer border", lineno)

            inner = line[1:-1]

            if _is_border_row(inner):
                style, title = _parse_border_row(inner, lineno)
                rows.append(BorderRow(style=style, title=title))
                i += 1
            elif _is_column_row(inner):
                # Collect consecutive column rows into a row group
                group_lines = []
                while i < len(processed):
                    ln, l = processed[i]
                    inner2 = l[1:-1]
                    if _is_column_row(inner2):
                        group_lines.append((ln, inner2))
                        i += 1
                    else:
                        break

                row_group, pct_used, new_names = _parse_row_group(group_lines, seen_names)
                # Check for duplicate names
                for name in new_names:
                    if name in seen_names:
                        raise _syntax_error(f"duplicate region name '{name}'", group_lines[0][0])
                    seen_names.add(name)

                if pct_used:
                    has_percentage = True
                rows.append(row_group)
            else:
                raise _syntax_error(f"unrecognized row format", lineno)

        return LayoutModel(rows=rows, has_percentage=has_percentage)


def _syntax_error(message, lineno=None):
    from .exceptions import ShellSyntaxError
    return ShellSyntaxError(message, line=lineno)


def _is_border_row(inner: str) -> bool:
    """Check if the inner content (without outer pipes) is a border row."""
    stripped = inner.strip()
    if not stripped:
        return False
    # Must be mostly = or - characters (with optional text)
    first_char = stripped[0]
    if first_char in ('=', '-'):
        return True
    return False


def _is_column_row(inner: str) -> bool:
    """Check if inner content is a column row (contains column blocks)."""
    return '{' in inner


def _parse_border_row(inner: str, lineno: int):
    """Parse border row inner content, return (style, title)."""
    stripped = inner.strip()
    if stripped[0] == '=':
        style = 'double'
        fill_char = '='
    else:
        style = 'single'
        fill_char = '-'

    # Extract title text between fill chars
    # e.g. "=== My Title ===" -> "My Title"
    # Strip leading/trailing fill chars
    content = stripped.strip(fill_char).strip()
    # Also handle percentage width specifiers like "100%==== Title ===="
    # Strip percentage prefix if present
    content = re.sub(r'^\d+%', '', content).strip(fill_char).strip()
    title = content if content else None
    return style, title


def _parse_row_group(group_lines: list, seen_names: set):
    """
    Parse a group of column row lines into a RowGroup.
    Returns (RowGroup, has_percentage, new_names_list)
    """
    # We need to parse all lines to find the column structure
    # Use the first line to determine column structure (widths, dividers)
    # Then scan all lines for names, row counts, headings

    if not group_lines:
        return RowGroup(columns=[], num_text_rows=0, border_top=None, border_bottom=None), False, []

    # Parse each line to extract column blocks
    # A line looks like: {width content}|{width content}|{content} or similar
    # Dividers between columns: | or #

    # We'll parse column blocks from the first non-filler line, or the first line
    # All lines should have the same column structure
    first_lineno, first_inner = group_lines[0]

    # Parse column blocks from first line to get structure
    columns_data = _parse_column_blocks(first_inner, first_lineno)
    # columns_data: list of (col_inner, divider_right) where divider_right is '|' or '#' or None

    num_cols = len(columns_data)

    # Initialize column specs
    col_specs = []
    for col_inner, divider_right in columns_data:
        spec = ColumnSpec(
            width=None,
            is_percentage=False,
            pct=None,
            row_count=None,
            row_count_is_pct=False,
            row_pct=None,
            region_name=None,
            heading_text=None,
            double_divider_right=(divider_right == '#'),
        )
        col_specs.append(spec)

    # Parse widths from first line
    has_percentage = False
    for i, (col_inner, _) in enumerate(columns_data):
        width, is_pct, pct_val, remaining_content = _parse_width(col_inner)
        col_specs[i].width = width
        col_specs[i].is_percentage = is_pct
        col_specs[i].pct = pct_val
        if is_pct:
            has_percentage = True

    # Scan all lines for names, row counts, headings
    new_names = []
    num_content_rows = 0

    for lineno, inner in group_lines:
        line_cols = _parse_column_blocks(inner, lineno)
        if len(line_cols) != num_cols:
            # Column count mismatch - just use what we have
            pass

        is_content_row = False
        for i, (col_inner, _) in enumerate(line_cols):
            if i >= num_cols:
                break
            # Strip width spec from first line
            if lineno == first_lineno:
                _, _, _, col_content = _parse_width(col_inner)
            else:
                col_content = col_inner

            # Check for row count marker
            row_match = re.search(r'\b(\d+)(%?)R\b', col_content)
            if row_match and col_specs[i].row_count is None:
                count_val = int(row_match.group(1))
                is_pct_r = row_match.group(2) == '%'
                col_specs[i].row_count = count_val
                col_specs[i].row_count_is_pct = is_pct_r
                if is_pct_r:
                    col_specs[i].row_pct = count_val
                    has_percentage = True
                is_content_row = True

            # Check for region name
            name_match = re.search(r'\$([a-z0-9_]+)\$', col_content)
            if name_match:
                region_name = name_match.group(1)
                # Validate name characters
                if not re.match(r'^[a-z0-9_]+$', region_name):
                    from .exceptions import ShellSyntaxError
                    raise ShellSyntaxError(f"invalid region name '{region_name}'", line=lineno)
                # Check for duplicates (in current group or previous groups)
                if region_name in seen_names or region_name in new_names:
                    from .exceptions import ShellSyntaxError
                    raise ShellSyntaxError(f"duplicate region name '{region_name}'", line=lineno)
                if col_specs[i].region_name is None:
                    col_specs[i].region_name = region_name
                    new_names.append(region_name)
                    is_content_row = True

            # Check for heading text
            heading_match = re.search(r'__(.+?)__', col_content)
            if heading_match and col_specs[i].heading_text is None:
                col_specs[i].heading_text = heading_match.group(1)
                is_content_row = True

        if is_content_row:
            num_content_rows += 1

    # Count filler rows (rows that aren't content rows)
    num_text_rows = len(group_lines)

    row_group = RowGroup(
        columns=col_specs,
        num_text_rows=num_text_rows,
        border_top=None,
        border_bottom=None,
    )

    return row_group, has_percentage, new_names


def _parse_column_blocks(inner: str, lineno: int) -> list:
    """
    Parse inner content of a column row into list of (col_content, divider_right).
    col_content is the content inside { }, divider_right is '|', '#', or None for last.
    """
    result = []
    pos = 0
    n = len(inner)

    while pos < n:
        # Skip any leading divider character (| or #) at start or between columns
        if pos < n and inner[pos] in ('|', '#'):
            pos += 1

        if pos >= n:
            break

        if inner[pos] != '{':
            # Not a column block - skip
            pos += 1
            continue

        # Find matching '}'
        depth = 0
        start = pos
        while pos < n:
            if inner[pos] == '{':
                depth += 1
            elif inner[pos] == '}':
                depth -= 1
                if depth == 0:
                    break
            pos += 1

        if depth != 0:
            from .exceptions import ShellSyntaxError
            raise ShellSyntaxError("unclosed column block '{'", line=lineno)

        col_content = inner[start+1:pos]  # content between { and }
        pos += 1  # skip '}'

        # Check what comes next: '|', '#', or end
        divider_right = None
        if pos < n and inner[pos] in ('|', '#'):
            divider_right = inner[pos]
            # Don't advance - the next column block will skip it

        result.append((col_content, divider_right))

    return result


def _parse_width(col_content: str):
    """
    Parse width specification from beginning of column content.
    Returns (width_chars, is_percentage, pct_val, remaining_content).
    """
    # Match percentage: e.g. "50%" at the very start
    pct_match = re.match(r'^(\d+)%', col_content)
    if pct_match:
        pct_val = float(pct_match.group(1))
        remaining = col_content[pct_match.end():]
        return None, True, pct_val, remaining

    # Match fixed char width: e.g. "25" at very start, NOT followed by R or %R (those are row counts)
    # Use negative lookahead: not followed by more digits or R
    char_match = re.match(r'^(\d+)(?=[^%\dR]|$)', col_content)
    if char_match:
        width = int(char_match.group(1))
        remaining = col_content[char_match.end():]
        return width, False, None, remaining

    # No width spec
    return None, False, None, col_content
