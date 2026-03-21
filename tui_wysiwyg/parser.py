import re
from .layout import LayoutModel, VSplit, BorderRow, ColumnDef, Panel, PartialBorder
from .style import strip_comments


class Parser:
    def parse(self, definition: str) -> LayoutModel:
        definition = strip_comments(definition)
        lines = definition.split('\n')

        processed = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped:
                processed.append((i, stripped))

        if not processed:
            return LayoutModel(items=[], has_percentage=False)

        items = []
        has_percentage = False
        seen_names = set()
        section_lines = []   # (lineno, inner) pairs for the current section

        def flush_section():
            nonlocal has_percentage
            if section_lines:
                vsplit, pct, new_names = _parse_section(section_lines, seen_names)
                for name in new_names:
                    seen_names.add(name)
                if pct:
                    has_percentage = True
                items.append(vsplit)
                section_lines.clear()

        for lineno, line in processed:
            if not (line.startswith('|') and line.endswith('|')):
                raise _syntax_error("missing outer border", lineno)

            inner = line[1:-1]

            if _is_full_border(inner):
                flush_section()
                style, title = _parse_border_row(inner, lineno)
                items.append(BorderRow(style=style, title=title))
            elif _is_column_row(inner):
                # Normal column row or partial border row — both go into section
                section_lines.append((lineno, inner))
            else:
                raise _syntax_error("unrecognized row format", lineno)

        flush_section()

        return LayoutModel(items=items, has_percentage=has_percentage)


# ---------------------------------------------------------------------------
# Line classification
# ---------------------------------------------------------------------------

def _is_full_border(inner: str) -> bool:
    """Full border: starts with = or -, contains no column blocks."""
    stripped = inner.strip()
    return bool(stripped) and stripped[0] in ('=', '-') and '{' not in inner


def _is_partial_border(inner: str) -> bool:
    """Partial border: starts with = or - but also has column blocks."""
    stripped = inner.strip()
    return bool(stripped) and stripped[0] in ('=', '-') and '{' in inner


def _is_column_row(inner: str) -> bool:
    return '{' in inner


# ---------------------------------------------------------------------------
# Section → VSplit
# ---------------------------------------------------------------------------

def _parse_section(section_lines: list, seen_names: set):
    """
    Parse a list of (lineno, inner) lines into a VSplit.
    Returns (VSplit, has_percentage, new_names).
    """
    if not section_lines:
        return VSplit(columns=[]), False, []

    # First pure column row determines column count and widths.
    first_col_idx = None
    for idx, (lineno, inner) in enumerate(section_lines):
        if _is_column_row(inner) and not _is_partial_border(inner):
            first_col_idx = idx
            break

    if first_col_idx is None:
        return VSplit(columns=[]), False, []

    first_lineno, first_inner = section_lines[first_col_idx]
    first_blocks = _parse_column_blocks(first_inner, first_lineno)
    n_cols = len(first_blocks)

    # '{' positions from the first row — used for partial border detection.
    col_brace_pos = _get_brace_positions(first_inner)

    # Initialise columns
    columns = []
    has_percentage = False
    for col_inner, divider_right in first_blocks:
        width, is_pct, pct_val, _ = _parse_width(col_inner)
        if is_pct:
            has_percentage = True
        columns.append(ColumnDef(
            width=width,
            is_percentage=is_pct,
            pct=pct_val,
            double_divider_right=(divider_right == '#'),
            panels=[Panel(name=None, row_count=None, row_count_is_pct=False,
                          row_pct=None, heading=None, num_rows_def=0)],
            partial_borders=[],
        ))

    cur_panel = [0] * n_cols   # current panel index per column
    new_names = []

    for lineno, inner in section_lines:
        if _is_partial_border(inner):
            pb_style = 'double' if inner.strip()[0] == '=' else 'single'
            for i in range(n_cols):
                # A column continues through this partial border if its known
                # '{' position in the inner string still contains '{'.
                pos = col_brace_pos[i] if i < len(col_brace_pos) else -1
                col_continues = (0 <= pos < len(inner) and inner[pos] == '{')
                if not col_continues:
                    columns[i].partial_borders.append(PartialBorder(style=pb_style))
                    columns[i].panels.append(Panel(
                        name=None, row_count=None, row_count_is_pct=False,
                        row_pct=None, heading=None, num_rows_def=0,
                    ))
                    cur_panel[i] = len(columns[i].panels) - 1
            continue

        # Normal column row
        blocks = _parse_column_blocks(inner, lineno)
        for i, (col_inner, _) in enumerate(blocks):
            if i >= n_cols:
                break
            panel = columns[i].panels[cur_panel[i]]

            if lineno == first_lineno:
                _, _, _, col_content = _parse_width(col_inner)
            else:
                col_content = col_inner

            # Row count
            row_match = re.search(r'\b(\d+)(%?)R\b', col_content)
            if row_match and panel.row_count is None:
                count_val = int(row_match.group(1))
                is_pct_r = row_match.group(2) == '%'
                panel.row_count = count_val
                panel.row_count_is_pct = is_pct_r
                if is_pct_r:
                    panel.row_pct = count_val
                    has_percentage = True

            # Region name
            name_match = re.search(r'\$([a-z0-9_]+)\$', col_content)
            if name_match:
                region_name = name_match.group(1)
                if not re.match(r'^[a-z0-9_]+$', region_name):
                    from .exceptions import ShellSyntaxError
                    raise ShellSyntaxError(f"invalid region name '{region_name}'",
                                           line=lineno)
                if region_name in seen_names or region_name in new_names:
                    from .exceptions import ShellSyntaxError
                    raise ShellSyntaxError(f"duplicate region name '{region_name}'",
                                           line=lineno)
                if panel.name is None:
                    panel.name = region_name
                    new_names.append(region_name)

            # Heading
            heading_match = re.search(r'__(.+?)__', col_content)
            if heading_match and panel.heading is None:
                panel.heading = heading_match.group(1)

            panel.num_rows_def += 1

    return VSplit(columns=columns), has_percentage, new_names


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _get_brace_positions(inner: str) -> list:
    """Return positions of each top-level '{' in a column row inner string."""
    positions = []
    pos = 0
    n = len(inner)
    while pos < n:
        if inner[pos] in ('|', '#'):
            pos += 1
            continue
        if inner[pos] == '{':
            positions.append(pos)
            depth = 0
            while pos < n:
                if inner[pos] == '{':
                    depth += 1
                elif inner[pos] == '}':
                    depth -= 1
                    if depth == 0:
                        pos += 1
                        break
                pos += 1
        else:
            pos += 1
    return positions


def _parse_column_blocks(inner: str, lineno: int) -> list:
    """Parse column row inner string into list of (col_content, divider_right)."""
    result = []
    pos = 0
    n = len(inner)

    while pos < n:
        if inner[pos] in ('|', '#'):
            pos += 1
        if pos >= n:
            break
        if inner[pos] != '{':
            pos += 1
            continue

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

        col_content = inner[start + 1:pos]
        pos += 1  # skip '}'

        divider_right = None
        if pos < n and inner[pos] in ('|', '#'):
            divider_right = inner[pos]

        result.append((col_content, divider_right))

    return result


def _parse_border_row(inner: str, lineno: int):
    """Parse a full border row inner string. Returns (style, title)."""
    stripped = inner.strip()
    fill_char = '=' if stripped[0] == '=' else '-'
    style = 'double' if fill_char == '=' else 'single'
    content = stripped.strip(fill_char).strip()
    content = re.sub(r'^\d+%', '', content).strip(fill_char).strip()
    title = content if content else None
    return style, title


def _parse_width(col_content: str):
    """
    Extract width spec from start of column content.
    Returns (width_chars, is_percentage, pct_val, remaining_content).
    """
    pct_match = re.match(r'^(\d+)%', col_content)
    if pct_match:
        return None, True, float(pct_match.group(1)), col_content[pct_match.end():]

    char_match = re.match(r'^(\d+)(?=[^%\dR]|$)', col_content)
    if char_match:
        return int(char_match.group(1)), False, None, col_content[char_match.end():]

    return None, False, None, col_content


def _syntax_error(message, lineno=None):
    from .exceptions import ShellSyntaxError
    return ShellSyntaxError(message, line=lineno)
