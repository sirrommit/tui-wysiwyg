import sys
import blessed
try:
    import termios as _termios
    _HAS_TERMIOS = True
except ImportError:
    _HAS_TERMIOS = False
from .parser import Parser
from .layout import LayoutModel, _fixed_width, _fixed_height
from .renderer import Renderer
from .events import EventLoop
from .observer import Observer, ChangeHandle
from .exceptions import RegionNotFoundError, CircularUpdateError


class Shell:
    def __init__(self, definition: str, _terminal=None):
        self._term = _terminal or blessed.Terminal()
        self._layout = Parser().parse(definition)
        self._regions = {}       # name -> Region (resolved geometry)
        self._interactions = {}  # name -> Interaction
        self._observer = Observer()
        self._focus_order = []   # list of region names in tab order
        self._focused = None
        self._dirty = set()      # region names needing redraw
        self._return_value = None
        self._should_exit = False
        self._renderer = None
        self._resolve_layout()

    def _resolve_layout(self, width=None, height=None,
                        offset_row: int = 0, offset_col: int = 0):
        w = width  if width  is not None else (self._term.width  or 80)
        h = height if height is not None else (self._term.height or 24)
        regions = self._layout.resolve(w, h, offset_row=offset_row, offset_col=offset_col)
        self._regions = {r.name: r for r in regions}
        # Focus order: reading order (top-to-bottom, left-to-right)
        self._focus_order = [r.name for r in sorted(regions, key=lambda r: (r.row, r.col))]

    def assign(self, name: str, interaction) -> None:
        """Assign an interaction to a named region."""
        if name not in self._regions:
            raise RegionNotFoundError(f"no region named '{name}' in this shell")
        if name in self._interactions:
            raise ValueError(f"region '{name}' already has an assigned interaction; call unassign() first")
        interaction._shell = self
        self._interactions[name] = interaction
        self._dirty.add(name)

    def unassign(self, name: str):
        """Remove the interaction assigned to a region."""
        if name not in self._regions:
            raise RegionNotFoundError(f"no region named '{name}' in this shell")
        interaction = self._interactions.pop(name, None)
        if self._focused == name:
            self._focused = None
        return interaction

    def get(self, name: str):
        """Get the current value of a named region."""
        if name not in self._regions:
            raise RegionNotFoundError(f"no region named '{name}' in this shell")
        interaction = self._interactions.get(name)
        if interaction is None:
            return None
        return interaction.get_value()

    def update(self, name: str, value, _updating: set | None = None) -> None:
        """Programmatically set a region's value and mark it dirty."""
        if name not in self._regions:
            raise RegionNotFoundError(f"no region named '{name}' in this shell")
        interaction = self._interactions.get(name)
        if interaction is None:
            return
        interaction.set_value(value)
        self._dirty.add(name)
        self._observer.notify(name, value, updating=_updating)

    def on_change(self, name: str, callback) -> ChangeHandle:
        """Register a callback to fire when a region's value changes."""
        if name not in self._regions:
            raise RegionNotFoundError(f"no region named '{name}' in this shell")

        def _cb(value, updating=None):
            callback(value)  # User callback doesn't need updating set

        return self._observer.register(name, _cb)

    def bind(self, source: str, target: str, transform=None) -> ChangeHandle:
        """When source changes, update target with the (optionally transformed) new value."""
        if source not in self._regions:
            raise RegionNotFoundError(f"no region named '{source}' in this shell")
        if target not in self._regions:
            raise RegionNotFoundError(f"no region named '{target}' in this shell")

        def _cb(value, updating=None):
            if transform is not None:
                value = transform(value)
            self.update(target, value, _updating=updating)

        return self._observer.register(source, _cb)

    def set_focus(self, name: str) -> None:
        """Move focus to a named region programmatically."""
        if name not in self._regions:
            raise RegionNotFoundError(f"no region named '{name}' in this shell")
        if name not in self._interactions:
            raise ValueError(f"region '{name}' has no assigned interaction and cannot receive focus")
        self._focused = name

    @property
    def focus(self):
        return self._focused

    @property
    def terminal(self):
        return self._term

    def _move_focus(self, direction: int) -> None:
        """Move focus by direction (+1 or -1) in tab order."""
        interactive = [
            n for n in self._focus_order
            if n in self._interactions and self._interactions[n].is_focusable
        ]
        if len(interactive) < 2:
            # Nothing to cycle to — stay put, no redraw needed
            return
        if self._focused not in interactive:
            self._focused = interactive[0]
            return
        idx = interactive.index(self._focused)
        new_idx = (idx + direction) % len(interactive)
        old_focus = self._focused
        self._focused = interactive[new_idx]
        self._dirty.add(old_focus)
        self._dirty.add(self._focused)

    def run(self):
        """Start the TUI event loop. Returns the exit value."""
        renderer = Renderer(self._term)
        self._renderer = renderer
        event_loop = EventLoop(self._term)

        # Find first focusable region for initial focus
        for name in self._focus_order:
            if name in self._interactions and self._interactions[name].is_focusable:
                self._focused = name
                break

        term = self._term
        w = term.width or 80
        h = term.height or 24

        with term.fullscreen(), term.cbreak(), term.hidden_cursor():
            # Disable XON/XOFF flow control so Ctrl+Q (0x11) reaches the app.
            # term.cbreak() does not clear IXON, leaving Ctrl+Q intercepted by
            # the terminal driver on most Linux/macOS systems.
            # Save original attrs so we can restore them on every exit path.
            _saved_attrs = None
            if _HAS_TERMIOS and hasattr(term, '_keyboard_fd'):
                try:
                    _saved_attrs = _termios.tcgetattr(term._keyboard_fd)
                    attrs = list(_saved_attrs)
                    attrs[0] &= ~_termios.IXON
                    _termios.tcsetattr(term._keyboard_fd, _termios.TCSANOW, attrs)
                except Exception:
                    _saved_attrs = None

            try:
                # Initial full render
                renderer.full_render(
                    self._layout,
                    self._regions,
                    self._interactions,
                    self._focused,
                    w,
                    h,
                )
                sys.stdout.flush()

                while not self._should_exit:
                    key = event_loop.next_key()
                    if key is None or not key:
                        continue

                    key_str = str(key)

                    # Ctrl+Q to exit
                    if key_str == chr(17):
                        return None

                    # Tab / Shift+Tab for focus movement
                    if key.is_sequence and key.name == 'KEY_BTAB':
                        self._move_focus(-1)
                    elif key_str == '\t':
                        self._move_focus(1)
                    elif self._focused and self._focused in self._interactions:
                        interaction = self._interactions[self._focused]
                        changed, value = interaction.handle_key(key)
                        # Always redraw after any keypress (cursor move, nav, etc.)
                        self._dirty.add(self._focused)
                        if changed:
                            self._observer.notify(self._focused, value)

                        # Check for exit signal
                        should_exit, rv = interaction.signal_return()
                        if should_exit:
                            return rv

                    # Handle resize
                    if key.is_sequence and hasattr(key, 'name') and key.name == 'KEY_RESIZE':
                        w = term.width or 80
                        h = term.height or 24
                        self._resolve_layout()
                        renderer.full_render(
                            self._layout,
                            self._regions,
                            self._interactions,
                            self._focused,
                            w,
                            h,
                        )
                        sys.stdout.flush()
                        continue

                    # Redraw dirty regions
                    for dirty_name in list(self._dirty):
                        if dirty_name in self._interactions and dirty_name in self._regions:
                            region = self._regions[dirty_name]
                            interaction = self._interactions[dirty_name]
                            focused = (dirty_name == self._focused)
                            renderer.render_region(region, interaction, term, focused)
                    self._dirty.clear()
                    sys.stdout.flush()

            finally:
                # Restore terminal attributes so IXON is not left disabled
                # after the TUI exits (covers normal return, Ctrl+Q, exceptions).
                if _saved_attrs is not None and _HAS_TERMIOS and hasattr(term, '_keyboard_fd'):
                    try:
                        _termios.tcsetattr(
                            term._keyboard_fd, _termios.TCSADRAIN, _saved_attrs
                        )
                    except Exception:
                        pass

        return None

    def run_modal(self, row=None, col=None, width=None, height=None,
                  parent_shell=None):
        """Run this Shell as a modal popup overlaid at (row, col, width, height).

        Must be called while a parent Shell is already running (i.e. the
        terminal is already in fullscreen/cbreak/hidden_cursor context — for
        example, from inside a MenuFunction callback).  Does NOT re-enter those
        context managers.

        width / height — if omitted, the shell's natural size is used when every
                         panel carries an explicit fixed dimension (nR / n-char).
                         Otherwise defaults to 60 % of the terminal dimension.
        row / col      — if omitted, the popup is centered on screen.
        parent_shell   — if provided, its display is fully restored when the
                         modal exits.

        Returns the modal's exit value (same semantics as run()).
        Escape or Ctrl+Q dismiss the modal and return None.
        """
        term = self._term
        tw = term.width  or 80
        th = term.height or 24
        root = self._layout.root

        if width is None:
            fw = _fixed_width(root)
            width = (fw + 2) if fw is not None else max(1, int(tw * 0.6))

        if height is None:
            fh = _fixed_height(root)
            height = fh if fh is not None else max(1, int(th * 0.6))

        if row is None:
            row = max(0, (th - height) // 2)

        if col is None:
            col = max(0, (tw - width) // 2)

        self._resolve_layout(width=width, height=height,
                             offset_row=row, offset_col=col)

        renderer = Renderer(self._term)
        self._renderer = renderer
        event_loop = EventLoop(self._term)
        term = self._term

        for name in self._focus_order:
            if name in self._interactions and self._interactions[name].is_focusable:
                self._focused = name
                break

        renderer.full_render(self._layout, self._regions, self._interactions,
                             self._focused, width, height,
                             offset_row=row, offset_col=col)
        sys.stdout.flush()

        result = None
        while True:
            key = event_loop.next_key()
            if key is None or not key:
                continue

            key_str = str(key)

            if key_str in (chr(27), chr(17)):   # Escape or Ctrl+Q → dismiss
                break

            if key.is_sequence and key.name == 'KEY_BTAB':
                self._move_focus(-1)
            elif key_str == '\t':
                self._move_focus(1)
            elif self._focused and self._focused in self._interactions:
                interaction = self._interactions[self._focused]
                changed, value = interaction.handle_key(key)
                self._dirty.add(self._focused)
                if changed:
                    self._observer.notify(self._focused, value)
                should_exit, rv = interaction.signal_return()
                if should_exit:
                    result = rv
                    break

            if key.is_sequence and getattr(key, 'name', None) == 'KEY_RESIZE':
                self._resolve_layout(width=width, height=height,
                                     offset_row=row, offset_col=col)
                renderer.full_render(self._layout, self._regions, self._interactions,
                                     self._focused, width, height,
                                     offset_row=row, offset_col=col)
                sys.stdout.flush()
                continue

            for dirty_name in list(self._dirty):
                if dirty_name in self._interactions and dirty_name in self._regions:
                    region = self._regions[dirty_name]
                    interaction = self._interactions[dirty_name]
                    renderer.render_region(region, interaction, term,
                                           dirty_name == self._focused)
            self._dirty.clear()
            sys.stdout.flush()

        # Restore parent display so the popup area doesn't leave a ghost.
        if parent_shell is not None and parent_shell._renderer is not None:
            tw = term.width or 80
            th = term.height or 24
            parent_shell._renderer.full_render(
                parent_shell._layout, parent_shell._regions,
                parent_shell._interactions, parent_shell._focused, tw, th)
            sys.stdout.flush()

        return result
