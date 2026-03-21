class EventLoop:
    def __init__(self, term):
        self._term = term

    def next_key(self, timeout=0.1):
        """Read the next keypress with a timeout. Returns None if no key pressed."""
        key = self._term.inkey(timeout=timeout)
        if not key:
            return None
        return key
