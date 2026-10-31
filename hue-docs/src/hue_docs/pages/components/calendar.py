from __future__ import annotations

from datetime import date, datetime
from typing import cast, get_args

from fastapi import HTTPException, Request
from hue import html
from hue.context import HueContext
from hue.types.core import ComponentType
from hue.ui import Button, Calendar, DatePicker, Event, Table
from hue.ui.molecules.calendar import CalendarView
from hue_fastapi import HueFragmentsView, Page, Router

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel


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
                    recurring=True,
                    location="Huddle room",
                    color=6,
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
                    color=2,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=3,
                ),
                Event(
                    "Release freeze",
                    date(2026, 10, 16),
                    date(2026, 10, 17),
                    color=4,
                ),
                Event(
                    "Deploy window",
                    datetime(2026, 10, 16, 22),
                    datetime(2026, 10, 17, 2),
                    color=2,
                ),
                Event("Time off", date(2026, 10, 26), date(2026, 10, 30), color=5),
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
                    color=2,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=3,
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
                    color=5,
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
                    recurring=True,
                    color=6,
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
                    color=2,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=3,
                ),
                Event(
                    "Release freeze",
                    date(2026, 10, 16),
                    date(2026, 10, 17),
                    color=4,
                ),
                Event(
                    "Deploy window",
                    datetime(2026, 10, 16, 22),
                    datetime(2026, 10, 17, 2),
                    color=2,
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
                    color=4,
                ),
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event("Release freeze", date(2026, 10, 15), color=4),
                Event(
                    "Contrast audit",
                    datetime(2026, 10, 15, 10),
                    datetime(2026, 10, 15, 12),
                    color=2,
                ),
                Event(
                    "Pairing",
                    datetime(2026, 10, 15, 11),
                    datetime(2026, 10, 15, 12, 30),
                    color=3,
                ),
                Event(
                    "Dentist",
                    datetime(2026, 10, 15, 15),
                    datetime(2026, 10, 15, 15, 45),
                    color=5,
                ),
                Event("Time off", date(2026, 10, 26), date(2026, 10, 30), color=5),
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
                Event("Offsite", date(2026, 3, 18), date(2026, 3, 20), color=4),
                Event("Summer break", date(2026, 7, 6), date(2026, 7, 24), color=5),
                Event(
                    "Design review",
                    datetime(2026, 10, 14, 13),
                    datetime(2026, 10, 14, 14, 30),
                ),
                Event("Year end", date(2026, 12, 18), color=2),
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
                    recurring=True,
                    location="Huddle room",
                    color=6,
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
                    color=4,
                ),
                Event("Time off", date(2026, 10, 26), date(2026, 10, 28), color=5),
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
                    recurring=True,
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
                Event("Time off", date(2026, 10, 26), date(2026, 10, 30), color=5),
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
        .events([Event("Time off", date(2026, 10, 26), date(2026, 10, 30), color=5)])
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
                Event("Release freeze", date(2026, 10, 16), color=4),
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
            'Event("Offsite", date(2026, 10, 19), date(2026, 10, 21), color=4)\n'
            "Event(\n"
            '    "Standup",\n'
            "    datetime(2026, 10, 14, 9, 30),\n"
            "    datetime(2026, 10, 14, 9, 45),\n"
            '    location="Huddle room",\n'
            "    recurring=True,\n"
            ")"
        ),
        pr.bullets(
            [
                "`color` is 1 to 6, one of the chart tokens. 1, the default, is "
                "the accent.",
                "`location` and `notes` show in the event's popover.",
                "`recurring=True` draws a repeat mark. The `Calendar` does not "
                "expand a rule into occurrences: pass each occurrence as its own "
                "`Event`.",
                "`href` adds an Open link to the popover.",
                "`id` names the event for the app's own routes.",
            ]
        ),
        pr.p(
            "An `Event` raises a `ValueError` when its title is empty, when its "
            "colour is outside 1 to 6, when it mixes a `date` with a `datetime` "
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
    )


PAGE = ComponentPage(
    Calendar,
    lede=(
        "A `Calendar` lays out events on a day, a week, a month, a year or the "
        "next 30 days. It is presentational: the app hands it the events, and "
        "`href()` turns its navigation into links to the app's own routes."
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
    ],
    notes=[
        Note(
            "a11y",
            "Every event is a button named with its title, its day and its "
            "times, and whether it repeats, since its place in a grid says "
            "nothing to a screen reader. An all-day bar cut off at the edge of "
            "the week adds (continues) to its name.",
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
            "the link that was followed when the new view has it again, as "
            "Previous, Today and Next do, and to the view's heading otherwise.",
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
    views=[CalendarDemo],
)
