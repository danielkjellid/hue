"""
A calendar that knows where its own state lives.

Calendar on its own only renders a month. A declaration owns which month
that is, reads it from the page's URL, fetches the events through one
function, and registers the route a day's click opens:

    def events_for(request: HttpRequest, shown: CalendarState) -> list[Event]:
        booked = Booking.objects.filter(
            starts__date__lte=shown.last, ends__date__gte=shown.first
        )
        return [Event(b.title, b.starts, b.ends, href=b.url) for b in booked]


    def new_booking(request: HttpRequest, day: date) -> Dialog:
        return Dialog().open().title(f"New booking on {day}")


    class BookingsView(HueView):
        router = Router[HttpRequest]()

        bookings = build_calendar_state(
            router,
            key="bookings",
            events=events_for,
            day=DayAction("New booking", new_booking),
        )

        async def index(self, request, context) -> Page:
            return Page(title="Bookings", body=Calendar.from_state(self.bookings))

The URL is /bookings/?bookings-month=2026-10. Previous, Today and Next are
links to the page with the month changed and every other query pair kept,
and today's link drops the parameter so a bookmark of it stays on today.
With a day action, every day's number is a button that fetches the
handler's fragment and drops it beside the calendar.

events() and the day handler run off the event loop, through the router,
because both usually use the ORM and the ORM refuses to run on the loop.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from http import HTTPStatus
from typing import Any, Protocol
from urllib.parse import urlencode

from htmy import Context, Fragment, html

from hue.context import HueContext
from hue.formats import Formats
from hue.js import ajax
from hue.router import PAGE_ROUTE, HueResponse
from hue.types.core import Component, ComponentType
from hue.ui.molecules._days import (
    FIRST_YEAR,
    LAST_YEAR,
    Weekday,
    first_of,
    week_of,
    weeks,
)
from hue.ui.molecules.calendar import Calendar, Event
from hue.ui.navigation import SYNC

__all__ = ["CalendarState", "DayAction", "build_calendar_state"]

_MONTH = "month"
_DAY = "day"
# YYYY-MM and nothing else; fromisoformat would also take 2026-10-14 and 202610.
_MONTH_PATTERN = re.compile(r"(\d{4})-(\d{2})")
_DAY_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class _Routes(Protocol):
    """
    What a calendar needs from its router. Its own and smaller than the
    table's: it reads the query and reverses URLs, and registers one GET
    fragment when it has a day action.
    """

    def fragment_get(
        self, path: str, *, name: str | None = None
    ) -> Callable[[Any], Any]: ...
    def _get_query_values(self, request: Any) -> dict[str, list[str]]: ...
    def _url_for(self, request: Any, name: str, **params: Any) -> str: ...
    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R: ...


@dataclass(frozen=True, slots=True)
class CalendarState:
    """
    What the URL asked for: the month shown, and so the days shown.

    events() reads first and last, the first and last day on the page
    including the days of the months either side that fill the first and
    last week. That is the whole contract: a week view later shows a
    different stretch of days, and an events() that filters on first and
    last answers it unchanged.
    """

    month: date
    week_start: Weekday = "monday"

    def __post_init__(self) -> None:
        if self.month.day != 1:
            raise ValueError("CalendarState.month is the first of the month.")

    @property
    def first(self) -> date:
        return week_of(self.month, self.week_start)[0]

    @property
    def last(self) -> date:
        return weeks(self.month, self.week_start)[-1][-1]


type EventsFor = Callable[[Any, CalendarState], Iterable[Event]]
type DayHandler = Callable[[Any, date], ComponentType]


@dataclass(frozen=True, slots=True)
class DayAction:
    """
    What clicking a day does, and what the day's button is called.

    The handler receives the request and the day and returns what to show,
    usually a Dialog().open() holding a form. It lands beside the calendar,
    so the calendar stays as it was underneath it.

        DayAction("New event", new_event_dialog)
    """

    label: str
    handler: DayHandler


class _Declaration:
    """
    A calendar declared once, at class scope, and the route its days open.

    key names the month's parameter in the URL (f"{key}-month") and the
    element every month swaps into, so it is unique on the page. events is
    the only part that is not fixed: it receives the request and the state
    and returns the events between first and last. day, when given, makes
    every day a button that fetches the handler's fragment.
    """

    def __init__(
        self,
        router: _Routes,
        *,
        key: str,
        events: EventsFor,
        day: DayAction | None = None,
    ) -> None:
        self.key = key
        self.events = events
        self.day = day
        self._router = router
        # One spelling of the route's name, used to register it and to find
        # it again. Two calendars on one view would otherwise collide.
        self._day_route = f"{key}_day"
        self._check()
        self._register()

    def _check(self) -> None:
        if not self.key:
            raise ValueError(
                "A calendar needs a key: it is the id every month swaps into "
                "and the prefix of its parameter in the URL."
            )
        if self.day is not None and not self.day.label.strip():
            raise ValueError(
                f"{self.key} has a day action with a blank label, and the "
                f"label is what every day's button is called."
            )

    def param(self) -> str:
        """
        What the month is called in the URL, under the key, so two calendars
        on one page keep their own.
        """
        return f"{self.key}-{_MONTH}"

    async def draw(self, calendar: Calendar, context: Context) -> Component:
        """
        The calendar bound to the request this page is rendered for, and the
        live region that says which month it is now.
        """
        request = HueContext.from_context(context).request
        formats = Formats.from_context(context)
        today = _today(formats)
        month, others = self._read(self._router._get_query_values(request), today)
        shown = CalendarState(month, calendar._props["week_start"])
        events = await self._router._run_sync(self._fetch, request, shown)
        page = self._router._url_for(request, PAGE_ROUTE)

        def href(target: date) -> str:
            # Today's month drops the parameter: it is the default, and a
            # bookmark of the Today link stays on today.
            own = (
                [] if target == first_of(today) else [(self.param(), f"{target:%Y-%m}")]
            )
            pairs = [*others, *own]
            return page + (f"?{urlencode(pairs)}" if pairs else "")

        calendar.id(self.key).month(month).today(today).events(events).href(href)
        if self.day is not None:
            url = self._router._url_for(request, self._day_route)
            calendar._day_action(
                self.day.label,
                lambda day: ajax(
                    f"{url}?{_DAY}={day.isoformat()}", target=f"{self.key}-day"
                ),
            )
        # Outside the swapped calendar, refreshed by SYNC, so its text
        # changes in place and is announced, as the table's summary is.
        status = html.p(
            formats.month(month),
            id=f"{self.key}-status",
            role="status",
            class_="sr-only",
            **SYNC,
        )
        return Fragment(calendar, status)

    def _read(
        self, values: Mapping[str, list[str]], today: date
    ) -> tuple[date, tuple[tuple[str, str], ...]]:
        """
        The month asked for and every other pair in the query, which the
        links carry back unchanged.

        Clamped where it enters: anything but YYYY-MM with a month from 01 to
        12 and a year whose grid fits in date is today's month, never an
        error page, because anyone can type into a query string.
        """
        raw = values.get(self.param())
        found = _MONTH_PATTERN.fullmatch(raw[-1] if raw else "")
        month = first_of(today)
        if found:
            year, number = int(found[1]), int(found[2])
            if 1 <= number <= 12 and FIRST_YEAR <= year <= LAST_YEAR:
                month = date(year, number, 1)
        others = tuple(
            (name, value)
            for name, each in values.items()
            if name != self.param()
            for value in each
        )
        return month, others

    def _fetch(self, request: Any, shown: CalendarState) -> list[Event]:
        """
        events(), run off the event loop by the router, materialised there
        so a lazy queryset is walked off the loop too. Anything that is not
        an Event is refused with the declaration's key in the message.
        """
        found = list(self.events(request, shown))
        for stranger in found:
            if not isinstance(stranger, Event):
                raise TypeError(
                    f"{self.key}: events() returned {stranger!r}, which is not "
                    f"an Event. Build one per row: Event(title, starts, ends)."
                )
        return found

    def _register(self) -> None:
        """
        The day's route, when there is a day action. Reading needs no route:
        a month is the page itself with ?{key}-month=YYYY-MM.

        GET, because opening a day reads and writes nothing; whatever the
        fragment holds posts to the app's own routes. fragment_get answers
        only an AJAX request, so the day buttons do nothing without
        JavaScript, while the months still work as plain links.
        """
        if self.day is None:
            return
        handler = self.day.handler

        async def open_day(view: Any, request: Any, context: Any) -> Any:
            # Clamped where it enters, as the month is: a malformed day is a
            # 404, the answer for a URL that names nothing.
            raw = self._router._get_query_values(request).get(_DAY)
            asked = raw[-1] if raw else ""
            try:
                if not _DAY_PATTERN.fullmatch(asked):
                    raise ValueError(asked)
                when = date.fromisoformat(asked)
            except ValueError:
                return HueResponse(
                    component=html.p(f"{self.key} has no day called {asked!r}."),
                    status_code=HTTPStatus.NOT_FOUND,
                )
            shown = await self._router._run_sync(handler, request, when)
            return HueResponse(component=shown, target=f"{self.key}-day")

        self._router.fragment_get(f"{self.key}/{_DAY}/", name=self._day_route)(open_day)


# What a view calls, at class scope, to declare a calendar.
build_calendar_state = _Declaration


def _today(formats: Formats) -> date:
    """
    The reader's today: now in their timezone when the framework says how
    to get there, the server's otherwise. Read through _now so a test can
    hold the clock still.
    """
    return formats.moment(_now()).date() if formats.localize else date.today()


def _now() -> datetime:
    return datetime.now(UTC)
