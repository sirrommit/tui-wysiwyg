# Python CLI library.

This project is a python library to create customized and rich text based user interfaces. At it's heart it is a markdown style language for building TUI layouts. A specifically formatted string is fed to the library to create the "shell" (or structure) of a TUI page. Each TUI shell is has names listed as $NAME$ in well defined regions. The TUI shell can be fed a "method of interaction" for each $NAME$ to define how users interact with that region of the user interface. The method of interaction for each $NAME$ section can come from a list of several prebuilt functions, or an externally defined function.


- An example of what a shell defintion looks like is given in example.shell
- The shell definition breaks the screen into a grid. Grid widths are specified in percentages of the terminal in the example, but can also be defined by number of characters.
- ==== creates a double horizontal line
- ---- creates a single horizontal line
- | creates a single vertical line
- # creates a double vertical line
- __Text__ Creates underlined text (if the terminal supports it)
- 12R specifies how many rows a particular block should be. (This can also be defined in percentages)
- {   } defines the edges of a column, but the { and } characters are not shown in the TUI shell unless they are escaped.
- $name$ names the region of the TUI shell so that it can be referenced by other sections of the program.
- {  } {  } would create two columns separated by a space.

## Shell API

The main entry points on a `Shell` object:

- `shell.assign(name, interaction)` — attach an interaction to a named region
- `shell.run()` — start the event loop; blocks until the user exits; returns the selected value or `None`
- `shell.run_modal(row, col, width, height, parent_shell=None)` — run this shell as a popup overlay at a fixed position on top of an already-running parent shell (see below)
- `shell.get(name)` — read the current value of a region
- `shell.update(name, value)` — programmatically set a region's value
- `shell.on_change(name, callback)` — register a callback for value changes
- `shell.bind(source, target, transform=None)` — wire one region's value to another

## Modal Dialogs

A modal dialog is a second `Shell` rendered as a popup overlay on top of a running parent shell. Use `Shell.run_modal()` instead of `Shell.run()` when the parent shell is already active (e.g., from inside a `MenuFunction` callback).

```python
CONFIRM_POPUP = """\
|================|
|{2R $msg$       }|
|----------------|
|{2R $choice$    }|
|================|
"""

def my_action(sh):
    term = sh.terminal
    tw, th = term.width or 80, term.height or 24
    popup = Shell(CONFIRM_POPUP, _terminal=term)
    popup.assign("msg",    ListView(["Are you sure?", ""], bullet=" "))   # 2 rows
    popup.assign("choice", MenuReturn({"Yes": True, "No": False}))        # 2 rows
    # height=7 auto-detected from the 2R declarations; row/col auto-center.
    # width must be explicit because $msg$ and $choice$ are fill panels.
    confirmed = popup.run_modal(width=30, parent_shell=sh)  # restores parent on close
    if confirmed:
        sh.update("status", ["Done!"])
```

Key points:
- Pass the same `_terminal` instance to both parent and popup Shells.
- Call `run_modal()` from inside a `MenuFunction` callback while `Shell.run()` is active.
- `parent_shell=sh` causes the parent display to be fully restored when the popup closes.
- Escape and Ctrl+Q both dismiss the popup and return `None`.

## Methods of Interaction

- menu-function
  - given a dictionary of key:function pairs, lists the keys and allows the user to select a key. Calls the function associated with that key on selection.
  - Selection is reverse highlight for the active line if supported, but falls back to #Line# if reverse highlighting is not supported by the terminal
- menu-return
  - given a dictionary of key:value pairs, lists the keys and allows the user to select a key. Returns the value on key selection.
  - Selection is reverse highlight for the active line if supported, but falls back to #Line# if reverse highlighting is not supported by the terminal
- menu-hybrid
  - given a dictionary of key:[value or function] pairs, lists the keys and returns the value or calls the function on selection.
  - Selection is reverse highlight for the active line if supported, but falls back to #Line# if reverse highlighting is not supported by the terminal
- textbox
  - Gives an open text entry box that fills the space allotted.
  - Optionally uses wrap-on-word, wrap-anywhere, or extend-beyond-line-length
  - If more text is given than fits in the space, scrolling is enabled
- list
  - Given a list of strings, shows a bulleted list or numbered list with those strings.
  - bullets default to "* string", but given any character #, it will show "# string" instead.
  - number options are numeric "1. string", capital "A. string", lowercase "a. string", or roman-cap "I string" or roman-lower "i string"
- sublist
  - Same as list, but if an list item is a list, it shows an indented sublist for that list item.
  - sublists can nest so that you have a list with a sublist with a subsublist....
- checkbox
  - given a dictionary of key:value pairs, displays "[ ] key" or "[X] key" depending on if the value is True or False. Selecting a line will toggle the value abck and forth.
  - optionally can be set to selection mode where only one can be selected. In selection mode the [ ] becomes ( ) to distinguish. If you select an option when one is already selected, the previous selection will automatically be unselected.
- function
  - The Calls a provided function to determine how the user interacts with that panel.
