from dataclasses import dataclass, field


@dataclass(frozen=True)
class Region:
    name: str
    row: int        # 0-based terminal row
    col: int        # 0-based terminal col
    width: int
    height: int


@dataclass
class Panel:
    """A single content leaf within a column."""
    name: str | None
    row_count: int | None       # None = infer from num_rows_def
    row_count_is_pct: bool
    row_pct: float | None
    heading: str | None
    num_rows_def: int = 0       # definition lines in this panel's slot


@dataclass
class PartialBorder:
    """A horizontal divider between panels within a single column."""
    style: str   # 'single' or 'double'


@dataclass
class ColumnDef:
    """One column within a VSplit."""
    width: int | None       # fixed chars; None = fill remainder
    is_percentage: bool
    pct: float | None       # percentage 0..100
    double_divider_right: bool
    panels: list            # list[Panel], at least one
    partial_borders: list   # list[PartialBorder], len == len(panels) - 1


@dataclass
class VSplit:
    """Columns arranged side by side."""
    columns: list   # list[ColumnDef]


@dataclass
class BorderRow:
    style: str          # 'single' or 'double'
    title: str | None


@dataclass
class LayoutModel:
    items: list         # list[BorderRow | VSplit], ordered top-to-bottom
    has_percentage: bool

    def resolve(self, term_width: int, term_height: int) -> list:
        """Return a flat list of Region objects with absolute coordinates."""
        regions = []
        current_row = 0

        for item in self.items:
            if isinstance(item, BorderRow):
                current_row += 1
                continue

            vsplit = item
            col_widths = _resolve_col_widths(vsplit.columns, term_width)

            # Resolve all panel heights
            all_ph = [_resolve_panel_heights(col, term_height) for col in vsplit.columns]

            # VSplit physical height = max total rows across all columns
            # Each column's physical rows = sum(panel heights) + number of partial borders
            vsplit_height = 0
            for col, ph in zip(vsplit.columns, all_ph):
                col_phys = sum(ph) + len(col.partial_borders)
                vsplit_height = max(vsplit_height, col_phys)
            vsplit_height = max(vsplit_height, 1)

            # Stretch the last panel of any column that's shorter than vsplit_height
            for i, (col, ph) in enumerate(zip(vsplit.columns, all_ph)):
                col_phys = sum(ph) + len(col.partial_borders)
                if col_phys < vsplit_height:
                    all_ph[i][-1] += vsplit_height - col_phys

            # Compute column start positions
            col_positions = []
            pos = 1  # after outer left border
            for i, col in enumerate(vsplit.columns):
                col_positions.append(pos)
                pos += col_widths[i] + 1  # +1 for divider

            # Emit regions
            for i, (col, ph) in enumerate(zip(vsplit.columns, all_ph)):
                panel_row = current_row
                for j, panel in enumerate(col.panels):
                    h = ph[j]
                    if panel.name:
                        regions.append(Region(
                            name=panel.name,
                            row=panel_row,
                            col=col_positions[i],
                            width=col_widths[i],
                            height=h,
                        ))
                    panel_row += h
                    if j < len(col.partial_borders):
                        panel_row += 1  # skip the partial border row

            current_row += vsplit_height

        return regions


def _resolve_col_widths(columns: list, term_width: int) -> list:
    """Resolve column widths to absolute character counts."""
    num_cols = len(columns)
    available = term_width - 2 - (num_cols - 1)

    widths = [None] * num_cols
    remaining = available
    fill_index = None

    for i, col in enumerate(columns):
        if col.width is None and not col.is_percentage:
            fill_index = i
        elif col.is_percentage:
            w = int(available * col.pct / 100)
            widths[i] = w
            remaining -= w
        else:
            widths[i] = col.width
            remaining -= col.width

    if fill_index is not None:
        widths[fill_index] = max(0, remaining)

    return [w if w is not None else 0 for w in widths]


def _resolve_panel_heights(col: ColumnDef, term_height: int) -> list:
    """Return a list of resolved heights (ints) for each panel in the column."""
    heights = []
    for panel in col.panels:
        if panel.row_count is not None:
            if panel.row_count_is_pct:
                h = int(term_height * panel.row_pct / 100)
            else:
                h = panel.row_count
        else:
            h = max(1, panel.num_rows_def)
        heights.append(h)
    return heights
