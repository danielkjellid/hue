from __future__ import annotations

from datetime import date, datetime
from typing import cast, get_args

from fastapi import HTTPException, Request
from hue import html, palette
from hue.context import HueContext
from hue.js import ajax, unsafe
from hue.types.core import ComponentType
from hue.ui import Alert, Button, Calendar, DatePicker, Empty, Event, Table
from hue.ui.molecules.calendar import CalendarView
from hue_fastapi import HueFragmentsView, Page, Router

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel
from hue_docs.pages.components import _calendar_demo


class CalendarDemo(HueFragmentsView):
    """
    The views and days behind the live example. A page route rather than a
    fragment, so a reload of the URL the swap pushed still answers with the
    whole page.
    """

    router = Router[Request]()

    @router.page("{view}/{day}/")
    async def calendar_page(
        self, request: Request, context: HueContext[Request], view: str, day: str
    ) -> ComponentType:
        if view not in get_args(CalendarView.__value__):
            raise HTTPException(status_code=404)
        try:
            shown = date.fromisoformat(day)
        except ValueError:
            raise HTTPException(status_code=404) from None
        return Page(
            title="Calendar",
            body=html.div(october().view(cast(CalendarView, view)).date(shown)).class_(
                "p-4"
            ),
        )


# Live


def october() -> Calendar:
    return (
        Calendar()
        .id("calendar-demo")
        .date(date(2026, 10, 14))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"/demos/calendar/{view}/{day}/")
        .events(
            [
                Event(
                    "Standup",
                    datetime(2026, 10, 12, 9),
                    datetime(2026, 10, 12, 9, 15),
                    repeat="weekly",
                    location="Huddle room",
                    color=palette.gray,
                ),
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                    location="Room 3B",
                    notes="Walk the range states and the contrast audit.",
                ),
                Event(
                    "Contrast audit",
                    datetime(2026, 10, 15, 10),
                    datetime(2026, 10, 15, 12),
                    color=palette.teal,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=palette.orange,
                ),
                Event(
                    "Release freeze",
                    date(2026, 10, 16),
                    date(2026, 10, 17),
                    color=palette.purple,
                ),
                Event(
                    "Deploy window",
                    datetime(2026, 10, 16, 22),
                    datetime(2026, 10, 17, 2),
                    color=palette.teal,
                ),
                Event(
                    "Time off",
                    date(2026, 10, 26),
                    date(2026, 10, 30),
                    color=palette.yellow,
                ),
            ]
        )
    )


# Views


def day() -> Calendar:
    return (
        Calendar()
        .view("day")
        .date(date(2026, 10, 15))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Contrast audit",
                    datetime(2026, 10, 15, 10),
                    datetime(2026, 10, 15, 12),
                    color=palette.teal,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=palette.orange,
                ),
                Event(
                    "Token naming",
                    datetime(2026, 10, 15, 11, 30),
                    datetime(2026, 10, 15, 12, 15),
                ),
                Event(
                    "Dentist",
                    datetime(2026, 10, 15, 15),
                    datetime(2026, 10, 15, 15, 45),
                    color=palette.yellow,
                ),
            ]
        )
    )


def week() -> Calendar:
    return (
        Calendar()
        .view("week")
        .date(date(2026, 10, 14))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Standup",
                    datetime(2026, 10, 12, 9),
                    datetime(2026, 10, 12, 9, 15),
                    repeat="weekly",
                    color=palette.gray,
                ),
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event(
                    "Contrast audit",
                    datetime(2026, 10, 15, 10),
                    datetime(2026, 10, 15, 12),
                    color=palette.teal,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=palette.orange,
                ),
                Event(
                    "Release freeze",
                    date(2026, 10, 16),
                    date(2026, 10, 17),
                    color=palette.purple,
                ),
                Event(
                    "Deploy window",
                    datetime(2026, 10, 16, 22),
                    datetime(2026, 10, 17, 2),
                    color=palette.teal,
                ),
            ]
        )
    )


def month() -> Calendar:
    return (
        Calendar()
        .view("month")
        .date(date(2026, 10, 1))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Quarterly planning",
                    date(2026, 10, 8),
                    date(2026, 10, 9),
                    color=palette.purple,
                ),
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event("Release freeze", date(2026, 10, 15), color=palette.purple),
                Event(
                    "Contrast audit",
                    datetime(2026, 10, 15, 10),
                    datetime(2026, 10, 15, 12),
                    color=palette.teal,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=palette.orange,
                ),
                Event(
                    "Dentist",
                    datetime(2026, 10, 15, 15),
                    datetime(2026, 10, 15, 15, 45),
                    color=palette.yellow,
                ),
                Event(
                    "Time off",
                    date(2026, 10, 26),
                    date(2026, 10, 30),
                    color=palette.yellow,
                ),
            ]
        )
    )


def year() -> Calendar:
    return (
        Calendar()
        .view("year")
        .date(date(2026, 1, 1))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event("Kickoff", date(2026, 1, 12)),
                Event(
                    "Offsite",
                    date(2026, 3, 18),
                    date(2026, 3, 20),
                    color=palette.purple,
                ),
                Event(
                    "Summer break",
                    date(2026, 7, 6),
                    date(2026, 7, 24),
                    color=palette.yellow,
                ),
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event("Year end", date(2026, 12, 18), color=palette.teal),
            ]
        )
    )


def agenda() -> Calendar:
    return (
        Calendar()
        .view("agenda")
        .date(date(2026, 10, 12))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Standup",
                    datetime(2026, 10, 12, 9),
                    datetime(2026, 10, 12, 9, 15),
                    repeat="weekly",
                    location="Huddle room",
                    color=palette.gray,
                ),
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                    location="Room 3B",
                ),
                Event(
                    "Release freeze",
                    date(2026, 10, 16),
                    date(2026, 10, 17),
                    color=palette.purple,
                ),
                Event(
                    "Time off",
                    date(2026, 10, 26),
                    date(2026, 10, 28),
                    color=palette.yellow,
                ),
            ]
        )
    )


# Anatomy


def event_details() -> Calendar:
    return (
        Calendar()
        .view("day")
        .date(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .actions(
            lambda event: [
                Button().variant("outline").size("sm").content("Edit"),
                Button().variant("ghost").size("sm").content("Duplicate"),
            ]
        )
        .events(
            [
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 9),
                    datetime(2026, 10, 14, 10, 30),
                    location="Room 3B",
                    notes="Walk the range states and the contrast audit.",
                    repeat="weekly",
                    href="#design-review",
                ),
            ]
        )
    )


def without_links() -> Calendar:
    return (
        Calendar()
        .view("month")
        .date(date(2026, 10, 1))
        .today(date(2026, 10, 14))
        .events(
            [
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event(
                    "Time off",
                    date(2026, 10, 26),
                    date(2026, 10, 30),
                    color=palette.yellow,
                ),
            ]
        )
    )


# Week


def sunday_first() -> Calendar:
    return (
        Calendar()
        .view("month")
        .date(date(2026, 10, 1))
        .today(date(2026, 10, 14))
        .week_start("sunday")
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Time off",
                    date(2026, 10, 26),
                    date(2026, 10, 30),
                    color=palette.yellow,
                )
            ]
        )
    )


def weekdays_only() -> Calendar:
    return (
        Calendar()
        .view("week")
        .date(date(2026, 10, 14))
        .today(date(2026, 10, 14))
        .weekdays()
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event("Release freeze", date(2026, 10, 16), color=palette.purple),
            ]
        )
    )


# Empty


def nothing_scheduled() -> Calendar:
    return (
        Calendar()
        .view("agenda")
        .date(date(2026, 12, 1))
        .href(lambda day, view: f"#{view}/{day}")
    )


# Width


def narrow_month() -> Calendar:
    return (
        Calendar()
        .view("month")
        .date(date(2026, 10, 1))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event("Release freeze", date(2026, 10, 15), color=palette.purple),
                Event(
                    "Time off",
                    date(2026, 10, 26),
                    date(2026, 10, 30),
                    color=palette.yellow,
                ),
            ]
        )
    )


def narrow_week() -> Calendar:
    return (
        Calendar()
        .view("week")
        .date(date(2026, 10, 14))
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{view}/{day}")
        .events(
            [
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event("Release freeze", date(2026, 10, 16), color=palette.purple),
            ]
        )
    )


# Declared


# The declared calendar loads from ScheduleView in _calendar_demo, and the
# panel shows that module as its code, which is the part worth copying. It
# asks for October 2026, where the demo's events are; without a date the
# calendar opens on today.
def declared_calendar() -> ComponentType:
    return (
        html.div(
            Empty()
            .variant("danger")
            .compact()
            .title("Could not load the demo")
            .description("The demo route did not answer. Reload to try again.")
            .x_show(unsafe("failed"))
            .x_cloak(),
        )
        .id("schedule-demo")
        .class_("w-full")
        .x_data("{ failed: false }")
        .x_on("ajax:error", unsafe("failed = true"))
        .x_init(
            unsafe(
                str(
                    ajax(
                        "/demos/calendar/?schedule-date=2026-10-14",
                        target="schedule-demo",
                    )
                )
                + ".catch(() => (failed = true))"
            )
        )
    )


_DECLARATION = """from hue import palette
from hue.calendar import CalendarState, Layer, build_calendar_state
from hue.ui import Calendar, Event


def events_for(request: HttpRequest, asked: CalendarState) -> list[Event]:
    found = Entry.objects.filter(
        starts__date__lte=asked.last,
        ends__date__gte=asked.first,
        layer__in=asked.layers,
    )
    if asked.query:
        found = found.filter(title__icontains=asked.query)
    return [entry.event() for entry in found]


def save_entry(request: HttpRequest, event: Event) -> int:
    entry, _ = Entry.objects.update_or_create(pk=event.id, defaults=fields_of(event))
    return entry.pk


def delete_entry(request: HttpRequest, id: str) -> None:
    Entry.objects.filter(pk=id).delete()


class EventsView(HueView):
    router = Router[HttpRequest]()

    events = build_calendar_state(
        router,
        key="events",
        events=events_for,
        layers=[
            Layer("product", "Product"),
            Layer("eng", "Engineering"),
            Layer("time-off", "Time off", color=palette.yellow),
        ],
        save=save_entry,
        delete=delete_entry,
        repeats={"weekly": "Every week", "monthly": "Every month"},
        search="Search events",
    )

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ) -> Page:
        return Page(title="Events", body=Calendar.from_state(self.events))"""


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Calendar` draws the events it is handed, the way a `Table` draws "
            "its rows. `date()` is required: it is the day the view is around, "
            "and a `Calendar` without one raises a `ValueError`. `view()` picks "
            'the view and defaults to `"week"`. `today()` marks a day as today. '
            "The `Calendar` never reads the clock for it, so a page renders the "
            "same for every reader."
        ),
        pr.code(
            "from datetime import date, datetime\n\n"
            "Calendar()"
            '.view("month")'
            ".date(date(2026, 10, 1))"
            ".today(date(2026, 10, 14))"
            ".events(events)"
        ),
        pr.h2("Calendar events"),
        pr.p(
            "Each `Event` is a title, a start and an optional end. A `date` "
            "makes it a whole-day event, and its end is the last day it covers, "
            "so an offsite from Monday to Wednesday ends on Wednesday. A "
            "`datetime` makes it a timed event, and its end is the moment it is "
            "over. Without an end it covers one day, or one moment."
        ),
        pr.code(
            "Event(\n"
            '    "Offsite",\n'
            "    date(2026, 10, 19),\n"
            "    date(2026, 10, 21),\n"
            "    color=palette.purple,\n"
            ")\n"
            "Event(\n"
            '    "Standup",\n'
            "    datetime(2026, 10, 14, 9, 30),\n"
            "    datetime(2026, 10, 14, 9, 45),\n"
            '    location="Huddle room",\n'
            '    repeat="weekly",\n'
            ")"
        ),
        pr.bullets(
            [
                "`color` is a `hue.palette` preset, such as `palette.purple`, or a "
                "`Color` of your own. Without one an event takes the accent, or "
                "its layer's colour in a declared `Calendar`.",
                "`location` and `notes` show in the event's popover.",
                "`repeat` is the key of the rule the event repeats by, and any key "
                "draws a repeat mark. The `Calendar` does not expand a rule into "
                "occurrences: pass each occurrence as its own `Event`.",
                "`layer` names the layer the event belongs to in a declared "
                "`Calendar`.",
                "`href` adds an Open link to the popover.",
                "`id` names the event for the app's own routes.",
            ]
        ),
        pr.p(
            "An `Event` raises a `ValueError` when its title is empty, when it "
            "mixes a `date` with a `datetime` "
            "or a naive `datetime` with an aware one, and when it ends before it "
            "starts. An aware `datetime` is moved into the reader's time by the "
            "`localize` of the `Formats` in the context, when there is one, "
            "before the event is put on a day."
        ),
        pr.h2("Calendar views"),
        pr.bullets(
            [
                '`"day"` and `"week"` are a time grid of 48 pixels an hour, '
                "opened at 07:30 and scrolled inside a box. All-day events sit "
                "in a row above the hours. Timed events that overlap share the "
                "column's width side by side, and one that runs past midnight is "
                "split at midnight and squared off where it continues.",
                '`"month"` is a table of six weeks. A day shows up to three '
                "events. With more, it shows two and a `+N more` button that "
                "opens the rest in a popover.",
                '`"year"` is twelve small months. A day with events has a dot '
                "under its number.",
                '`"agenda"` lists the days with something on in the 30 days '
                "from `date()`. A whole-day event over several days says which "
                "day of how many it is, such as Day 2 of 3.",
            ]
        ),
        pr.p(
            "`week_start()` sets the first column of the week and the month, "
            'and defaults to `"monday"`. `weekdays()` leaves Saturday and Sunday '
            "out of the week and month views."
        ),
        pr.h2("Navigating a Calendar"),
        pr.p(
            "`href()` takes a function from a day and a view to the URL of that "
            "view on that day. With it, the `Calendar` shows Previous, Today and "
            "Next, a switcher between the views, and makes every day's number a "
            "link to its day view. Without it the `Calendar` is a picture of its "
            "events: those controls are left out. The event popovers work either "
            "way."
        ),
        pr.code(
            "Calendar()"
            '.id("schedule")'
            ".date(day)"
            ".view(view)"
            '.href(lambda day, view: f"/schedule/{view}/{day}/")'
            ".events(events)"
        ),
        pr.p(
            "Previous and Next move by one day, week, month, year or 30 days, "
            "after the view. A month step keeps the day of the month, or takes "
            "the last day of a shorter month. Today appears when `today()` is set "
            "and leads to that day in the current view."
        ),
        pr.p(
            "Give the `Calendar` an `id()` and its links swap the calendar in "
            "place and push the URL they lead to. "
            "The route behind `href()` returns a page with a `Calendar` of the "
            "same id. Without an id the links are plain navigation."
        ),
        pr.h2("Actions on a Calendar event"),
        pr.p(
            "`actions()` takes a function from an `Event` to the buttons at the "
            "foot of its popover, such as Edit and Delete."
        ),
        pr.code(
            "Calendar().date(day).actions(\n"
            "    lambda event: [\n"
            '        Button().variant("outline").size("sm").content("Edit"),\n'
            "    ]\n"
            ")"
        ),
        pr.p(
            "Day and month names and the time format come from the `Formats` in "
            "the context, so a 12-hour clock is a `Formats` setting rather than a "
            "`Calendar` option."
        ),
        pr.h2("Declare a Calendar on a view"),
        pr.p(
            "A `Calendar` declared once on a `HueView` with "
            "`build_calendar_state()` keeps its state in the URL, fetches its "
            "events through one function, and draws a sidebar, a search box, "
            "view options and an event dialog around itself. The declaration "
            "names the function that finds the events, the layers a reader can "
            "show and hide, and what saves and deletes an event. "
            "`Calendar.from_state()` draws it, bound to the request in the "
            "context, so the view passes nothing else."
        ),
        pr.p(
            "The example below is written for `hue-django`, with a Django "
            "queryset behind `events`. With `hue-fastapi`, `HueView`, `Router` "
            "and `Page` come from `hue_fastapi`, and the request is Starlette's "
            "`Request`."
        ),
        pr.code(_DECLARATION),
        pr.p(
            "The Declared panel at the top of this page runs a declaration like "
            "this one, written for `hue-fastapi` over a list of events. Its Code "
            "button shows the whole view."
        ),
        pr.bullets(
            [
                "`key` names the route, every parameter in the URL and every id, "
                "so it has to be unique on the page. An empty key raises a "
                "`ValueError`.",
                "`layers` is a list of `Layer`. Two layers with one key raise, "
                "and so does a key with a comma in it.",
                "`save` and `delete` make the `Calendar` editable, and a `save` "
                "also lets the reader drag its events. Without either it "
                "registers no route.",
                "`repeats` maps your own repeat keys to the labels the dialog "
                "offers. It needs a `save`, and raises without one.",
                "`search` is the label and placeholder of the search box, which "
                "only exists when it is given.",
                '`view` and `week_start` are the defaults, `"week"` and '
                '`"monday"` unless you set them.',
            ]
        ),
        pr.p(
            "The declaration registers its route on the view's router when it "
            "is made, and the route has to exist before the URLs are built: "
            "Django builds its URL table when the URLconf is imported, and "
            "FastAPI's `include_router()` copies a router's routes when it is "
            "called. So a `Calendar` is declared once at class scope, as a "
            "`DataTable` is, and bound to each request when "
            "`Calendar.from_state()` renders it."
        ),
        pr.h3("Calendar events come from one function"),
        pr.p(
            "`events` is the only part of a declared `Calendar` that changes "
            "with each request, so it is the only part that is a function. It "
            "receives the request and a `CalendarState`, and returns every "
            "`Event` between `asked.first` and `asked.last` that matches "
            "`asked.query` and belongs to one of `asked.layers`. `first` and "
            "`last` cover the days the view shows and the six weeks of the month "
            "around `asked.date`, which the sidebar's picker marks. Anything "
            "other than an `Event` in what it returns raises a `TypeError`."
        ),
        pr.p(
            "`CalendarState` also holds `view`, `hidden`, `week_start` and "
            "`weekdays`, which say how the view is drawn, and `days`, the first "
            "and last day the view itself shows."
        ),
        pr.p(
            "An event without a `color` of its own takes its layer's. `repeat` "
            "is your key for the rule an event repeats by: the `Calendar` draws "
            "the repeat mark and the dialog shows the key's label, and expanding "
            "the rule into occurrences is the job of `events`. With a `save`, "
            "every occurrence of a repeating event also needs `series_starts`, "
            "as ",
            pr.link(
                "Moving a repeating Calendar event",
                "#moving-a-repeating-calendar-event",
            ),
            " explains.",
        ),
        pr.p(
            "A sync `events` function runs in a thread, off the event loop. In "
            "`hue-django` that is because the ORM refuses a query made on the "
            "loop, and in `hue-fastapi` it keeps a blocking call from holding "
            "up other requests. An async `events` is awaited on the loop "
            "instead."
        ),
        pr.h2("A declared Calendar keeps its state in the URL"),
        pr.p(
            "The view, the day it is around, the search, the hidden layers, the "
            "day the week starts on and whether the weekend shows are all in the "
            "address bar, each named under the calendar's key. A part at its "
            "default is left out, and the default day is today, so the link "
            "Today leads to in the declared view is the page with no query at all."
        ),
        pr.code(
            "/events/?events-view=month&events-date=2026-10-14&events-hide=personal",
            language="bash",
        ),
        pr.p(
            "Previous, Today, Next, the view switcher and every day are links "
            "to the page with one part changed. The search, the sidebar's picker "
            "and layers and the view options are `GET` forms to the same page. "
            "Alpine AJAX fetches the page and swaps the calendar in place, and the "
            "address bar follows, so it reloads to the same calendar and can be "
            "sent to someone. With JavaScript off, the "
            "links and the search still work as full page loads."
        ),
        pr.p(
            "Each move loads the whole page, so whatever else `index` computes "
            "runs on every step too."
        ),
        pr.p(
            "A value in the URL that is not one, such as a view nobody has or a "
            "date that is not `YYYY-MM-DD`, falls back to the default instead of "
            "an error page, and a hidden layer nobody declared is dropped. Two "
            "calendars on one page keep separate state in one URL, and each "
            "carries the other's parameters through unchanged."
        ),
        pr.h2("Calendar layers, search and view options"),
        pr.p(
            "Each `Layer` is one of the calendars a reader can show or hide: a "
            "key, a name and a colour. A `Layer` without a `color` takes the "
            "next `hue.palette` preset by its place in the list, so the first "
            "is the accent and the second teal. Past six layers, each needs a "
            "colour of its own. The sidebar lists the "
            "layers under Calendars as checkboxes. Unticking one adds its key to "
            "`{key}-hide`, so the URL carries the hidden layers and a layer added "
            "later shows up for someone following an old link. It is called a "
            "layer because `Calendar` is the component."
        ),
        pr.p(
            "`search` gives the `Calendar` a search box, a `GET` form that "
            "submits 300 milliseconds after the last keystroke. Enter submits it "
            "at once. Escape empties it, and leaves the key alone while the box "
            "is already empty, so Escape still reaches a dialog the calendar sits "
            "in. Beside the box, a count says how many events in the view's days "
            'match, such as 2 events match "re". Responses leave the box alone, '
            "so the caret stays in it while the events change."
        ),
        pr.p(
            "The view options sit behind one button: which day the week starts "
            "on, and Weekdays only, which leaves the weekend out. Each change "
            "submits at once."
        ),
        pr.p(
            "The sidebar also holds New event, when there is a `save`, and a "
            "picker that jumps to a day and marks each day that has events. "
            "Picking a day from the year view opens that day. Below the "
            "`lg` breakpoint the sidebar is hidden behind a button at the start "
            "of the toolbar."
        ),
        pr.h2("Saving and deleting Calendar events"),
        pr.p(
            "With a `save`, the sidebar has New event, a click on an empty part "
            "of a day opens the dialog for that day, and an event's popover "
            "offers Edit and Duplicate. In the day and week views the click also "
            "fills in the half hour under the pointer. With a `delete`, the "
            "popover of an event with an `id` offers Delete, and so does the "
            "dialog when it edits one."
        ),
        pr.p(
            "A new event starts on the day the view is around, at 09:00, and "
            "runs an hour, stopping at 23:59 when the hour would cross midnight. "
            "It starts in the first layer."
        ),
        pr.p(
            "`save` receives the request and an `Event` holding the title, when "
            "it is, its layer, location, notes and repeat key, and the `id` of "
            "the event it replaces, or `None` for a new one. The times are naive "
            "datetimes in the reader's time, or dates for a whole-day event. "
            "`delete` receives the request and the id. Duplicate is a `save` of a "
            'copy with no `id` and no `repeat`, titled with "(copy)" after the '
            "original's title."
        ),
        pr.p(
            "For a new event, `save` returns the id it gave the event, or the "
            "saved `Event` with its `id` set. The toast's Undo deletes that id, "
            "so a `save` that returns `None` leaves a create without Undo. Any "
            "string or number returned for a new event is read as its id, so "
            "never return a count of rows. What `save` returns for an edit is "
            "not read."
        ),
        pr.code(
            "def save_entry(request, event: Event) -> str | int | Event | None: ...\n"
            "def delete_entry(request, id: str) -> None: ..."
        ),
        pr.p(
            "The dialog asks for a title, whether the event is all day, when it "
            "starts and ends, its layer when there are layers, how it repeats "
            "when there are `repeats`, where it is, and any notes. Each of these "
            "comes back as an error on its field, and nothing reaches `save`:"
        ),
        pr.bullets(
            [
                "an empty title",
                "a date or a time that cannot be read",
                "an end before the start, or a timed event that starts and ends "
                "at the same moment",
                "an event that runs more than a year",
                "a layer or a repeat key the declaration does not offer",
                "a time the clocks skip going forward, when the `Formats` in the "
                "context moves times into a timezone",
            ]
        ),
        pr.p(
            "While the fields are filled in, the dialog asks the server whether "
            "the times overlap another timed event, in any layer and whatever "
            "the search. It names the events it overlaps in a warning, and the "
            "event can still be saved."
        ),
        pr.p(
            "All of it posts to one route, `{key}/<action>/` under the view's "
            "mount. The dialog and the popover's buttons post the calendar's "
            "state along with the fields, so after a save or a delete the "
            "`Calendar` comes back as the reader left it, with a toast such as "
            'Created "Design review". The fields are posted under the key like '
            "the state, `events-title` and `events-starts`, and those are the "
            "controls' ids too, so two calendars on one page keep their dialogs "
            "apart."
        ),
        pr.p(
            "A sync handler runs in a thread and an async one is awaited on the "
            "loop. If a handler raises, the reader gets a danger toast and the "
            "error is logged with its traceback under `hue.calendar`. A save that "
            "failed keeps the dialog open over what was typed, and a delete or a "
            "duplicate that failed redraws the calendar as it now is. In "
            "`hue-django`, a `PermissionDenied`, an `Http404` or a bad request "
            "keeps its status and is not logged."
        ),
        pr.h2("Dragging Calendar events"),
        pr.p(
            "A declared `Calendar` with a `save` lets the reader drag its "
            "events. In the day and week views:"
        ),
        pr.bullets(
            [
                "Dragging across an empty part of a day draws a range and opens "
                "the dialog with that range filled in.",
                "Dragging an event moves it up and down its day, or across to "
                "another day's column.",
                "Dragging an event's bottom edge changes when it ends.",
            ]
        ),
        pr.p(
            "The time grid snaps to the quarter hour, and an event shows its "
            "new times while it is dragged. A move keeps the start inside the "
            "event's own day, and the end no later than the midnight after the "
            "day the event ends on."
        ),
        pr.p(
            "In the month view and along the all-day row, a drag moves an event "
            "by whole days, counted from the day the reader took hold of, and "
            "keeps its times and length. Only the `Calendar`'s own days take a "
            "drop. An event let go over the sidebar's picker, or anywhere off "
            "the calendar, stays where it was."
        ),
        pr.bullets(
            [
                "A press that travels less than five pixels is a click, so it "
                "still opens an event's popover or the dialog.",
                "A drag that ends where it began posts nothing, and Escape "
                "during a drag puts the event back.",
                "Mouse, pen and touch share one pointer drag. On a touch screen "
                "a finger on an event drags it.",
                "The agenda view's rows move from the keyboard only.",
                "An event without an `id` cannot be moved, since the move route "
                "finds an event by its id.",
            ]
        ),
        pr.h3("Moving a Calendar event from the keyboard"),
        pr.p(
            "On a focused event, Alt with Up or Down moves it by a quarter "
            "hour, and Alt with Left or Right moves it by a day. Alt and Shift "
            "together change when it ends: Up and Down by a quarter hour for a "
            "timed event, Left and Right by a day for an all-day event. A key "
            "that would take the event out of its day posts nothing."
        ),
        pr.p(
            "Focus stays on the event once the `Calendar` is redrawn, and the "
            "event's accessible name gives its new times. A key pressed again "
            "before the answer arrives is dropped, so holding a key never posts "
            "times the event no longer has. The `Calendar` listens for these keys "
            "itself, so they work without a shortcut registry. "
            "The Edit dialog remains the full keyboard path."
        ),
        pr.h2("The move route of a declared Calendar"),
        pr.p(
            "A drag or an Alt key posts to `{key}/move/`, beside the other "
            "actions, which exists when the declaration has a `save`. The "
            "browser posts the event's `id`, which occurrence the reader took "
            "hold of, and the new times. That is all it knows, so the route "
            "looks the event up through `events` on the day that occurrence "
            "starts, in every layer and with no search. `save` then receives "
            "that same `Event` at the new times, with its title, layer, "
            "location, notes and repeat key unchanged. Whether the event is "
            "timed or all day comes from what `events` returned, not from the "
            "request."
        ),
        pr.p(
            "The toast says Moved, or Resized when the start stayed put. An id "
            "that `events` no longer has gets a 404 and a danger toast, and a "
            "time the clocks skip going forward gets a 422 with the reason in "
            "the toast. Both redraw the `Calendar` as it is now."
        ),
        pr.h3("Moving a repeating Calendar event"),
        pr.p(
            "A series moves as a whole. With a `save`, each repeating `Event` "
            "that `events` returns needs `series_starts`: when the first "
            "occurrence of its series starts. Without it the `Calendar` raises "
            "a `TypeError` that names the event."
        ),
        pr.code(
            "Event(\n"
            '    "Standup",\n'
            "    datetime(2026, 10, 14, 9, 30),\n"
            "    datetime(2026, 10, 14, 9, 45),\n"
            '    id="12",\n'
            '    repeat="weekly",\n'
            "    series_starts=datetime(2026, 9, 2, 9, 30),\n"
            ")"
        ),
        pr.p(
            "When one occurrence moves, `save` receives the series: its first "
            "occurrence moved by the same number of days, at the occurrence's "
            "new time of day and with its new length. An app that stores a "
            "series as its first occurrence and a rule saves it like any other "
            "edit. An edit of one occurrence in the dialog reaches `save` the "
            "same way. When the series' new first occurrence would start or end "
            "in an hour the clocks skip, the move is refused, and the dialog "
            "puts the error on the start time."
        ),
        pr.h2("Undo in a declared Calendar"),
        pr.p(
            "A success toast offers Undo when the route that reverses the "
            "change exists. Undo posts to the same route:"
        ),
        pr.bullets(
            [
                "After an edit, it saves the event as `events` had it, a series "
                "from its first occurrence.",
                "After a move or a resize, it moves the event back.",
                "After a delete, it saves the event as `events` had it, without "
                "its `id`, so `save` makes it again under a new id.",
                "After a create or a duplicate, it deletes the id `save` "
                "returned. That needs a `delete`, and a `save` that returns the "
                "id.",
            ]
        ),
        pr.p(
            "Undo goes one level deep: the toast an Undo earns offers none. "
            "Once the `Calendar` is back, focus goes to the event the Undo "
            "restored, or to New event after an undone create."
        ),
        pr.p(
            "The `save` in the Declared panel stores nothing and returns "
            "nothing. Its events stay where they are: a drag gets the toast "
            "and its Undo, and the event is drawn where it was. A create there "
            "has no Undo."
        ),
        pr.h2("Keyboard shortcuts for a declared Calendar"),
        pr.p(
            "`CalendarShortcuts` holds the keys a declared `Calendar` answers "
            "to. An app opts in by having its shortcut registry, the one in the "
            "render context, inherit it. Without that the `Calendar` binds no "
            "keys. ",
            pr.link("Keyboard shortcuts", "/keyboard-shortcuts/"),
            " covers the registry and how each framework is given it.",
        ),
        pr.code(
            "from hue.calendar import CalendarShortcuts\n"
            "from hue.shortcuts import Shortcut\n\n\n"
            "class Shortcuts(CalendarShortcuts):\n"
            '    billing = Shortcut("Go to Billing", "g", "b", href="/billing/")'
        ),
        pr.bullets(
            [
                "`t` goes to today, and `j` and `k` to the previous and next "
                "day, week, month, year or 30 days.",
                "`d`, `w`, `m`, `y` and `a` switch to the day, week, month, year "
                "and agenda views.",
                "`n` opens New event, when there is a `save`.",
                "`/` focuses the search box, when there is a `search`.",
                "`?` opens a dialog listing every shortcut on for the page, the "
                "app's own included, and the Alt keys that move an event. The "
                "view options have a Keyboard shortcuts button that opens it "
                "too.",
            ]
        ),
        pr.p(
            "Each key presses the control a click would, so a key and a click "
            "cannot drift apart. The keys are scoped, so they are on only "
            "where a declared `Calendar` is drawn, and like every shortcut they "
            "stay silent while someone types or a dialog is open. The arrow "
            "keys on their own are not among them: they move through the "
            "sidebar's picker and any listbox, and the registry refuses them."
        ),
        pr.p(
            "Only one `Calendar` on a page holds the keys, the first one the "
            "view builds. The calendar whose route answered last takes them, so "
            "a change made in another calendar on the page hands that one the "
            "keys. The docs' own registry does not inherit `CalendarShortcuts`, "
            "so the Declared panel has no shortcuts."
        ),
        pr.h2("What a reader of a declared Calendar sees and hears"),
        pr.bullets(
            [
                "The range in the title is announced from a status region "
                "outside what a response replaces, so a screen reader hears where "
                "the calendar moved to. The search's count and the dialog's "
                "overlap warning are status regions too.",
                "In the sidebar's picker, a day with events has has events after "
                "its name.",
                "The dialog opens on its title field. When a save or a delete "
                "closes it, focus goes to New event.",
                "After a move or an Undo, the event that moved or came back "
                "takes focus as the `Calendar` is swapped in. An event drawn on "
                "several days takes it on the day it starts. On a full month day "
                "it takes the place of the last event shown, which moves into "
                "+N more, so focus never lands in a closed popover.",
                "The button that opens the sidebar below `lg` is named Calendar "
                "tools and says whether the sidebar is open. Below `sm` the "
                "dialog docks to the bottom edge as a sheet, as every `Dialog` "
                "does.",
                "When the `Formats` in the context moves times into a timezone, "
                "the sidebar says which one, such as Times in Europe/Oslo.",
            ]
        ),
        pr.h2("A Calendar on a narrow screen"),
        pr.bullets(
            [
                "Below the `md` breakpoint, 768 pixels, a declared `Calendar` "
                "that loads on a week shows the day it is around, and so does "
                "one on a week when the window narrows past it. The day view is "
                "fetched in place with no history entry, and the URL keeps "
                "saying week, so the same link opens the week on a wider "
                "screen. The server cannot know the viewport, so the week shows "
                "for one request before the day replaces it.",
                "In the day and week views, every `Calendar` keeps each day's "
                "column at least 4.5rem wide. A week picked from its tab on a "
                "phone scrolls sideways.",
                "Below `md` the month view folds its events to bars: an all-day "
                "event keeps its fill and a timed one its dot, without the "
                "words. Each event's accessible name stays the same.",
            ]
        ),
        pr.h2("Assumptions of a declared Calendar"),
        pr.bullets(
            [
                "Today is the reader's today: now in the timezone the `Formats` "
                "in the context moves times into, or the server's date when it "
                "moves them into none.",
                "The picker marks the days `events` covered. Paging the picker to "
                "another month shows that month without marks until the calendar "
                "moves there.",
            ]
        ),
        Alert()
        .variant("warning")
        .title("Known gaps in a declared Calendar")
        .content(
            html.ul(
                *[
                    html.li(pr.rich(gap))
                    for gap in [
                        "The grid does not scroll by itself when a drag nears "
                        "its edge.",
                        "The times shown during a drag use a 24-hour clock, "
                        "whatever the `Formats` says. The redraw after the drop "
                        "follows the `Formats`.",
                        "A swipe that starts on an event drags it instead of "
                        "scrolling.",
                        "After a series move is undone, focus goes to the first "
                        "occurrence of the series on screen rather than the one "
                        "that was dragged.",
                        "A move whose answer has no calendar in it, such as a "
                        "proxy's error page, puts the event back with no "
                        "message.",
                    ]
                ]
            ).class_("list-disc space-y-1 ps-5")
        ),
    )


PAGE = ComponentPage(
    Calendar,
    lede=(
        "A `Calendar` lays out events on a day, a week, a month, a year or the "
        "next 30 days. Handed its events, it is presentational, and `href()` "
        "turns its navigation into links to the app's own routes. Declared on "
        "a view, it also searches, shows and hides layers, saves and deletes "
        "events through a dialog, and moves them by drag or by key, with its "
        "state in the URL."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            october,
            layout="stack",
            min_width=720,
            min_height=720,
            hint="Step through the weeks, switch views and open an event",
        ),
        panel(
            "Declared",
            declared_calendar,
            layout="stack",
            min_width=960,
            min_height=820,
            hint="A declared calendar and its view. Drag an event, or press Alt "
            "and an arrow key on one. Nothing is saved",
            source=_calendar_demo,
        ),
        panel(
            "Views",
            day,
            week,
            month,
            year,
            agenda,
            layout="stack",
            min_width=720,
            hint="`view()` picks one. Click an event or `+2 more` for its popover",
        ),
        panel(
            "Anatomy",
            event_details,
            without_links,
            layout="stack",
            min_width=720,
            hint="An event's popover with `actions()`, and a `Calendar` without "
            "`href()`",
        ),
        panel(
            "Week",
            sunday_first,
            weekdays_only,
            layout="stack",
            min_width=720,
            hint="`week_start()` and `weekdays()`",
        ),
        panel("Empty", nothing_scheduled, layout="stack"),
        panel(
            "Width",
            narrow_month,
            narrow_week,
            layout="stack",
            width="sm",
            hint="Below `md` the month folds its events to bars. Narrow the frame "
            "and the week scrolls sideways",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "Every event is a button named with its title, its day and its "
            "times, and whether it repeats, since its place in a grid says "
            "nothing to a screen reader. An all-day bar's name gives its first "
            "and last day, so a bar cut off at the edge of the week says how "
            "far it runs.",
        ),
        Note(
            "a11y",
            "The month and year views are tables with a caption, and each "
            "column header carries the full weekday name in `abbr`.",
        ),
        Note(
            "a11y",
            'Today\'s number has `aria-current="date"`, and its link says today '
            "after the date. In the year view a day's link also says how many "
            "events it has.",
        ),
        Note(
            "a11y",
            "With an `id()`, a visually hidden status region outside the swapped "
            "part announces the new title after each swap. Focus goes back to "
            "the control that was used when the new view has it again, as "
            "Previous, Today, Next and the view tabs do, and to the view's "
            "heading otherwise, such as after a day's link.",
        ),
        Note(
            "a11y",
            "In a declared `Calendar` with a `save`, Alt with the arrow keys "
            "moves or resizes the focused event, so dragging has a keyboard "
            "equivalent, and focus stays on the event after the redraw.",
        ),
        Note(
            "note",
            "The red line in today's column of the day and week views follows "
            "the browser's clock and moves every minute.",
        ),
        Note(
            "warn",
            "The line for the current time assumes the browser's timezone is the "
            "one `Formats` moves events into. Where they differ, the line and "
            "the events disagree.",
        ),
        Note("warn", "A `Calendar` raises a `ValueError` without `date()`."),
    ],
    related=[DatePicker, Table],
    # The declared demo first: its action route, schedule/<action>/, would
    # otherwise reach CalendarDemo's {view}/{day}/ first and be refused.
    views=[_calendar_demo.ScheduleView, CalendarDemo],
)
