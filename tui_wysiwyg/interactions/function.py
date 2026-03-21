from .base import Interaction


class Function(Interaction):
    """Custom interaction that delegates to a user-provided function."""

    def __init__(self, handler):
        """
        handler: Callable[[Shell, Region, key | None], None]
        Called with key=None on initial render, with key on each keypress.
        """
        self._handler = handler
        self._value = None
        self._region = None
        self._shell = None

    def render(self, region, term, focused: bool = False) -> None:
        self._region = region
        self._handler(self._shell, region, None)

    def handle_key(self, key) -> tuple:
        self._handler(self._shell, self._region, key)
        return False, self.get_value()

    def get_value(self):
        return self._value

    def set_value(self, value) -> None:
        self._value = value
