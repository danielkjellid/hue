"""
What a declared calendar reads off a request and builds every link from:
its layers, its state, the names of its parts and the binding to one request.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from typing import TYPE_CHECKING, Any, Literal, get_args

from hue._declared import Bound, Pairs, Urls
from hue.formats import Formats
from hue.shortcuts import ShortcutRegistry
from hue.ui.molecules import _calendar_views as views
from hue.ui.molecules._calendar_views import CalendarView
from hue.ui.molecules._days import EventColor, month_grid, week_of
from hue.ui.molecules.calendar import Event
from hue.ui.molecules.date_picker import Weekday

if TYPE_CHECKING:
    from hue.calendar import _Declaration

# date is a field of CalendarState, which hides the type by that name
# inside the class, as Formats' fields do.
type _Day = date

# What each part of the state is called in the query string.
_VIEW = "view"
_DATE = "date"
_QUERY = "q"
_HIDE = "hide"
_START = "start"
_WEEKDAYS = "weekdays"
_STATE = (_VIEW, _DATE, _QUERY, _HIDE, _START, _WEEKDAYS)

# The actions the one POST route serves.
_DIALOG = "dialog"
_OVERLAPS = "overlaps"
_SAVE = "save"
_DELETE = "delete"
_MOVE = "move"

_VIEWS: tuple[CalendarView, ...] = get_args(CalendarView.__value__)

# YYYY-MM-DD and HH:MM and nothing else; fromisoformat would also take
# 20261014 and 09:30:15.
_DAY_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_CLOCK_PATTERN = re.compile(r"\d{2}:\d{2}")


@dataclass(frozen=True, slots=True)
class Layer:
    """
    One of the calendars a reader can show or hide: Product, Engineering,
    Personal. Called a layer here because Calendar is the component.

    key is what an Event names in layer and what the URL hides it by. The
    name is what the sidebar and the dialog show, and color is the chart
    token its events take unless they chose their own.
    """

    key: str
    name: str
    color: EventColor = 1


@dataclass(frozen=True, slots=True)
class CalendarState:
    """
    What was asked for, read off the request and written back into every
    link and form the calendar builds.

    events() reads first and last, the first and last day it has to cover:
    the view's own days, and the six weeks of the month around date, which
    the sidebar's picker marks. It reads query and layers, the keys of the
    layers to show, and narrows on those. The rest says how the view is
    drawn.
    """

    date: _Day
    view: CalendarView = "week"
    query: str = ""
    hidden: tuple[str, ...] = ()
    week_start: Weekday = "monday"
    weekdays: bool = False
    layers: tuple[str, ...] = ()
    first: _Day = field(init=False)
    last: _Day = field(init=False)

    def __post_init__(self) -> None:
        shown = self.days
        grid = month_grid(self.date, self.week_start)
        object.__setattr__(self, "first", min(shown[0], grid[0][0]))
        object.__setattr__(self, "last", max(shown[1], grid[-1][-1]))

    @property
    def days(self) -> tuple[_Day, _Day]:
        """
        The first and last day the view itself shows.
        """
        cursor = self.date
        if self.view == "day":
            return cursor, cursor
        if self.view == "week":
            week = week_of(cursor, self.week_start)
            return week[0], week[-1]
        if self.view == "month":
            grid = month_grid(cursor, self.week_start)
            return grid[0][0], grid[-1][-1]
        if self.view == "year":
            return date(cursor.year, 1, 1), date(cursor.year, 12, 31)
        return cursor, cursor + timedelta(days=views._AGENDA_DAYS - 1)


def _day(text: str) -> date | None:
    """
    A date typed or posted as YYYY-MM-DD, or None for anything else.
    """
    if not _DAY_PATTERN.fullmatch(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _clock(text: str) -> time | None:
    if not _CLOCK_PATTERN.fullmatch(text):
        return None
    try:
        return time.fromisoformat(text)
    except ValueError:
        return None


def _today(formats: Formats) -> date:
    """
    The reader's today: now in their timezone when the framework says how
    to get there, the server's otherwise. Read through _now so a test can
    hold the clock still.
    """
    return formats.moment(_now()).date() if formats.localize else date.today()


def _now() -> datetime:
    return datetime.now(UTC)


def _zone(formats: Formats) -> tzinfo | None:
    """
    The timezone events are drawn in, when the framework moves them into
    one. Without that, a naive time is shown as given and there is nothing
    honest to say about it.
    """
    if formats.localize is None:
        return None
    return formats.moment(_now()).tzinfo


def _timezone(formats: Formats) -> str | None:
    zone = _zone(formats)
    if zone is None:
        return None
    return getattr(zone, "key", None) or zone.tzname(_now())


def _slot(key: str) -> str:
    """
    The id of the element the dialog lands in, and every action targets.
    """
    return f"{key}-dialog"


def _overlap(key: str) -> str:
    """
    The id of the dialog's overlap warning, which the check swaps.
    """
    return f"{key}-overlap"


def _state(key: str) -> str:
    """
    The id of the hidden fields that hold the whole state, which a click on
    an empty slot reads.
    """
    return f"{key}-state"


def _new(key: str) -> str:
    """
    The id of New event, where focus goes once the dialog has closed.
    """
    return f"{key}-new"


def _side(key: str) -> str:
    """
    The id of the sidebar, which the toolbar's button opens.
    """
    return f"{key}-side"


def _view_options(key: str) -> str:
    """
    The id of the view options' form, which the fields it carries name.
    """
    return f"{key}-options"


@dataclass(frozen=True, slots=True)
class BoundCalendar(Bound):
    """
    One calendar for one request: what was asked, the events that answered,
    and the reader's today. Every part of the calendar reads this from the
    context and builds its links from it.
    """

    declaration: _Declaration
    state: CalendarState
    events: list[Event]
    today: date
    urls: Urls
    others: Pairs
    formats: Formats
    # The app's registry when it inherits CalendarShortcuts, so the keys
    # are switched on and the help lists them. None otherwise.
    shortcuts: type[ShortcutRegistry] | None = None
    # Where focus lands once a change is drawn: an event, New event after
    # an undone create, or nowhere in particular.
    focus: Event | Literal["new"] | None = None

    def href(self, **changes: Any) -> str:
        """
        This calendar with something changed. Every link on it is one of
        these.
        """
        return self._link(replace(self.state, **changes))

    def _params(self, state: CalendarState) -> dict[str, str]:
        """
        The parts of state that differ from the defaults. Today's week in
        the declared view is the page with no query at all.
        """
        declared = self.declaration
        asked = {
            _VIEW: state.view if state.view != declared.view else "",
            _DATE: state.date.isoformat() if state.date != self.today else "",
            _QUERY: state.query,
            _HIDE: ",".join(state.hidden),
            _START: state.week_start if state.week_start != declared.week_start else "",
            _WEEKDAYS: "1" if state.weekdays else "",
        }
        return {name: value for name, value in asked.items() if value}
