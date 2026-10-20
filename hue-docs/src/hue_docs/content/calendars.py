from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from hue.calendar import CalendarState, Layer, build_calendar_state
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
    declaration is handed the view's own Router and registers its route on
    it; here it is registered on nothing and never called.
    """

    def fragment_post(self, path: str) -> Any:
        return lambda view_func: view_func

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {name: [value] for name, value in request.params.items()}

    def _get_form_values(self, request: Any) -> dict[str, list[str]]:
        # Nothing is ever posted to a docs page.
        return {}

    def _refusal(self, error: Exception) -> None:
        return None

    def _csrf_field(self) -> None:
        return None

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        # Django reverses these against the URLconf. Here they are spelled
        # out, since there is nothing to reverse against.
        action = params.get("action")
        return f"/calendars/{action}/" if action else "/calendars/"

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
        # A list has no event loop to keep off.
        return func(*args)


_LAYERS = [
    Layer("product", "Product"),
    Layer("eng", "Engineering", color=2),
    Layer("personal", "Personal", color=3),
]

# The one week the page draws, whatever the day: the docs render the same
# every day, so the events are fixed rather than placed around today.
_EVENTS = [
    Event(
        "Standup",
        datetime(2026, 10, 12, 9),
        datetime(2026, 10, 12, 9, 15),
        id="1",
        layer="eng",
        repeat="weekdays",
        location="Huddle room",
    ),
    Event(
        "Design review",
        datetime(2026, 10, 14, 13),
        datetime(2026, 10, 14, 14, 30),
        id="2",
        layer="product",
        location="Room 3B",
        notes="Walk the range state matrix.",
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
        "Release 2.4 freeze",
        date(2026, 10, 16),
        date(2026, 10, 17),
        id="5",
        layer="eng",
    ),
]


def _events(request: Any, asked: CalendarState) -> list[Event]:
    """
    The one part of a calendar that is not fixed: which events answer it.
    """
    query = asked.query.lower()
    return [
        event
        for event in _EVENTS
        if event.layer in asked.layers and query in event.title.lower()
    ]


def _save(request: Any, event: Event) -> None:
    """A service function, which is all a handler ever is."""


def _delete(request: Any, id: str) -> None:
    """A service function, which is all a handler ever is."""


def _calendar(key: str) -> Any:
    """
    The declaration, once per specimen: two calendars on one page need two
    keys, because the key is the id every part of a calendar is named from.
    """
    return build_calendar_state(
        _Router(),
        key=key,
        events=_events,
        layers=_LAYERS,
        save=_save,
        delete=_delete,
        repeats={"weekdays": "Every weekday", "weekly": "Every week"},
        search="Search events",
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
    request: HttpRequest, asked: CalendarState
) -> list[Event]:
    \"\"\"The one part of a calendar that is not fixed: which events answer it.\"\"\"
    found = Entry.objects.filter(
        starts__date__lte=asked.last,
        ends__date__gte=asked.first,
        layer__in=asked.layers,
    )
    if asked.query:
        found = found.filter(title__icontains=asked.query)
    return [entry.event() for entry in found]


def save_entry(request: HttpRequest, event: Event) -> None:
    fields = Entry.fields_of(event)
    if event.id is None:
        Entry.objects.create(**fields)
    else:
        Entry.objects.filter(pk=event.id).update(**fields)


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
            Layer("eng", "Engineering", color=2),
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


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Calendars"),
        pr.lead(
            "A calendar whose state lives in the URL. You declare it once on a "
            "view: the function that finds its events, the calendars a reader can "
            "show and hide, and what saves and deletes an event. The calendar "
            "draws its own sidebar, search, view options and event dialog, and "
            "every way of moving around it is a link or a form."
        ),
        pr.h2("The declaration"),
        pr.code(_DECLARATION),
        pr.p(
            "The view draws the calendar with Calendar.from_state(self.events). "
            "The rest of this page covers what the declaration does."
        ),
        pr.p(
            "The examples further down use the same declaration over a list of "
            "events, so the narrowing they show is plain Python and the page "
            "needs no database."
        ),
        pr.h2("Events come from one function"),
        pr.p(
            "events is the only part of a calendar that changes with each "
            "request, so it is the only part that is a function. It receives the "
            "request and a CalendarState, and returns every Event between "
            "asked.first and asked.last that matches asked.query and belongs to "
            "one of asked.layers. first and last cover the days the view shows "
            "and the six weeks of the month around them, which the sidebar's "
            "picker marks. Filter on those and nothing else."
        ),
        pr.p(
            "An Event is a title and when it is. A date is a whole day, and ends "
            "is the last day it covers, so an offsite from Monday to Wednesday "
            "ends on Wednesday. A datetime is a moment, and ends is when it is "
            "over. An aware datetime is placed on the reader's day under USE_TZ. "
            "layer names the calendar it belongs to, and an event without a "
            "colour of its own takes its layer's. repeat is your own key for the "
            "rule it repeats by; the calendar draws the repeat mark and shows the "
            "key's label in the dialog, and expanding the rule into occurrences "
            "is your job, since only you know what the rule means."
        ),
        pr.code(
            'Event("Offsite", date(2026, 10, 19), date(2026, 10, 21), layer="eng")\n'
            'Event("Standup", datetime(2026, 10, 14, 9, 30), id="12", repeat="weekly")'
        ),
        pr.h2("The URL is the state"),
        pr.p(
            "Everything a reader does to the calendar is in the address bar: the "
            "view, the day it is around, the search, the hidden layers, which day "
            "the week starts on and whether the weekend shows. Each one is named "
            "under the calendar's key, and one at its default is left out, so "
            "Today's link is the page with no query at all."
        ),
        pr.code(
            "/events/?events-view=month&events-date=2026-10-14&events-hide=personal",
            language="bash",
        ),
        pr.p(
            "Previous, Today, Next, the view switcher and every day are links to "
            "the page with one part changed. The search, the sidebar's picker and "
            "calendars and the view options are GET forms to the same page. Alpine "
            "AJAX fetches it and swaps the calendar in place, keeping focus on the "
            "control you pressed, and the address bar ends up holding a URL that "
            "reloads to the same calendar and can be sent to someone. With "
            "JavaScript off the links still work, as full page loads."
        ),
        pr.p(
            "Because each calendar keeps to names under its own key, two on one "
            "page keep separate state in one URL, and each carries the other's "
            "parameters through unchanged. A value typed into the URL by hand "
            "that is not one, such as a thirteenth month or a view nobody has, "
            "shows the default rather than an error page."
        ),
        pr.h2("Layers, search and view options"),
        pr.p(
            "Each Layer is one of the calendars a reader can show or hide: a key, "
            "a name and a chart colour. The sidebar lists them as boxes, and "
            "unticking one puts its key in the URL under hide, so a layer added "
            "later shows up for someone following an old link. It is called a "
            "layer here because Calendar is the component."
        ),
        pr.p(
            "search gives the calendar a search box, with the text as its "
            "placeholder. It is a GET form that submits itself 300 milliseconds "
            "after the last keystroke, Escape empties it, and a count beside it "
            "says how many events the view holds that match. The box sits outside "
            "what a response replaces, so it keeps its caret while the events "
            "change."
        ),
        pr.p(
            "The view options sit behind one button: which day the week starts on, "
            "and whether to leave the weekend out. Both are state like the rest, "
            "and the declaration's view and week_start are the defaults the URL "
            "leaves out."
        ),
        pr.h2("Saving and deleting"),
        pr.p(
            "save and delete make the calendar editable. With a save, the sidebar "
            "has a New event button, a click on an empty slot in the time grid or "
            "on a day opens the dialog with that time filled in, and an event's "
            "popover offers Edit and Duplicate. With a delete, the popover and the "
            "dialog offer Delete. Without either, the calendar is a picture of its "
            "events and registers no route."
        ),
        pr.p(
            "save receives the request and an Event: the title, when it is, its "
            "layer, location, notes and repeat key, and the id of the event it "
            "replaces, or None for a new one. The times are naive, in the "
            "reader's time, or dates for a whole day. Make them aware with your "
            "framework's current timezone when you store them. delete receives "
            "the request and the id. Duplicate is a save of a copy with no id."
        ),
        pr.code(
            "def save_entry(request: HttpRequest, event: Event) -> None: ...\n"
            "def delete_entry(request: HttpRequest, id: str) -> None: ..."
        ),
        pr.p(
            "The dialog asks for a title, whether the event is all day, when it "
            "starts and ends, which calendar it is in, where it is and any notes, "
            "and how it repeats when the declaration offers repeats, a mapping of "
            "your keys to their labels. A field that cannot be read, a missing "
            "title, an end before the start, an event longer than a year or, under "
            "USE_TZ, a time the clocks skip going forward comes back as an error on "
            "the field, and nothing reaches save. While the fields are being filled "
            "in, the dialog asks the server whether the times overlap another timed "
            "event and says which, as a warning rather than a refusal."
        ),
        pr.p(
            "All of it goes through one route, POST events/<action>/, named after "
            "the key. The dialog, the popover's buttons and a slot click post the "
            "calendar's state along with the fields, so after a save the calendar "
            "comes back in the view the reader was in, with a toast saying what "
            "happened. The fields are posted under the key like the state, "
            "events-title and events-starts, and those are the controls' ids too, "
            "so two calendars on one page keep their dialogs apart and a page "
            "parameter called title is left alone. The form also carries Django's "
            "CSRF token, so it posts even where the script has failed. If a "
            "handler raises, the reader gets a danger toast, the calendar redraws "
            "as it now is, and the error is logged with its traceback. A "
            "permission denied or a not found, such as a save of an event someone "
            "else has deleted, keeps its status but is answered the same way, "
            "since Django's own page has nowhere on it for the browser to put "
            "the answer."
        ),
        pr.h2("What the reader sees and hears"),
        pr.p(
            "The range in the title is announced from a live region outside what "
            "a response replaces, so a screen reader hears where the calendar "
            "moved to. The search's count is announced the same way. Every event "
            "is a button named in full, and the sidebar's picker says which days "
            "have something on them."
        ),
        pr.p(
            "Below the lg breakpoint the sidebar folds away behind a button at "
            "the start of the toolbar, and the dialog docks to the bottom edge as "
            "a sheet, as every Dialog does."
        ),
        pr.p(
            "The names of the months and days come from Formats, which hue-django "
            "fills from Django's own translations, and the times follow "
            "HUE_TIME_FORMAT. The sidebar says which timezone the times are in "
            "when the framework moves them into one."
        ),
        pr.h2("Two examples"),
        pr.p(
            "Both calendars below are the declaration from the top of the page, "
            "bound to different requests, over a fixed list of events. Their "
            "buttons post to nowhere, since a docs page has no view."
        ),
        _specimen("events", date="2026-10-14"),
        pr.p(
            "The second is the month, searched, with the personal calendar hidden "
            "and the week starting on Sunday."
        ),
        _specimen(
            "planning",
            view="month",
            date="2026-10-14",
            q="re",
            hide="personal",
            start="sunday",
        ),
        pr.h2("Assumptions"),
        pr.bullets(
            [
                pr.p(
                    "Today is the reader's today: now in the current timezone "
                    "under USE_TZ, the server's otherwise."
                ),
                pr.p(
                    "events and the handlers are plain functions, run in a thread "
                    "rather than on the event loop, because Django raises "
                    "SynchronousOnlyOperation for a query made on the loop."
                ),
                pr.p(
                    "Each move loads the page, so whatever else index computes "
                    "runs on every step as well. Keep index cheap on a page with "
                    "a calendar."
                ),
                pr.p(
                    "The picker marks the days events() covered. Paging the picker "
                    "to another month shows that month without marks until the "
                    "calendar moves there."
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
                        "Dragging an event to move or resize it. It will be a save "
                        "of the new times through the same route."
                    ),
                    pr.p(
                        "Undo. A delete removes the event straight away, with a "
                        "toast and no way back yet."
                    ),
                    pr.p("Keyboard shortcuts for the views, Today and New event."),
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
