"""List Select widget — pick one item (single) or many items (multi) from a list.

Shell layout — single mode (no buttons row; exits immediately on selection)
---------------------------------------------------------------------------

    |=== <bold>Title</> ===|
    |{2R  $prompt$         }|
    |----------------------|
    |{10R $items$          }|
    |======================|

Shell layout — multi mode (CheckBox + OK/Cancel buttons)
---------------------------------------------------------

    |=== <bold>Title</> ===|
    |{2R  $prompt$         }|
    |----------------------|
    |{10R $items$          }|
    |----------------------|
    |{1R  $buttons$        }|
    |======================|

Usage
-----

    from tui_wysiwyg.widgets.list_select import ListSelect

    # Single mode — returns the selected value immediately
    choice = ListSelect(
        title="Pick a colour",
        items=["Red", "Green", "Blue"],
    ).show(parent_shell=sh)

    # Multi mode — returns {label: bool} on OK
    selections = ListSelect(
        title="Pick toppings",
        items={"Cheese": True, "Tomato": False, "Basil": False},
        multi=True,
    ).show(parent_shell=sh)
"""

from tui_wysiwyg import Shell
from tui_wysiwyg.interactions import ListView, MenuReturn, CheckBox
from tui_wysiwyg.widgets._utils import _SubmittingMenu


def _single_shell(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{2R  $prompt$           }|\n"
        "|------------------------|\n"
        "|{10R $items$            }|\n"
        "|========================|\n"
    )


def _multi_shell(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{2R  $prompt$           }|\n"
        "|------------------------|\n"
        "|{10R $items$            }|\n"
        "|------------------------|\n"
        "|{1R  $buttons$          }|\n"
        "|========================|\n"
    )


def _to_menu_return(items) -> dict:
    """Convert a list or dict into a MenuReturn-compatible dict."""
    if isinstance(items, dict):
        return dict(items)
    return {str(item): item for item in items}


def _to_checkbox(items) -> dict:
    """Convert a list or dict into a CheckBox-compatible {label: bool} dict."""
    if isinstance(items, dict):
        return {str(k): bool(v) for k, v in items.items()}
    return {str(item): False for item in items}


class ListSelect:
    """Pick one item (single mode) or many items (multi mode) from a scrollable list.

    Parameters
    ----------
    title : str
        Text displayed in the popup border (rendered bold).
    prompt_lines : list[str]
        Descriptive text shown above the list (2 rows visible).
    items : list[str] | dict
        The items to display.

        - **Single mode** — a ``list`` maps each label to itself; a ``dict``
          maps each label to an arbitrary return value.
        - **Multi mode** — a ``list`` initialises all checkboxes unchecked;
          a ``dict[str, bool]`` sets initial checked states.
    multi : bool
        If ``False`` (default), single-selection mode: selecting an item
        immediately returns its value.  If ``True``, multi-selection mode:
        checkboxes are shown and an OK/Cancel button row appears.
    width : int
        Width of the popup in characters (including border walls).
        Height is auto-detected: 14 rows (single) or 16 rows (multi).

    Returns
    -------
    - **Single mode:** the value mapped to the selected label.  For a list,
      this is the label string itself; for a dict, it is the dict value.
    - **Multi mode:** ``dict[str, bool]`` of all items and their checked
      states on OK, ``None`` on Cancel / Escape / Ctrl+Q.
    """

    def __init__(
        self,
        title: str = "Select",
        prompt_lines: list = None,
        items=None,
        multi: bool = False,
        width: int = 40,
    ):
        self.title = title
        self.prompt_lines = list(prompt_lines) if prompt_lines is not None else []
        self.items = items if items is not None else []
        self.multi = multi
        self.width = width

    def show(self, parent_shell=None, **run_modal_kwargs):
        """Display the list popup and block until the user makes a selection.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is restored when the popup
            closes.  Pass the ``sh`` argument from a ``MenuFunction`` callback.
        **run_modal_kwargs
            Forwarded to ``Shell.run_modal()``.  Use ``row``/``col`` to
            override auto-centering.

        Returns
        -------
        Single mode: the selected item value, or ``None`` on Escape / Ctrl+Q.
        Multi mode: ``dict[str, bool]`` on OK, ``None`` on Cancel / Escape / Ctrl+Q.
        """
        term = parent_shell.terminal if parent_shell is not None else None

        if self.multi:
            popup = Shell(_multi_shell(self.title), _terminal=term)
            popup.assign("prompt",  ListView(self.prompt_lines, bullet=" "))
            popup.assign("items",   CheckBox(_to_checkbox(self.items), mode="multi"))
            popup.assign("buttons", _SubmittingMenu("items"))
        else:
            popup = Shell(_single_shell(self.title), _terminal=term)
            popup.assign("prompt", ListView(self.prompt_lines, bullet=" "))
            popup.assign("items",  MenuReturn(_to_menu_return(self.items)))

        return popup.run_modal(
            width=self.width,
            parent_shell=parent_shell,
            **run_modal_kwargs,
        )
