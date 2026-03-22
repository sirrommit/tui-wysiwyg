"""StatusMessage interaction — inline status/validation feedback region.

Displays a single-line message with one of three severity styles:

  - ``"error"``   — prefixed with ``✗ ``, rendered in red (or reverse if no colour)
  - ``"success"`` — prefixed with ``✓ ``, rendered in green
  - ``"info"``    — prefixed with ``ℹ ``, rendered in the terminal default colour

Not focusable; receives updates via ``shell.update(name, value)`` where
*value* is one of:

  - ``None`` or ``""``          — clears the region (shows blank)
  - ``(style, message)`` tuple  — style is ``"error"``, ``"success"``, or ``"info"``
  - A plain ``str``             — treated as ``("info", str)``

Example::

    from tui_wysiwyg.interactions import StatusMessage

    shell.assign("status", StatusMessage())
    shell.update("status", ("error", "File not found"))
    shell.update("status", ("success", "Saved"))
    shell.update("status", None)          # clear
"""

from .base import Interaction


_PREFIXES = {
    "error":   "✗ ",
    "success": "✓ ",
    "info":    "ℹ ",
}


class StatusMessage(Interaction):
    """Inline status / validation feedback region.

    Not focusable.  Updated programmatically via ``shell.update()``.
    """

    def __init__(self):
        self._style   = "info"
        self._message = ""

    @property
    def is_focusable(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, region, term, focused: bool = False) -> None:
        if not self._message:
            blank = " " * region.width
            print(term.move(region.row, region.col) + blank, end="", flush=False)
            for r in range(1, region.height):
                print(term.move(region.row + r, region.col) + blank, end="", flush=False)
            return

        prefix  = _PREFIXES.get(self._style, "")
        text    = f"{prefix}{self._message}"
        clipped = text[:region.width].ljust(region.width)

        # Apply colour if supported
        styled = clipped
        try:
            if self._style == "error":
                styled = term.red + clipped + term.normal
            elif self._style == "success":
                styled = term.green + clipped + term.normal
        except Exception:
            pass  # terminal has no colour support; fall back to plain text

        print(term.move(region.row, region.col) + styled, end="", flush=False)
        blank = " " * region.width
        for r in range(1, region.height):
            print(term.move(region.row + r, region.col) + blank, end="", flush=False)

    # ------------------------------------------------------------------
    # Interaction protocol (display-only)
    # ------------------------------------------------------------------

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self):
        if not self._message:
            return None
        return (self._style, self._message)

    def set_value(self, value) -> None:
        if value is None or value == "":
            self._style   = "info"
            self._message = ""
        elif isinstance(value, tuple) and len(value) == 2:
            style, message = value
            self._style   = style if style in _PREFIXES else "info"
            self._message = str(message) if message else ""
        else:
            self._style   = "info"
            self._message = str(value)
