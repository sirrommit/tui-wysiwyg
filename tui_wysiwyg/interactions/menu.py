from .base import Interaction


class MenuFunction(Interaction):
    """Menu where each item calls a function when selected."""

    def __init__(self, items: dict):
        """
        items: dict[str, Callable[[Shell], None]]
        """
        self._items = items
        self._labels = list(items.keys())
        self._active_index = 0
        self._last_activated = None
        self._shell = None

    def render(self, region, term, focused: bool = False) -> None:
        for i, label in enumerate(self._labels):
            row = region.row + i
            if row >= region.row + region.height:
                break
            col = region.col

            line = label[:region.width].ljust(region.width)

            if i == self._active_index and focused:
                try:
                    text = term.reverse + line + term.normal
                except Exception:
                    text = f'> {label}'[:region.width].ljust(region.width)
            elif i == self._active_index:
                text = f'> {label}'[:region.width].ljust(region.width)
            else:
                text = line

            print(term.move(row, col) + text, end='', flush=False)

        # Clear remaining lines
        for i in range(len(self._labels), region.height):
            row = region.row + i
            print(term.move(row, region.col) + ' ' * region.width, end='', flush=False)

    def handle_key(self, key) -> tuple:
        if key.is_sequence:
            name = key.name
            if name in ('KEY_UP', 'KEY_SUP') or str(key) == 'k':
                self._active_index = max(0, self._active_index - 1)
                return True, self.get_value()
            elif name in ('KEY_DOWN', 'KEY_SDOWN') or str(key) == 'j':
                self._active_index = min(len(self._labels) - 1, self._active_index + 1)
                return True, self.get_value()
            elif name == 'KEY_ENTER':
                return self._activate()
        elif str(key) == 'k':
            self._active_index = max(0, self._active_index - 1)
            return True, self.get_value()
        elif str(key) == 'j':
            self._active_index = min(len(self._labels) - 1, self._active_index + 1)
            return True, self.get_value()
        elif str(key) == '\n' or str(key) == '\r':
            return self._activate()
        return False, self.get_value()

    def _activate(self):
        if self._labels:
            label = self._labels[self._active_index]
            self._last_activated = label
            callback = self._items[label]
            if self._shell is not None:
                callback(self._shell)
            else:
                callback(None)
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self):
        return self._last_activated

    def set_value(self, value) -> None:
        if value is not None and value in self._labels:
            self._active_index = self._labels.index(value)
        self._last_activated = value


class MenuReturn(Interaction):
    """Menu where each item returns a value when selected."""

    def __init__(self, items: dict):
        """
        items: dict[str, Any]
        """
        self._items = items
        self._labels = list(items.keys())
        self._active_index = 0
        self._wants_exit = False
        self._exit_value = None

    def render(self, region, term, focused: bool = False) -> None:
        for i, label in enumerate(self._labels):
            row = region.row + i
            if row >= region.row + region.height:
                break
            col = region.col

            line = label[:region.width].ljust(region.width)

            if i == self._active_index and focused:
                try:
                    text = term.reverse + line + term.normal
                except Exception:
                    text = f'> {label}'[:region.width].ljust(region.width)
            elif i == self._active_index:
                text = f'> {label}'[:region.width].ljust(region.width)
            else:
                text = line

            print(term.move(row, col) + text, end='', flush=False)

        # Clear remaining lines
        for i in range(len(self._labels), region.height):
            row = region.row + i
            print(term.move(row, region.col) + ' ' * region.width, end='', flush=False)

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        if key.is_sequence:
            name = key.name
            if name in ('KEY_UP',):
                self._active_index = max(0, self._active_index - 1)
                return True, self.get_value()
            elif name in ('KEY_DOWN',):
                self._active_index = min(len(self._labels) - 1, self._active_index + 1)
                return True, self.get_value()
            elif name == 'KEY_ENTER':
                return self._select()
        elif str(key) == 'k':
            self._active_index = max(0, self._active_index - 1)
            return True, self.get_value()
        elif str(key) == 'j':
            self._active_index = min(len(self._labels) - 1, self._active_index + 1)
            return True, self.get_value()
        elif str(key) == '\n' or str(key) == '\r':
            return self._select()
        return False, self.get_value()

    def _select(self):
        if self._labels:
            label = self._labels[self._active_index]
            self._exit_value = self._items[label]
            self._wants_exit = True
            return True, self.get_value()
        return False, self.get_value()

    def get_value(self):
        if self._labels:
            return self._labels[self._active_index]
        return None

    def set_value(self, value) -> None:
        if value in self._labels:
            self._active_index = self._labels.index(value)

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None


class MenuHybrid(Interaction):
    """Menu where items can be callables or return values."""

    def __init__(self, items: dict):
        """
        items: dict[str, Callable | Any]
        """
        self._items = items
        self._labels = list(items.keys())
        self._active_index = 0
        self._wants_exit = False
        self._exit_value = None
        self._last_activated = None
        self._shell = None

    def render(self, region, term, focused: bool = False) -> None:
        for i, label in enumerate(self._labels):
            row = region.row + i
            if row >= region.row + region.height:
                break
            col = region.col

            line = label[:region.width].ljust(region.width)

            if i == self._active_index and focused:
                try:
                    text = term.reverse + line + term.normal
                except Exception:
                    text = f'> {label}'[:region.width].ljust(region.width)
            elif i == self._active_index:
                text = f'> {label}'[:region.width].ljust(region.width)
            else:
                text = line

            print(term.move(row, col) + text, end='', flush=False)

        # Clear remaining lines
        for i in range(len(self._labels), region.height):
            row = region.row + i
            print(term.move(row, region.col) + ' ' * region.width, end='', flush=False)

    def handle_key(self, key) -> tuple:
        self._wants_exit = False
        if key.is_sequence:
            name = key.name
            if name in ('KEY_UP',):
                self._active_index = max(0, self._active_index - 1)
                return True, self.get_value()
            elif name in ('KEY_DOWN',):
                self._active_index = min(len(self._labels) - 1, self._active_index + 1)
                return True, self.get_value()
            elif name == 'KEY_ENTER':
                return self._activate()
        elif str(key) == 'k':
            self._active_index = max(0, self._active_index - 1)
            return True, self.get_value()
        elif str(key) == 'j':
            self._active_index = min(len(self._labels) - 1, self._active_index + 1)
            return True, self.get_value()
        elif str(key) == '\n' or str(key) == '\r':
            return self._activate()
        return False, self.get_value()

    def _activate(self):
        if not self._labels:
            return False, self.get_value()
        label = self._labels[self._active_index]
        value = self._items[label]
        self._last_activated = label
        if callable(value):
            if self._shell is not None:
                value(self._shell)
            else:
                value(None)
            return True, self.get_value()
        else:
            self._exit_value = value
            self._wants_exit = True
            return True, self.get_value()

    def get_value(self):
        return self._last_activated

    def set_value(self, value) -> None:
        if value in self._labels:
            self._active_index = self._labels.index(value)
        self._last_activated = value

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._exit_value
        return False, None
