import sys
from .layout import LayoutModel, Region, BorderRow, VSplit, _resolve_col_widths, _resolve_panel_heights
from .style import render_styled, styled_plain_text

# ---------------------------------------------------------------------------
# Box-drawing character tables
# Keys: tl tr bl br lt rt tt bt cr h v
# ---------------------------------------------------------------------------
_SS = dict(h='─', v='│', tl='┌', tr='┐', bl='└', br='┘',
           lt='├', rt='┤', tt='┬', bt='┴', cr='┼')
_DD = dict(h='═', v='║', tl='╔', tr='╗', bl='╚', br='╝',
           lt='╠', rt='╣', tt='╦', bt='╩', cr='╬')
_DS = dict(h='═', v='│', tl='╒', tr='╕', bl='╘', br='╛',
           lt='╞', rt='╡', tt='╤', bt='╧', cr='╪')
_SD = dict(h='─', v='║', tl='╓', tr='╖', bl='╙', br='╜',
           lt='╟', rt='╢', tt='╥', bt='╨', cr='╫')


def _box(h_style: str, v_style: str) -> dict:
    if h_style == 'double' and v_style == 'double':
        return _DD
    if h_style == 'single' and v_style == 'single':
        return _SS
    if h_style == 'double' and v_style == 'single':
        return _DS
    return _SD


def _border_end_char(h_style, v_above, v_below, side):
    v = v_above or v_below or 'single'
    tbl = _box(h_style, v)
    if v_above is None:
        return tbl['tl'] if side == 'l' else tbl['tr']
    if v_below is None:
        return tbl['bl'] if side == 'l' else tbl['br']
    return tbl['lt'] if side == 'l' else tbl['rt']


def _border_cross_char(h_style, v_above, v_below):
    v = v_above or v_below or 'single'
    tbl = _box(h_style, v)
    if v_above is None:
        return tbl['tt']
    if v_below is None:
        return tbl['bt']
    return tbl['cr']


# ---------------------------------------------------------------------------
# Divider map helpers
# ---------------------------------------------------------------------------

def _vsplit_dividers(vsplit: VSplit, term_width: int) -> dict:
    """Return {col_pos: div_style} for all vertical lines of a VSplit."""
    col_widths = _resolve_col_widths(vsplit.columns, term_width)
    dividers = {0: 'single', term_width - 1: 'single'}
    col_pos = 1
    for i, col in enumerate(vsplit.columns):
        col_pos += col_widths[i]
        if i < len(vsplit.columns) - 1:
            style = 'double' if col.double_divider_right else 'single'
            dividers[col_pos] = style
            col_pos += 1
    return dividers


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class Renderer:
    def __init__(self, term):
        self._term = term

    def full_render(self, layout_model, regions, interactions,
                    focused_name, term_width, term_height):
        term = self._term
        print(term.clear, end='', flush=False)

        items = layout_model.items

        # Pass 1: structural drawing (full borders + column dividers)
        current_row = 0
        for idx, item in enumerate(items):
            if isinstance(item, BorderRow):
                prev_item = items[idx - 1] if idx > 0 else None
                next_item = items[idx + 1] if idx < len(items) - 1 else None
                prev_div = (_vsplit_dividers(prev_item, term_width)
                            if isinstance(prev_item, VSplit) else None)
                next_div = (_vsplit_dividers(next_item, term_width)
                            if isinstance(next_item, VSplit) else None)
                self.draw_border(current_row, term_width, item.style, item.title,
                                 prev_dividers=prev_div, next_dividers=next_div)
                current_row += 1
            else:
                vsplit = item
                col_widths = _resolve_col_widths(vsplit.columns, term_width)
                all_ph = [_resolve_panel_heights(col, term_height)
                          for col in vsplit.columns]
                vsplit_height = _calc_vsplit_height(vsplit, all_ph)
                self._draw_vsplit_dividers(vsplit, current_row, vsplit_height,
                                           col_widths, term_width)
                current_row += vsplit_height

        # Pass 2: content regions
        for name, region in regions.items():
            interaction = interactions.get(name)
            focused = (name == focused_name)
            if interaction:
                self.render_region(region, interaction, term, focused)
            else:
                self._render_empty_region(region, focused)

        # Pass 3: partial borders (overlay on top of content)
        current_row = 0
        for item in items:
            if isinstance(item, BorderRow):
                current_row += 1
            else:
                vsplit = item
                col_widths = _resolve_col_widths(vsplit.columns, term_width)
                all_ph = [_resolve_panel_heights(col, term_height)
                          for col in vsplit.columns]
                vsplit_height = _calc_vsplit_height(vsplit, all_ph)
                self._draw_partial_borders(vsplit, current_row, col_widths,
                                           all_ph, term_width)
                current_row += vsplit_height

        sys.stdout.flush()

    def _draw_vsplit_dividers(self, vsplit: VSplit, start_row: int,
                               height: int, col_widths: list,
                               term_width: int) -> None:
        """Draw outer border bars and internal column dividers for all rows."""
        term = self._term
        for row_offset in range(height):
            row = start_row + row_offset
            print(term.move(row, 0) + '│', end='', flush=False)
            print(term.move(row, term_width - 1) + '│', end='', flush=False)
            col_pos = 1
            for i, col in enumerate(vsplit.columns):
                col_pos += col_widths[i]
                if i < len(vsplit.columns) - 1:
                    divider = '║' if col.double_divider_right else '│'
                    print(term.move(row, col_pos) + divider, end='', flush=False)
                    col_pos += 1

    def _draw_partial_borders(self, vsplit: VSplit, vsplit_start_row: int,
                               col_widths: list, all_ph: list,
                               term_width: int) -> None:
        """Draw partial border rows within a VSplit."""
        term = self._term
        n_cols = len(vsplit.columns)

        # For each column, compute the set of row offsets (within the VSplit)
        # where a partial border appears, and the border style at that offset.
        pb_at_offset = {}  # row_offset -> {col_idx -> pb_style}
        for i, col in enumerate(vsplit.columns):
            ph = all_ph[i]
            offset = 0
            for j, panel in enumerate(col.panels):
                offset += ph[j]
                if j < len(col.partial_borders):
                    pb = col.partial_borders[j]
                    if offset not in pb_at_offset:
                        pb_at_offset[offset] = {}
                    pb_at_offset[offset][i] = pb.style
                    offset += 1  # the partial border row itself

        if not pb_at_offset:
            return

        # Compute column start positions within the terminal row
        col_start = []
        pos = 1
        for i, col in enumerate(vsplit.columns):
            col_start.append(pos)
            pos += col_widths[i] + 1

        for row_offset, col_borders in pb_at_offset.items():
            row = vsplit_start_row + row_offset
            # Determine the border style for this row (use first col's style)
            pb_style = next(iter(col_borders.values()))

            fill_char = '═' if pb_style == 'double' else '─'

            # Build the line character by character
            # First set all positions to either fill or vertical divider
            line = [' '] * term_width

            # Left outer edge
            left_has_border = 0 in col_borders
            v_style = 'single'  # outer border is always single vertical
            tbl = _box(pb_style, v_style)
            line[0] = tbl['lt'] if left_has_border else '│'

            # Right outer edge
            right_has_border = (n_cols - 1) in col_borders
            line[term_width - 1] = tbl['rt'] if right_has_border else '│'

            # Fill each column's area
            for i in range(n_cols):
                start = col_start[i]
                w = col_widths[i]
                if i in col_borders:
                    for x in range(start, start + w):
                        line[x] = fill_char
                # else: leave as spaces (content region)

            # Internal divider positions
            divider_pos = 1
            for i, col in enumerate(vsplit.columns):
                divider_pos += col_widths[i]
                if i < n_cols - 1:
                    left_col_has_border = i in col_borders
                    right_col_has_border = (i + 1) in col_borders
                    v_style = 'double' if col.double_divider_right else 'single'
                    tbl = _box(pb_style, v_style)
                    if left_col_has_border and right_col_has_border:
                        line[divider_pos] = tbl['cr']
                    elif left_col_has_border:
                        line[divider_pos] = tbl['rt']
                    elif right_col_has_border:
                        line[divider_pos] = tbl['lt']
                    else:
                        line[divider_pos] = '║' if col.double_divider_right else '│'
                    divider_pos += 1

            print(term.move(row, 0) + ''.join(line), end='', flush=False)

    def render_region(self, region: Region, interaction, term, focused: bool):
        interaction.render(region, term, focused)

    def _render_empty_region(self, region: Region, focused: bool):
        term = self._term
        for row_offset in range(region.height):
            row = region.row + row_offset
            print(term.move(row, region.col) + ' ' * region.width,
                  end='', flush=False)

    def draw_border(self, row: int, term_width: int, style: str, title=None,
                    prev_dividers: dict | None = None,
                    next_dividers: dict | None = None) -> None:
        """Draw a full-width horizontal border row."""
        term = self._term
        fill = '═' if style == 'double' else '─'
        prev = prev_dividers or {}
        nxt = next_dividers or {}

        chars = [fill] * term_width

        v_up = prev.get(0)
        v_dn = nxt.get(0)
        chars[0] = _border_end_char(style, v_up, v_dn, 'l')

        v_up = prev.get(term_width - 1)
        v_dn = nxt.get(term_width - 1)
        chars[term_width - 1] = _border_end_char(style, v_up, v_dn, 'r')

        all_positions = set(prev.keys()) | set(nxt.keys())
        for pos in all_positions:
            if 0 < pos < term_width - 1:
                v_up = prev.get(pos)
                v_dn = nxt.get(pos)
                chars[pos] = _border_cross_char(style, v_up, v_dn)

        line = ''.join(chars)
        print(term.move(row, 0) + line, end='', flush=False)

        if title:
            plain_title = f' {styled_plain_text(title)} '
            title_len = len(plain_title)
            inner_width = term_width - 2
            if title_len <= inner_width:
                left_fill = (inner_width - title_len) // 2
                title_start = 1 + left_fill
                rendered = render_styled(f' {title} ', term)
                try:
                    reset = str(term.normal) if term.normal else ''
                except Exception:
                    reset = ''
                print(term.move(row, title_start) + rendered + reset,
                      end='', flush=False)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _calc_vsplit_height(vsplit: VSplit, all_ph: list) -> int:
    """Compute physical height of a VSplit from already-resolved panel heights."""
    h = 0
    for col, ph in zip(vsplit.columns, all_ph):
        col_phys = sum(ph) + len(col.partial_borders)
        h = max(h, col_phys)
    return max(h, 1)
