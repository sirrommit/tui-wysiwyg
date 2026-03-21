"""MockTerminal for headless testing of tui_wysiwyg components."""
import contextlib
import io


class MockKeystroke:
    """Simulates a blessed.keyboard.Keystroke object."""

    def __init__(self, value: str, is_sequence: bool = False, name: str = None):
        self._value = value
        self.is_sequence = is_sequence
        self.name = name

    def __str__(self):
        return self._value

    def __repr__(self):
        return f'MockKeystroke({self._value!r}, is_sequence={self.is_sequence}, name={self.name!r})'

    def __bool__(self):
        return bool(self._value)

    def __eq__(self, other):
        if isinstance(other, str):
            return self._value == other
        if isinstance(other, MockKeystroke):
            return self._value == other._value
        return NotImplemented

    def __hash__(self):
        return hash(self._value)


# Common key mappings
_KEY_SEQUENCES = {
    'KEY_UP': '\x1b[A',
    'KEY_DOWN': '\x1b[B',
    'KEY_LEFT': '\x1b[D',
    'KEY_RIGHT': '\x1b[C',
    'KEY_ENTER': '\n',
    'KEY_BACKSPACE': '\x7f',
    'KEY_DELETE': '\x08',
    'KEY_DC': '\x1b[3~',
    'KEY_HOME': '\x1b[H',
    'KEY_END': '\x1b[F',
    'KEY_BTAB': '\x1b[Z',
    'KEY_TAB': '\t',
}


def make_key(value: str) -> MockKeystroke:
    """Create a MockKeystroke from a string value or key name."""
    # Check if it's a named key
    if value.startswith('KEY_'):
        return MockKeystroke(
            _KEY_SEQUENCES.get(value, ''),
            is_sequence=True,
            name=value,
        )
    # Single printable char
    return MockKeystroke(value, is_sequence=False, name=None)


class _ContextManagerStr:
    """A string that also acts as a context manager (for terminal attributes)."""
    def __init__(self, value: str = ''):
        self._value = value

    def __str__(self):
        return self._value

    def __add__(self, other):
        return str(self._value) + str(other)

    def __radd__(self, other):
        return str(other) + str(self._value)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class MockTerminal:
    """
    A fake terminal for headless testing.
    Implements enough of the blessed.Terminal interface for Renderer and Shell.
    """

    def __init__(self, width: int = 80, height: int = 24):
        self._width = width
        self._height = height
        self._key_queue = []
        self.buffer = []  # list of (row, col, text) tuples
        self._grid = {}   # (row, col) -> char

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def move(self, row: int, col: int) -> str:
        """Return a positioning sequence (stored as marker for buffer)."""
        return f'\x1b[{row};{col}H'

    @property
    def reverse(self) -> _ContextManagerStr:
        return _ContextManagerStr('\x1b[7m')

    @property
    def normal(self) -> str:
        return '\x1b[0m'

    @property
    def bold(self) -> str:
        return '\x1b[1m'

    @property
    def underline(self) -> str:
        return '\x1b[4m'

    @property
    def clear(self) -> str:
        return '\x1b[2J\x1b[H'

    @contextlib.contextmanager
    def fullscreen(self):
        yield

    @contextlib.contextmanager
    def cbreak(self):
        yield

    @contextlib.contextmanager
    def hidden_cursor(self):
        yield

    def inkey(self, timeout=None):
        """Return the next key from the queue, or empty MockKeystroke if queue is empty."""
        if self._key_queue:
            return self._key_queue.pop(0)
        return MockKeystroke('', is_sequence=False)

    def feed_keys(self, keys: list) -> None:
        """Add keys to the input queue. Keys can be strings or MockKeystroke objects."""
        for key in keys:
            if isinstance(key, str):
                self._key_queue.append(make_key(key))
            else:
                self._key_queue.append(key)

    def get_buffer_text(self) -> str:
        """Return all captured output as a single string."""
        return ''.join(self.buffer)

    def get_rendered_lines(self) -> list:
        """
        Parse the buffer to reconstruct a 2D grid of characters.
        Returns list of strings, one per row.
        """
        import re
        output = ''.join(self.buffer)

        # Parse ANSI escape sequences to build a character grid
        grid = {}
        row, col = 0, 0

        i = 0
        while i < len(output):
            if output[i] == '\x1b' and i + 1 < len(output):
                # ANSI escape sequence
                if output[i+1] == '[':
                    # CSI sequence
                    j = i + 2
                    while j < len(output) and output[j] not in 'ABCDHJKmsu~':
                        j += 1
                    seq = output[i+2:j]
                    terminator = output[j] if j < len(output) else ''

                    if terminator == 'H':
                        # Cursor position: ESC[row;colH
                        parts = seq.split(';')
                        try:
                            row = int(parts[0]) if parts[0] else 0
                            col = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                        except ValueError:
                            pass
                    elif terminator == 'J':
                        # Clear screen
                        if seq == '2':
                            grid.clear()
                            row, col = 0, 0
                    # Other sequences (colors, etc.) are ignored for text content

                    i = j + 1
                else:
                    i += 1
            elif output[i] == '\n':
                row += 1
                col = 0
                i += 1
            elif output[i] == '\r':
                col = 0
                i += 1
            else:
                grid[(row, col)] = output[i]
                col += 1
                i += 1

        if not grid:
            return []

        max_row = max(r for r, c in grid)
        lines = []
        for r in range(max_row + 1):
            if any(k[0] == r for k in grid):
                max_col = max(c for rr, c in grid if rr == r)
                line = ''
                for c in range(max_col + 1):
                    line += grid.get((r, c), ' ')
                lines.append(line)
            else:
                lines.append('')

        return lines

    def reset(self) -> None:
        """Clear the buffer and key queue."""
        self.buffer = []
        self._key_queue = []
        self._grid = {}

    def __add__(self, other):
        """Allow string concatenation with terminal attributes."""
        return str(other)
