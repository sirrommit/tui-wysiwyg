import re
from .layout import LayoutModel, HSplit, VSplit, Panel, BorderRow
from .style import strip_comments
from .exceptions import ShellSyntaxError


class Parser:
    def parse(self, definition: str) -> LayoutModel:
        definition = strip_comments(definition)
        raw_lines = definition.split('\n')

        processed = []  # list of (lineno, inner_string)
        for i, line in enumerate(raw_lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            if not (stripped.startswith('|') and stripped.endswith('|')):
                raise ShellSyntaxError("missing outer border", line=i)
            inner = stripped[1:-1]
            processed.append((i, inner))

        if not processed:
            return LayoutModel(root=None, has_percentage=False)

        seen_names = set()
        root = _parse_block(processed, seen_names)
        return LayoutModel(root=root, has_percentage=_contains_pct(root))


# ---------------------------------------------------------------------------
# Block parsing (recursive)
# ---------------------------------------------------------------------------

def _parse_block(lines, seen_names):
    """
    Recursively parse a list of (lineno, inner) pairs into a LayoutNode.

    Algorithm:
      1. Find a full HSplit (border row with no '{') → split there, recurse
      2. Else find a full VSplit (column divider '|'/'#' in ALL rows) → split, recurse
      3. Else → parse as a leaf Panel
    """
    if not lines:
        return None

    # 1. Try horizontal split
    hi = _find_full_hsplit(lines)
    if hi is not None:
        _, border_inner = lines[hi]
        border = _parse_border(border_inner)
        top = _parse_block(lines[:hi], seen_names)
        bottom = _parse_block(lines[hi + 1:], seen_names)
        return HSplit(top=top, bottom=bottom, border=border)

    # 2. Try vertical split
    div_char = _find_full_vsplit(lines)
    if div_char is not None:
        left_lines, right_lines = _split_vertical(lines, div_char)
        return VSplit(
            left=_parse_block(left_lines, seen_names),
            right=_parse_block(right_lines, seen_names),
            divider='double' if div_char == '#' else 'single',
        )

    # 3. Leaf
    return _parse_leaf(lines, seen_names)


# ---------------------------------------------------------------------------
# Split finders
# ---------------------------------------------------------------------------

def _find_full_hsplit(lines):
    """Return index of first full border row (starts with =/-  and has no '{'), or None."""
    for i, (_, inner) in enumerate(lines):
        s = inner.strip()
        if s and s[0] in ('=', '-') and '{' not in inner:
            return i
    return None


def _find_full_vsplit(lines):
    """
    Return the divider char ('|' or '#') if ALL column rows (rows containing
    '{') have an outer divider (a '|' or '#' that lies outside any '{…}'
    block) as their first such character, and all agree on the same char.
    Returns None if no consistent structural vertical split exists.
    """
    col_rows = [inner for (_, inner) in lines if '{' in inner]
    if not col_rows:
        return None

    div_char = None
    for inner in col_rows:
        p, ch = _first_outer_divider(inner)
        if p is None:
            return None       # this row has no outer divider → can't split
        if div_char is None:
            div_char = ch
        elif ch != div_char:
            return None       # inconsistent divider chars
    return div_char           # just the char; splitting is done structurally


def _first_outer_divider(inner):
    """
    Return (pos, char) of the first '|' or '#' that lies outside all
    '{…}' blocks in *inner*, or (None, None) if none exists.
    """
    depth = 0
    for p, ch in enumerate(inner):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif ch in ('|', '#') and depth == 0:
            return p, ch
    return None, None


def _split_vertical(lines, div_char):
    """
    Split each (lineno, inner) at its first outer divider structurally,
    i.e. at the first '|'/'#' outside '{…}' blocks.
    Lines with no outer divider are split at position 0 (empty left side).
    """
    left = []
    right = []
    for ln, inner in lines:
        p, _ = _first_outer_divider(inner)
        if p is not None:
            left.append((ln, inner[:p]))
            right.append((ln, inner[p + 1:]))
        else:
            # No divider (shouldn't happen if _find_full_vsplit passed)
            left.append((ln, inner))
            right.append((ln, ''))
    return left, right


# ---------------------------------------------------------------------------
# Leaf parser
# ---------------------------------------------------------------------------

def _parse_leaf(lines, seen_names):
    """Parse a single-column block (no splits found) into a Panel."""
    name = None
    heading = None
    width = None
    is_pct = False
    pct = None
    row_count = None
    row_count_is_pct = False
    row_pct = None
    num_rows_def = 0
    first_content = True

    for lineno, inner in lines:
        content = _extract_block_content(inner)
        if content is None:
            continue  # not a {…} block (border line that ended up here)

        num_rows_def += 1

        if first_content:
            # Width spec comes from the first content row only
            width, is_pct, pct, content = _parse_width(content)
            first_content = False

        # Row count: NR or N%R
        row_match = re.search(r'\b(\d+)(%?)R\b', content)
        if row_match and row_count is None:
            count_val = int(row_match.group(1))
            is_pct_r = row_match.group(2) == '%'
            row_count = count_val
            row_count_is_pct = is_pct_r
            if is_pct_r:
                row_pct = float(count_val)

        # Region name: $name$
        name_match = re.search(r'\$([a-z0-9_]+)\$', content)
        if name_match:
            region_name = name_match.group(1)
            if not re.match(r'^[a-z0-9_]+$', region_name):
                raise ShellSyntaxError(
                    f"invalid region name '{region_name}'", line=lineno)
            if region_name in seen_names:
                raise ShellSyntaxError(
                    f"duplicate region name '{region_name}'", line=lineno)
            if name is None:
                name = region_name
                seen_names.add(region_name)

        # Heading: __text__
        heading_match = re.search(r'__(.+?)__', content)
        if heading_match and heading is None:
            heading = heading_match.group(1)

    return Panel(
        name=name, heading=heading,
        width=width, is_pct=is_pct, pct=pct,
        row_count=row_count, row_count_is_pct=row_count_is_pct, row_pct=row_pct,
        num_rows_def=num_rows_def,
    )


def _extract_block_content(inner):
    """
    Return the content inside a '{content}' block, or None if the line
    doesn't look like a block (e.g. it's a stray border line).
    """
    s = inner.strip()
    if s.startswith('{') and s.endswith('}'):
        return s[1:-1]
    return None


# ---------------------------------------------------------------------------
# Border parsing
# ---------------------------------------------------------------------------

def _parse_border(inner):
    """Parse a full border inner string into a BorderRow."""
    stripped = inner.strip()
    fill_char = '=' if stripped[0] == '=' else '-'
    style = 'double' if fill_char == '=' else 'single'
    content = stripped.strip(fill_char).strip()
    content = re.sub(r'^\d+%', '', content).strip(fill_char).strip()
    # Strip stray structural chars that sometimes appear in border lines
    content = content.strip('}|').strip()
    title = content if content else None
    return BorderRow(style=style, title=title)


# ---------------------------------------------------------------------------
# Width spec parsing
# ---------------------------------------------------------------------------

def _parse_width(col_content):
    """
    Extract a width specification from the start of column content.
    Returns (width_chars, is_percentage, pct_val, remaining_content).
    """
    pct_match = re.match(r'^(\d+)%', col_content)
    if pct_match:
        return None, True, float(pct_match.group(1)), col_content[pct_match.end():]

    char_match = re.match(r'^(\d+)(?=[^%\dR]|$)', col_content)
    if char_match:
        return int(char_match.group(1)), False, None, col_content[char_match.end():]

    return None, False, None, col_content


# ---------------------------------------------------------------------------
# has_percentage helper
# ---------------------------------------------------------------------------

def _contains_pct(node):
    """Return True if any Panel in the tree uses a percentage width or height."""
    if node is None:
        return False
    if isinstance(node, Panel):
        return node.is_pct or node.row_count_is_pct
    if isinstance(node, HSplit):
        return _contains_pct(node.top) or _contains_pct(node.bottom)
    if isinstance(node, VSplit):
        return _contains_pct(node.left) or _contains_pct(node.right)
    return False
