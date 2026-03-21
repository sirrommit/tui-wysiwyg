from .base import Interaction


def _to_roman(n: int, upper: bool = True) -> str:
    """Convert integer to Roman numeral."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    result = ''
    for i in range(len(val)):
        while n >= val[i]:
            result += syms[i]
            n -= val[i]
    if not upper:
        result = result.lower()
    return result


def _get_bullet(bullet: str, index: int) -> str:
    """Get the bullet/prefix for an item at the given index (0-based)."""
    if bullet in ('*', '-', '•'):
        return bullet
    elif bullet == '1':
        return str(index + 1) + '.'
    elif bullet == 'A':
        return chr(ord('A') + index) + '.'
    elif bullet == 'a':
        return chr(ord('a') + index) + '.'
    elif bullet == 'I':
        return _to_roman(index + 1, upper=True) + '.'
    elif bullet == 'i':
        return _to_roman(index + 1, upper=False) + '.'
    return bullet


class ListView(Interaction):
    """Display-only list of items with optional bullet styles."""

    is_focusable = False

    def __init__(self, items: list, bullet: str = '*'):
        self._items = list(items)
        self._bullet = bullet

    def render(self, region, term, focused: bool = False) -> None:
        for i, item in enumerate(self._items):
            row = region.row + i
            if row >= region.row + region.height:
                break
            bullet = _get_bullet(self._bullet, i)
            line = f'{bullet} {item}'
            display = line[:region.width].ljust(region.width)
            print(term.move(row, region.col) + display, end='', flush=False)

        # Clear remaining lines
        for i in range(len(self._items), region.height):
            row = region.row + i
            print(term.move(row, region.col) + ' ' * region.width, end='', flush=False)

    def handle_key(self, key) -> tuple:
        # Display only, no key handling
        return False, self.get_value()

    def get_value(self) -> list:
        return list(self._items)

    def set_value(self, value) -> None:
        self._items = list(value)


class SubList(Interaction):
    """Display-only list with support for nested sublists."""

    is_focusable = False

    def __init__(self, items: list, bullet: str = '*'):
        self._items = items
        self._bullet = bullet

    def _render_items(self, items: list, region, term, start_row: int, indent: int, max_row: int) -> int:
        """Recursively render items. Returns the next row to render to."""
        row = start_row
        i = 0
        for item in items:
            if row >= max_row:
                break
            if isinstance(item, list):
                row = self._render_items(item, region, term, row, indent + 2, max_row)
            else:
                bullet = _get_bullet(self._bullet, i)
                prefix = ' ' * indent
                line = f'{prefix}{bullet} {item}'
                display = line[:region.width].ljust(region.width)
                print(term.move(row, region.col) + display, end='', flush=False)
                row += 1
                i += 1
        return row

    def render(self, region, term, focused: bool = False) -> None:
        max_row = region.row + region.height
        next_row = self._render_items(self._items, region, term, region.row, 0, max_row)

        # Clear remaining lines
        for row in range(next_row, max_row):
            print(term.move(row, region.col) + ' ' * region.width, end='', flush=False)

    def handle_key(self, key) -> tuple:
        return False, self.get_value()

    def get_value(self) -> list:
        return self._items

    def set_value(self, value) -> None:
        self._items = value
