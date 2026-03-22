from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    name: str
    row: int        # 0-based terminal row
    col: int        # 0-based terminal col
    width: int
    height: int


@dataclass
class BorderRow:
    style: str          # 'single' or 'double'
    title: str | None


@dataclass
class Panel:
    """Leaf node — a single named (or unnamed) content region."""
    name: str | None
    heading: str | None
    # Width spec
    width: int | None       # fixed chars; None = fill or use pct
    is_pct: bool
    pct: float | None       # percentage 0..100; used when is_pct is True
    # Height spec
    row_count: int | None   # None = infer from num_rows_def
    row_count_is_pct: bool
    row_pct: float | None
    num_rows_def: int = 0   # definition lines in this panel's slot


@dataclass
class HSplit:
    """Horizontal split: top child above a border line, bottom child below."""
    top: object         # LayoutNode | None
    bottom: object      # LayoutNode | None
    border: BorderRow | None


@dataclass
class VSplit:
    """Vertical split: left and right children side by side."""
    left: object        # LayoutNode
    right: object       # LayoutNode
    divider: str        # 'single' or 'double'


# Type alias (for documentation only — Python does not enforce it)
# LayoutNode = HSplit | VSplit | Panel | None


@dataclass
class LayoutModel:
    root: object        # LayoutNode | None
    has_percentage: bool

    def resolve(self, term_width: int, term_height: int,
                offset_row: int = 0, offset_col: int = 0) -> list:
        """Return a flat list of Region objects with absolute coordinates.

        offset_row / offset_col shift the origin so that modal shells
        (which render at an arbitrary screen position) produce regions
        with the correct absolute terminal coordinates from the start.
        """
        if self.root is None:
            return []
        # Content area starts one column inside the left border wall.
        return _resolve_node(self.root,
                             offset_row,
                             offset_col + 1,
                             term_width - 2, term_height,
                             pct_base=None)


# ---------------------------------------------------------------------------
# Recursive resolve
# ---------------------------------------------------------------------------

def _resolve_node(node, row: int, col: int, width: int, height: int,
                  pct_base: int | None) -> list:
    """
    Recursively resolve a layout node to a flat list of Regions.

    row, col   — absolute top-left position of this node
    width      — available width (excluding outer border chars)
    height     — available height in terminal rows
    pct_base   — total interior width used as the denominator for % specs;
                 None means "compute on first VSplit encountered"
    """
    if node is None:
        return []

    if isinstance(node, Panel):
        if node.name:
            return [Region(name=node.name, row=row, col=col,
                           width=width, height=height)]
        return []

    if isinstance(node, VSplit):
        if pct_base is None:
            num_cols = _num_vsplit_cols(node)
            # Subtract one divider per internal column boundary
            pct_base = width - (num_cols - 1)

        left_width = _vsplit_left_width(node, width, pct_base)
        right_width = width - left_width - 1

        regions = _resolve_node(node.left, row, col,
                                left_width, height, pct_base)
        regions += _resolve_node(node.right, row, col + left_width + 1,
                                 right_width, height, pct_base)
        return regions

    if isinstance(node, HSplit):
        top_height = (_declared_height(node.top, height)
                      if node.top is not None else 0)
        border_rows = 1 if node.border is not None else 0
        bottom_height = max(0, height - top_height - border_rows)

        regions = []
        if node.top is not None:
            regions += _resolve_node(node.top, row, col, width, top_height,
                                     None)
        if node.bottom is not None:
            regions += _resolve_node(node.bottom,
                                     row + top_height + border_rows,
                                     col, width, bottom_height, None)
        return regions

    return []


# ---------------------------------------------------------------------------
# Width / height helpers
# ---------------------------------------------------------------------------

def _declared_width(node, available: int, pct_base: int) -> int:
    """
    How wide does this node want to be?

    available  — remaining width at this level (after subtracting the
                 divider that separates it from its sibling)
    pct_base   — total interior width for percentage calculations
    """
    if node is None:
        return available

    if isinstance(node, Panel):
        if node.is_pct and node.pct is not None:
            return int(pct_base * node.pct / 100)
        if node.width is not None:
            return node.width
        return available  # fill

    if isinstance(node, HSplit):
        # Both halves of an HSplit share the same width; delegate to a child.
        child = node.top if node.top is not None else node.bottom
        return _declared_width(child, available, pct_base)

    if isinstance(node, VSplit):
        # A VSplit takes all available width.
        return available

    return available


def _declared_height(node, available: int) -> int:
    """
    How tall does this node want to be?
    Panels without an explicit row_count use num_rows_def as a minimum.
    The caller may give a Panel more height than it declares (stretch).
    """
    if node is None:
        return 0

    if isinstance(node, Panel):
        if node.row_count is not None:
            if node.row_count_is_pct and node.row_pct is not None:
                return int(available * node.row_pct / 100)
            return node.row_count
        return max(1, node.num_rows_def)

    if isinstance(node, VSplit):
        lh = _declared_height(node.left, available)
        rh = _declared_height(node.right, available)
        return max(lh, rh)

    if isinstance(node, HSplit):
        top_h = (_declared_height(node.top, available)
                 if node.top is not None else 0)
        border_h = 1 if node.border is not None else 0
        bot_h = (_declared_height(node.bottom, available)
                 if node.bottom is not None else 0)
        return top_h + border_h + bot_h

    return 0


def _fixed_width(node) -> int | None:
    """
    Return the node's exact content width if every column uses a fixed character
    count (no percentages, no fill).  Returns None if any dimension is variable.

    Does NOT include the two outer border-wall columns — add 2 for terminal width.
    """
    if node is None:
        return 0

    if isinstance(node, Panel):
        if node.width is not None and not node.is_pct:
            return node.width
        return None   # fill or percentage

    if isinstance(node, VSplit):
        lw = _fixed_width(node.left)
        rw = _fixed_width(node.right)
        if lw is None or rw is None:
            return None
        return lw + 1 + rw   # left content + divider + right content

    if isinstance(node, HSplit):
        child = node.top if node.top is not None else node.bottom
        return _fixed_width(child)

    return None


def _fixed_height(node) -> int | None:
    """
    Return the node's exact height in rows if every row-bearing panel carries an
    explicit nR declaration (no fill, no percentage rows).  Returns None otherwise.

    Border rows are always 1 row each and are always counted.
    """
    if node is None:
        return 0

    if isinstance(node, Panel):
        if node.row_count is not None and not node.row_count_is_pct:
            return node.row_count
        return None   # fill (num_rows_def) or percentage

    if isinstance(node, VSplit):
        lh = _fixed_height(node.left)
        rh = _fixed_height(node.right)
        if lh is None or rh is None:
            return None
        return max(lh, rh)

    if isinstance(node, HSplit):
        top_h = 0
        if node.top is not None:
            top_h = _fixed_height(node.top)
            if top_h is None:
                return None
        bot_h = 0
        if node.bottom is not None:
            bot_h = _fixed_height(node.bottom)
            if bot_h is None:
                return None
        border_h = 1 if node.border is not None else 0
        return top_h + border_h + bot_h

    return None


def _vsplit_left_width(node: "VSplit", width: int, pct_base: int) -> int:
    """Return the left-panel width for a VSplit given *width* available chars.

    If the left side is fill and the right side has an explicit fixed/pct
    declaration, the right side gets its declared width and the left side
    fills the remainder.  Otherwise the left side is allocated first and the
    right side takes what is left.

    ``pct_base`` must already be computed before calling this helper.
    """
    if _is_fill_node(node.left) and not _is_fill_node(node.right):
        right_w = min(_declared_width(node.right, width - 1, pct_base), width - 1)
        return width - right_w - 1
    return _declared_width(node.left, width - 1, pct_base)


def _is_fill_node(node) -> bool:
    """Return True if *node* has no explicit fixed-char or percentage width.

    A fill node takes whatever space is left after fixed/pct siblings are
    allocated.  Used by VSplit resolution to decide which side to allocate
    first when one side is fill and the other is fixed.
    """
    if node is None:
        return True
    if isinstance(node, Panel):
        return node.width is None and not node.is_pct
    if isinstance(node, HSplit):
        child = node.top if node.top is not None else node.bottom
        return _is_fill_node(child)
    if isinstance(node, VSplit):
        # A VSplit consumes all available width; treat it as non-fill so that
        # a sibling fixed panel still gets its declared width.
        return False
    return True


def _num_vsplit_cols(node) -> int:
    """Count the total number of leaf Panel columns in a node's subtree."""
    if node is None:
        return 0
    if isinstance(node, Panel):
        return 1
    if isinstance(node, VSplit):
        return _num_vsplit_cols(node.left) + _num_vsplit_cols(node.right)
    if isinstance(node, HSplit):
        # Both halves of an HSplit are in the same column — count one side.
        child = node.top if node.top is not None else node.bottom
        return _num_vsplit_cols(child)
    return 1
