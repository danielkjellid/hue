"""
A calendar that knows where its own state lives.

Calendar on its own draws the events it is handed. A declaration owns
which day and which view those are, reads them from the page's URL,
fetches the events through one function, and registers the route the
event dialog posts to:

    def events_for(request: HttpRequest, asked: CalendarState) -> list[Event]:
        found = Entry.objects.filter(
            starts__date__lte=asked.last,
            ends__date__gte=asked.first,
            layer__in=asked.layers,
        )
        if asked.query:
            found = found.filter(title__icontains=asked.query)
        return [entry.event() for entry in found]


    def save_entry(request: HttpRequest, event: Event) -> None:
        Entry.objects.update_or_create(pk=event.id, defaults=fields_of(event))


    def delete_entry(request: HttpRequest, id: str) -> None:
        Entry.objects.filter(pk=id).delete()


    class EventsView(HueView):
        router = Router[HttpRequest]()

        events = build_calendar_state(
            router,
            key="events",
            events=events_for,
            layers=[Layer("work", "Work"), Layer("home", "Home", color=3)],
            save=save_entry,
            delete=delete_entry,
            repeats={"weekly": "Every week"},
            search="Search events",
        )

        async def index(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ) -> Page:
            return Page(title="Events", body=Calendar.from_state(self.events))

The URL is the state: /events/?events-view=month&events-date=2026-10-14.
Previous, Today, Next, the view switcher and every day are links to the
page with one part changed and every other query pair kept, and a part at
its default is left out, so a bookmark of Today stays on today. The search,
the sidebar's picker and calendars and the view options are GET forms to
the same page. Alpine AJAX swaps the calendar in place for all of them.

events() is the only part that is not fixed, so it is the only part that is
a function. It receives the request and the state, and returns the events
between asked.first and asked.last that match the query and belong to the
layers shown. Expanding a repeating event into its occurrences is its job.
An event without a colour takes its layer's.

save and delete make the calendar editable: a New event button, a click on
an empty slot or day, and Edit, Duplicate and Delete in an event's popover
open a dialog or act straight away. The dialog's fields arrive as an Event
with naive datetimes in the reader's time, or dates for a whole day, and an
id when it is an existing one. A field that cannot be read comes back as an
error on the field rather than reaching save. One route serves all of it,
POST {key}/<action>/, with the state in the body so the calendar comes back
as the reader left it.

events() and the handlers run off the event loop, through the router,
because both usually use the ORM and the ORM refuses to run on the loop.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, time, timedelta
from http import HTTPStatus
from typing import Any, ClassVar, Protocol, get_args
from urllib.parse import urlencode

from htmy import Context, html
from pydantic import BaseModel

from hue import toast
from hue.context import HueContext
from hue.formats import Formats
from hue.js import Expression, ajax, call, close, unsafe
from hue.router import PAGE_ROUTE, HueResponse
from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button
from hue.ui.atoms.checkbox import Checkbox
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import SEARCH_DELAY, SearchInput, TextInput
from hue.ui.atoms.native_select import NativeSelect
from hue.ui.atoms.radio import Radio, RadioGroup
from hue.ui.atoms.switch import Switch
from hue.ui.atoms.textarea import Textarea
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _calendar_views as views
from hue.ui.molecules._days import WEEKDAYS, EventColor, WeekStart, month_grid, week_of
from hue.ui.molecules.calendar import (
    _AGENDA_DAYS,
    _FIRST,
    _LAST,
    _SOLID,
    Calendar,
    CalendarView,
    Event,
)
from hue.ui.molecules.date_input import DateInput, TimeInput
from hue.ui.molecules.date_picker import DatePicker
from hue.ui.molecules.dialog import Dialog
from hue.ui.molecules.form import Form
from hue.ui.molecules.popover import Popover
from hue.ui.navigation import SYNC, swap
from hue.utils import classnames, render_if, render_when

__all__ = ["CalendarState", "Layer", "build_calendar_state"]

_log = logging.getLogger(__name__)

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
_ACTIONS = (_DIALOG, _OVERLAPS, _SAVE, _DELETE)

_VIEWS: tuple[CalendarView, ...] = get_args(CalendarView.__value__)
_STARTS: tuple[WeekStart, ...] = get_args(WeekStart.__value__)

# YYYY-MM-DD and HH:MM and nothing else; fromisoformat would also take
# 20261014 and 09:30:15.
_DAY_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_CLOCK_PATTERN = re.compile(r"\d{2}:\d{2}")

# A new event with no time of its own: an hour from nine.
_NEW_STARTS = time(9)
_NEW_ENDS = time(10)

_SIDE_HEADING = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-muted"


class _Routes(Protocol):
    """
    What a declaration needs from the router it is handed: somewhere to
    register its route, and the framework's answers to the questions only
    the framework can answer.
    """

    def fragment_post(self, path: str) -> Callable[[Any], Any]: ...
    def _get_query_values(self, request: Any) -> dict[str, list[str]]: ...
    def _get_form_values(self, request: Any) -> dict[str, list[str]]: ...
    def _url_for(self, request: Any, name: str, **params: Any) -> str: ...
    def _passes_through(self, error: Exception) -> bool: ...
    def _form_fields(self) -> AbstractSet[str]: ...
    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R: ...


# Given the request and what it asked for, every event that answers it.
type EventsFor = Callable[[Any, "CalendarState"], Iterable[Event]]
# Given the request and an event, with an id when it exists, keep it.
type SaveHandler = Callable[[Any, Event], Any]
# Given the request and an event's id, remove it.
type DeleteHandler = Callable[[Any, str], Any]


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
    week_start: WeekStart = "monday"
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
        return cursor, cursor + timedelta(days=_AGENDA_DAYS - 1)


class _Posted(BaseModel):
    """
    The dialog's fields as the form posts them, every one text, so that a
    value that cannot be read is an error on its field and never a 422
    nobody drew.
    """

    id: str = ""
    title: str = ""
    all_day: str = ""
    starts: str = ""
    starts_time: str = ""
    ends: str = ""
    ends_time: str = ""
    layer: str = ""
    location: str = ""
    notes: str = ""
    repeat: str = ""


def _one(asked: Mapping[str, list[str]], name: str) -> str | None:
    values = asked.get(name)
    return values[-1] if values else None


def _many(asked: Mapping[str, list[str]], name: str) -> tuple[str, ...]:
    return tuple(
        part for value in asked.get(name, ()) for part in value.split(",") if part
    )


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


def _timezone(formats: Formats) -> str | None:
    """
    The name of the timezone events are drawn in, when the framework moves
    them into one. Without that, a naive time is shown as given and there
    is nothing honest to say.
    """
    if formats.localize is None:
        return None
    moment = formats.moment(_now())
    return getattr(moment.tzinfo, "key", None) or moment.tzname()


def _bound_from(context: Context, component: object) -> BoundCalendar:
    found = context.get(BoundCalendar)
    if isinstance(found, BoundCalendar):
        return found
    raise ValueError(
        f"{type(component).__name__} draws part of a calendar bound to a "
        "request, and there is none here. It is drawn by Calendar.from_state()."
    )


def _slot(key: str) -> str:
    """
    The id of the element the dialog lands in, and every action targets.
    """
    return f"{key}-dialog"


@dataclass(frozen=True, slots=True)
class _Urls:
    """
    Where this calendar lives, for one request: the page it is drawn on,
    which every link and form points at, and the route of each action.
    """

    read: str
    act: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class BoundCalendar:
    """
    One calendar for one request: what was asked, the events that answered,
    and the reader's today. Every part of the calendar reads this from the
    context and builds its links from it.
    """

    declaration: _Declaration
    state: CalendarState
    events: list[Event]
    today: date
    urls: _Urls
    # Everything else the URL held, such as a table's state on the same
    # page. Every link and form sends it back unchanged.
    others: tuple[tuple[str, str], ...]
    formats: Formats

    @property
    def key(self) -> str:
        return self.declaration.key

    def href(self, **changes: Any) -> str:
        """
        This calendar with something changed. Every link on it is one of
        these.
        """
        asked = self._query(replace(self.state, **changes))
        return self.urls.read + (f"?{urlencode(asked)}" if asked else "")

    def _query(
        self, state: CalendarState, *, without: AbstractSet[str] = frozenset()
    ) -> list[tuple[str, str]]:
        """
        The query string for this calendar in state, as pairs: its own part
        under its key, apart from without, and everything else as it was.
        """
        own = [
            (self.declaration.param(name), value)
            for name, value in self._params(state).items()
            if name not in without
        ]
        return [*self.others, *own]

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


class _Declaration:
    """
    A calendar declared once, at class scope, and the route its dialog
    posts to.

    key names the route, the parameters in the URL and the element every
    response is swapped into, so it has to be unique on the page. events is
    the one part that is a function. layers are the calendars a reader can
    show and hide, save and delete are what the dialog and the popover do,
    repeats are the rules the dialog offers by key and label, and search
    is the placeholder of the search box, which exists when it is given.
    view and week_start are the defaults the URL leaves out.
    """

    def __init__(
        self,
        router: _Routes,
        *,
        key: str,
        events: EventsFor,
        layers: Sequence[Layer] = (),
        save: SaveHandler | None = None,
        delete: DeleteHandler | None = None,
        repeats: Mapping[str, str] | None = None,
        search: str | None = None,
        view: CalendarView = "week",
        week_start: WeekStart = "monday",
    ) -> None:
        self.key = key
        self.events = events
        self.layers = list(layers)
        self.save = save
        self.delete = delete
        self.repeats = dict(repeats or {})
        self.search = search
        self.view = view
        self.week_start = week_start
        self._router = router
        # One spelling of the route's name, used to register it and to find
        # it again. Two calendars on one view would otherwise both call
        # theirs "act", since the router names a route after the handler.
        self._act_route = f"{key}_act"
        self._check()
        self._register()

    def _check(self) -> None:
        if not self.key:
            raise ValueError(
                "A calendar needs a key: it is the id every response swaps "
                "into and the prefix of its parameters in the URL."
            )
        keys = [layer.key for layer in self.layers]
        for twice in {key for key in keys if keys.count(key) > 1}:
            raise ValueError(
                f"{self.key} has two layers called {twice!r}. The key is what "
                f"an event names and the URL hides, so each needs its own."
            )
        for taken in [key for key in keys if "," in key]:
            raise ValueError(
                f"{self.key} has a layer called {taken!r}. The URL joins the "
                f"hidden layers with a comma, so it would come back as two."
            )
        if self.repeats and self.save is None:
            raise ValueError(
                f"{self.key} offers repeats but has no save, and the dialog "
                f"that shows them is the dialog that saves. Give it a save."
            )

    @property
    def edits(self) -> bool:
        return self.save is not None or self.delete is not None

    def param(self, name: str) -> str:
        """
        What one part of this calendar's state is called in the URL. Under
        the key, because a page can hold two calendars.
        """
        return f"{self.key}-{name}"

    def _names(self) -> dict[str, str]:
        return {self.param(name): name for name in _STATE}

    async def draw(self, calendar: Calendar, context: Context) -> Component:
        """
        The calendar bound to the request this page is rendered for, with
        the sidebar, the search and the view options around it.

        Calendar.from_state() hands over to this. The request is already in
        the context, so the view has nothing to pass.
        """
        request = HueContext.from_context(context).request
        formats = Formats.from_context(context)
        today = _today(formats)
        asked, others = self._read(self._router._get_query_values(request), today)
        bound = await self._bind(request, asked, others, today, formats)
        return self._drawn(calendar, bound)

    def _read(
        self, values: Mapping[str, list[str]], today: date
    ) -> tuple[CalendarState, tuple[tuple[str, str], ...]]:
        """
        A query or a posted form, split into this calendar's state and
        everything else, which goes back out as it came.

        Clamped where it enters: a view, a date or a week start that is not
        one is the default, and a hidden layer nobody declared is dropped.
        Anyone can type into a query string, and it is never an error page.
        """
        names = self._names()
        # The dialog posts its fields beside the state, and they are no
        # more the page's than the framework's CSRF token is.
        skipped = {*_Posted.model_fields, *self._router._form_fields()}
        own = {names[name]: found for name, found in values.items() if name in names}
        others = tuple(
            (name, value)
            for name, found in values.items()
            if name not in names and name not in skipped
            for value in found
        )
        return self._state_from(own, today), others

    def _state_from(self, asked: Mapping[str, list[str]], today: date) -> CalendarState:
        view = _one(asked, _VIEW)
        start = _one(asked, _START)
        cursor = _day(_one(asked, _DATE) or "") or today
        declared = [layer.key for layer in self.layers]
        hidden = tuple(key for key in _many(asked, _HIDE) if key in declared)
        return CalendarState(
            date=min(max(cursor, _FIRST), _LAST),
            view=view if view in _VIEWS else self.view,  # type: ignore[arg-type]
            query=(_one(asked, _QUERY) or "").strip(),
            hidden=hidden,
            week_start=start if start in _STARTS else self.week_start,  # type: ignore[arg-type]
            weekdays=_one(asked, _WEEKDAYS) == "1",
            layers=tuple(key for key in declared if key not in hidden),
        )

    async def _bind(
        self,
        request: Any,
        asked: CalendarState,
        others: tuple[tuple[str, str], ...],
        today: date,
        formats: Formats,
        urls: _Urls | None = None,
    ) -> BoundCalendar:
        events = await self._router._run_sync(self._fetch, request, asked)
        return BoundCalendar(
            self, asked, events, today, urls or self._urls_for(request), others, formats
        )

    def _fetch(self, request: Any, asked: CalendarState) -> list[Event]:
        """
        events(), run off the event loop by the router and materialised
        there, each event in its layer's colour unless it chose its own.
        """
        colors = {layer.key: layer.color for layer in self.layers}
        found: list[Event] = []
        for returned in self.events(request, asked):
            if not isinstance(returned, Event):
                raise TypeError(
                    f"{self.key}: events() returned {returned!r}, which is not an "
                    f"Event. Build one per row: Event(title, starts, ends)."
                )
            own = colors.get(returned.layer or "")
            if returned.color is None and own is not None:
                found.append(replace(returned, color=own))
            else:
                found.append(returned)
        return found

    def _urls_for(self, request: Any) -> _Urls:
        return _Urls(
            read=self._router._url_for(request, PAGE_ROUTE),
            act={
                name: self._router._url_for(request, self._act_route, action=name)
                for name in (_ACTIONS if self.edits else ())
            },
        )

    def _drawn(self, calendar: Calendar, bound: BoundCalendar) -> ComponentType:
        """
        The whole thing for one binding: the sidebar, then the search and
        the view options above the calendar, inside the component that
        offers the binding to every part of it.
        """
        state = bound.state
        calendar.id(self.key).view(state.view).date(state.date).today(bound.today)
        calendar.week_start(state.week_start).weekdays(state.weekdays)
        calendar.events(bound.events)
        calendar.href(lambda day, view: bound.href(date=day, view=view))
        if self.save is not None:
            # A click on an empty slot or day opens the dialog with that
            # time filled in. Only the calendar hears it: the sidebar's
            # picker has day cells of its own.
            calendar.x_on("click", unsafe("slot($event)"))
        if self.edits:
            calendar.actions(lambda event: _event_actions(bound, event))
        return _Frame(bound).content(
            _Side(),
            html.div(_Band(), calendar, class_="flex min-w-0 flex-1 flex-col gap-3"),
        )

    def _draft(self, posted: _Posted) -> tuple[Event | None, dict[str, str]]:
        """
        The posted fields as an Event, or what is wrong with them by field.
        """
        errors: dict[str, str] = {}
        title = posted.title.strip()
        if not title:
            errors["title"] = "Give the event a title."
        starts, ends = _when(posted, errors)
        layer = posted.layer or None
        if self.layers and layer not in {each.key for each in self.layers}:
            errors["layer"] = "Choose a calendar."
        repeat = posted.repeat or None
        if repeat is not None and repeat not in self.repeats:
            errors["repeat"] = "Choose how it repeats."
        if errors or starts is None or ends is None:
            return None, errors
        return Event(
            title,
            starts,
            ends,
            id=posted.id or None,
            location=posted.location.strip() or None,
            notes=posted.notes.strip() or None,
            repeat=repeat,
            layer=layer,
        ), {}

    def _overlapping(
        self, request: Any, asked: CalendarState, draft: Event, formats: Formats
    ) -> list[Event]:
        """
        The timed events that share a moment with the draft, apart from
        the draft itself, from events() asked for the days it covers.
        """
        first, last = draft.span(formats)
        # first and last follow the view, and the draft can be on any day,
        # so a copy of the state is widened to reach it by hand.
        covering = replace(asked)
        object.__setattr__(covering, "first", min(asked.first, first))
        object.__setattr__(covering, "last", max(asked.last, last))
        starts, ends = draft.moments(formats)
        found = []
        for event in self._fetch(request, covering):
            if not event.timed or (event.id is not None and event.id == draft.id):
                continue
            opens, closes = event.moments(formats)
            if opens.tzinfo is not None:
                opens, closes = opens.replace(tzinfo=None), closes.replace(tzinfo=None)
            if opens < ends and closes > starts:
                found.append(event)
        return found

    def _dialog(
        self, bound: BoundCalendar, posted: _Posted, errors: Mapping[str, str]
    ) -> ComponentType:
        """
        The event dialog, open, over the posted fields: a new event, or an
        existing one when they carry an id.
        """
        key = bound.key
        editing = bool(posted.id)
        all_day = bool(posted.all_day)
        form_id = f"{key}-form"
        layers = [(layer.key, layer.name) for layer in self.layers]
        week_start = bound.state.week_start

        def when(label: str, name: str) -> list[ComponentType]:
            day = _day(getattr(posted, name))
            moment = _clock(getattr(posted, f"{name}_time"))
            day_field = DateInput().name(name).label(label).week_start(week_start)
            time_field = TimeInput().name(f"{name}_time").label(f"{label} at")
            if day is not None:
                day_field.value(day)
            if moment is not None:
                time_field.value(moment)
            # Hidden rather than removed while all day is on, so the times
            # come back when it is switched off again. The route ignores
            # them for a whole-day event.
            return [day_field, html.div(time_field, **{"x-show": "!allDay"})]

        form = (
            Form()
            .id(form_id)
            .action(bound.urls.act[_SAVE])
            .method("post")
            .errors(errors)
            .class_("gap-4")
            .content(
                *_carried(bound),
                render_when(
                    editing, html.input_(type="hidden", name="id", value=posted.id)
                ),
                _title_field(posted.title),
                Switch()
                .name("all_day")
                .label("All day")
                .checked(all_day)
                .x_model(unsafe("allDay")),
                html.div(
                    *when("Starts", "starts"),
                    *when("Ends", "ends"),
                    class_="grid grid-cols-2 gap-3",
                ),
                render_when(
                    bool(layers or self.repeats),
                    html.div(
                        render_when(
                            bool(layers),
                            NativeSelect()
                            .name("layer")
                            .label("Calendar")
                            .options(layers)
                            .value(posted.layer or (layers[0][0] if layers else "")),
                        ),
                        render_when(
                            bool(self.repeats),
                            NativeSelect()
                            .name("repeat")
                            .label("Repeat")
                            .options([("", "Does not repeat"), *self.repeats.items()])
                            .value(posted.repeat),
                        ),
                        class_="grid grid-cols-2 gap-3",
                    ),
                ),
                TextInput()
                .name("location")
                .label("Location")
                .value(posted.location)
                .placeholder("Room, address or link")
                .leading_icon(HueIcon("map-pin")),
                Textarea().name("notes").label("Notes").value(posted.notes).rows(3),
                # Where the overlap warning lands, and announced when it
                # does, since it arrives while the reader is elsewhere.
                html.div(id=f"{key}-overlap", role="status"),
            )
        )
        form._attrs.update(
            {
                "x-target": _slot(key),
                # The route says what is wrong, on the field, so the
                # browser's own bubbles are not a second opinion.
                "novalidate": True,
                "x-data": f"{{ allDay: {json.dumps(all_day)} }}",
                # Asked again whenever a field settles, which the date and
                # time fields announce as a change once a value is read.
                "@change.debounce.200ms": _overlaps_check(bound),
            }
        )
        footer = [
            render_when(
                editing and self.delete is not None,
                Button()
                .variant("ghost")
                .type("submit")
                .form(form_id)
                .formaction(bound.urls.act[_DELETE])
                .class_("me-auto text-danger-text")
                .content("Delete"),
            ),
            Button().variant("ghost").content("Cancel").x_on("click", close()),
            Button()
            .variant("primary")
            .type("submit")
            .form(form_id)
            .content("Save changes" if editing else "Save event"),
        ]
        return (
            Dialog()
            .open()
            .size("lg")
            .title("Edit event" if editing else "New event")
            .content(form)
            .footer(*footer)
        )

    def _register(self) -> None:
        """
        The one route the dialog and the popover post to, when there is
        anything to post. Reading needs no route of its own: the page the
        calendar is drawn on reads its state from the query string.
        """
        if not self.edits:
            return

        async def act(
            view: Any, request: Any, context: Any, action: str, body: _Posted
        ) -> Any:
            # Delete is the one action the delete handler serves; the dialog,
            # the overlap check and a save all need the save handler.
            handler = self.delete if action == _DELETE else self.save
            refused = None
            if action not in _ACTIONS or handler is None:
                refused = f"{self.key} has no action called {action!r}."
            elif action == _DELETE and not body.id:
                refused = f"{self.key}: delete needs the event's id."
            if refused is not None or handler is None:
                return HueResponse(
                    component=html.p(refused or ""), status_code=HTTPStatus.NOT_FOUND
                )
            # Before the handler, so a view with no page to draw the
            # calendar on is an error before anything is written. The
            # state comes in the body, from fields the dialog and the
            # popover's buttons carry.
            urls = self._urls_for(request)
            formats: Formats = context.formats
            today = _today(formats)
            asked, others = self._read(self._router._get_form_values(request), today)
            bound = BoundCalendar(self, asked, [], today, urls, others, formats)

            if action == _DIALOG:
                shown = _prefilled(body, asked, self.layers)
                return HueResponse(
                    component=self._dialog(bound, shown, {}), target=_slot(self.key)
                )
            if action == _OVERLAPS:
                return await self._checked(request, bound, body)
            if action == _SAVE:
                draft, errors = self._draft(body)
                if draft is None:
                    return HueResponse(
                        component=self._dialog(bound, body, errors),
                        target=_slot(self.key),
                        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                    )
                return await self._changed(
                    request, bound, handler, draft, "Save" if draft.id else "Create"
                )
            return await self._changed(request, bound, handler, body.id, "Delete")

        act.__name__ = self._act_route
        self._router.fragment_post(f"{self.key}/<str:action>/")(act)

    async def _checked(self, request: Any, bound: BoundCalendar, body: _Posted) -> Any:
        """
        The overlap warning for the fields as they stand, or nothing, in
        the dialog's own region.
        """
        draft, _ = self._draft(body)
        found = (
            await self._router._run_sync(
                self._overlapping, request, bound.state, draft, bound.formats
            )
            if draft is not None and draft.timed
            else []
        )
        return HueResponse(
            component=_overlap_warning(found, bound.formats),
            target=f"{self.key}-overlap",
        )

    async def _changed(
        self,
        request: Any,
        bound: BoundCalendar,
        handler: Callable[..., Any],
        given: Event | str,
        verb: str,
    ) -> Any:
        """
        The calendar after a handler has run, with a toast saying what
        happened, or what failed.
        """
        status = HTTPStatus.OK
        try:
            await self._router._run_sync(handler, request, given)
        except Exception as error:
            # A permission denied or a not found is the framework's own
            # answer, and it gives it.
            if self._router._passes_through(error):
                raise
            # Logged with its traceback, since nothing is raised for an
            # error tracker to catch. The reader is told on the page.
            _log.exception("%s: %s failed", self.key, verb.lower())
            toast.danger(
                f"{verb} failed", description="The calendar is shown as it is now."
            )
            status = HTTPStatus.INTERNAL_SERVER_ERROR
        else:
            named = given.title if isinstance(given, Event) else "event"
            toast.success(f'{_DONE[verb]} "{named}"')
        # Drawn after, because the events have just changed under it. The
        # whole thing, with an empty slot: the response targets the slot,
        # which closes the dialog, and the synced parts refresh.
        redrawn = await self._bind(
            request, bound.state, bound.others, bound.today, bound.formats, bound.urls
        )
        return HueResponse(
            component=self._drawn(Calendar(), redrawn), status_code=status
        )


# What a toast says once a change has been made.
_DONE = {"Create": "Created", "Save": "Saved", "Delete": "Deleted"}


# What a view calls, at class scope, to declare a calendar.
build_calendar_state = _Declaration


def _when(
    posted: _Posted, errors: dict[str, str]
) -> tuple[date | datetime | None, date | datetime | None]:
    """
    When the posted fields say the event is, adding what is wrong with
    them to errors: whole days when all day is on, naive moments in the
    reader's time otherwise. A timed event has to end after it starts; a
    whole-day one may end on the day it starts.
    """
    all_day = bool(posted.all_day)
    first, last = _day(posted.starts), _day(posted.ends)
    if first is None:
        errors["starts"] = "Enter a date."
    if last is None:
        errors["ends"] = "Enter a date."
    starts: date | datetime | None = first
    ends: date | datetime | None = last
    if not all_day:
        opens, closes = _clock(posted.starts_time), _clock(posted.ends_time)
        if opens is None:
            errors["starts_time"] = "Enter a time."
        if closes is None:
            errors["ends_time"] = "Enter a time."
        starts = datetime.combine(first, opens) if first and opens else None
        ends = datetime.combine(last, closes) if last and closes else None
    if starts is None or ends is None:
        return starts, ends
    if ends < starts:
        errors["ends" if all_day else "ends_time"] = "Ends before it starts."
    elif ends == starts and not all_day:
        errors["ends_time"] = "Starts and ends at the same time."
    return starts, ends


def _prefilled(
    posted: _Posted, asked: CalendarState, layers: Sequence[Layer]
) -> _Posted:
    """
    What a new event starts with when the request said nothing: an hour
    from nine on the day the view is around, in the first layer.
    """
    filled = posted
    if not posted.starts:
        day = asked.date.isoformat()
        filled = filled.model_copy(
            update={
                "starts": day,
                "starts_time": _NEW_STARTS.strftime("%H:%M"),
                "ends": day,
                "ends_time": _NEW_ENDS.strftime("%H:%M"),
            }
        )
    if not posted.layer and layers:
        filled = filled.model_copy(update={"layer": layers[0].key})
    return filled


def _fields(event: Event, formats: Formats) -> dict[str, str | None]:
    """
    An event as the dialog's fields, for the popover's actions to post.
    """
    if event.timed:
        starts, ends = event.moments(formats)
        when = {
            "starts": starts.date().isoformat(),
            "starts_time": starts.strftime("%H:%M"),
            "ends": ends.date().isoformat(),
            "ends_time": ends.strftime("%H:%M"),
        }
    else:
        first, last = event.span(formats)
        when = {"all_day": "1", "starts": first.isoformat(), "ends": last.isoformat()}
    return {
        "id": event.id,
        "title": event.title,
        **when,
        "layer": event.layer,
        "location": event.location,
        "notes": event.notes,
        "repeat": event.repeat,
    }


def _title_field(value: str) -> ComponentType:
    """
    The title, which the dialog opens on. The attribute is autofocus itself
    rather than x-autofocus alone: the focus trap reads the one and Alpine
    AJAX the other, and the dialog is only ever fetched, never on a page as
    it loads, so the attribute cannot steal focus there.
    """
    field = (
        TextInput()
        .name("title")
        .label("Title")
        .value(value)
        .placeholder("Design review")
        .autocomplete("off")
        .required()
        .x_autofocus()
    )
    field._attrs["autofocus"] = True
    return field


def _overlaps_check(bound: BoundCalendar) -> str:
    """
    The request the dialog makes when a field settles: the form as it
    stands, answered with the warning or with nothing.
    """
    url, target = bound.urls.act[_OVERLAPS], f"{bound.key}-overlap"
    return (
        f"$ajax({json.dumps(url)}, {{ method: 'post', target: {json.dumps(target)}, "
        f"body: new FormData($el) }})"
    )


def _overlap_warning(found: list[Event], formats: Formats) -> ComponentType:
    """
    Which events the draft overlaps, two by name and the rest counted, or
    nothing. A warning rather than a refusal: two meetings at once is a
    choice the reader may be making on purpose.
    """
    if not found:
        return ""

    def named(event: Event) -> str:
        starts, ends = event.moments(formats)
        return (
            f"{event.title} ({starts.strftime(formats.time)} to "
            f"{ends.strftime(formats.time)})"
        )

    text = " and ".join(named(event) for event in found[:2])
    if len(found) > 2:
        text += f" and {len(found) - 2} more"
    return html.p(
        HueIcon("triangle-alert").class_("mt-0.5 size-4 flex-none"),
        html.span(f"Overlaps {text}."),
        class_="flex items-start gap-2 text-sm text-warning-text",
    )


def _event_actions(bound: BoundCalendar, event: Event) -> list[ComponentType]:
    """
    The popover's buttons: Edit opens the dialog over the event's fields,
    Duplicate saves a copy of them, Delete removes it. Each posts the state
    too, so the calendar comes back as it was.
    """
    declared = bound.declaration
    slot = _slot(bound.key)
    carried: dict[str, Any] = dict(bound._query(bound.state))
    fields = {**carried, **_fields(event, bound.formats)}

    def then_close(expression: Expression) -> Expression:
        # The popover first, which hands focus back to the event, so the
        # dialog that follows has somewhere to return it.
        return unsafe(f"{close()}; {expression}")

    actions: list[ComponentType] = []
    if declared.save is not None:
        actions.append(
            Button()
            .variant("outline")
            .size("sm")
            .content(HueIcon("pencil"), "Edit")
            .x_on(
                "click",
                then_close(
                    ajax(
                        bound.urls.act[_DIALOG], method="post", target=slot, body=fields
                    )
                ),
            )
        )
        actions.append(
            Button()
            .variant("ghost")
            .size("sm")
            .content(HueIcon("copy"), "Duplicate")
            .x_on(
                "click",
                then_close(
                    ajax(
                        bound.urls.act[_SAVE],
                        method="post",
                        target=slot,
                        # A copy of this occurrence alone, with a title that
                        # says so, the way the design duplicates.
                        body={
                            **fields,
                            "id": None,
                            "repeat": None,
                            "title": f"{event.title} (copy)",
                        },
                    )
                ),
            )
        )
    if declared.delete is not None and event.id is not None:
        actions.append(
            Button()
            .variant("ghost")
            .size("sm")
            .icon_only("Delete event")
            .class_("ms-auto")
            .content(HueIcon("trash-2"))
            .x_on(
                "click",
                then_close(
                    ajax(
                        bound.urls.act[_DELETE],
                        method="post",
                        target=slot,
                        body={**carried, "id": event.id, "title": event.title},
                    )
                ),
            )
        )
    return actions


def _carried(
    bound: BoundCalendar,
    *,
    form: str | None = None,
    without: AbstractSet[str] = frozenset(),
    state: CalendarState | None = None,
) -> tuple[ComponentType, ...]:
    """
    The URL's state apart from this calendar's without, as hidden fields,
    tied to form when they sit outside it.
    """
    return tuple(
        html.input_(type="hidden", name=name, value=value, form=form)
        for name, value in bound._query(state or bound.state, without=without)
    )


def _marked(bound: BoundCalendar) -> list[date]:
    """
    Every day between first and last with something on it, for the
    sidebar's picker.
    """
    days: set[date] = set()
    for event in bound.events:
        first, last = event.span(bound.formats)
        day = max(first, bound.state.first)
        while day <= min(last, bound.state.last):
            days.add(day)
            day += timedelta(days=1)
    return sorted(days)


def _matches(bound: BoundCalendar) -> str:
    """
    How many events the search found among the days the view shows, in
    words, or nothing when there is no search.
    """
    query = bound.state.query
    if not query:
        return ""
    first, last = bound.state.days
    count = 0
    for event in bound.events:
        opens, closes = event.span(bound.formats)
        if opens <= last and closes >= first:
            count += 1
    if count == 0:
        return f'No events match "{query}".'
    events = "1 event matches" if count == 1 else f"{count} events match"
    return f'{events} "{query}".'


# ----------------------------------------------------------------------
# The components a bound calendar draws itself with
# ----------------------------------------------------------------------


class _Frame(ChainableComponent):
    """
    Offers one binding to every part of a calendar rendered inside it, and
    holds the slot the dialog lands in.

    Its x-data is hueCalendar: whether the sidebar is open on a narrow
    screen, and the click on an empty slot that opens the dialog.
    """

    category: ClassVar[str | None] = None

    def __init__(self, bound: BoundCalendar) -> None:
        super().__init__()
        self._bound = bound

    def htmy_context(self) -> Context:
        return {BoundCalendar: self._bound}

    def _render(self, context: Context) -> Component:
        bound = self._bound
        config = {
            "url": bound.urls.act.get(_DIALOG),
            "target": _slot(bound.key),
            # Where the state is read from at the click, since this root
            # is drawn once and the state moves under it.
            "state": f"{bound.key}-state",
            "home": f"{bound.key}-new",
            "hour": views._HOUR,
        }
        return html.div(
            *self._children,
            html.div(id=_slot(bound.key)),
            class_="flex flex-col gap-4 lg:flex-row lg:items-start",
            **{"x-data": call("hueCalendar", config)},
        )


class _Side(ChainableComponent):
    """
    The sidebar: New event, a picker to jump by, the calendars to show and
    hide, and which timezone the times are in.

    Synced, so every response refreshes it: the picker's marks and the
    state the toolbar's forms carry both live here. Below lg it is hidden
    until the button in the toolbar opens it.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        declared, state, key = bound.declaration, bound.state, bound.key
        formats = bound.formats
        view = f"{key}-view"
        # Picking a day in the year view goes to that day; elsewhere the
        # view stays and moves to it.
        picked = replace(state, view="day" if state.view == "year" else state.view)
        return html.aside(
            render_when(
                declared.save is not None,
                Button()
                .variant("primary")
                .id(f"{key}-new")
                .content(HueIcon("plus"), "New event")
                .x_on("click", unsafe("create()")),
            ),
            html.form(
                DatePicker()
                .name(declared.param(_DATE))
                .id(f"{key}-picker")
                .label("Go to a day")
                .size("sm")
                .value(state.date)
                .week_start(state.week_start)
                .markers(*_marked(bound))
                # Named so nothing in the picker's own scope, which has a
                # day() of its own, can stand in for it.
                .x_model(unsafe("pickedDay")),
                *_carried(bound, without={_DATE}, state=picked),
                method="get",
                action=bound.urls.read,
                **swap(view),
                **{
                    "x-data": (
                        f"{{ pickedDay: {json.dumps([state.date.isoformat()])} }}"
                    ),
                    # After the tick, so the picker's hidden field holds
                    # the new day before the form reads it.
                    "x-init": (
                        "$watch('pickedDay', "
                        "() => $nextTick(() => $el.requestSubmit()))"
                    ),
                },
            ),
            render_when(
                bool(declared.layers),
                html.section(
                    html.h2("Calendars", class_=_SIDE_HEADING),
                    html.ul(
                        *(_layer_row(bound, layer) for layer in declared.layers),
                        class_="flex flex-col gap-2",
                    ),
                    # The boxes sit outside the form, so they are read and
                    # never submitted: a box can only submit itself while
                    # it is ticked, and what the URL wants is the ones that
                    # are not. One hidden field carries those, left out of
                    # the URL while there are none.
                    html.form(
                        html.input_(
                            type="hidden",
                            name=declared.param(_HIDE),
                            **{
                                ":value": "hiddenLayers.join(',')",
                                ":disabled": "!hiddenLayers.length",
                            },
                        ),
                        *_carried(bound, without={_HIDE}),
                        method="get",
                        action=bound.urls.read,
                        hidden=True,
                        **swap(view),
                        **{"x-ref": "form"},
                    ),
                    class_="flex flex-col gap-2",
                    **{
                        "x-data": (
                            f"{{ hiddenLayers: {json.dumps(list(state.hidden))} }}"
                        )
                    },
                ),
            ),
            render_if(
                _timezone(formats),
                lambda name: html.p(
                    HueIcon("clock").class_("size-3.5 flex-none"),
                    f"Times in {name.replace('_', ' ')}",
                    class_="flex items-center gap-1.5 text-xs text-fg-muted",
                ),
            ),
            # What the toolbar's forms send besides their own part, tied to
            # each by id, and the whole state for the script that opens the
            # dialog from a click.
            html.div(
                *_carried(bound, form=f"{key}-search", without={_QUERY}),
                *_carried(bound, form=f"{key}-options", without={_START, _WEEKDAYS}),
                html.div(*_carried(bound), id=f"{key}-state"),
                hidden=True,
            ),
            id=f"{key}-side",
            aria_label="Calendar tools",
            class_="w-full flex-none flex-col gap-5 lg:flex lg:w-60",
            **{":class": "side ? 'flex' : 'hidden lg:flex'", **SYNC},
        )


def _layer_row(bound: BoundCalendar, layer: Layer) -> ComponentType:
    """
    One calendar in the sidebar: a box ticked while it shows, and its
    colour. The boxes are read from the scope, which the click changes.
    """
    key = json.dumps(layer.key)
    return html.li(
        Checkbox()
        .name(f"{bound.key}-show")
        .value(layer.key)
        .label(layer.name)
        .checked(layer.key not in bound.state.hidden)
        .id(f"{bound.key}-show-{layer.key}")
        .class_("flex-1")
        .x_on(
            "change",
            unsafe(
                f"hiddenLayers = $event.target.checked "
                f"? hiddenLayers.filter(k => k !== {key}) : [...hiddenLayers, {key}]; "
                f"$nextTick(() => $refs.form.requestSubmit())"
            ),
        ),
        html.span(
            aria_hidden="true",
            class_=classnames("size-2.5 flex-none rounded-xs", _SOLID[layer.color]),
        ),
        class_="flex items-center gap-3",
    )


class _Band(ChainableComponent):
    """
    The row above the calendar: the button that opens the sidebar on a
    narrow screen, the search, how many it found, and the view options.

    Left alone by every response, so the search keeps its caret and an
    open options panel stays open; the count inside it is synced by id.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        declared, key = bound.declaration, bound.key
        return html.div(
            Button()
            .variant("ghost")
            .size("sm")
            .icon_only("Calendar tools")
            .class_("lg:hidden")
            .aria_controls(f"{key}-side")
            .content(HueIcon("panel-left"))
            .x_on("click", unsafe("side = !side"))
            .x_bind("aria-expanded", unsafe("side")),
            render_when(declared.search is not None, _search_form(bound)),
            render_when(
                declared.search is not None,
                html.span(
                    _matches(bound),
                    id=f"{key}-matches",
                    role="status",
                    class_="text-sm tabular-nums text-fg-muted",
                    **SYNC,
                ),
            ),
            html.span(class_="flex-1"),
            _options(bound),
            class_="flex flex-wrap items-center gap-2",
        )


def _search_form(bound: BoundCalendar) -> ComponentType:
    """
    The search box's own GET form, so Enter submits it and it works with
    Alpine off; typing submits it after a pause.
    """
    declared, key = bound.declaration, bound.key
    return html.form(
        SearchInput()
        .name(declared.param(_QUERY))
        .id(f"{key}-{_QUERY}")
        .size("sm")
        .label(declared.search or "")
        .hidden_label()
        .placeholder(declared.search or "")
        .value(bound.state.query)
        .leading_icon(HueIcon("search"))
        # Stopped, so an escape that empties the box is not also an escape
        # that closes whatever the calendar is inside.
        .x_on(
            "keydown.escape",
            unsafe(
                "if ($el.value) { $event.stopPropagation(); $el.value = ''; "
                "$el.form.requestSubmit() }"
            ),
        ),
        id=f"{key}-search",
        method="get",
        action=bound.urls.read,
        class_="min-w-0 flex-1 basis-56 sm:max-w-[320px]",
        **{
            # replace rather than push: a word typed at speed would
            # otherwise be a history entry per pause in it.
            "x-target.replace": f"{key}-view",
            f"@input.debounce.{SEARCH_DELAY}": "$el.requestSubmit()",
        },
    )


def _options(bound: BoundCalendar) -> ComponentType:
    """
    The view options behind one button: which day the week starts on, and
    whether to leave the weekend out. A GET form that submits itself on
    any change, like the table's filters.
    """
    declared, state, key = bound.declaration, bound.state, bound.key
    names = bound.formats.day_names
    return (
        Popover()
        .fit()
        .placement("bottom-end")
        .label("View options")
        .trigger(
            Button()
            .variant("ghost")
            .size("sm")
            .icon_only("View options")
            .content(HueIcon("sliders-horizontal"))
        )
        .content(
            html.form(
                RadioGroup()
                .name(declared.param(_START))
                .id(f"{key}-{_START}")
                .legend("Week starts on")
                .value(state.week_start)
                .content(
                    *(
                        Radio().value(day).label(names[WEEKDAYS.index(day)])
                        for day in _STARTS
                    )
                ),
                Checkbox()
                .name(declared.param(_WEEKDAYS))
                .id(f"{key}-{_WEEKDAYS}")
                .value("1")
                .label("Weekdays only")
                .checked(state.weekdays),
                id=f"{key}-options",
                method="get",
                action=bound.urls.read,
                class_="flex w-52 flex-col gap-4",
                **swap(f"{key}-view"),
                **{"@change": "$el.requestSubmit()"},
            )
        )
    )
