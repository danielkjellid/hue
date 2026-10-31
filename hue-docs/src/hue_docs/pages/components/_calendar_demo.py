from __future__ import annotations

from datetime import date, datetime

from fastapi import Request
from hue import html, toast
from hue.calendar import CalendarState, Layer, build_calendar_state
from hue.context import HueContext
from hue.ui import Calendar, Event, ToastRegion
from hue_fastapi import HueView, Page, Router

# A list of events, so the narrowing below is plain Python. A database query
# does the same in events=.
EVENTS = [
    Event(
        "Standup",
        datetime(2026, 10, 12, 9),
        datetime(2026, 10, 12, 9, 15),
        id="1",
        layer="eng",
        repeat="weekdays",
        # When the series began, which a calendar with a save needs from
        # every occurrence: moving one moves the series.
        series_starts=datetime(2026, 10, 12, 9),
        location="Huddle room",
    ),
    Event(
        "Design review",
        datetime(2026, 10, 14, 13),
        datetime(2026, 10, 14, 14, 30),
        id="2",
        layer="product",
        location="Room 3B",
        notes="Walk the range states and the contrast audit.",
    ),
    Event(
        "Contrast audit",
        datetime(2026, 10, 15, 10),
        datetime(2026, 10, 15, 12),
        id="3",
        layer="eng",
    ),
    Event(
        "Dentist",
        datetime(2026, 10, 15, 15),
        datetime(2026, 10, 15, 15, 45),
        id="4",
        layer="personal",
    ),
    Event(
        "Release freeze",
        date(2026, 10, 16),
        date(2026, 10, 17),
        id="5",
        layer="eng",
    ),
    Event(
        "Time off",
        date(2026, 10, 26),
        date(2026, 10, 30),
        id="6",
        layer="personal",
    ),
]


def _day(moment: date | datetime) -> date:
    return moment.date() if isinstance(moment, datetime) else moment


def events_for(request: Request, asked: CalendarState) -> list[Event]:
    query = asked.query.lower()
    return [
        event
        for event in EVENTS
        if event.layer in asked.layers
        and query in event.title.lower()
        and _day(event.starts) <= asked.last
        and _day(event.ends or event.starts) >= asked.first
    ]


# Every reader of the docs shares these events, so saving, moving and
# deleting change nothing. Returning no id leaves a create without an Undo.
def save_event(request: Request, event: Event) -> None:
    toast.info("The demo keeps its events", description=event.title)


def delete_event(request: Request, id: str) -> None:
    toast.info("The demo keeps its events")


class ScheduleView(HueView):
    router = Router[Request]()

    schedule = build_calendar_state(
        router,
        key="schedule",
        events=events_for,
        layers=[
            Layer("product", "Product"),
            Layer("eng", "Engineering", color=2),
            Layer("personal", "Personal", color=3),
        ],
        save=save_event,
        delete=delete_event,
        repeats={"weekdays": "Every weekday", "weekly": "Every week"},
        search="Search events",
    )

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(
            title="Schedule",
            body=html.div(
                html.div(Calendar.from_state(self.schedule))
                .id("schedule-demo")
                .class_("w-full"),
                ToastRegion(),
            ).class_("p-4"),
        )
