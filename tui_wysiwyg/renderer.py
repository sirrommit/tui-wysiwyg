import sys
from .layout import LayoutModel, Region, BorderRow, RowGroup

# ---------------------------------------------------------------------------
# Box-drawing character tables
# Each table is keyed by position role:
#   tl=top-left corner,  tr=top-right corner
#   bl=bottom-left,      br=bottom-right
#   lt=left T-junction,  rt=right T-junction
#   tt=top T-junction,   bt=bottom T-junction
#   cr=cross
# ---------------------------------------------------------------------------

# Single horizontal + single vertical
_SS = dict(h='─', v='│', tl='┌', tr='┐', bl='└', br='┘',
           lt='├', rt='┤', tt='┬', bt='┴', cr='┼')

# Double horizontal + double vertical
_DD = dict(h='═', v='║', tl='╔', tr='╗', bl='╚', br='╝',
           lt='╠', rt='╣', tt='╦', bt='╩', cr='╬')

# Double horizontal + single vertical
_DS = dict(h='═', v='│', tl='╒', tr='╕', bl='╘', br='╛',
           lt='╞', rt='╡', tt='╤', bt='╧', cr='╪')

# Single horizontal + double vertical
_SD = dict(h='─', v='║', tl='╓', tr='╖', bl='╙', br='╜',
           lt='╟', rt='╢', tt='╥', bt='╨', cr='╫')


def _box(h_style: str, v_style: str) -> dict:
    """Return the right box-drawing table for this h/v style combination."""
    if h_style == 'double' and v_style == 'double':
        return _DD
    if h_style == 'single' and v_style == 'single':
        return _SS
    if h_style == 'double' and v_style == 'single':
        return _DS
    return _SD  # single h, double v


def _border_end_char(h_style: str, v_above: str | None, v_below: str | None,
                     side: str) -> str:
    """
    Return the character for the left ('l') or right ('r') end of a border row.
    v_above / v_below: 'single', 'double', or None if no row group there.
    """
    # Prefer the vertical style present; if both, use v_above (arbitrary)
    v = v_above or v_below or 'single'
    tbl = _box(h_style, v)
    if v_above is None:
        return tbl['tl'] if side == 'l' else tbl['tr']
    if v_below is None:
        return tbl['bl'] if side == 'l' else tbl['br']
    return tbl['lt'] if side == 'l' else tbl['rt']


def _border_cross_char(h_style: str, v_above: str | None, v_below: str | None) -> str:
    """Return the character for an internal column-divider intersection."""
    v = v_above or v_below or 'single'
    tbl = _box(h_style, v)
    if v_above is None:
        return tbl['tt']
    if v_below is None:
        return tbl['bt']
    return tbl['cr']


class Renderer:
    def __init__(self, term):
        self._term = term

    def _get_dividers(self, row_group: RowGroup, term_width: int) -> dict:
        """
        Return {col_position: div_style} for all vertical lines in a row group,
        including the outer left (col 0) and outer right (col term_width-1).
        """
        from .layout import _resolve_widths
        dividers = {0: 'single', term_width - 1: 'single'}
        col_widths = _resolve_widths(row_group.columns, term_width)
        col_pos = 1
        for i, col_spec in enumerate(row_group.columns):
            col_pos += col_widths[i]
            if i < len(row_group.columns) - 1:
                style = 'double' if col_spec.double_divider_right else 'single'
                dividers[col_pos] = style
                col_pos += 1
        return dividers

    def full_render(self, layout_model, regions, interactions,
                    focused_name, term_width, term_height):
        """Render the full layout."""
        term = self._term
        print(term.clear, end='', flush=False)

        rows = layout_model.rows
        current_row = 0
        for i, item in enumerate(rows):
            prev_item = rows[i - 1] if i > 0 else None
            next_item = rows[i + 1] if i < len(rows) - 1 else None

            if isinstance(item, BorderRow):
                prev_div = (self._get_dividers(prev_item, term_width)
                            if isinstance(prev_item, RowGroup) else None)
                next_div = (self._get_dividers(next_item, term_width)
                            if isinstance(next_item, RowGroup) else None)
                self.draw_border(current_row, term_width, item.style, item.title,
                                 prev_dividers=prev_div, next_dividers=next_div)
                current_row += 1
            else:
                row_group = item
                height = self._group_height(row_group, term_height)
                self._draw_row_group(row_group, current_row, height, term_width)
                current_row += height

        # Render each named region
        for name, region in regions.items():
            interaction = interactions.get(name)
            focused = (name == focused_name)
            if interaction:
                self.render_region(region, interaction, term, focused)
            else:
                self._render_empty_region(region, focused)

        sys.stdout.flush()

    def _group_height(self, row_group: RowGroup, term_height: int) -> int:
        from .layout import _resolve_height
        return _resolve_height(row_group, term_height)

    def _draw_row_group(self, row_group: RowGroup, start_row: int,
                        height: int, term_width: int) -> None:
        """Draw the outer borders and column dividers for a row group."""
        from .layout import _resolve_widths
        term = self._term
        col_widths = _resolve_widths(row_group.columns, term_width)

        for row_offset in range(height):
            row = start_row + row_offset
            print(term.move(row, 0) + '│', end='', flush=False)
            print(term.move(row, term_width - 1) + '│', end='', flush=False)

            col_pos = 1
            for i, col_spec in enumerate(row_group.columns):
                col_pos += col_widths[i]
                if i < len(row_group.columns) - 1:
                    divider = '║' if col_spec.double_divider_right else '│'
                    print(term.move(row, col_pos) + divider, end='', flush=False)
                    col_pos += 1

    def render_region(self, region: Region, interaction, term, focused: bool):
        """Render a single region using its interaction."""
        interaction.render(region, term, focused)

    def _render_empty_region(self, region: Region, focused: bool):
        """Render an empty (unassigned) region."""
        term = self._term
        for row_offset in range(region.height):
            row = region.row + row_offset
            print(term.move(row, region.col) + ' ' * region.width, end='', flush=False)

    def draw_border(self, row: int, term_width: int, style: str, title=None,
                    prev_dividers: dict | None = None,
                    next_dividers: dict | None = None) -> None:
        """
        Draw a full-width horizontal border row using box-drawing characters.

        prev_dividers: {col_pos: div_style} for row group above (None if none)
        next_dividers: {col_pos: div_style} for row group below (None if none)
        The outer edges (0 and term_width-1) are always present in each dict.
        """
        term = self._term
        fill = '═' if style == 'double' else '─'

        prev = prev_dividers or {}
        nxt = next_dividers or {}

        # Build the line as a list of characters (default: fill)
        chars = [fill] * term_width

        # Left outer edge
        v_up = prev.get(0)   # 'single'/'double'/None
        v_dn = nxt.get(0)
        chars[0] = _border_end_char(style, v_up, v_dn, 'l')

        # Right outer edge
        v_up = prev.get(term_width - 1)
        v_dn = nxt.get(term_width - 1)
        chars[term_width - 1] = _border_end_char(style, v_up, v_dn, 'r')

        # Internal column-divider positions
        all_positions = set(prev.keys()) | set(nxt.keys())
        for pos in all_positions:
            if 0 < pos < term_width - 1:
                v_up = prev.get(pos)
                v_dn = nxt.get(pos)
                chars[pos] = _border_cross_char(style, v_up, v_dn)

        # Overlay title (centered)
        if title:
            title_str = f' {title} '
            title_len = len(title_str)
            inner_width = term_width - 2   # exclude corner characters
            if title_len <= inner_width:
                left_fill = (inner_width - title_len) // 2
                title_start = 1 + left_fill
                for j, ch in enumerate(title_str):
                    chars[title_start + j] = ch

        line = ''.join(chars)
        print(term.move(row, 0) + line, end='', flush=False)
