"""
One page with one declared calendar on it, and no model behind it.

The events are made up from the days shown, so every month has the same
few and nothing needs seeding. The page exists to try the calendar in a
real browser: the month links, the focus they keep, and the dialog a day
opens.
"""

from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

from django.http import HttpRequest
from hue import html
from hue.calendar import CalendarState, DayAction, build_calendar_state
from hue.context import HueContext
from hue.js import close
from hue.ui import (
    Button,
    Calendar,
    DateInput,
    Dialog,
    Event,
    Stack,
    Text,
    TextInput,
    ToastRegion,
)
from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueView


def _months(first: date, last: date) -> Iterator[date]:
    month = first.replace(day=1)
    while month <= last:
        yield month
        month = (month + timedelta(days=31)).replace(day=1)


def events_for(request: HttpRequest, shown: CalendarState) -> list[Event]:
    """
    The same handful every month, on fixed days, in every tone: one across
    three days, two at a time of day, two with somewhere to go.
    """
    found: list[Event] = []
    for month in _months(shown.first, shown.last):
        year, number = month.year, month.month
        found += [
            Event("Planning", month.replace(day=5), variant="warning"),
            Event(
                "Offsite",
                month.replace(day=10),
                month.replace(day=12),
                variant="info",
                href="#",
            ),
            Event(
                "Design review", datetime(year, number, 14, 9, 30, tzinfo=UTC), href="#"
            ),
            Event(
                "Invoice run",
                datetime(year, number, 20, 15, tzinfo=UTC),
                datetime(year, number, 20, 16, tzinfo=UTC),
                variant="danger",
            ),
            Event("Release", month.replace(day=27), variant="success"),
        ]
    return found


def new_event(request: HttpRequest, day: date) -> Dialog:
    """
    What a day opens: a dialog naming the day, with the start filled in.
    """
    return (
        Dialog()
        .open()
        .title(f"New event on {day:%d %B %Y}")
        .content(
            html.form(
                Stack()
                .spacing("md")
                .align_items("items-stretch")
                .content(
                    TextInput().name("title").label("Title"),
                    DateInput().name("starts").label("Starts").value(day),
                )
            )
        )
        .footer(
            Button().variant("ghost").content("Cancel").x_on("click", close()),
            # Nothing is saved: the page has no model. The button is here so
            # the dialog's focus order has a primary action in it.
            Button().variant("primary").content("Save").x_on("click", close()),
        )
    )


class EventsView(HueView):
    router = Router[HttpRequest]()

    events = build_calendar_state(
        router,
        key="events",
        events=events_for,
        day=DayAction("New event", new_event),
    )

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ) -> Page:
        return Page(
            title="Events",
            body=html.main()
            .class_("example-page")
            .content(
                Stack()
                .spacing("lg")
                .align_items("items-stretch")
                .content(
                    Text("Events").variant("title-2").tag("h1"),
                    Calendar.from_state(self.events),
                ),
                ToastRegion(),
            ),
        )
