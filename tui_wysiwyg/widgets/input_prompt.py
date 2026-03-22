"""Input Prompt widget — ask the user to type a single line of text.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{2R $prompt$          }|
    |----------------------|
    |{2R $entry$           }|
    |----------------------|
    |{1R $buttons$         }|
    |======================|

Height is always auto-detected from the explicit row declarations:
**9 rows** (1 title + 2 prompt + 1 divider + 2 entry + 1 divider + 1 buttons + 1 border).

Usage
-----

    from tui_wysiwyg.widgets.input_prompt import InputPrompt

    def rename_item(sh):
        new_name = InputPrompt(
            title="Rename",
            prompt_lines=["Enter a new name for the item:"],
            initial="old name",
        ).show(parent_shell=sh)
        if new_name is not None:
            ...
"""

from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import ListView, TextBox
from tui_wysiwyg.widgets._utils import _SubmittingMenu


def _shell_def(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{2R $prompt$            }|\n"
        "|------------------------|\n"
        "|{2R $entry$             }|\n"
        "|------------------------|\n"
        "|{1R $buttons$           }|\n"
        "|========================|\n"
    )


class InputPrompt:
    """Ask the user to enter a single line of text.

    Parameters
    ----------
    title : str
        Text displayed in the popup border (rendered bold).
    prompt_lines : list[str]
        Lines of descriptive text shown above the entry box (2 rows visible).
    initial : str
        Pre-filled text in the entry box.
    width : int
        Width of the popup in characters (including border walls).
        Height is always auto-detected from the row declarations.

    Returns
    -------
    The typed text string on OK, ``None`` on Cancel / Escape / Ctrl+Q.
    """

    def __init__(
        self,
        title: str = "Input",
        prompt_lines: list = None,
        initial: str = "",
        width: int = 50,
    ):
        self.title = title
        self.prompt_lines = list(prompt_lines) if prompt_lines is not None else []
        self.initial = initial
        self.width = width

    def show(self, parent_shell=None, **run_modal_kwargs):
        """Display the input popup and block until the user submits or cancels.

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
        The typed string on OK, ``None`` on Cancel / Escape / Ctrl+Q.

        Notes
        -----
        Focus opens on the entry box.  Tab moves focus to the buttons.
        Enter inside the entry box inserts a newline (extend mode); to
        submit, Tab to OK and press Enter, or use the mouse (if supported).
        """
        term = parent_shell.terminal if parent_shell is not None else None
        popup = Shell(_shell_def(self.title), _terminal=term)
        popup.assign("prompt",  ListView(self.prompt_lines, bullet=" "))
        popup.assign("entry",   TextBox(initial=self.initial, wrap="extend"))
        popup.assign("buttons", _SubmittingMenu("entry"))
        return popup.run_modal(
            width=self.width,
            parent_shell=parent_shell,
            **run_modal_kwargs,
        )
