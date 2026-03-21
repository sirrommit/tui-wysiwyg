from .exceptions import CircularUpdateError


class ChangeHandle:
    def __init__(self, observer, name, callback_id):
        self._observer = observer
        self._name = name
        self._callback_id = callback_id

    def remove(self) -> None:
        self._observer._remove(self._name, self._callback_id)


class Observer:
    def __init__(self):
        self._callbacks = {}  # name -> dict of {id: callback}
        self._next_id = 0

    def register(self, name: str, callback) -> ChangeHandle:
        if name not in self._callbacks:
            self._callbacks[name] = {}
        cb_id = self._next_id
        self._next_id += 1
        self._callbacks[name][cb_id] = callback
        return ChangeHandle(self, name, cb_id)

    def _remove(self, name: str, callback_id: int) -> None:
        if name in self._callbacks and callback_id in self._callbacks[name]:
            del self._callbacks[name][callback_id]

    def notify(self, name: str, value, updating: set | None = None) -> None:
        """
        Notify all callbacks registered on name.
        updating is the set of currently-updating region names for cycle detection.
        Raises CircularUpdateError if name is already in updating.
        """
        if updating is None:
            updating = set()

        if name in updating:
            raise CircularUpdateError(
                f"circular update detected involving '{name}'"
            )

        updating = updating | {name}

        callbacks = self._callbacks.get(name, {})
        for cb_id, callback in list(callbacks.items()):
            callback(value, updating)
