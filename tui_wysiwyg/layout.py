from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Region:
    name: str
    row: int        # 0-based terminal row
    col: int        # 0-based terminal col
    width: int
    height: int


@dataclass
class ColumnSpec:
    width: int | None       # None = fill remainder; int = chars
    is_percentage: bool
    pct: float | None       # if is_percentage, 0..100
    row_count: int | None   # None = infer
    row_count_is_pct: bool
    row_pct: float | None
    region_name: str | None
    heading_text: str | None    # underlined text in this column (may be None)
    double_divider_right: bool  # True if column is followed by # instead of |


@dataclass
class RowGroup:
    """A group of column rows between border rows."""
    columns: list  # list[ColumnSpec], one entry per column
    num_text_rows: int          # filler rows visible in definition
    border_top: str | None      # "double" or "single" or None
    border_bottom: str | None


@dataclass
class BorderRow:
    style: str         # "double" or "single"
    title: str | None


@dataclass
class LayoutModel:
    rows: list  # list[RowGroup | BorderRow], ordered top-to-bottom
    has_percentage: bool  # any % widths/heights?

    def resolve(self, term_width: int, term_height: int) -> list:
        """Convert the layout model to a flat list of Regions with absolute coordinates."""
        regions = []
        current_row = 0

        for item in self.rows:
            if isinstance(item, BorderRow):
                current_row += 1
                continue

            # RowGroup
            row_group = item

            # Resolve column widths
            col_widths = _resolve_widths(row_group.columns, term_width)

            # Resolve row height
            height = _resolve_height(row_group, term_height)

            # Compute column positions
            col_positions = []
            col_pos = 1  # start after outer left border '|'
            for i, col_spec in enumerate(row_group.columns):
                col_positions.append(col_pos)
                # Add 1 for divider between columns
                col_pos += col_widths[i] + 1

            # Create regions for named columns
            for i, col_spec in enumerate(row_group.columns):
                if col_spec.region_name:
                    region = Region(
                        name=col_spec.region_name,
                        row=current_row,
                        col=col_positions[i],
                        width=col_widths[i],
                        height=height,
                    )
                    regions.append(region)

            current_row += height

        return regions


def _resolve_widths(columns: list, term_width: int) -> list:
    """Resolve column widths to absolute character counts."""
    # Account for outer borders (2 chars) and dividers between columns
    # Total available = term_width - 2 (outer borders) - (num_cols - 1) dividers
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


def _resolve_height(row_group, term_height: int) -> int:
    """Resolve row group height."""
    for col in row_group.columns:
        if col.row_count is not None:
            if col.row_count_is_pct:
                return int(term_height * col.row_pct / 100)
            return col.row_count
    # Default to num_text_rows if no explicit row count
    return max(1, row_group.num_text_rows)
