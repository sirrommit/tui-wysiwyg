#!/usr/bin/env python3
"""
tui-wysiwyg demo application.

Walks through five separate shells, each showcasing different interaction types:

  Shell 1  — Main Menu         (MenuReturn, ListView)
  Shell 2  — Catalog Browser   (MenuReturn, SubList, ListView, shell.bind)
  Shell 3  — Note Editor       (TextBox, CheckBox, shell.on_change)
  Shell 4  — Settings Form     (FormInput — all five field types)
  Shell 5  — Custom Widget     (Function, MenuFunction)

Run with:
    python3 example.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import blessed
from tui_wysiwyg import Shell

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
# ---------------------------------------------------------------------------

MAIN_LAYOUT = """\
|=100%================================== tui-wysiwyg Demo ==================================|
|{32%  __Demos__                         }|{  __About__                                   }|
|{14R  $menu$                            }|{14R  $about$                                  }|
|{                                        }|{                                              }|
|===========================================================================================|
|{100%  2R  $status$                                                                        }|
|===========================================================================================|
"""

ABOUT_TEXT = [
    "This demo walks through the five",
    "interaction types built into",
    "tui-wysiwyg.",
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
    "5. Quit":             None,
}

STATUS_HINTS = {
    "catalog":  "MenuReturn + SubList + ListView + shell.bind()",
    "notes":    "TextBox + CheckBox + shell.on_change()",
    "settings": "FormInput (str / int / float / bool / choices)",
    "custom":   "Function + MenuFunction",
    None:       "Bye!",
}


def run_main_menu() -> str | None:
    """Show the main navigation menu. Returns the selected demo key, or None to quit."""
    shell = Shell(MAIN_LAYOUT, _terminal=_TERM)
    menu = MenuReturn(DEMO_CHOICES)
    shell.assign("menu", menu)
    shell.assign("about", ListView(ABOUT_TEXT, bullet="-"))
    shell.assign("status", ListView(["Use ↑ ↓ to navigate, Enter to open a demo."]))

    # Update the status bar whenever the highlighted menu item changes.
    def on_menu_change(label):
        key = DEMO_CHOICES.get(label)
        hint = STATUS_HINTS.get(key, "")
        shell.update("status", [f"  {label}  —  {hint}" if hint else f"  {label}"])

    shell.on_change("menu", on_menu_change)

    return shell.run()   # returns the value from DEMO_CHOICES


# ---------------------------------------------------------------------------
# Shell 2 — Catalog Browser
# Uses: MenuReturn (category picker), SubList (hierarchical contents),
#        ListView (detail panel), shell.bind() for wiring
# ---------------------------------------------------------------------------

CATALOG_LAYOUT = """\
|=100%================================ Catalog Browser ====================================|
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

    # Also update the status bar.
    def on_category_change(cat):
        count = sum(
            1 for item in CATALOG_DATA.get(cat, {}).get("contents", [])
            if isinstance(item, str) and item not in
            [x for x in CATALOG_DATA.get(cat, {}).get("contents", []) if isinstance(x, list)]
        )
        shell.update("status", [f"  Category: {cat}  |  Tab to switch panels  |  Ctrl+Q to go back"])

    shell.on_change("category", on_category_change)

    shell.run()   # Ctrl+Q returns None; we discard it and go back to main menu


# ---------------------------------------------------------------------------
# Shell 3 — Note Editor
# Uses: TextBox (main edit area), CheckBox (tag picker),
#        ListView (live summary panel), shell.on_change
# ---------------------------------------------------------------------------

NOTE_LAYOUT = """\
|=100%=================================== Note Editor ====================================|
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
|=100%================================= Settings Form =====================================|
|{100%  24R  $form$                                                                         }|
|===========================================================================================|
"""

RESULT_LAYOUT = """\
|=100%================================ Submission Result ==================================|
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
            "placeholder": "0.0 – 1.0",
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
|=100%================================ Custom Widget Demo =================================|
|{30%  __Commands__               }|{  __Canvas__                                        }|
|{16R  $commands$                 }|{16R  $canvas$                                       }|
|{                                }|{                                                    }|
|=========================================================================================|
|{100%  2R  $hint$                                                                         }|
|=========================================================================================|
"""

# Shared mutable state for the Function canvas handler.
# (A class with __call__ would be cleaner in production code.)
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
        "".join("█" if (r + c) % 2 == 0 else "░" for c in range(w))
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
            sh.update("canvas", None)    # trigger re-render via set_value+dirty
            sh.update("hint",   [f"  Pattern: {name}  |  Use ↑ ↓ to choose a command, Enter to run"])
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

    # Trigger the initial pattern draw.
    _canvas_state["pattern"] = "grid"

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
            # "Quit" was selected (or Ctrl+Q).
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
        # Any other value (shouldn't happen) loops back to main menu.


if __name__ == "__main__":
    main()
