"""Date Picker widget — monthly calendar for selecting a date.

Shell layout
------------

    |=== <bold>Title</> ===|
    |{2R $nav$             }|
    |----------------------|
    |{8R $calendar$        }|
    |----------------------|
    |{1R $buttons$         }|
    |======================|

- ``$nav$``      — Displays the current month/year label and ``< Prev`` /
                   ``Next >`` navigation cues.  Left/Right arrows change month.
- ``$calendar$`` — Draws the weekday header and date grid.  Arrow keys move
                   the highlighted cursor date.  Enter selects the date and
                   exits.
- ``$buttons$``  — ``_SubmittingMenu("calendar")``: OK returns the cursor
                   date; Cancel returns ``None``.

Height is auto-detected: **14 rows** (1+2+1+8+1+1+1).

Usage
-----

    from tui_wysiwyg.widgets.date_picker import DatePicker
    import datetime

    def pick_date(sh):
        d = DatePicker(title="Pick a date").show(parent_shell=sh)
        if d is not None:
            schedule(d)
"""

import datetime
import calendar as _calendar

from tui_wysiwyg import Shell
from tui_wysiwyg.interactions.base import Interaction
from tui_wysiwyg.widgets._utils import _SubmittingMenu


# ---------------------------------------------------------------------------
# Month helpers
# ---------------------------------------------------------------------------

def _first_of(d: datetime.date) -> datetime.date:
    return d.replace(day=1)


def _prev_month(d: datetime.date) -> datetime.date:
    """Return the first day of the month before *d*."""
    if d.month == 1:
        return d.replace(year=d.year - 1, month=12, day=1)
    return d.replace(month=d.month - 1, day=1)


def _next_month(d: datetime.date) -> datetime.date:
    """Return the first day of the month after *d*."""
    if d.month == 12:
        return d.replace(year=d.year + 1, month=1, day=1)
    return d.replace(month=d.month + 1, day=1)


def _clamp_day(d: datetime.date, year: int, month: int) -> datetime.date:
    """Return *d* moved to (year, month), clamping the day if needed."""
    max_day = _calendar.monthrange(year, month)[1]
    return d.replace(year=year, month=month, day=min(d.day, max_day))


# ---------------------------------------------------------------------------
# Shell definition
# ---------------------------------------------------------------------------

def _shell_def(title: str) -> str:
    return (
        f"|=== <bold>{title}</> ===|\n"
        "|{2R $nav$               }|\n"
        "|------------------------|\n"
        "|{8R $calendar$          }|\n"
        "|------------------------|\n"
        "|{1R $buttons$           }|\n"
        "|========================|\n"
    )


# ---------------------------------------------------------------------------
# _NavBar interaction
# ---------------------------------------------------------------------------

class _NavBar(Interaction):
    """Renders the month/year label and Prev/Next hints; handles arrow keys.

    Row 0: centred  ``April 2026``
    Row 1: ``< Prev``  ···  ``Next >``

    Left / Right (or Up / Down) arrows change the displayed month.
    When the month changes, the calendar region is also marked dirty.
    """

    def __init__(self, state: dict):
        self._state = state  # shared with _CalendarInteraction

    def render(self, region, term, focused: bool = False) -> None:
        month_str = self._state["month"].strftime("%B %Y")

        # Row 0: month/year label, bold when focused
        label = month_str.center(region.width)
        if focused:
            try:
                label = term.bold + label + term.normal
            except Exception:
                pass
        print(term.move(region.row, region.col) + label, end="", flush=False)

        # Row 1: < Prev on left, Next > on right (only if 2+ rows allocated)
        if region.height >= 2:
            gap = max(0, region.width - 6 - 6)
            nav_line = "< Prev" + " " * gap + "Next >"
            nav_line = nav_line[: region.width].ljust(region.width)
            print(
                term.move(region.row + 1, region.col) + nav_line,
                end="", flush=False,
            )

    def handle_key(self, key) -> tuple:
        if key.is_sequence:
            name = key.name
            if name in ("KEY_LEFT", "KEY_UP"):
                new = _prev_month(self._state["month"])
                self._state["month"] = new
                self._state["cursor"] = _clamp_day(
                    self._state["cursor"], new.year, new.month
                )
                if self._shell is not None:
                    self._shell.update("calendar", None)
                return True, self.get_value()
            elif name in ("KEY_RIGHT", "KEY_DOWN"):
                new = _next_month(self._state["month"])
                self._state["month"] = new
                self._state["cursor"] = _clamp_day(
                    self._state["cursor"], new.year, new.month
                )
                if self._shell is not None:
                    self._shell.update("calendar", None)
                return True, self.get_value()
        return False, self.get_value()

    def get_value(self):
        return self._state["month"]

    def set_value(self, value) -> None:
        pass  # nav always reads from state; set_value is used only to mark dirty


# ---------------------------------------------------------------------------
# _CalendarInteraction
# ---------------------------------------------------------------------------

_SUNDAY_CAL = _calendar.Calendar(firstweekday=6)  # week starts Sunday
_DAY_HEADER = "Su Mo Tu We Th Fr Sa"               # 20 chars
_CELL_W = 3                                         # chars per cell


class _CalendarInteraction(Interaction):
    """Draws a monthly calendar grid; arrow keys move the cursor; Enter selects.

    Rendering uses three visual states:
    - Cursor date      → ``bold + reverse``
    - Today's date     → ``bold``
    - Other dates      → plain text
    - Padding (day 0)  → blank
    """

    def __init__(self, state: dict):
        self._state = state
        self._wants_exit = False

    def render(self, region, term, focused: bool = False) -> None:
        year   = self._state["month"].year
        month  = self._state["month"].month
        cursor = self._state["cursor"]
        today  = datetime.date.today()

        cal_w = 7 * _CELL_W          # 21
        pad   = max(0, (region.width - cal_w) // 2)
        col   = region.col
        row   = region.row

        # -- Header row ---------------------------------------------------------
        header_line = (" " * pad + _DAY_HEADER)[: region.width].ljust(region.width)
        print(term.move(row, col) + header_line, end="", flush=False)
        row += 1

        # -- Date rows ----------------------------------------------------------
        weeks = _SUNDAY_CAL.monthdayscalendar(year, month)
        for week in weeks:
            if row >= region.row + region.height:
                break
            # Clear the row first (styled chars can't be ljust-padded safely)
            print(term.move(row, col) + " " * region.width, end="", flush=False)

            for i, day in enumerate(week):
                cell_col = col + pad + i * _CELL_W
                if day == 0:
                    continue  # padding cell — already blank

                d    = datetime.date(year, month, day)
                cell = f"{day:2d} "

                if d == cursor:
                    try:
                        styled = term.reverse + term.bold + cell + term.normal
                    except Exception:
                        styled = f"[{day:>2}]"
                elif d == today:
                    try:
                        styled = term.bold + cell + term.normal
                    except Exception:
                        styled = cell
                else:
                    styled = cell

                print(term.move(row, cell_col) + styled, end="", flush=False)

            row += 1

        # -- Clear any remaining rows -------------------------------------------
        while row < region.row + region.height:
            print(term.move(row, col) + " " * region.width, end="", flush=False)
            row += 1

    def handle_key(self, key) -> tuple:
        cursor = self._state["cursor"]
        delta  = None

        if key.is_sequence:
            name = key.name
            if name == "KEY_LEFT":
                delta = datetime.timedelta(days=-1)
            elif name == "KEY_RIGHT":
                delta = datetime.timedelta(days=1)
            elif name == "KEY_UP":
                delta = datetime.timedelta(weeks=-1)
            elif name == "KEY_DOWN":
                delta = datetime.timedelta(weeks=1)
            elif name == "KEY_ENTER":
                self._wants_exit = True
                return True, self.get_value()
        else:
            if str(key) in ("\n", "\r"):
                self._wants_exit = True
                return True, self.get_value()

        if delta is None:
            return False, self.get_value()

        new_cursor = cursor + delta
        self._state["cursor"] = new_cursor

        # If the cursor crossed into a new month, follow it and refresh nav.
        if (new_cursor.year, new_cursor.month) != (
            self._state["month"].year, self._state["month"].month
        ):
            self._state["month"] = new_cursor.replace(day=1)
            if self._shell is not None:
                self._shell.update("nav", None)

        return True, self.get_value()

    def get_value(self):
        return self._state["cursor"]

    def set_value(self, value) -> None:
        pass  # calendar always reads from state; set_value used only to mark dirty

    def signal_return(self) -> tuple:
        if self._wants_exit:
            return True, self._state["cursor"]
        return False, None


# ---------------------------------------------------------------------------
# Public widget class
# ---------------------------------------------------------------------------

class DatePicker:
    """Monthly calendar popup for selecting a date.

    Parameters
    ----------
    initial : datetime.date | None
        Date to highlight on open.  Defaults to today.
    title : str
        Text displayed in the popup border (rendered bold).
    width : int
        Width of the popup in characters (including border walls).
        Must be at least 23 (room for ``Su Mo Tu We Th Fr Sa`` + borders).
        Default 30 gives comfortable padding.

    Returns
    -------
    ``datetime.date`` on OK or Enter, ``None`` on Cancel / Escape / Ctrl+Q.
    """

    def __init__(
        self,
        initial: datetime.date = None,
        title: str = "Select Date",
        width: int = 30,
    ):
        self.initial = initial or datetime.date.today()
        self.title = title
        self.width = width

    def show(self, parent_shell=None, **run_modal_kwargs):
        """Display the calendar popup.

        Parameters
        ----------
        parent_shell : Shell | None
            If provided, the parent's display is restored when the popup
            closes.  Pass the ``sh`` argument from a ``MenuFunction`` callback.
        **run_modal_kwargs
            Forwarded to ``Shell.run_modal()``.

        Returns
        -------
        ``datetime.date`` on selection, ``None`` on Cancel / Escape / Ctrl+Q.
        """
        term = parent_shell.terminal if parent_shell is not None else None

        # Shared mutable state — both interactions read/write through this dict.
        state = {
            "month":  _first_of(self.initial),
            "cursor": self.initial,
        }

        popup = Shell(_shell_def(self.title), _terminal=term)
        popup.assign("nav",      _NavBar(state))
        popup.assign("calendar", _CalendarInteraction(state))
        popup.assign("buttons",  _SubmittingMenu("calendar"))

        return popup.run_modal(
            width=self.width,
            parent_shell=parent_shell,
            **run_modal_kwargs,
        )
