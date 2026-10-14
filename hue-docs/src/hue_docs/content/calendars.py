from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from hue.calendar import CalendarState, DayAction, build_calendar_state
from hue.context import HueContext
from hue.types.core import ComponentType
from hue.ui import Alert, Calendar, Event

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage


class _Request:
    """
    Just enough of a request to carry a query string.
    """

    def __init__(self, **params: str) -> None:
        self.params = params


class _Router:
    """
    A stand-in, because a docs page has no view to hang routes on. A real
    declaration is handed the view's own Router and registers its day route
    on it; here it is registered on nothing and never called.
    """

    def fragment_get(self, path: str, *, name: str | None = None) -> Any:
        return lambda view_func: view_func

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {name: [value] for name, value in request.params.items()}

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        # Django reverses these against the URLconf. Here they are spelled
        # out, since there is nothing to reverse against.
        return "/calendars/" if name == "index" else f"/calendars/{name}/"

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
        # A list has no event loop to keep off.
        return func(*args)


def _events(request: Any, shown: CalendarState) -> list[Event]:
    """
    The one part of a calendar that is not fixed: which events answer it.
    """
    month = shown.month
    return [
        Event("Design review", datetime(month.year, month.month, 14, 9, 30), href="#"),
        Event(
            "Offsite",
            month.replace(day=19),
            month.replace(day=21),
            variant="info",
            href="#",
        ),
        Event("Release", month.replace(day=27), variant="success"),
    ]


def _open(request: Any, day: date) -> ComponentType:
    """A handler, which is all a day action ever is."""
    return pr.p(f"New event on {day.isoformat()}")


def _calendar(key: str) -> Any:
    """
    The declaration, once per specimen: two calendars on one page need two
    keys, because the key is the id every part of a calendar is named from.
    """
    return build_calendar_state(
        _Router(), key=key, events=_events, day=DayAction("New event", _open)
    )


def _specimen(key: str, **params: str) -> ComponentType:
    """
    The calendar drawn the way a view draws it. Each specimen is a request of
    its own, so each is wrapped in a context carrying it.
    """
    return pr.section(
        HueContext(
            Calendar.from_state(_calendar(key)),
            request=_Request(
                **{f"{key}-{name}": value for name, value in params.items()}
            ),
            csrf_token="",
        )
    )


_DECLARATION = """def events_for(
    request: HttpRequest, shown: CalendarState
) -> list[Event]:
    \"\"\"The one part of a calendar that is not fixed: which events answer it.\"\"\"
    booked = Booking.objects.filter(
        starts__date__lte=shown.last, ends__date__gte=shown.first
    )
    return [
        Event(b.title, b.starts, b.ends, href=b.get_absolute_url())
        for b in booked
    ]


def new_booking(request: HttpRequest, day: date) -> Dialog:
    return Dialog().open().title(f"New booking, {day:%d %B}").content(
        html.form(TextInput().name("title").label("Title"))
    )


class BookingsView(HueView):
    router = Router[HttpRequest]()

    bookings = build_calendar_state(
        router,
        key="bookings",
        events=events_for,
        day=DayAction("New booking", new_booking),
    )

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ) -> Page:
        return Page(title="Bookings", body=Calendar.from_state(self.bookings))"""


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Calendars"),
        pr.lead(
            "A month of events whose month lives in the URL. You declare it once "
            "on a view: the function that finds its events, and what clicking a "
            "day does. The calendar draws its own month links and day buttons, "
            "and the month links are plain links."
        ),
        pr.h2("The declaration"),
        pr.code(_DECLARATION),
        pr.p(
            "The view draws the calendar with Calendar.from_state(self.bookings). "
            "Chain week_start() after it to start the week on another day."
        ),
        pr.h2("Events come from one function"),
        pr.p(
            "events is the only part of a calendar that changes with each "
            "request, so it is the only part that is a function. It receives the "
            "request and a CalendarState, and returns every Event between "
            "shown.first and shown.last: the first and last day on the page, "
            "including the days of the months either side that fill the first "
            "and last week. Filter on those two and nothing else."
        ),
        pr.p(
            "An Event is a title and when it is. A date is a whole day, and ends "
            "is the last day it covers, so an offsite from Monday to Wednesday "
            "ends on Wednesday. A datetime is a moment, and ends is when it is "
            "over, so a party that ends at midnight does not spill onto the next "
            "day. An aware datetime is placed on the reader's day under USE_TZ. "
            "href makes the event a link, and variant colours it in the shared "
            "tones."
        ),
        pr.code(
            'Event("Offsite", date(2026, 10, 19), date(2026, 10, 21), variant="info")\n'
            'Event("Standup", datetime(2026, 10, 14, 9, 30), href="/events/12/")'
        ),
        pr.h2("The URL is the state"),
        pr.p(
            "The month is named under the calendar's key, and everything else in "
            "the query rides along on every link, so two calendars on one page "
            "keep separate months in one URL."
        ),
        pr.code("/bookings/?bookings-month=2026-10", language="bash"),
        pr.p(
            "Previous and Next point at the page with the month changed. Today "
            "drops the parameter, so a bookmark of it stays on today. Alpine "
            "AJAX fetches the page and swaps the calendar in place, keeping focus "
            "on the link you pressed, and a live region outside the calendar "
            "announces the new month. With JavaScript off the links still work, "
            "as full page loads."
        ),
        pr.p(
            "A month typed into the URL by hand that is not one, such as 2026-13, "
            "shows this month rather than an error page."
        ),
        pr.h2("Opening a day"),
        pr.p(
            "A DayAction makes every day's number a button named after the "
            "action and the day, such as New booking, Wednesday 14 October 2026. "
            "Pressing it fetches the handler's fragment and drops it into a slot "
            "under the calendar, so a Dialog().open() returned from the handler "
            "appears over the month, which stays as it was underneath. The route "
            "is a GET, because opening a day reads nothing; whatever the dialog "
            "holds posts to your own routes."
        ),
        pr.code(
            "# GET /bookings/bookings/day/?day=2026-10-14\n"
            'DayAction("New booking", new_booking)'
        ),
        pr.p(
            "A day that is not one is a 404, and the route answers only AJAX, so "
            "the day buttons do nothing without JavaScript."
        ),
        pr.h2("What the reader sees and hears"),
        pr.p(
            "The calendar is a table with a column per weekday, not an ARIA grid. "
            "Every event is a link to read and follow, and browse-mode table "
            "navigation already announces the column header with each cell. "
            "The caption names the month. Each column header abbreviates the day "
            "and carries the full name in abbr. A day outside the month says "
            "which month it is in, and today carries aria-current."
        ),
        pr.p(
            "The names of the months and days come from Formats, which "
            "hue-django fills from Django's own translations under the request's "
            "language. The time on a timed event follows HUE_TIME_FORMAT."
        ),
        pr.h2("Two examples"),
        pr.p(
            "Both calendars below are the declaration from the top of the page, "
            "bound to different requests, over a fixed list of events."
        ),
        _specimen("bookings", month="2026-10"),
        pr.p("The second starts its week on Sunday and shows the month before."),
        pr.section(
            HueContext(
                Calendar.from_state(_calendar("rooms")).week_start("sunday"),
                request=_Request(**{"rooms-month": "2026-09"}),
                csrf_token="",
            )
        ),
        pr.h2("Assumptions"),
        pr.bullets(
            [
                pr.p(
                    "Today is the reader's today: now in the current timezone "
                    "under USE_TZ, the server's otherwise."
                ),
                pr.p(
                    "events and the day handler are plain functions, run in a "
                    "thread rather than on the event loop, because Django raises "
                    "SynchronousOnlyOperation for a query made on the loop."
                ),
                pr.p(
                    "Each month loads the page, so whatever else index computes "
                    "runs on every step as well."
                ),
            ]
        ),
        Alert()
        .variant("warning")
        .title("What is not done yet")
        .content(
            pr.bullets(
                [
                    pr.p(
                        "A day's events are listed in full; a day with many of "
                        "them grows rather than folding into a count."
                    ),
                    pr.p(
                        "A multi-day event is one chip per day, squared off "
                        "where it continues, without a lane kept across the week."
                    ),
                    pr.p("There is no week, day or agenda view yet."),
                ]
            )
        ),
    )


PAGE = ProsePage(
    slug="calendars",
    title="Calendars",
    nav_label="Calendars",
    group="Guides",
    order=6,
    build=_build,
)
