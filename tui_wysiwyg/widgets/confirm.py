"""Confirm widget — a centered confirmation popup with caller-supplied buttons.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{2R $message$         }|
    |----------------------|
    |{2R $buttons$         }|
    |======================|

The title is injected at construction time.  Height is always auto-detected
from the explicit ``2R`` declarations (7 rows total: 1+2+1+2+1).

Usage
-----

    from tui_wysiwyg.widgets.confirm import Confirm

    def delete_item(sh):
        result = Confirm(
            title="Delete item?",
            message_lines=["This cannot be undone.", ""],
            buttons={"Yes": True, "No": False},
        ).show(parent_shell=sh)
        if result:
            ...
"""

from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import ListView, MenuReturn


def _shell_def(title: str) -> str:
    # Braces in the region rows are literal shell syntax (not f-string placeholders),
    # so they are written as plain strings and concatenated with the formatted title.
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{2R $message$           }|\n"
        "|------------------------|\n"
        "|{2R $buttons$           }|\n"
        "|========================|\n"
    )


class Confirm:
    """Centered confirmation popup with a message area and caller-supplied buttons.

    Parameters
    ----------
    title : str
        Text displayed in the popup border (rendered bold).
    message_lines : list[str]
        Lines of text shown in the message area (2 rows visible).
    buttons : dict
        Mapping of button label → return value.
        Default: ``{"OK": True, "Cancel": False}``.
    width : int
        Width of the popup in characters (including border walls).
        Height is always auto-detected from the ``2R`` declarations.

    Returns
    -------
    The value associated with the chosen button label, or ``None`` on
    Escape / Ctrl+Q.
    """

    def __init__(
        self,
        title: str = "Confirm",
        message_lines: list = None,
        buttons: dict = None,
        width: int = 40,
    ):
        self.title = title
        self.message_lines = list(message_lines) if message_lines is not None else []
        self.buttons = dict(buttons) if buttons is not None else {"OK": True, "Cancel": False}
        self.width = width

    def show(self, parent_shell=None, **run_modal_kwargs):
        """Display the popup and block until the user makes a choice.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is fully restored when the popup
            closes (erasing any ghost).  Pass the ``sh`` argument received
            inside a ``MenuFunction`` callback.
        **run_modal_kwargs
            Forwarded to ``Shell.run_modal()``.  Useful for overriding
            ``row`` / ``col`` to position the popup at a specific location
            instead of the default centered position.

        Returns
        -------
        The selected button value, or ``None`` on Escape / Ctrl+Q.
        """
        term = parent_shell.terminal if parent_shell is not None else None
        popup = Shell(_shell_def(self.title), _terminal=term)
        popup.assign("message", ListView(self.message_lines, bullet=" "))
        popup.assign("buttons", MenuReturn(self.buttons))
        return popup.run_modal(
            width=self.width,
            parent_shell=parent_shell,
            **run_modal_kwargs,
        )
