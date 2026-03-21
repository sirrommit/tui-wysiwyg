class ShellSyntaxError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line  # 1-based line number or None
        super().__init__(f"line {line}: {message}" if line else message)


class RegionNotFoundError(Exception):
    pass


class CircularUpdateError(Exception):
    pass
