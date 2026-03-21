from abc import ABC, abstractmethod


class Interaction(ABC):
    _shell = None  # Set by Shell.assign()

    @property
    def is_focusable(self) -> bool:
        """Return True if this interaction can meaningfully receive keyboard focus.
        Display-only interactions (ListView, SubList) override this to return False."""
        return True

    @abstractmethod
    def render(self, region, term, focused: bool = False) -> None:
        """Render the interaction into the given region using the terminal."""
        ...

    @abstractmethod
    def handle_key(self, key) -> tuple:
        """
        Handle a keypress.
        Returns (value_changed, new_value).
        new_value is whatever Shell.get returns.
        """
        ...

    @abstractmethod
    def get_value(self):
        """Return the current value of this interaction."""
        ...

    @abstractmethod
    def set_value(self, value) -> None:
        """Set the current value of this interaction."""
        ...

    def signal_return(self) -> tuple:
        """
        Called after handle_key to check if this interaction wants Shell.run() to return.
        Returns (should_exit, return_value).
        """
        return False, None
