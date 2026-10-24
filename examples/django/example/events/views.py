"""
One page with one declared calendar on it, backed by a real table.

Everything the calendar does is on the declaration: the route the dialog
posts to is registered here, at class scope, and the view draws it with
Calendar.from_state(). The entries are plain rows; a series is one row and
the rule, expanded here into the occurrences the days shown hold.
"""

from django.db.models import Q
from django.http import Http404, HttpRequest
from hue import html
from hue.calendar import CalendarState, Layer, build_calendar_state
from hue.context import HueContext
from hue.ui import Calendar, Event, Stack, Text, ToastRegion
from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueView

from example.events.models import Entry
from example.events.repeats import occurrences

# Each calendar in its own chart colour, which its events take.
_LAYERS = [
    Layer(Entry.Layer.PRODUCT, "Product", color=1),
    Layer(Entry.Layer.ENGINEERING, "Engineering", color=2),
    Layer(Entry.Layer.PERSONAL, "Personal", color=3),
    Layer(Entry.Layer.TIME_OFF, "Time off", color=5),
]


def events_for(request: HttpRequest, asked: CalendarState) -> list[Event]:
    """
    Every occurrence between the days asked for, in the layers shown, that
    matches the search.
    """
    found = Entry.objects.filter(layer__in=asked.layers, starts__date__lte=asked.last)
    # A series that began before the first day may still reach it; a
    # single entry that ended before it cannot.
    found = found.exclude(repeat="", ends__date__lt=asked.first)
    if asked.query:
        found = found.filter(
            Q(title__icontains=asked.query)
            | Q(location__icontains=asked.query)
            | Q(notes__icontains=asked.query)
        )
    return [
        event
        for entry in found.order_by("starts", "pk")
        for event in occurrences(entry, asked.first, asked.last)
    ]


def _entry(id: str) -> Entry:
    # A posted id is text, and a key that is not a number is nobody's.
    if not id.isdigit():
        raise Http404
    try:
        return Entry.objects.get(pk=id)
    except Entry.DoesNotExist:
        raise Http404 from None


def save_entry(request: HttpRequest, event: Event) -> int:
    """
    Keep what the dialog said: a new entry, or the whole of an existing
    one, series and all, moved to where the dialog put it. The key comes
    back, which is what Undo deletes after a create.
    """
    fields = Entry.fields_of(event)
    if event.id is None:
        return Entry.objects.create(**fields).pk
    entry = _entry(event.id)
    for name, value in fields.items():
        setattr(entry, name, value)
    entry.save()
    return entry.pk


def delete_entry(request: HttpRequest, id: str) -> None:
    _entry(id).delete()


class EventsView(HueView):
    router = Router[HttpRequest]()

    events = build_calendar_state(
        router,
        key="events",
        events=events_for,
        layers=_LAYERS,
        save=save_entry,
        delete=delete_entry,
        repeats={value: str(label) for value, label in Entry.Repeat.choices},
        search="Search events",
    )

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ) -> Page:
        return Page(
            title="Events",
            body=html.main()
            .class_("example-page example-page-wide")
            .content(
                Stack()
                .spacing("lg")
                .align_items("items-stretch")
                .content(
                    Text("Events").variant("title-2").tag("h1"),
                    Calendar.from_state(self.events),
                ),
                # Once per page, and there before the first toast: a live
                # region made together with its content is not read out.
                ToastRegion(),
            ),
        )
