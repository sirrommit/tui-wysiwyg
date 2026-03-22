"""_ScrollableList — shared base for vertically scrollable list interactions.

Subclasses inherit:
  - ``_active_index``  / ``_scroll_offset`` state
  - ``_clamp_scroll()`` — adjusts offset so the active item is always visible
  - ``_render_rows()``  — renders the visible viewport slice with focus/active
                          highlighting and clears trailing rows

Usage in a subclass render()::

    def render(self, region, term, focused: bool = False) -> None:
        viewport = self._labels[self._scroll_offset:
                                 self._scroll_offset + region.height]
        self._render_rows(viewport, region, term, focused)

Usage after moving _active_index in handle_key()::

    self._active_index = max(0, self._active_index - 1)
    self._clamp_scroll()
"""

from .base import Interaction


class _ScrollableList(Interaction):
    """Abstract base for list-like interactions that support scroll offset."""

    _active_index: int = 0
    _scroll_offset: int = 0
    _last_height: int = 10   # updated on every render call

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------

    def _clamp_scroll(self) -> None:
        """Adjust _scroll_offset so _active_index is within the viewport.

        Uses the height recorded on the last render() call.  Safe to call
        before the first render (falls back to _last_height = 10).
        """
        h = max(1, self._last_height)
        if self._active_index < self._scroll_offset:
            self._scroll_offset = self._active_index
        elif self._active_index >= self._scroll_offset + h:
            self._scroll_offset = self._active_index - h + 1

    # ------------------------------------------------------------------
    # Shared render helper
    # ------------------------------------------------------------------

    def _render_rows(
        self,
        display_lines: list,
        region,
        term,
        focused: bool,
        active_marker: bool = True,
    ) -> None:
        """Render *display_lines* (the visible viewport slice) into *region*.

        Parameters
        ----------
        display_lines:
            Pre-sliced list of strings — one per visible row, starting at
            ``_scroll_offset``.  Each string is the full display text for
            that item (e.g. ``'label'`` or ``'[X] label'``).
        region:
            The Region object describing position and size.
        term:
            Blessed Terminal (or mock).
        focused:
            Whether this interaction has keyboard focus.
        active_marker:
            If True (default), the active row gets a ``>`` prefix when the
            interaction is not focused.  Set to False for interactions
            (e.g. CheckBox) that only highlight when focused.
        """
        self._last_height = region.height

        for screen_i, line in enumerate(display_lines):
            item_idx = self._scroll_offset + screen_i
            row = region.row + screen_i
            clipped = line[:region.width].ljust(region.width)

            if item_idx == self._active_index and focused:
                try:
                    text = term.reverse + clipped + term.normal
                except Exception:
                    text = f'> {line}'[:region.width].ljust(region.width)
            elif item_idx == self._active_index and active_marker:
                text = f'> {line}'[:region.width].ljust(region.width)
            else:
                text = clipped

            print(term.move(row, region.col) + text, end='', flush=False)

        # Clear any rows below the rendered items
        for r in range(region.row + len(display_lines), region.row + region.height):
            print(term.move(r, region.col) + ' ' * region.width, end='', flush=False)
