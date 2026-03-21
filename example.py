#!/usr/bin/env python3
"""
tui-wysiwyg demo application.

Walks through six separate shells, each showcasing different features:

  Shell 1  — Main Menu         (MenuReturn, ListView)
  Shell 2  — Catalog Browser   (MenuReturn, SubList, ListView, shell.bind)
  Shell 3  — Note Editor       (TextBox, CheckBox, shell.on_change)
  Shell 4  — Settings Form     (FormInput — all five field types)
  Shell 5  — Custom Widget     (Function, MenuFunction)
  Shell 6  — Style Demo        (style tags, C-style comments, Function rendering)

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
    "7. Quit":             None,
}

STATUS_HINTS = {
    "catalog":    "MenuReturn + SubList + ListView + shell.bind()",
    "notes":      "TextBox + CheckBox + shell.on_change()",
    "settings":   "FormInput (str / int / float / bool / choices)",
    "custom":     "Function + MenuFunction",
    "styles":     "style tags, C-style comments, render_styled()",
    "shell_file": "layout loaded from example.shell at runtime",
    None:         "Bye!",
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


if __name__ == "__main__":
    main()
