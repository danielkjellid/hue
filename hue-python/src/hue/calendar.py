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
as the reader left it. The fields are posted under the key like the state,
{key}-title and {key}-starts, which is also what their ids are.

events() and the handlers run off the event loop, through the router,
because both usually use the ORM and the ORM refuses to run on the loop.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, fields, replace
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from http import HTTPStatus
from typing import Any, ClassVar, get_args

from htmy import Context, html

from hue import toast
from hue._declared import (
    Bound,
    Declaration,
    Routes,
    Urls,
    bound_from,
    carried,
    many,
    one,
    search_form,
)
from hue.context import HueContext
from hue.formats import Formats
from hue.js import Expression, ajax, call, close, unsafe
from hue.router import HueResponse
from hue.types.core import Component, ComponentType
from hue.ui._styles import PANEL_LABEL
from hue.ui.atoms.button import Button
from hue.ui.atoms.checkbox import Checkbox
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import TextInput
from hue.ui.atoms.native_select import NativeSelect
from hue.ui.atoms.radio import Radio, RadioGroup
from hue.ui.atoms.switch import Switch
from hue.ui.atoms.textarea import Textarea
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _calendar_views as views
from hue.ui.molecules._calendar_views import FIRST, LAST, CalendarView
from hue.ui.molecules._days import EventColor, month_grid, week_of
from hue.ui.molecules.calendar import Calendar, Event
from hue.ui.molecules.date_input import DateInput, TimeInput
from hue.ui.molecules.date_picker import WEEKDAYS, DatePicker, Weekday
from hue.ui.molecules.dialog import Dialog
from hue.ui.molecules.form import Form
from hue.ui.molecules.popover import Popover
from hue.ui.navigation import SYNC, swap
from hue.utils import classnames, render_if, render_when

__all__ = ["CalendarState", "Layer", "build_calendar_state"]

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

# YYYY-MM-DD and HH:MM and nothing else; fromisoformat would also take
# 20261014 and 09:30:15.
_DAY_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_CLOCK_PATTERN = re.compile(r"\d{2}:\d{2}")

# A new event with no time of its own starts at nine, and a new event
# runs an hour unless that would take it past the end of its day.
_NEW_STARTS = time(9)
_NEW_LASTS = timedelta(hours=1)

# The most days an event may run, a year, which is also the longest view.
# A draft past that would have events() asked for thousands of days at
# every change of a field.
_LONGEST = 366


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


@dataclass(frozen=True, slots=True)
class _Posted:
    """
    The dialog's fields as the form posts them, every one text, so that a
    value that cannot be read is an error on its field and never a 422
    nobody drew. Each is posted under the key, like the state, so a page
    parameter called title is nobody's business but the page's.
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


_FIELDS = tuple(each.name for each in fields(_Posted))


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


def _exists(moment: datetime, zone: tzinfo) -> bool:
    """
    Whether a naive time is one the clocks in zone show that day. The hour
    they skip going forward is not, and zoneinfo would answer for it with
    the hour after and say nothing.
    """
    aware = moment.replace(tzinfo=zone)
    return aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == moment


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
    others: tuple[tuple[str, str], ...]
    formats: Formats

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


class _Declaration(Declaration[Routes]):
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
        router: Routes,
        *,
        key: str,
        events: EventsFor,
        layers: Sequence[Layer] = (),
        save: SaveHandler | None = None,
        delete: DeleteHandler | None = None,
        repeats: Mapping[str, str] | None = None,
        search: str | None = None,
        view: CalendarView = "week",
        week_start: Weekday = "monday",
    ) -> None:
        super().__init__(router, key)
        self.events = events
        self.layers = list(layers)
        self.save = save
        self.delete = delete
        self.repeats = dict(repeats or {})
        self.search = search
        self.view = view
        self.week_start = week_start
        self._check()
        if self.edits:
            self._register_route(self._served(), self._act)

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

    def _served(self) -> tuple[str, ...]:
        """
        The actions the route serves: the dialog, the overlap check and a
        save with a save handler, and a delete with a delete handler.
        """
        saves = (_DIALOG, _OVERLAPS, _SAVE) if self.save is not None else ()
        return (*saves, *((_DELETE,) if self.delete is not None else ()))

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
        asked, _, others = self._read(self._router._get_query_values(request), today)
        bound = await self._bind(request, asked, others, today, formats)
        return self._drawn(calendar, bound)

    def _read(
        self, values: Mapping[str, list[str]], today: date
    ) -> tuple[CalendarState, _Posted, tuple[tuple[str, str], ...]]:
        """
        A query or a posted form, split into this calendar's state, the
        dialog's fields, and everything else, which goes back out as it
        came. The first two are the names under the key; the framework's
        own field, its CSRF token, is nobody's and goes nowhere.

        Clamped where it enters: a view, a date or a week start that is not
        one is the default, and a hidden layer nobody declared is dropped.
        Anyone can type into a query string, and it is never an error page.
        """
        own, others = self._split(values, (*_STATE, *_FIELDS))
        given = {name: one(own, name) or "" for name in _FIELDS if name in own}
        return self._state_from(own, today), _Posted(**given), others

    def _state_from(self, asked: Mapping[str, list[str]], today: date) -> CalendarState:
        view = one(asked, _VIEW)
        start = one(asked, _START)
        cursor = _day(one(asked, _DATE) or "") or today
        declared = [layer.key for layer in self.layers]
        hidden = tuple(key for key in many(asked, _HIDE) if key in declared)
        return CalendarState(
            date=min(max(cursor, FIRST), LAST),
            view=view if view in _VIEWS else self.view,  # type: ignore[arg-type]
            query=(one(asked, _QUERY) or "").strip(),
            hidden=hidden,
            week_start=start if start in WEEKDAYS else self.week_start,  # type: ignore[arg-type]
            weekdays=one(asked, _WEEKDAYS) == "1",
            layers=tuple(key for key in declared if key not in hidden),
        )

    async def _bind(
        self,
        request: Any,
        asked: CalendarState,
        others: tuple[tuple[str, str], ...],
        today: date,
        formats: Formats,
        urls: Urls | None = None,
    ) -> BoundCalendar:
        events = await self._router._run_sync(self._fetch, request, asked)
        return BoundCalendar(
            self,
            asked,
            events,
            today,
            urls or self._urls_for(request, self._served()),
            others,
            formats,
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
            # Under the internal key, so a click handler of the page's own
            # on the Calendar is kept beside it.
            calendar._attrs["x-on:click"] = "calendarSlot($event)"
        if self.edits:
            calendar.actions(lambda event: _event_actions(bound, event))
        return _Frame(bound).content(
            _Side(),
            html.div(_Band(), calendar, class_="flex min-w-0 flex-1 flex-col gap-3"),
        )

    def _draft(
        self, posted: _Posted, formats: Formats
    ) -> tuple[Event | None, dict[str, str]]:
        """
        The posted fields as an Event, or what is wrong with them by field.
        """
        errors: dict[str, str] = {}
        title = posted.title.strip()
        if not title:
            errors["title"] = "Give the event a title."
        starts, ends = _when(posted, errors, _zone(formats))
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
        the draft itself: events() asked for the draft's own days, in every
        layer and with no search, since an event the reader has hidden or
        searched away is still in the way.
        """
        first, last = draft.span(formats)
        # events() reads first and last, which follow the view, so a copy
        # of the state is pointed at the draft's days by hand.
        covering = replace(
            asked,
            query="",
            hidden=(),
            layers=tuple(layer.key for layer in self.layers),
        )
        object.__setattr__(covering, "first", first)
        object.__setattr__(covering, "last", last)
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
        self,
        bound: BoundCalendar,
        posted: _Posted,
        errors: Mapping[str, str],
        *,
        csrf_token: str,
    ) -> ComponentType:
        """
        The event dialog, open, over the posted fields: a new event, or an
        existing one when they carry an id. The form carries the
        framework's CSRF token, so it still posts where the script has
        failed and the browser submits it on its own.
        """
        key = bound.key
        csrf_field = self._router._csrf_field()
        editing = bool(posted.id)
        all_day = bool(posted.all_day)
        form_id = f"{key}-form"
        layers = [(layer.key, layer.name) for layer in self.layers]
        week_start = bound.state.week_start
        # The controls are named under the key, which is also what makes
        # their ids the calendar's own on a page with two of them.
        param = self.param

        def when(label: str, name: str) -> list[ComponentType]:
            day = _day(getattr(posted, name))
            moment = _clock(getattr(posted, f"{name}_time"))
            day_field = DateInput().name(param(name)).label(label)
            day_field.week_start(week_start)
            time_field = TimeInput().name(param(f"{name}_time")).label(f"{label} at")
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
            .errors({param(name): message for name, message in errors.items()})
            .class_("gap-4")
            .content(
                *carried(bound._query(bound.state)),
                render_if(
                    csrf_field,
                    lambda name: html.input_(
                        type="hidden", name=name, value=csrf_token
                    ),
                ),
                render_when(
                    editing,
                    html.input_(type="hidden", name=param("id"), value=posted.id),
                ),
                _title_field(param("title"), posted.title),
                Switch()
                .name(param("all_day"))
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
                            .name(param("layer"))
                            .label("Calendar")
                            .options(layers)
                            .value(posted.layer or (layers[0][0] if layers else "")),
                        ),
                        render_when(
                            bool(self.repeats),
                            NativeSelect()
                            .name(param("repeat"))
                            .label("Repeat")
                            .options([("", "Does not repeat"), *self.repeats.items()])
                            .value(posted.repeat),
                        ),
                        class_="grid grid-cols-2 gap-3",
                    ),
                ),
                TextInput()
                .name(param("location"))
                .label("Location")
                .value(posted.location)
                .placeholder("Room, address or link")
                .leading_icon(HueIcon("map-pin")),
                Textarea()
                .name(param("notes"))
                .label("Notes")
                .value(posted.notes)
                .rows(3),
                # Where the overlap warning lands, and announced when it
                # does, since it arrives while the reader is elsewhere.
                html.div(id=_overlap(key), role="status"),
            )
        )
        form.x_data(f"{{ allDay: {json.dumps(all_day)} }}")
        # Asked again whenever a field settles, which the date and time
        # fields announce as a change once a value is read.
        form._attrs["x-on:change.debounce.200ms"] = _overlaps_check(bound)
        # Neither has a modifier. The route says what is wrong, on the
        # field, so the browser's own bubbles are not a second opinion.
        form._attrs.update({"x-target": _slot(key), "novalidate": True})
        footer = [
            # Built only where there is a delete route to point it at.
            render_if(
                bound.urls.act.get(_DELETE) if editing else None,
                lambda url: Button()
                .variant("ghost")
                .type("submit")
                .form(form_id)
                .formaction(url)
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

    async def _act(self, request: Any, context: Any, action: str) -> Any:
        """
        One of the served actions, with the state and the dialog's fields
        from the body the dialog and the popover's buttons post.
        """
        formats: Formats = context.formats
        today = _today(formats)
        asked, body, others = self._read(self._router._get_form_values(request), today)
        if action == _DELETE and not body.id:
            return HueResponse(
                component=html.p(f"{self.key}: delete needs the event's id."),
                status_code=HTTPStatus.NOT_FOUND,
            )
        # Before the handler, so a view with no page to draw the calendar on
        # is an error before anything is written.
        urls = self._urls_for(request, self._served())
        bound = BoundCalendar(self, asked, [], today, urls, others, formats)

        csrf_token: str = context.csrf_token
        if action == _DIALOG:
            shown = _prefilled(body, asked, self.layers)
            return HueResponse(
                component=self._dialog(bound, shown, {}, csrf_token=csrf_token),
                target=_slot(self.key),
            )
        if action == _OVERLAPS:
            return await self._checked(request, bound, body)
        if action == _SAVE and self.save is not None:
            draft, errors = self._draft(body, formats)
            if draft is None:
                return HueResponse(
                    component=self._dialog(bound, body, errors, csrf_token=csrf_token),
                    target=_slot(self.key),
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            verb = "Save" if draft.id else "Create"
            return await self._changed(
                request, bound, self.save, draft, verb, draft.title
            )
        if self.delete is None:  # pragma: no cover - only served with one
            raise AssertionError(action)
        # Named by the title the popover or the dialog posts beside the id.
        named = body.title.strip() or "the event"
        return await self._changed(
            request, bound, self.delete, body.id, "Delete", named
        )

    async def _checked(self, request: Any, bound: BoundCalendar, body: _Posted) -> Any:
        """
        The overlap warning for the fields as they stand, or nothing, in
        the dialog's own region.
        """
        draft, _ = self._draft(body, bound.formats)
        found = (
            await self._router._run_sync(
                self._overlapping, request, bound.state, draft, bound.formats
            )
            if draft is not None and draft.timed
            else []
        )
        return HueResponse(
            component=_overlap_warning(found, bound.formats),
            target=_overlap(self.key),
        )

    async def _changed(
        self,
        request: Any,
        bound: BoundCalendar,
        handler: Callable[..., Any],
        given: Event | str,
        verb: str,
        named: str,
    ) -> Any:
        """
        The calendar after a handler has run, with a toast saying what
        happened, or what failed.
        """
        status = await self._run(
            request,
            handler,
            given,
            label=verb,
            description="The calendar is shown as it is now.",
        )
        if status == HTTPStatus.OK:
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
    posted: _Posted, errors: dict[str, str], zone: tzinfo | None
) -> tuple[date | datetime | None, date | datetime | None]:
    """
    When the posted fields say the event is, adding what is wrong with
    them to errors: whole days when all day is on, naive moments in the
    reader's time otherwise. A timed event has to end after it starts; a
    whole-day one may end on the day it starts. Neither runs past a year.
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
        starts, ends = _clocked(first, last, posted, errors, zone)
    if starts is None or ends is None:
        return starts, ends
    if ends < starts:
        errors["ends" if all_day else "ends_time"] = "Ends before it starts."
    elif ends == starts and not all_day:
        errors["ends_time"] = "Starts and ends at the same time."
    elif first is not None and last is not None and (last - first).days > _LONGEST:
        errors["ends"] = "Ends more than a year after it starts."
    return starts, ends


def _clocked(
    first: date | None,
    last: date | None,
    posted: _Posted,
    errors: dict[str, str],
    zone: tzinfo | None,
) -> tuple[datetime | None, datetime | None]:
    """
    The moments a timed event's fields say, adding what is wrong with the
    times to errors.

    With a zone, a time the clocks skip that day is refused rather than
    moved: made aware, 02:30 the night they go forward would come out as
    03:30, and an event typed to run until 03:30 would be no time at all.
    """
    opens, closes = _clock(posted.starts_time), _clock(posted.ends_time)
    if opens is None:
        errors["starts_time"] = "Enter a time."
    if closes is None:
        errors["ends_time"] = "Enter a time."
    starts = datetime.combine(first, opens) if first and opens else None
    ends = datetime.combine(last, closes) if last and closes else None
    if zone is None:
        return starts, ends
    skipped = "That time is skipped when the clocks go forward."
    if starts is not None and not _exists(starts, zone):
        errors["starts_time"] = skipped
        starts = None
    if ends is not None and not _exists(ends, zone):
        errors["ends_time"] = skipped
        ends = None
    return starts, ends


def _prefilled(
    posted: _Posted, asked: CalendarState, layers: Sequence[Layer]
) -> _Posted:
    """
    What a new event starts with where the request said nothing: the day
    the view is around, nine o'clock when no time was given, an hour that
    stops at the end of its day, and the first layer.
    """
    filled = posted
    if not posted.starts:
        filled = replace(filled, starts=asked.date.isoformat())
    if not filled.all_day and not filled.starts_time:
        filled = replace(filled, starts_time=_NEW_STARTS.strftime("%H:%M"))
    if not filled.ends:
        filled = replace(filled, ends=filled.starts)
    starts, opens = _day(filled.starts), _clock(filled.starts_time)
    if not filled.all_day and not filled.ends_time and starts and opens:
        later = datetime.combine(starts, opens) + _NEW_LASTS
        closes = time(23, 59) if later.date() != starts else later.time()
        filled = replace(filled, ends_time=closes.strftime("%H:%M"))
    if not posted.layer and layers:
        filled = replace(filled, layer=layers[0].key)
    return filled


def _fields(bound: BoundCalendar, event: Event) -> dict[str, str | None]:
    """
    An event as the dialog's fields, under the key, for the popover's
    actions to post.
    """
    if event.timed:
        starts, ends = event.moments(bound.formats)
        when = {
            "starts": starts.date().isoformat(),
            "starts_time": starts.strftime("%H:%M"),
            "ends": ends.date().isoformat(),
            "ends_time": ends.strftime("%H:%M"),
        }
    else:
        first, last = event.span(bound.formats)
        when = {"all_day": "1", "starts": first.isoformat(), "ends": last.isoformat()}
    given = {
        "id": event.id,
        "title": event.title,
        **when,
        "layer": event.layer,
        "location": event.location,
        "notes": event.notes,
        "repeat": event.repeat,
    }
    return {bound.declaration.param(name): value for name, value in given.items()}


def _title_field(name: str, value: str) -> ComponentType:
    """
    The title, which the dialog opens on. The attribute is autofocus itself
    rather than x-autofocus alone: the focus trap reads the one and Alpine
    AJAX the other, and the dialog is only ever fetched, never on a page as
    it loads, so the attribute cannot steal focus there.
    """
    field = (
        TextInput()
        .name(name)
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
    url, target = bound.urls.act[_OVERLAPS], _overlap(bound.key)
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
    fields = {**carried, **_fields(bound, event)}

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
                            declared.param("id"): None,
                            declared.param("repeat"): None,
                            declared.param("title"): f"{event.title} (copy)",
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
                        body={
                            **carried,
                            declared.param("id"): event.id,
                            declared.param("title"): event.title,
                        },
                    )
                ),
            )
        )
    return actions


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
    screen, and the click on an empty slot that opens the dialog. The slot
    says where focus goes when the dialog closes under it: New event, the
    one control that is always there, since what opened the dialog may be
    gone with the sidebar's refresh.
    """

    category: ClassVar[str | None] = None

    def __init__(self, bound: BoundCalendar) -> None:
        super().__init__()
        self._bound = bound

    def htmy_context(self) -> Context:
        return {BoundCalendar: self._bound}

    def _render(self, context: Context) -> Component:
        bound = self._bound
        param = bound.declaration.param
        config = {
            "url": bound.urls.act.get(_DIALOG),
            "target": _slot(bound.key),
            # Where the state is read from at the click, since this root
            # is drawn once and the state moves under it.
            "state": _state(bound.key),
            # What a click posts the day and the time it fell on under.
            "fields": {"day": param("starts"), "time": param("starts_time")},
            "hour": views._HOUR,
        }
        refocus = _new(bound.key) if bound.declaration.save is not None else None
        return html.div(
            *self._children,
            html.div(id=_slot(bound.key), **{"data-hue-refocus": refocus}),
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
        bound = bound_from(context, BoundCalendar, self, "Calendar")
        declared, state, key = bound.declaration, bound.state, bound.key
        formats = bound.formats
        view = views.region_id(key)
        # Picking a day in the year view goes to that day; elsewhere the
        # view stays and moves to it.
        picked = replace(state, view="day" if state.view == "year" else state.view)
        return html.aside(
            render_when(
                declared.save is not None,
                Button()
                .variant("primary")
                .id(_new(key))
                .content(HueIcon("plus"), "New event")
                .x_on("click", unsafe("calendarCreate()")),
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
                *carried(bound._query(picked, without={_DATE})),
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
                    html.h2("Calendars", class_=PANEL_LABEL),
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
                        *carried(bound._query(bound.state, without={_HIDE})),
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
                *carried(bound._query(state, without={_QUERY}), form=f"{key}-search"),
                *carried(
                    bound._query(state, without={_START, _WEEKDAYS}),
                    form=f"{key}-options",
                ),
                html.div(*carried(bound._query(state)), id=_state(key)),
                hidden=True,
            ),
            id=f"{key}-side",
            aria_label="Calendar tools",
            class_="w-full flex-none flex-col gap-5 lg:flex lg:w-60",
            **{":class": "calendarSide ? 'flex' : 'hidden lg:flex'", **SYNC},
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
            class_=classnames(
                "size-2.5 flex-none rounded-xs", views._SOLID[layer.color]
            ),
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
        bound = bound_from(context, BoundCalendar, self, "Calendar")
        declared, key = bound.declaration, bound.key
        return html.div(
            Button()
            .variant("ghost")
            .size("sm")
            .icon_only("Calendar tools")
            .class_("lg:hidden")
            .aria_controls(f"{key}-side")
            .content(HueIcon("panel-left"))
            .x_on("click", unsafe("calendarSide = !calendarSide"))
            .x_bind("aria-expanded", unsafe("calendarSide")),
            render_when(
                declared.search is not None,
                search_form(
                    declared,
                    param=_QUERY,
                    label=declared.search or "",
                    value=bound.state.query,
                    read=bound.urls.read,
                    target=views.region_id(key),
                ),
            ),
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
                        for day in WEEKDAYS
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
                **swap(views.region_id(key)),
                **{"@change": "$el.requestSubmit()"},
            )
        )
    )
