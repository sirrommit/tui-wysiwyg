#!/usr/bin/env python3
"""
tui-wysiwyg demo application.

Walks through seven separate shells, each showcasing different features:

  Shell 1  — Main Menu         (MenuReturn, ListView)
  Shell 2  — Catalog Browser   (MenuReturn, SubList, ListView, shell.bind)
  Shell 3  — Note Editor       (TextBox, CheckBox, shell.on_change)
  Shell 4  — Settings Form     (FormInput — all five field types)
  Shell 5  — Custom Widget     (Function, MenuFunction)
  Shell 6  — Style Demo        (style tags, C-style comments, Function rendering)
  Shell 7  — Modal Dialog      (Shell.run_modal() — popup overlay from MenuFunction)

Run with:
    python3 example.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import blessed
from tui_wysiwyg import Shell
from tui_wysiwyg.style import render_styled

# A single terminal instance is shared across all shells.
# Creating multiple blessed.Terminal objects for the same TTY causes state
# conflicts when switching between fullscreen contexts.
_TERM = blessed.Terminal()
from tui_wysiwyg.interactions import (
    MenuReturn,
    MenuFunction,
    MenuHybrid,
    TextBox,
    ListView,
    SubList,
    CheckBox,
    Function,
    FormInput,
)


# ---------------------------------------------------------------------------
# Shell 1 — Main Menu
# Uses: MenuReturn (navigation), ListView (static info panel)
#
# Note the style tags in the border title:
#   <bold;color=cyan>tui-wysiwyg Demo</>
# They render with color on capable terminals and degrade to plain text
# on terminals that don't support the attribute.
# ---------------------------------------------------------------------------

MAIN_LAYOUT = """\
|=100%========================= <bold;color=cyan>tui-wysiwyg Demo</> ==========================|
|{32%  __Demos__                         }|{  __About__                                   }|
|{16R  $menu$                            }|{16R  $about$                                  }|
|{                                        }|{                                              }|
|===========================================================================================|
|{100%  2R  $status$                                                                        }|
|===========================================================================================|
"""

ABOUT_TEXT = [
    "This demo walks through the",
    "interaction types and features",
    "built into tui-wysiwyg.",
    "",
    "Navigation:",
    "  Tab / Shift+Tab  switch focus",
    "  Arrow keys       move in menus",
    "  Enter            select",
    "  Ctrl+Q           quit / go back",
    "",
    "Each demo opens a new shell.",
    "Return here with Ctrl+Q.",
]

DEMO_CHOICES = {
    "1. Catalog Browser":  "catalog",
    "2. Note Editor":      "notes",
    "3. Settings Form":    "settings",
    "4. Custom Widget":    "custom",
    "5. Style Demo":       "styles",
    "6. Shell File Demo":  "shell_file",
    "7. Modal Dialog":     "modal",
    "8. Confirm Widget":   "confirm_widget",
    "9. Alert Widget":      "alert_widget",
    "10. Input Prompt":     "input_prompt",
    "11. List Select":      "list_select",
    "12. File Picker":      "file_picker",
    "13. Date Picker":      "date_picker",
    "14. Progress Bar":     "progress_bar",
    "15. Quit":             None,
}

STATUS_HINTS = {
    "catalog":    "MenuReturn + SubList + ListView + shell.bind()",
    "notes":      "TextBox + CheckBox + shell.on_change()",
    "settings":   "FormInput (str / int / float / bool / choices)",
    "custom":     "Function + MenuFunction",
    "styles":     "style tags, C-style comments, render_styled()",
    "shell_file": "layout loaded from example.shell at runtime",
    "modal":          "Shell.run_modal() — popup overlay from a MenuFunction callback",
    "confirm_widget": "widgets.Confirm — reusable confirmation popup",
    "alert_widget":  "widgets.Alert — informational / warning popup",
    "input_prompt":  "widgets.InputPrompt — single-line text entry popup",
    "list_select":   "widgets.ListSelect — pick one or many from a list",
    "file_picker":   "widgets.FilePicker — browse filesystem to select a file",
    "date_picker":   "widgets.DatePicker — monthly calendar date selection popup",
    "progress_bar":  "widgets.Progress — programmatic progress bar with optional Cancel",
    None:            "Bye!",
}


def run_main_menu() -> str | None:
    """Show the main navigation menu. Returns the selected demo key, or None to quit."""
    shell = Shell(MAIN_LAYOUT, _terminal=_TERM)
    menu = MenuReturn(DEMO_CHOICES)
    shell.assign("menu", menu)
    shell.assign("about", ListView(ABOUT_TEXT, bullet="-"))
    shell.assign("status", ListView(["Use \u2191 \u2193 to navigate, Enter to open a demo."]))

    # Update the status bar whenever the highlighted menu item changes.
    def on_menu_change(label):
        key = DEMO_CHOICES.get(label)
        hint = STATUS_HINTS.get(key, "")
        shell.update("status", [f"  {label}  \u2014  {hint}" if hint else f"  {label}"])

    shell.on_change("menu", on_menu_change)

    return shell.run()   # returns the value from DEMO_CHOICES


# ---------------------------------------------------------------------------
# Shell 2 — Catalog Browser
# Uses: MenuReturn (category picker), SubList (hierarchical contents),
#        ListView (detail panel), shell.bind() for wiring
# ---------------------------------------------------------------------------

CATALOG_LAYOUT = """\
|=100%================================ <bold>Catalog Browser</> ====================================|
|{28%  __Category__    }|{38%  __Contents__              }|{  __Details__                }|
|{16R  $category$      }|{16R  $contents$                }|{16R  $details$               }|
|{                     }|{                               }|{                             }|
|==========================================================================================|
|{100%  2R  $status$                                                                       }|
|==========================================================================================|
"""

CATALOG_DATA = {
    "Fruits": {
        "contents": [
            "Citrus",
            ["Orange", "Lemon", "Lime", "Grapefruit"],
            "Stone Fruit",
            ["Peach", "Plum", "Cherry", "Apricot"],
            "Berries",
            ["Strawberry", "Blueberry", "Raspberry"],
        ],
        "details": [
            "Fruits are the seed-bearing",
            "structures of flowering plants.",
            "",
            "Rich in vitamins, minerals,",
            "and natural sugars.",
            "",
            "Select a category to explore",
            "further.",
        ],
    },
    "Vegetables": {
        "contents": [
            "Root Vegetables",
            ["Carrot", "Parsnip", "Turnip", "Beet"],
            "Leafy Greens",
            ["Spinach", "Kale", "Lettuce", "Chard"],
            "Brassicas",
            ["Broccoli", "Cauliflower", "Cabbage"],
        ],
        "details": [
            "Vegetables are edible parts",
            "of plants consumed by humans.",
            "",
            "High in fiber, vitamins,",
            "and minerals.",
        ],
    },
    "Grains": {
        "contents": [
            "Cereals",
            ["Wheat", "Rice", "Corn", "Oats", "Barley"],
            "Pseudo-grains",
            ["Quinoa", "Amaranth", "Buckwheat"],
        ],
        "details": [
            "Grains are the seeds of",
            "grass-like plants (cereals).",
            "",
            "A dietary staple worldwide,",
            "providing carbohydrates",
            "and protein.",
        ],
    },
    "Legumes": {
        "contents": [
            "Beans",
            ["Black Bean", "Kidney Bean", "Navy Bean"],
            "Lentils",
            ["Red Lentil", "Green Lentil", "Black Lentil"],
            "Peas",
            ["Green Pea", "Chickpea", "Snow Pea"],
        ],
        "details": [
            "Legumes are the fruit or seed",
            "of plants in the Fabaceae",
            "family.",
            "",
            "Excellent source of protein",
            "and dietary fiber.",
        ],
    },
}


def run_catalog():
    """
    Catalog Browser demo.

    Demonstrates:
      - MenuReturn: select a category from the left panel
      - SubList:    hierarchical content list in the center
      - ListView:   detail text in the right panel
      - shell.bind: automatically update both panels when category changes
    """
    shell = Shell(CATALOG_LAYOUT, _terminal=_TERM)

    categories = list(CATALOG_DATA.keys())
    shell.assign("category", MenuReturn({c: c for c in categories}))

    first = categories[0]
    shell.assign("contents", SubList(CATALOG_DATA[first]["contents"]))
    shell.assign("details",  ListView(CATALOG_DATA[first]["details"], bullet="-"))
    shell.assign("status",   ListView(["  Select a category (left) to browse its contents."]))

    # Bind category selection → contents and details panels.
    shell.bind(
        "category", "contents",
        transform=lambda cat: CATALOG_DATA.get(cat, {}).get("contents", []),
    )
    shell.bind(
        "category", "details",
        transform=lambda cat: CATALOG_DATA.get(cat, {}).get("details", []),
    )

    def on_category_change(cat):
        shell.update("status", [f"  Category: {cat}  |  Tab to switch panels  |  Ctrl+Q to go back"])

    shell.on_change("category", on_category_change)

    shell.run()


# ---------------------------------------------------------------------------
# Shell 3 — Note Editor
# Uses: TextBox (main edit area), CheckBox (tag picker),
#        ListView (live summary panel), shell.on_change
# ---------------------------------------------------------------------------

NOTE_LAYOUT = """\
|=100%=================================== <bold>Note Editor</> ====================================|
|{60%  __Note__                          }|{  __Tags__                                   }|
|{18R  $note$                            }|{18R  $tags$                                  }|
|{                                        }|{                                            }|
|=========================================================================================|
|{100%  __Summary__                                                                       }|
|{4R    $summary$                                                                         }|
|=========================================================================================|
"""

AVAILABLE_TAGS = {
    "Work":      False,
    "Personal":  False,
    "Idea":      False,
    "Todo":      False,
    "Reference": False,
    "Urgent":    False,
}


def run_notes():
    """
    Note Editor demo.

    Demonstrates:
      - TextBox:       free-form text entry with word-wrap
      - CheckBox:      multi-select tag picker
      - ListView:      live summary panel (display only)
      - shell.on_change: update the summary whenever note or tags change
    """
    shell = Shell(NOTE_LAYOUT, _terminal=_TERM)

    note = TextBox(
        initial="Type your note here.\n\nUse arrow keys to move, Tab to switch to tags.",
        wrap="word",
    )
    tags = CheckBox(dict(AVAILABLE_TAGS), mode="multi")

    shell.assign("note",    note)
    shell.assign("tags",    tags)
    shell.assign("summary", ListView([], bullet="-"))

    def rebuild_summary(_=None):
        text = shell.get("note") or ""
        checked = [k for k, v in (shell.get("tags") or {}).items() if v]
        word_count = len(text.split())
        lines = [
            f"Words: {word_count}",
            f"Tags:  {', '.join(checked) if checked else '(none)'}",
            f"Chars: {len(text)}",
        ]
        shell.update("summary", lines)

    shell.on_change("note", rebuild_summary)
    shell.on_change("tags", rebuild_summary)
    rebuild_summary()   # populate on first render

    shell.run()


# ---------------------------------------------------------------------------
# Shell 4 — Settings Form
# Uses: FormInput with all five field types (str, int, float, bool, choices)
#        Results are shown in a second shell after submission.
# ---------------------------------------------------------------------------

FORM_LAYOUT = """\
|=100%================================= <bold>Settings Form</> =====================================|
|{100%  24R  $form$                                                                         }|
|===========================================================================================|
"""

RESULT_LAYOUT = """\
|=100%================================ <bold>Submission Result</> ==================================|
|{100%  __Your settings were saved:__                                                      }|
|{18R   $result$                                                                           }|
|{                                                                                         }|
|==========================================================================================|
|{100%  2R  $footer$                                                                       }|
|==========================================================================================|
"""


def run_settings():
    """
    Settings Form demo.

    Demonstrates:
      - FormInput with str, int, float, bool, and choices field types
      - Validators, required fields, placeholders, and defaults
      - Chaining to a second shell to display the submission result
    """
    shell = Shell(FORM_LAYOUT, _terminal=_TERM)
    shell.assign("form", FormInput({
        "username": {
            "type":        "str",
            "descriptor":  "Username",
            "required":    True,
            "placeholder": "e.g. alice",
            "validator":   lambda v: True if v.replace("_", "").isalnum()
                           else "Letters, digits, and underscores only",
        },
        "max_items": {
            "type":        "int",
            "descriptor":  "Max items",
            "default":     50,
            "validator":   lambda v: True if 1 <= v <= 1000 else "Must be between 1 and 1000",
        },
        "opacity": {
            "type":        "float",
            "descriptor":  "Opacity",
            "default":     1.0,
            "placeholder": "0.0 \u2013 1.0",
            "validator":   lambda v: True if 0.0 <= v <= 1.0 else "Must be between 0.0 and 1.0",
        },
        "dark_mode": {
            "type":        "bool",
            "descriptor":  "Dark mode",
            "default":     True,
        },
        "language": {
            "type":        "choices",
            "descriptor":  "Language",
            "options":     ["English", "Spanish", "French", "German", "Japanese"],
            "default":     "English",
        },
        "role": {
            "type":        "choices",
            "descriptor":  "Role",
            "options":     ["Admin", "Editor", "Viewer"],
            "default":     "Viewer",
        },
    }))

    result = shell.run()

    if result is None:
        return   # user pressed Ctrl+Q

    # Show results in a second shell
    result_lines = []
    for key, val in result.items():
        display_val = str(val) if val is not None else "(empty)"
        result_lines.append(f"{key:<12}  =  {display_val}")

    result_shell = Shell(RESULT_LAYOUT, _terminal=_TERM)
    result_shell.assign("result", ListView(result_lines, bullet=" "))
    result_shell.assign("footer", ListView(["  Press Ctrl+Q to go back to the main menu."]))
    result_shell.run()


# ---------------------------------------------------------------------------
# Shell 5 — Custom Widget
# Uses: MenuFunction (command palette), Function (custom canvas rendering)
# ---------------------------------------------------------------------------

CUSTOM_LAYOUT = """\
|=100%================================ <bold>Custom Widget Demo</> =================================|
|{30%  __Commands__               }|{  __Canvas__                                        }|
|{16R  $commands$                 }|{16R  $canvas$                                       }|
|{                                }|{                                                    }|
|=========================================================================================|
|{100%  2R  $hint$                                                                         }|
|=========================================================================================|
"""

# Shared mutable state for the Function canvas handler.
_canvas_state = {"pattern": "grid", "char": "#"}

PATTERNS = {
    "grid": lambda w, h: [
        "".join("#" if (c % 4 == 0 or r % 2 == 0) else " " for c in range(w))
        for r in range(h)
    ],
    "diagonal": lambda w, h: [
        "".join("\\" if c == r % w else " " for c in range(w))
        for r in range(h)
    ],
    "checkerboard": lambda w, h: [
        "".join("\u2588" if (r + c) % 2 == 0 else "\u2591" for c in range(w))
        for r in range(h)
    ],
    "border": lambda w, h: [
        ("+" + "-" * (w - 2) + "+") if r in (0, h - 1)
        else ("|" + " " * (w - 2) + "|")
        for r in range(h)
    ],
    "empty": lambda w, h: [" " * w for _ in range(h)],
}


def canvas_handler(shell, region, key):
    """
    Custom Function handler: draws the current pattern onto the canvas region.

    Called with key=None on initial render, and on each keypress while focused.
    """
    term = shell.terminal
    pattern_fn = PATTERNS.get(_canvas_state["pattern"], PATTERNS["empty"])
    lines = pattern_fn(region.width, region.height)

    for row_offset, line in enumerate(lines):
        r = region.row + row_offset
        if r >= region.row + region.height:
            break
        print(term.move(r, region.col) + line[:region.width], end="", flush=False)


def run_custom():
    """
    Custom Widget demo.

    Demonstrates:
      - MenuFunction: each menu item calls a function that mutates state
        and forces a re-render of the canvas
      - Function: a custom handler that draws directly to the terminal
        using blessed, with full control over the region's content
    """
    shell = Shell(CUSTOM_LAYOUT, _terminal=_TERM)

    def set_pattern(name):
        def handler(sh):
            _canvas_state["pattern"] = name
            sh.update("canvas", None)
            sh.update("hint",   [f"  Pattern: {name}  |  Use \u2191 \u2193 to choose, Enter to run"])
        return handler

    shell.assign("commands", MenuFunction({
        "Grid":         set_pattern("grid"),
        "Diagonal":     set_pattern("diagonal"),
        "Checkerboard": set_pattern("checkerboard"),
        "Box Border":   set_pattern("border"),
        "Clear":        set_pattern("empty"),
    }))

    shell.assign("canvas", Function(canvas_handler))
    shell.assign("hint",   ListView([
        "  Select a pattern with Enter  |  Tab to switch to canvas  |  Ctrl+Q to go back",
    ]))

    _canvas_state["pattern"] = "grid"

    shell.run()


# ---------------------------------------------------------------------------
# Shell 6 — Style Demo
#
# Demonstrates C-style comments and style tags:
#
#   Comments  /* ... */   are stripped before parsing — they never appear
#             in the rendered TUI, so you can annotate complex layouts
#             without affecting the output.
#
#   Style tags  <attr[=val][;...]>text</>  apply terminal attributes to
#               border titles.  Every attribute degrades gracefully to
#               plain text when the terminal doesn't support it.
#
# The layout string below uses both features:
# ---------------------------------------------------------------------------

STYLE_LAYOUT = """\
/* Style Demo shell                                                          */
/* The title below uses <bold;color=bright_yellow> style tags.               */
/* Comments like these are stripped before parsing — they never appear in    */
/* the rendered TUI, but you can use them to annotate complex layouts.       */
|=100%================ <bold;color=bright_yellow>Style Tag Demo</> =================|
|{45%  __Syntax Reference__       }|{  __Live Preview__                   }|
|{20R  $reference$                }|{20R  $preview$                       }|
|{                                }|{                                      }|
|=========================================================================|
|{100%  2R  $footer$                                                       }|
|=========================================================================|
"""  # The title above demonstrates a multi-attribute style tag.

# ── Reference panel content ─────────────────────────────────────────────────

STYLE_REFERENCE = [
    "-- Text styles --",
    "<bold>text</>         bold",
    "<dim>text</>          dim / faint",
    "<italic>text</>       italic",
    "<underline>text</>    underline",
    "<blink>text</>        blink",
    "<reverse>text</>      reverse video",
    "<strike>text</>       strikethrough",
    "",
    "-- Colours --",
    "<color=NAME>text</>   foreground",
    "<bg=NAME>text</>      background",
    "",
    "-- Named colours --",
    "red, green, blue",
    "yellow, cyan, magenta",
    "white, black",
    "bright_red, bright_green",
    "bright_blue, bright_yellow",
    "bright_cyan, bright_magenta",
    "bright_white, bright_black",
    "",
    "-- Aliases --",
    "gray/grey -> bright_black",
    "purple    -> magenta",
    "pink      -> bright_magenta",
    "orange    -> yellow",
    "navy      -> blue",
    "teal      -> cyan",
    "",
    "-- Multiple attrs --",
    "<bold;color=red>",
    "<color=white;bg=blue>",
    "<bold;underline;color=cyan>",
    "",
    "-- Closing tags --",
    "</>         resets all",
    "</bold>     also resets",
]

# ── Preview panel: styled text rendered by a Function handler ────────────────
#
# The preview panel uses Function + render_styled() to draw styled text
# lines directly to the terminal, demonstrating what each style tag looks
# like in practice.

_STYLE_EXAMPLES = [
    # (tagged text string, plain-text label for the right column)
    ("<bold>Bold</> text",                           "bold"),
    ("<dim>Dim</> text",                             "dim"),
    ("<italic>Italic</> text",                       "italic"),
    ("<underline>Underlined</> text",                "underline"),
    ("<blink>Blinking</> text",                      "blink"),
    ("<reverse>Reverse video</>",                    "reverse"),
    ("<strike>Strikethrough</> text",                "strike"),
    ("",                                             ""),
    ("<color=red>Red foreground</>",                 "color=red"),
    ("<color=green>Green foreground</>",             "color=green"),
    ("<color=blue>Blue foreground</>",               "color=blue"),
    ("<color=yellow>Yellow foreground</>",           "color=yellow"),
    ("<color=cyan>Cyan foreground</>",               "color=cyan"),
    ("<color=magenta>Magenta foreground</>",         "color=magenta"),
    ("<color=bright_red>Bright red</>",              "color=bright_red"),
    ("<color=bright_green>Bright green</>",          "color=bright_green"),
    ("<color=gray>Gray (bright_black)</>",           "color=gray"),
    ("",                                             ""),
    ("<bg=red>Red background</>",                    "bg=red"),
    ("<bg=blue>Blue background</>",                  "bg=blue"),
    ("<bg=green>Green background</>",                "bg=green"),
    ("<bg=yellow;color=black>Yellow bg</>",          "bg=yellow;color=black"),
    ("",                                             ""),
    ("<bold;color=bright_green>Bold bright green</>",     "bold;color=bright_green"),
    ("<color=white;bg=blue>White on blue</>",             "color=white;bg=blue"),
    ("<bold;underline;color=cyan>Multi-style</>",         "bold;underline;color=cyan"),
    ("<bold;color=bright_yellow>Like the title!</>",      "bold;color=bright_yellow"),
]


def style_preview_handler(shell, region, key):
    """
    Function handler for the style preview panel.

    Calls render_styled() for each example line, which applies terminal
    escape sequences and falls back gracefully to plain text.
    """
    term = shell.terminal
    for i, (tagged, _label) in enumerate(_STYLE_EXAMPLES):
        row = region.row + i
        if row >= region.row + region.height:
            break
        # Clear the row first so previous content doesn't bleed through.
        print(term.move(row, region.col) + " " * region.width, end="", flush=False)
        if tagged:
            rendered = render_styled("  " + tagged, term, max_len=region.width)
            print(term.move(row, region.col) + rendered, end="", flush=False)


def run_style():
    """
    Style Tag Demo.

    Demonstrates:
      - C-style /* ... */ comments in shell definition strings
      - Style tags (<bold>, <color=red>, <bg=blue;color=white>, …) in border titles
      - render_styled() used directly inside a Function handler to draw
        styled text anywhere in a region
      - Graceful fallback: each attribute is applied independently, so
        unsupported attributes are silently skipped
    """
    shell = Shell(STYLE_LAYOUT, _terminal=_TERM)

    shell.assign("reference", ListView(STYLE_REFERENCE, bullet=" "))
    shell.assign("preview",   Function(style_preview_handler))
    shell.assign("footer",    ListView([
        "  Style tags work in border titles today; use render_styled() for"
        " styled content inside regions.  Ctrl+Q to go back.",
    ]))

    shell.run()


# ---------------------------------------------------------------------------
# Shell 7 — Shell File Demo
#
# Reads example.shell from disk at runtime and passes its contents to
# Shell().  This shows users exactly how an external .shell file renders
# without hard-coding the definition string in Python.
# ---------------------------------------------------------------------------

# Reference data used by the sidemenu callbacks.
_SHELL_FILE_DETAILS = {
    "overview": [
        "tui-wysiwyg is a Python library",
        "for building rich TUIs from a",
        "WYSIWYG layout definition.",
        "",
        "Define your layout as an ASCII",
        "diagram, assign interactions,",
        "and call shell.run().",
    ],
    "start": [
        "pip install tui-wysiwyg",
        "",
        "from tui_wysiwyg import Shell",
        "from tui_wysiwyg.interactions \\",
        "    import MenuReturn",
        "",
        "shell = Shell(LAYOUT)",
        "shell.assign('menu',",
        "    MenuReturn({'Quit': None}))",
        "shell.run()",
    ],
    "interactions": [
        "MenuReturn   return a value",
        "MenuFunction call a function",
        "MenuHybrid   both",
        "TextBox      text entry",
        "ListView     display list",
        "SubList      nested list",
        "CheckBox     toggles",
        "FormInput    data entry form",
        "Function     custom handler",
    ],
    "styling": [
        "Style tags in border titles:",
        "",
        "  <bold>text</>",
        "  <color=red>text</>",
        "  <bg=blue;color=white>",
        "    text</>",
        "",
        "C-style comments: /* ... */",
        "",
        "render_styled() for content",
        "inside Function handlers.",
    ],
    "testing": [
        "from tui_wysiwyg.testing \\",
        "    import MockTerminal",
        "",
        "term = MockTerminal(80, 24)",
        "shell = Shell(LAYOUT,",
        "    _terminal=term)",
        "term.feed_keys(['KEY_ENTER'])",
        "result = shell.run()",
    ],
    "api": [
        "shell.assign(name, interaction)",
        "shell.unassign(name)",
        "shell.get(name)",
        "shell.update(name, value)",
        "shell.on_change(name, cb)",
        "shell.bind(source, target)",
        "shell.set_focus(name)",
        "shell.run()",
    ],
}


def _make_sidemenu_handler(key):
    """Return a MenuFunction callback that updates text_response for key."""
    def handler(sh):
        sh.update("text_response", _SHELL_FILE_DETAILS[key])
    return handler


def run_example_shell():
    """
    Shell File Demo.

    Demonstrates:
      - Loading a shell definition from a .shell file at runtime
      - Shell() accepts any string, so file-based definitions work
        identically to inline strings
      - A fully populated complex layout: three columns at the top,
        a mid-layout single-border divider, and a full-width bottom section
    """
    shell_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "example.shell")
    with open(shell_file) as f:
        definition = f.read()

    shell = Shell(definition, _terminal=_TERM)

    # ── sidemenu: topic picker ─────────────────────────────────────────────
    shell.assign("sidemenu", MenuFunction({
        "Overview":        _make_sidemenu_handler("overview"),
        "Getting Started": _make_sidemenu_handler("start"),
        "Interactions":    _make_sidemenu_handler("interactions"),
        "Styling":         _make_sidemenu_handler("styling"),
        "Testing":         _make_sidemenu_handler("testing"),
        "API Reference":   _make_sidemenu_handler("api"),
    }))

    # ── mainmenu: description of the layout file ───────────────────────────
    shell.assign("mainmenu", TextBox(
        initial=(
            "This shell was loaded from example.shell.\n"
            "\n"
            "It demonstrates a complex multi-region\n"
            "layout with:\n"
            "  - Three top columns (25 / 50 / fill)\n"
            "  - A mid-layout single-border divider\n"
            "  - A full-width bottom section\n"
            "\n"
            "Tab between regions to explore.\n"
            "Select a topic in the left menu\n"
            "to update the bottom panel."
        ),
        wrap="word",
    ))

    # ── info1: library info sidebar ────────────────────────────────────────
    shell.assign("info1", ListView([
        "tui-wysiwyg",
        "",
        "Python library for",
        "WYSIWYG TUI layouts.",
        "",
        "Layout loaded from:",
        "  example.shell",
        "",
        "Ctrl+Q to go back.",
    ], bullet=" "))

    # ── textbox: free-form notes area ──────────────────────────────────────
    shell.assign("textbox", TextBox(
        initial="Type notes here...",
        wrap="word",
    ))

    # ── checkbox: feature flags ────────────────────────────────────────────
    shell.assign("checkbox", CheckBox({
        "Comments":  True,
        "Style tags": True,
        "MenuReturn": False,
        "TextBox":   False,
        "FormInput": False,
    }, mode="multi"))

    # ── text_response: bottom panel, updated by sidemenu selections ────────
    shell.assign("text_response", ListView(
        _SHELL_FILE_DETAILS["overview"],
        bullet=" ",
    ))

    shell.run()


# ---------------------------------------------------------------------------
# Shell 7 — Modal Dialog
#
# Demonstrates Shell.run_modal():
#
#   A second Shell is constructed with its own layout and interactions,
#   then rendered as a popup overlaid at a fixed (row, col, width, height)
#   position on top of the running parent shell.  run_modal() does NOT
#   re-enter fullscreen() — the parent's terminal context is already active.
#
#   The modal is called from inside a MenuFunction callback, which fires
#   synchronously while Shell.run() is executing.  When the popup is
#   dismissed (Enter on Yes/No, or Escape/Ctrl+Q), the parent display is
#   fully restored via parent_shell._renderer.full_render().
# ---------------------------------------------------------------------------

MODAL_DEMO_LAYOUT = """\
|=100%============================== <bold>Modal Dialog Demo</> ==============================|
|{30%  __Actions__              }|{  __Items__                                             }|
|{16R  $actions$                }|{16R  $items$                                            }|
|{                              }|{                                                        }|
|============================================================================================|
|{100%  2R  $hint$                                                                          }|
|============================================================================================|
"""

# Popup layout: a 2-row message area, a single-line divider, then Yes/No.
# The outer dimensions are fixed: POPUP_WIDTH × POPUP_HEIGHT characters.
CONFIRM_POPUP = """\
|================|
|{2R $msg$       }|
|----------------|
|{2R $choice$    }|
|================|
"""
POPUP_WIDTH = 30
# Height (7) and row/col are intentionally omitted from the run_modal call:
# height is auto-detected from the 2R declarations; row/col auto-center.


def _confirm(shell, lines):
    """Show a centered Yes/No modal over *shell*.

    *lines* is a list of strings displayed in the message area (2 rows shown).

    Returns True (Yes), False (No), or None (Escape / Ctrl+Q).
    """
    popup = Shell(CONFIRM_POPUP, _terminal=shell.terminal)
    popup.assign("msg",    ListView(lines, bullet=" "))
    popup.assign("choice", MenuReturn({"Yes": True, "No": False}))
    return popup.run_modal(width=POPUP_WIDTH, parent_shell=shell)


def run_modal_demo():
    """
    Modal Dialog demo.

    Demonstrates:
      - Shell.run_modal(): a second Shell rendered as a popup overlay,
        positioned at an arbitrary (row, col, width, height) on the screen
      - Calling run_modal() from inside a MenuFunction callback while the
        parent Shell's terminal context is already active
      - parent_shell parameter: the parent display is fully restored when
        the popup closes, erasing the popup ghost
    """
    shell = Shell(MODAL_DEMO_LAYOUT, _terminal=_TERM)
    items = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]

    def refresh():
        display = (
            [f"  {i + 1}. {item}" for i, item in enumerate(items)]
            if items else ["  (empty)"]
        )
        shell.update("items", display)

    def add_item(sh):
        name = f"Item {len(items) + 1}"
        items.append(name)
        refresh()
        sh.update("hint", [f"  Added '{name}'.  Use \u2191 \u2193 to navigate, Enter to act.  Ctrl+Q to go back."])

    def delete_last(sh):
        if not items:
            sh.update("hint", ["  Nothing to delete."])
            return
        name = items[-1]
        confirmed = _confirm(sh, [f"Delete '{name}'?", ""])
        if confirmed:
            items.pop()
            refresh()
            sh.update("hint", [f"  Deleted '{name}'.  Ctrl+Q to go back."])
        else:
            sh.update("hint", ["  Cancelled.  Ctrl+Q to go back."])

    def clear_all(sh):
        if not items:
            sh.update("hint", ["  List is already empty."])
            return
        confirmed = _confirm(sh, [f"Clear all {len(items)} items?",
                                  "This cannot be undone."])
        if confirmed:
            items.clear()
            refresh()
            sh.update("hint", ["  All items cleared.  Ctrl+Q to go back."])
        else:
            sh.update("hint", ["  Cancelled.  Ctrl+Q to go back."])

    shell.assign("actions", MenuFunction({
        "Add item":    add_item,
        "Delete last": delete_last,
        "Clear all":   clear_all,
    }))
    shell.assign("items", ListView([], bullet=" "))
    shell.assign("hint",  ListView([
        "  Select an action — Delete and Clear will ask for confirmation via a modal popup.",
    ]))

    refresh()
    shell.run()


# ---------------------------------------------------------------------------
# Shell 8 — Confirm Widget
#
# Demonstrates tui_wysiwyg.widgets.Confirm:
#
#   A self-contained popup class built on Shell.run_modal().  The caller
#   passes a title, message lines, and a buttons dict; Confirm handles
#   all shell construction, interaction assignment, and modal display.
#
#   Three scenarios are shown, each customising the title, message, and
#   button labels/values to suit the action being confirmed.
# ---------------------------------------------------------------------------

CONFIRM_WIDGET_LAYOUT = """\
|=100%======================== <bold>Confirm Widget Demo</bold> ========================|
|{100%  __Actions__                                                              }|
|{8R    $actions$                                                                }|
|{                                                                               }|
|================================================================================|
|{100%  2R  $result$                                                             }|
|================================================================================|
"""


def run_confirm_demo():
    """
    Confirm Widget demo.

    Demonstrates:
      - Confirm widget from tui_wysiwyg.widgets
      - Customising title, message_lines, and buttons per use case
      - Returning True / False / None and acting on the result
      - Using run_modal_kwargs to override positioning if needed
    """
    from tui_wysiwyg.widgets.confirm import Confirm

    shell = Shell(CONFIRM_WIDGET_LAYOUT, _terminal=_TERM)

    def do_delete(sh):
        result = Confirm(
            title="Delete file?",
            message_lines=["This action cannot be undone.", ""],
            buttons={"Yes, delete": True, "Cancel": False},
        ).show(parent_shell=sh)
        if result is True:
            msg = "File deleted."
        elif result is False:
            msg = "Cancelled — file kept."
        else:
            msg = "Dismissed (Escape)."
        sh.update("result", [f"  \u2192 {msg}"])

    def do_overwrite(sh):
        result = Confirm(
            title="Overwrite?",
            message_lines=["output.txt already exists.", "Overwrite it?"],
            buttons={"Overwrite": True, "Keep existing": False},
        ).show(parent_shell=sh)
        if result is True:
            msg = "File overwritten."
        elif result is False:
            msg = "Kept existing file."
        else:
            msg = "Dismissed (Escape)."
        sh.update("result", [f"  \u2192 {msg}"])

    def do_quit(sh):
        result = Confirm(
            title="Unsaved changes",
            message_lines=["You have unsaved changes.", "Quit anyway?"],
            buttons={"Quit without saving": True, "Go back": False},
            width=44,
        ).show(parent_shell=sh)
        if result is True:
            msg = "Quit confirmed."
        elif result is False:
            msg = "Returned to editor."
        else:
            msg = "Dismissed (Escape)."
        sh.update("result", [f"  \u2192 {msg}"])

    shell.assign("actions", MenuFunction({
        "Delete file":          do_delete,
        "Overwrite file":       do_overwrite,
        "Quit without saving":  do_quit,
    }))
    shell.assign("result", ListView([
        "  Select an action above — each triggers a Confirm popup.  Ctrl+Q to go back.",
    ]))

    shell.run()


# ---------------------------------------------------------------------------
# Shell 9 — Alert Widget
#
# Demonstrates tui_wysiwyg.widgets.Alert:
#
#   A single-button popup that surfaces errors, warnings, or informational
#   messages.  The caller supplies a title and message lines; the widget
#   blocks until the user presses OK, Escape, or Ctrl+Q.
# ---------------------------------------------------------------------------

ALERT_WIDGET_LAYOUT = """\
|=100%========================== <bold>Alert Widget Demo</bold> ==========================|
|{100%  __Scenarios__                                                              }|
|{8R    $scenarios$                                                                }|
|{                                                                                 }|
|==================================================================================|
|{100%  2R  $result$                                                               }|
|==================================================================================|
"""


def run_alert_demo():
    """
    Alert Widget demo.

    Demonstrates:
      - Alert widget from tui_wysiwyg.widgets
      - Error, warning, and informational message styles
      - Custom width to accommodate longer message lines
      - Return value (True / None) — typically ignored for Alert
    """
    from tui_wysiwyg.widgets.alert import Alert

    shell = Shell(ALERT_WIDGET_LAYOUT, _terminal=_TERM)

    def show_error(sh):
        Alert(
            title="Error",
            message_lines=[
                "Could not write to output.txt.",
                "Permission denied.",
                "Check file permissions and try again.",
            ],
            width=46,
        ).show(parent_shell=sh)
        sh.update("result", ["  \u2192 Error alert dismissed."])

    def show_warning(sh):
        Alert(
            title="Warning",
            message_lines=[
                "Configuration file not found.",
                "Default settings will be used.",
            ],
        ).show(parent_shell=sh)
        sh.update("result", ["  \u2192 Warning alert dismissed."])

    def show_info(sh):
        Alert(
            title="Complete",
            message_lines=[
                "Export finished successfully.",
                "42 records written to export.csv.",
            ],
        ).show(parent_shell=sh)
        sh.update("result", ["  \u2192 Info alert dismissed."])

    shell.assign("scenarios", MenuFunction({
        "Show error":    show_error,
        "Show warning":  show_warning,
        "Show info":     show_info,
    }))
    shell.assign("result", ListView([
        "  Select a scenario above — each triggers an Alert popup.  Ctrl+Q to go back.",
    ]))

    shell.run()


# ---------------------------------------------------------------------------
# Shell 10 — Input Prompt Widget
#
# Demonstrates tui_wysiwyg.widgets.InputPrompt:
#
#   A popup with a 2-row prompt, a 2-row text entry box, and OK/Cancel
#   buttons.  OK returns the typed string; Cancel / Escape return None.
#   The entry box uses wrap='extend' so long lines scroll horizontally.
# ---------------------------------------------------------------------------

INPUT_PROMPT_LAYOUT = """\
|=100%====================== <bold>Input Prompt Widget Demo</bold> ======================|
|{100%  __Scenarios__                                                            }|
|{8R    $scenarios$                                                              }|
|{                                                                               }|
|================================================================================|
|{100%  2R  $result$                                                             }|
|================================================================================|
"""


def run_input_prompt_demo():
    """
    Input Prompt Widget demo.

    Demonstrates:
      - InputPrompt widget from tui_wysiwyg.widgets
      - Prompt text, pre-filled initial value, and custom width
      - Handling OK (text string), Cancel (None), and Escape (None)
      - Chaining InputPrompt with Alert for simple validation feedback
    """
    from tui_wysiwyg.widgets.input_prompt import InputPrompt
    from tui_wysiwyg.widgets.alert import Alert

    shell = Shell(INPUT_PROMPT_LAYOUT, _terminal=_TERM)

    def do_rename(sh):
        result = InputPrompt(
            title="Rename item",
            prompt_lines=["Enter a new name:", ""],
            initial="my_file.txt",
        ).show(parent_shell=sh)
        if result is not None:
            sh.update("result", [f"  \u2192 Renamed to: {result!r}"])
        else:
            sh.update("result", ["  \u2192 Rename cancelled."])

    def do_edit_url(sh):
        result = InputPrompt(
            title="Edit URL",
            prompt_lines=["Modify the URL below:"],
            initial="https://example.com/path?query=1",
            width=60,
        ).show(parent_shell=sh)
        if result is not None:
            sh.update("result", [f"  \u2192 URL set to: {result!r}"])
        else:
            sh.update("result", ["  \u2192 Edit cancelled."])

    def do_search(sh):
        query = InputPrompt(
            title="Search",
            prompt_lines=["Enter search query:"],
        ).show(parent_shell=sh)
        if query is None:
            sh.update("result", ["  \u2192 Search cancelled."])
        elif not query.strip():
            Alert(
                title="Empty query",
                message_lines=["Please enter a search term.", ""],
            ).show(parent_shell=sh)
            sh.update("result", ["  \u2192 Empty query — not submitted."])
        else:
            sh.update("result", [f"  \u2192 Searching for: {query!r}"])

    shell.assign("scenarios", MenuFunction({
        "Rename item":   do_rename,
        "Edit URL":      do_edit_url,
        "Search":        do_search,
    }))
    shell.assign("result", ListView([
        "  Select a scenario — each opens an Input Prompt popup.  Ctrl+Q to go back.",
    ]))

    shell.run()


# ---------------------------------------------------------------------------
# Shell 11 — List Select Widget
#
# Demonstrates tui_wysiwyg.widgets.ListSelect in all four combinations:
#   single + list, single + dict, multi + list, multi + dict with pre-checks.
# ---------------------------------------------------------------------------

LIST_SELECT_LAYOUT = """\
|=100%====================== <bold>List Select Widget Demo</bold> ======================|
|{100%  __Scenarios__                                                            }|
|{10R   $scenarios$                                                              }|
|{                                                                               }|
|================================================================================|
|{100%  2R  $result$                                                             }|
|================================================================================|
"""


def run_list_select_demo():
    """
    List Select Widget demo.

    Demonstrates:
      - Single mode with a list (label is the return value)
      - Single mode with a dict (mapped return values)
      - Multi mode with a list (all start unchecked)
      - Multi mode with a dict (pre-set checked states)
    """
    from tui_wysiwyg.widgets.list_select import ListSelect

    shell = Shell(LIST_SELECT_LAYOUT, _terminal=_TERM)

    def single_list(sh):
        result = ListSelect(
            title="Choose theme",
            prompt_lines=["Select a colour theme:"],
            items=["Dark", "Light", "High Contrast", "Solarized", "Monokai"],
        ).show(parent_shell=sh)
        if result is not None:
            sh.update("result", [f"  \u2192 Theme selected: {result!r}"])
        else:
            sh.update("result", ["  \u2192 Dismissed."])

    def single_dict(sh):
        result = ListSelect(
            title="Set priority",
            prompt_lines=["Choose a priority level:"],
            items={"Low": 1, "Medium": 2, "High": 3, "Critical": 4},
        ).show(parent_shell=sh)
        if result is not None:
            sh.update("result", [f"  \u2192 Priority value: {result}"])
        else:
            sh.update("result", ["  \u2192 Dismissed."])

    def multi_list(sh):
        result = ListSelect(
            title="Choose toppings",
            prompt_lines=["Select all that apply:"],
            items=["Cheese", "Tomato", "Basil", "Olives", "Mushrooms", "Peppers"],
            multi=True,
        ).show(parent_shell=sh)
        if result is not None:
            chosen = [t for t, v in result.items() if v] or ["(none)"]
            sh.update("result", [f"  \u2192 Chosen: {', '.join(chosen)}"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    def multi_dict(sh):
        result = ListSelect(
            title="Features",
            prompt_lines=["Enable or disable features:"],
            items={
                "Auto-save":    True,
                "Spell-check":  True,
                "Line numbers": False,
                "Word-wrap":    False,
                "Dark mode":    False,
            },
            multi=True,
            width=44,
        ).show(parent_shell=sh)
        if result is not None:
            on  = [k for k, v in result.items() if v]     or ["(none)"]
            off = [k for k, v in result.items() if not v] or ["(none)"]
            sh.update("result", [f"  \u2192 On: {', '.join(on)}  |  Off: {', '.join(off)}"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    shell.assign("scenarios", MenuFunction({
        "Single — list (theme)":       single_list,
        "Single — dict (priority)":    single_dict,
        "Multi  — list (toppings)":    multi_list,
        "Multi  — dict (features)":    multi_dict,
    }))
    shell.assign("result", ListView([
        "  Select a scenario — each opens a List Select popup.  Ctrl+Q to go back.",
    ]))

    shell.run()


# ---------------------------------------------------------------------------
# Shell 12 — File Picker Widget
#
# Demonstrates tui_wysiwyg.widgets.FilePicker:
#
#   A 70-wide popup with a path bar, glob filter, directory tree (left 30%),
#   and filtered file list (right fill).  Navigation rebuilds both panels
#   live; the filter TextBox updates the file list as the user types.
# ---------------------------------------------------------------------------

FILE_PICKER_LAYOUT = """\
|=100%====================== <bold>File Picker Widget Demo</bold> ======================|
|{100%  __Scenarios__                                                            }|
|{8R    $scenarios$                                                              }|
|{                                                                               }|
|================================================================================|
|{100%  2R  $result$                                                             }|
|================================================================================|
"""


DATE_PICKER_LAYOUT = """\
|=100%====================== <bold>Date Picker Widget Demo</bold> =======================|
|{100%  __Scenarios__                                                             }|
|{8R    $scenarios$                                                               }|
|{                                                                                }|
|=================================================================================|
|{100%  2R  $result$                                                              }|
|=================================================================================|
"""


def run_date_picker_demo():
    """
    Date Picker Widget demo.

    Demonstrates:
      - DatePicker with today as the initial selection
      - DatePicker with a specific initial date
      - DatePicker with a custom title
    """
    import datetime
    from tui_wysiwyg.widgets.date_picker import DatePicker

    shell = Shell(DATE_PICKER_LAYOUT, _terminal=_TERM)

    def pick_today(sh):
        d = DatePicker(
            title="Pick a date",
        ).show(parent_shell=sh)
        if d is not None:
            sh.update("result", [f"  \u2192 Selected: {d.strftime('%A, %B %d %Y')}"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    def pick_specific(sh):
        initial = datetime.date(2026, 6, 15)
        d = DatePicker(
            initial=initial,
            title="Choose a date",
        ).show(parent_shell=sh)
        if d is not None:
            sh.update("result", [f"  \u2192 Selected: {d.isoformat()}"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    def pick_deadline(sh):
        d = DatePicker(
            title="Set Deadline",
            width=34,
        ).show(parent_shell=sh)
        if d is not None:
            today = datetime.date.today()
            delta = (d - today).days
            if delta < 0:
                sh.update("result", [f"  \u2192 {d.isoformat()} ({-delta} days ago)"])
            elif delta == 0:
                sh.update("result", [f"  \u2192 {d.isoformat()} (today)"])
            else:
                sh.update("result", [f"  \u2192 {d.isoformat()} (in {delta} days)"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    shell.assign("scenarios", MenuFunction({
        "Pick any date (today default)": pick_today,
        "Pick from June 2026":           pick_specific,
        "Set a deadline":                pick_deadline,
    }))
    shell.assign("result", ListView([
        "  Select a scenario — each opens a Date Picker popup.  Ctrl+Q to go back.",
    ]))

    shell.run()


def run_file_picker_demo():
    """
    File Picker Widget demo.

    Demonstrates:
      - FilePicker with default settings (any file from cwd)
      - Pre-set glob filter to narrow file types shown
      - dirs_only=True for directory selection
    """
    import os
    from tui_wysiwyg.widgets.file_picker import FilePicker

    shell = Shell(FILE_PICKER_LAYOUT, _terminal=_TERM)
    here = os.path.dirname(os.path.abspath(__file__))

    def pick_any(sh):
        path = FilePicker(
            start_dir=here,
            title="Select any file",
        ).show(parent_shell=sh)
        if path is not None:
            sh.update("result", [f"  \u2192 Selected: {path}"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    def pick_python(sh):
        path = FilePicker(
            start_dir=here,
            title="Select Python file",
            filter="*.py",
        ).show(parent_shell=sh)
        if path is not None:
            sh.update("result", [f"  \u2192 Selected: {path}"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    def pick_dir(sh):
        path = FilePicker(
            start_dir=here,
            title="Select directory",
            dirs_only=True,
        ).show(parent_shell=sh)
        if path is not None:
            sh.update("result", [f"  \u2192 Directory: {path}"])
        else:
            sh.update("result", ["  \u2192 Cancelled."])

    shell.assign("scenarios", MenuFunction({
        "Pick any file":        pick_any,
        "Pick Python file":     pick_python,
        "Pick directory":       pick_dir,
    }))
    shell.assign("result", ListView([
        "  Select a scenario — each opens a File Picker popup.  Ctrl+Q to go back.",
    ]))

    shell.run()


PROGRESS_LAYOUT = """\
|=100%======================= <bold>Progress Bar Widget Demo</bold> ====================|
|{100%  __Scenarios__                                                              }|
|{8R    $scenarios$                                                                }|
|{                                                                                 }|
|==================================================================================|
|{100%  2R  $result$                                                               }|
|==================================================================================|
"""


def run_progress_demo():
    """
    Progress Bar Widget demo.

    Demonstrates:
      - Cancellable progress bar (user can press Cancel at any time)
      - Non-cancellable progress bar (runs to completion)
      - Progress bar that checks for cancellation mid-run
    """
    import time
    from tui_wysiwyg.widgets.progress import Progress

    shell = Shell(PROGRESS_LAYOUT, _terminal=_TERM)

    def run_cancellable(sh):
        total = 20
        with Progress(
            title="Processing…",
            total=total,
            cancellable=True,
            width=52,
        ).show(parent_shell=sh) as prog:
            for i in range(1, total + 1):
                time.sleep(0.08)
                prog.set_progress(i, f"Step {i} of {total}")
                if prog.cancelled:
                    sh.update("result", ["  \u2192 Cancelled by user."])
                    return
        sh.update("result", [f"  \u2192 Completed all {total} steps."])

    def run_quiet(sh):
        total = 15
        with Progress(
            title="Importing data",
            total=total,
            cancellable=False,
            width=52,
        ).show(parent_shell=sh) as prog:
            for i in range(1, total + 1):
                time.sleep(0.07)
                prog.set_progress(i, f"Row {i}")
        sh.update("result", [f"  \u2192 Imported {total} rows."])

    def run_with_phases(sh):
        phases = [
            ("Connecting…",   5),
            ("Downloading…", 10),
            ("Verifying…",    5),
        ]
        total = sum(n for _, n in phases)
        done  = 0
        with Progress(
            title="Multi-phase task",
            total=total,
            cancellable=True,
            width=52,
        ).show(parent_shell=sh) as prog:
            for label, steps in phases:
                for _ in range(steps):
                    time.sleep(0.06)
                    done += 1
                    prog.set_progress(done, label)
                    if prog.cancelled:
                        sh.update("result", [f"  \u2192 Cancelled during '{label}'."])
                        return
        sh.update("result", ["  \u2192 All phases complete."])

    shell.assign("scenarios", MenuFunction({
        "Cancellable (20 steps)":       run_cancellable,
        "Non-cancellable (15 steps)":   run_quiet,
        "Multi-phase (3 phases)":       run_with_phases,
    }))
    shell.assign("result", ListView([
        "  Select a scenario — each opens a Progress popup.  Ctrl+Q to go back.",
    ]))

    shell.run()


# ---------------------------------------------------------------------------
# Entry point — main navigation loop
# ---------------------------------------------------------------------------

def main():
    """
    Outer loop: show the main menu, dispatch to the selected demo shell,
    then return to the main menu until the user quits.
    """
    print("Starting tui-wysiwyg demo...")

    while True:
        choice = run_main_menu()

        if choice is None:
            print("\nThanks for trying tui-wysiwyg!")
            break
        elif choice == "catalog":
            run_catalog()
        elif choice == "notes":
            run_notes()
        elif choice == "settings":
            run_settings()
        elif choice == "custom":
            run_custom()
        elif choice == "styles":
            run_style()
        elif choice == "shell_file":
            run_example_shell()
        elif choice == "modal":
            run_modal_demo()
        elif choice == "confirm_widget":
            run_confirm_demo()
        elif choice == "alert_widget":
            run_alert_demo()
        elif choice == "input_prompt":
            run_input_prompt_demo()
        elif choice == "list_select":
            run_list_select_demo()
        elif choice == "file_picker":
            run_file_picker_demo()
        elif choice == "date_picker":
            run_date_picker_demo()
        elif choice == "progress_bar":
            run_progress_demo()


if __name__ == "__main__":
    main()
