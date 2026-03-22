"""Progress Bar widget — programmatically-driven progress indicator.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{2R $message$           }|
    |------------------------|
    |{2R $bar$               }|
    |------------------------|
    |{1R $buttons$           }|  ← omitted when cancellable=False
    |========================|

- ``$message$``  — ``ListView``: status text lines updated by the caller.
- ``$bar$``      — ``_BarInteraction``: draws ``[████████░░░░] 55%``.
- ``$buttons$``  — ``MenuReturn({"Cancel": None})``: optional Cancel button.

Height is auto-detected:
  - **9 rows** when ``cancellable=True``  (1+2+1+2+1+1+1)
  - **7 rows** when ``cancellable=False`` (1+2+1+2+1)

The widget does **not** use ``Shell.run_modal()`` — it manages its own
rendering so that ``set_progress()`` can push updates synchronously from
the caller's thread without waiting for a keypress.

Usage
-----

    from tui_wysiwyg.widgets.progress import Progress

    def do_work(sh):
        with Progress(title="Crunching…", total=len(items)).show(sh) as prog:
            for i, item in enumerate(items, 1):
                process(item)
                prog.set_progress(i, f"Processing {item}")
                if prog.cancelled:
                    break
"""

import sys
import contextlib
import datetime

from tui_wysiwyg import Shell
from tui_wysiwyg.interactions.base import Interaction
from tui_wysiwyg.interactions import ListView, MenuReturn
from tui_wysiwyg.renderer import Renderer
from tui_wysiwyg.events import EventLoop


# ---------------------------------------------------------------------------
# Shell definitions
# ---------------------------------------------------------------------------

def _shell_with_buttons(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{2R $message$           }|\n"
        "|------------------------|\n"
        "|{2R $bar$               }|\n"
        "|------------------------|\n"
        "|{1R $buttons$           }|\n"
        "|========================|\n"
    )


def _shell_no_buttons(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{2R $message$           }|\n"
        "|------------------------|\n"
        "|{2R $bar$               }|\n"
        "|========================|\n"
    )


# ---------------------------------------------------------------------------
# _BarInteraction
# ---------------------------------------------------------------------------

class _BarInteraction(Interaction):
    """Draws a filled progress bar: ``[████████░░░░░░] 55%``."""

    def __init__(self, state: dict):
        self._state = state

    @property
    def is_focusable(self):
        return False

    def render(self, region, term, focused: bool = False) -> None:
        current = self._state.get("current", 0)
        total   = self._state.get("total",   100) or 1
        pct     = int(100 * current / total)
        pct     = max(0, min(100, pct))

        # Reserve 7 chars for "[ ] XXX%" (brackets + space + 3-digit pct + %)
        bar_w   = max(1, region.width - 7)
        filled  = min(bar_w, int(bar_w * current / total))
        bar_str = "\u2588" * filled + "\u2591" * (bar_w - filled)
        line    = f"[{bar_str}] {pct:3d}%"
        line    = line[: region.width].ljust(region.width)

        print(term.move(region.row, region.col) + line, end="", flush=False)

        # Clear any remaining rows in the region
        for r in range(1, region.height):
            print(
                term.move(region.row + r, region.col) + " " * region.width,
                end="", flush=False,
            )

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self):
        return self._state.get("current", 0)

    def set_value(self, value) -> None:
        if value is not None:
            self._state["current"] = int(value)


# ---------------------------------------------------------------------------
# _CancelInteraction — wraps MenuReturn to record cancellation
# ---------------------------------------------------------------------------

class _CancelInteraction(MenuReturn):
    """MenuReturn that sets state["cancelled"] when Cancel is selected."""

    def __init__(self, state: dict):
        self._state = state
        super().__init__({"Cancel": None})

    def handle_key(self, key) -> tuple:
        changed, value = super().handle_key(key)
        should_exit, _ = super().signal_return()
        if should_exit:
            self._state["cancelled"] = True
        return changed, value


# ---------------------------------------------------------------------------
# _ProgressHandle — the object yielded to the caller
# ---------------------------------------------------------------------------

class _ProgressHandle:
    """Live handle to an active Progress popup.

    Returned by the context manager created by ``Progress.show()``.
    """

    def __init__(self, popup: Shell, state: dict, term, renderer: Renderer):
        self._popup   = popup
        self._state   = state
        self._term    = term
        self._renderer = renderer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_progress(self, current: int, message: str = "") -> None:
        """Update the bar to *current* and display *message*."""
        self._state["current"] = current

        popup = self._popup
        popup.update("bar", current)
        popup.update("message", [message] if message else [" "])

        # Render dirty regions immediately (don't wait for a keypress).
        self._flush_dirty()

        # Non-blocking check for Cancel keypress.
        self._poll_cancel()

    @property
    def cancelled(self) -> bool:
        return self._state.get("cancelled", False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _flush_dirty(self) -> None:
        popup    = self._popup
        renderer = self._renderer
        term     = self._term
        for name in list(popup._dirty):
            if name in popup._interactions and name in popup._regions:
                renderer.render_region(
                    popup._regions[name],
                    popup._interactions[name],
                    term,
                    name == popup._focused,
                )
        popup._dirty.clear()
        sys.stdout.flush()

    def _poll_cancel(self) -> None:
        """Read a keystroke without blocking; handle Cancel / Escape."""
        if self._state.get("cancelled"):
            return
        term = self._term
        key  = term.inkey(timeout=0)
        if not key:
            return
        key_str = str(key)

        # Escape or Ctrl+Q → cancel
        if key_str in (chr(27), chr(17)):
            self._state["cancelled"] = True
            return

        # Tab / Shift+Tab — move focus
        if key_str == "\t":
            self._popup._move_focus(1)
            self._flush_dirty()
        elif key.is_sequence and key.name == "KEY_BTAB":
            self._popup._move_focus(-1)
            self._flush_dirty()
        elif self._popup._focused and self._popup._focused in self._popup._interactions:
            interaction = self._popup._interactions[self._popup._focused]
            interaction.handle_key(key)
            self._popup._dirty.add(self._popup._focused)
            # Check if cancel button was activated
            should_exit, _ = interaction.signal_return()
            if should_exit:
                self._state["cancelled"] = True
            self._flush_dirty()


# ---------------------------------------------------------------------------
# Public widget class
# ---------------------------------------------------------------------------

class Progress:
    """Programmatically-driven progress bar popup.

    Parameters
    ----------
    title : str
        Text displayed in the popup border (rendered bold).
    total : int
        Total number of steps (used to compute the fill fraction).
    cancellable : bool
        If ``True`` (default), a Cancel button is shown.  The caller should
        check ``handle.cancelled`` after each ``set_progress()`` call.
    width : int
        Width of the popup in characters (including border walls).

    Usage
    -----

    Call ``show()`` as a context manager::

        with Progress(title="Working…", total=100).show(parent_shell=sh) as prog:
            for i, item in enumerate(items, 1):
                process(item)
                prog.set_progress(i, f"Item {i}/{len(items)}")
                if prog.cancelled:
                    break

    ``show()`` accepts the same keyword arguments as ``Shell.run_modal()``
    (``row``, ``col``) to override auto-centering.
    """

    def __init__(
        self,
        title: str = "Progress",
        total: int = 100,
        cancellable: bool = True,
        width: int = 50,
    ):
        self.title       = title
        self.total       = total
        self.cancellable = cancellable
        self.width       = width

    @contextlib.contextmanager
    def show(self, parent_shell=None, row=None, col=None):
        """Display the progress popup as a context manager.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is restored when the popup
            closes.
        row, col : int | None
            Override automatic centering.

        Yields
        ------
        _ProgressHandle
            Object with ``set_progress(current, message)`` and
            ``cancelled`` attribute.
        """
        term = parent_shell.terminal if parent_shell is not None else None
        if term is None:
            import blessed
            term = blessed.Terminal()

        state = {
            "current":   0,
            "total":     self.total,
            "cancelled": False,
        }

        shell_def = (
            _shell_with_buttons(self.title)
            if self.cancellable
            else _shell_no_buttons(self.title)
        )
        popup = Shell(shell_def, _terminal=term)
        popup.assign("message", ListView([" "]))
        popup.assign("bar",     _BarInteraction(state))
        if self.cancellable:
            popup.assign("buttons", _CancelInteraction(state))

        # ---- Resolve layout (mirrors run_modal geometry logic) ----
        tw = term.width  or 80
        th = term.height or 24

        from tui_wysiwyg.layout import _fixed_width, _fixed_height
        from tui_wysiwyg.parser import Parser

        fw = _fixed_width(popup._layout.root)
        width  = (fw + 2) if fw is not None else max(1, int(tw * 0.6))
        width  = self.width  # caller override always wins

        fh = _fixed_height(popup._layout.root)
        height = fh if fh is not None else max(1, int(th * 0.6))

        if row is None:
            row = max(0, (th - height) // 2)
        if col is None:
            col = max(0, (tw - width)  // 2)

        popup._resolve_layout(width=width, height=height,
                              offset_row=row, offset_col=col)

        # Set initial focus
        for name in popup._focus_order:
            if name in popup._interactions and popup._interactions[name].is_focusable:
                popup._focused = name
                break

        # ---- Initial render ----
        renderer = Renderer(term)
        popup._renderer = renderer
        renderer.full_render(
            popup._layout, popup._regions, popup._interactions,
            popup._focused, width, height,
            offset_row=row, offset_col=col,
        )
        sys.stdout.flush()

        handle = _ProgressHandle(popup, state, term, renderer)

        try:
            yield handle
        finally:
            # Restore parent display
            if parent_shell is not None and parent_shell._renderer is not None:
                parent_shell._renderer.full_render(
                    parent_shell._layout, parent_shell._regions,
                    parent_shell._interactions, parent_shell._focused,
                    tw, th,
                )
                sys.stdout.flush()
