"""Alert widget — an informational or warning popup with a single OK button.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{3R $message$         }|
    |----------------------|
    |{1R $ok$              }|
    |======================|

Height is always auto-detected from the explicit row declarations:
**7 rows** (1 title + 3 message + 1 divider + 1 ok + 1 bottom border).

Usage
-----

    from tui_wysiwyg.widgets.alert import Alert

    def warn_user(sh):
        Alert(
            title="Warning",
            message_lines=["No internet connection.", "Check your settings."],
        ).show(parent_shell=sh)
"""

from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import ListView, MenuReturn


def _shell_def(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{3R $message$           }|\n"
        "|------------------------|\n"
        "|{1R $ok$                }|\n"
        "|========================|\n"
    )


class Alert:
    """Informational or warning popup with a single OK button.

    Parameters
    ----------
    title : str
        Text displayed in the popup border (rendered bold).
    message_lines : list[str]
        Lines of text shown in the message area (3 rows visible).
    width : int
        Width of the popup in characters (including border walls).
        Height is always auto-detected from the row declarations.

    Returns
    -------
    ``True`` when OK is pressed, ``None`` on Escape / Ctrl+Q.
    """

    def __init__(
        self,
        title: str = "Alert",
        message_lines: list = None,
        width: int = 40,
    ):
        self.title = title
        self.message_lines = list(message_lines) if message_lines is not None else []
        self.width = width

    def show(self, parent_shell=None, **run_modal_kwargs):
        """Display the popup and block until the user dismisses it.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is fully restored when the popup
            closes.  Pass the ``sh`` argument received inside a
            ``MenuFunction`` callback.
        **run_modal_kwargs
            Forwarded to ``Shell.run_modal()``.  Use ``row``/``col`` to
            override auto-centering.

        Returns
        -------
        ``True`` on OK, ``None`` on Escape / Ctrl+Q.
        """
        term = parent_shell.terminal if parent_shell is not None else None
        popup = Shell(_shell_def(self.title), _terminal=term)
        popup.assign("message", ListView(self.message_lines, bullet=" "))
        popup.assign("ok", MenuReturn({"OK": True}))
        return popup.run_modal(
            width=self.width,
            parent_shell=parent_shell,
            **run_modal_kwargs,
        )
