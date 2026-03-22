"""Internal utilities shared across widget modules.  Not part of the public API."""

from tui_wysiwyg.interactions.menu import MenuFunction


class _SubmittingMenu(MenuFunction):
    """A MenuFunction with OK / Cancel that signals run_modal() to exit.

    On OK, reads ``shell.get(value_region)`` and signals exit with that value.
    On Cancel, signals exit with ``None``.

    Parameters
    ----------
    value_region : str
        The region name whose value OK should capture and return.
    ok_label : str
        Label for the submit button (default ``"OK"``).
    cancel_label : str
        Label for the cancel button (default ``"Cancel"``).
    """

    def __init__(
        self,
        value_region: str,
        ok_label: str = "OK",
        cancel_label: str = "Cancel",
    ):
        self._value_region = value_region
        self._submitted = False
        self._result = None
        super().__init__({
            ok_label: self._handle_ok,
            cancel_label: self._handle_cancel,
        })

    def _handle_ok(self, sh):
        self._result = sh.get(self._value_region)
        self._submitted = True

    def _handle_cancel(self, sh):
        self._result = None
        self._submitted = True

    def signal_return(self) -> tuple:
        if self._submitted:
            return True, self._result
        return False, None
