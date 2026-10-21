"""
A calendar that knows where its own state lives.

Calendar on its own draws the events it is handed. build_calendar_state,
called at class scope, owns which day and view those are, reads them from
the page's URL, fetches the events through events(), and registers the one
route the dialog, the popover and a drag post to. The Calendars guide in
the docs says how to use it, from events() and save to dragging, Undo and
the keys.

This module is the declaration. What it reads off a request and builds its
links from is in _calendar_state, what it edits with in _calendar_edit,
and what it draws around the Calendar in _calendar_chrome.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import replace
from datetime import date
from functools import partial
from http import HTTPStatus
from typing import Any, Literal

from htmy import Context, html

from hue import toast
from hue._calendar_chrome import (
    DRAGS,
    Band,
    CalendarShortcuts,
    Frame,
    Side,
    keys_in,
    switch_on,
)
from hue._calendar_edit import (
    FIELDS,
    SERIES_SKIPPED,
    Posted,
    Undo,
    event_actions,
    event_dialog,
    id_of,
    landing,
    overlap_warning,
    prefilled,
    series_times,
    toast_title,
    undo_button,
    undo_create,
    undo_delete,
    undo_move,
    undo_save,
    when_posted,
)
from hue._calendar_state import (
    DATE,
    DELETE,
    DIALOG,
    HIDE,
    MOVE,
    OVERLAPS,
    QUERY,
    SAVE,
    START,
    STATE,
    VIEW,
    VIEWS,
    WEEKDAYS_ONLY,
    BoundCalendar,
    CalendarState,
    Layer,
    overlap_id,
    read_day,
    slot_id,
    today_in,
    zone_of,
)
from hue._declared import Declaration, Pairs, Routes, many, one
from hue.context import HueContext
from hue.formats import Formats
from hue.router import HueResponse
from hue.shortcuts import ShortcutRegistry, shortcuts
from hue.types.core import Component, ComponentType
from hue.ui.molecules._calendar_views import FIRST, LAST, CalendarView, stamps
from hue.ui.molecules.calendar import Calendar, Event
from hue.ui.molecules.date_picker import WEEKDAYS, Weekday
from hue.utils import render_if

__all__ = ["CalendarShortcuts", "CalendarState", "Layer", "build_calendar_state"]


# The group of keys that one calendar on a page holds, the first to ask.
_KEYS_CLAIM = "calendar"


# Given the request and what it asked for, every event that answers it.
type EventsFor = Callable[[Any, "CalendarState"], Iterable[Event]]
# Given the request and an event, with an id when it exists, keep it. For a
# new event, what it returns is taken as the new event's id, which the
# toast's Undo deletes: the id itself or the saved Event. None leaves the
# create without an Undo. For an edit the return is not read.
type SaveHandler = Callable[[Any, Event], str | int | Event | None]
# Given the request and an event's id, remove it.
type DeleteHandler = Callable[[Any, str], Any]


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
        The actions the route serves: the dialog, the overlap check, a save
        and a move with a save handler, and a delete with a delete handler.
        """
        saves = (DIALOG, OVERLAPS, SAVE, MOVE) if self.save is not None else ()
        return (*saves, *((DELETE,) if self.delete is not None else ()))

    async def draw(self, calendar: Calendar, context: Context) -> Component:
        """
        The calendar bound to the request this page is rendered for, with
        the sidebar, the search and the view options around it.

        Calendar.from_state() hands over to this. The request is already in
        the context, so the view has nothing to pass.
        """
        hue = HueContext.from_context(context)
        formats = Formats.from_context(context)
        today = today_in(formats)
        asked, _, others = self._read(
            self._router._get_query_values(hue.request), today
        )
        # The app's registry when it has the calendar's keys and this
        # calendar holds them on the page, claimed only when there is one.
        registry = keys_in(hue.shortcuts)
        keys = registry if registry and shortcuts.claim(_KEYS_CLAIM, self.key) else None
        # On for the page, which the shortcut host reads once the whole
        # body has rendered.
        switch_on(self, keys)
        bound = await self._bind(hue.request, asked, others, today, formats, keys=keys)
        return self._drawn(calendar, bound)

    def claim_keys(self) -> None:
        """
        Ask for the calendar's keys on this request's page, where the first
        calendar to ask has them. Called as the view builds the page, in
        the order its calendars are written, rather than as they render,
        which is in no order a reader would guess.
        """
        shortcuts.claim(_KEYS_CLAIM, self.key)

    def _read(
        self, values: Mapping[str, list[str]], today: date
    ) -> tuple[CalendarState, Posted, Pairs]:
        """
        A query or a posted form, split into this calendar's state, the
        dialog's fields, and everything else, which goes back out as it
        came. The first two are the names under the key; the framework's
        own field, its CSRF token, is nobody's and goes nowhere.

        Clamped where it enters: a view, a date or a week start that is not
        one is the default, and a hidden layer nobody declared is dropped.
        Anyone can type into a query string, and it is never an error page.
        """
        own, others = self._split(values, (*STATE, *FIELDS))
        given = {name: one(own, name) or "" for name in FIELDS if name in own}
        return self._state_from(own, today), Posted(**given), others

    def _state_from(self, asked: Mapping[str, list[str]], today: date) -> CalendarState:
        view = one(asked, VIEW)
        start = one(asked, START)
        cursor = read_day(one(asked, DATE) or "") or today
        declared = [layer.key for layer in self.layers]
        hidden = tuple(key for key in many(asked, HIDE) if key in declared)
        return CalendarState(
            date=min(max(cursor, FIRST), LAST),
            view=view if view in VIEWS else self.view,  # type: ignore[arg-type]
            query=(one(asked, QUERY) or "").strip(),
            hidden=hidden,
            week_start=start if start in WEEKDAYS else self.week_start,  # type: ignore[arg-type]
            weekdays=one(asked, WEEKDAYS_ONLY) == "1",
            layers=tuple(key for key in declared if key not in hidden),
        )

    async def _bind(
        self,
        request: Any,
        asked: CalendarState,
        others: Pairs,
        today: date,
        formats: Formats,
        keys: type[ShortcutRegistry] | None = None,
    ) -> BoundCalendar:
        events = await self._router._run_sync(self._fetch, request, asked)
        urls = self._urls_for(request, self._served())
        return BoundCalendar(self, asked, events, today, urls, others, formats, keys)

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
            if (
                self.save is not None
                and returned.repeat
                and (returned.series_starts is None)
            ):
                raise TypeError(
                    f"{self.key}: events() returned {returned.title!r}, which "
                    f"repeats, without series_starts. Moving it moves the whole "
                    f"series, from when its first occurrence starts."
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
        if isinstance(bound.focus, Event):
            calendar._props["focus"] = bound.focus
        calendar.href(lambda day, view: bound.href(date=day, view=view))
        if self.save is not None:
            # A click on an empty slot or day opens the dialog with that
            # time filled in. Only the calendar hears it: the sidebar's
            # picker has day cells of its own. Dragging listens on the same
            # element. Under the internal keys, so a click handler of the
            # page's own on the Calendar is kept beside them.
            calendar._attrs["x-on:click"] = "calendarSlot($event)"
            calendar._attrs.update(DRAGS)
            calendar._props["movable"] = True
        if self.edits:
            calendar.actions(lambda event: event_actions(bound, event))
        return Frame(bound).content(
            Side(),
            html.div(Band(), calendar, class_="flex min-w-0 flex-1 flex-col gap-3"),
        )

    def _draft(
        self, posted: Posted, formats: Formats
    ) -> tuple[Event | None, dict[str, str]]:
        """
        The posted fields as an Event, or what is wrong with them by field.
        """
        errors: dict[str, str] = {}
        title = posted.title.strip()
        if not title:
            errors["title"] = "Give the event a title."
        starts, ends = when_posted(posted, errors, zone_of(formats))
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
        the draft itself, among the draft's own days.
        """
        first, last = draft.span(formats)
        starts, ends = draft.moments(formats)
        found = []
        for event in self._fetch(request, self._covering(asked, first, last)):
            if not event.timed or (event.id is not None and event.id == draft.id):
                continue
            opens, closes = event.moments(formats)
            if opens.tzinfo is not None:
                opens, closes = opens.replace(tzinfo=None), closes.replace(tzinfo=None)
            if opens < ends and closes > starts:
                found.append(event)
        return found

    def _covering(self, asked: CalendarState, first: date, last: date) -> CalendarState:
        """
        A state that asks events() for these days alone, in every layer and
        with no search: what the overlap check and a lookup by id ask with,
        since an event the reader has hidden or searched away is still
        there. events() reads first and last, which follow the view, so a
        copy is pointed at the days by hand.
        """
        covering = replace(
            asked,
            query="",
            hidden=(),
            layers=tuple(layer.key for layer in self.layers),
        )
        object.__setattr__(covering, "first", first)
        object.__setattr__(covering, "last", last)
        return covering

    def _find(
        self,
        request: Any,
        asked: CalendarState,
        id: str,
        occurrence: str,
        formats: Formats,
    ) -> Event | None:
        """
        The event events() has under this id, as it stands: the occurrence
        that started when occurrence says, or the first of them when the
        button that was pressed said nothing. Asked of events() itself
        rather than of the page, which has nothing but the times. A day
        the calendar cannot draw is nobody's, and events() is never asked
        for it.
        """
        day = read_day(occurrence[:10]) if occurrence else None
        if day is not None and not FIRST <= day <= LAST:
            return None
        first, last = (day, day) if day else (asked.first, asked.last)
        for event in self.events(request, self._covering(asked, first, last)):
            if not isinstance(event, Event) or event.id != id:
                continue
            if not occurrence or stamps(event, formats)[0] == occurrence:
                return event
        return None

    async def _act(self, request: Any, context: Any, action: str) -> Any:
        """
        One of the served actions, with the state and the dialog's fields
        from the body the dialog and the popover's buttons post.
        """
        formats: Formats = context.formats
        today = today_in(formats)
        asked, body, others = self._read(self._router._get_form_values(request), today)
        if action in (DELETE, MOVE) and not body.id:
            return HueResponse(
                component=html.p(f"{self.key}: {action} needs the event's id."),
                status_code=HTTPStatus.NOT_FOUND,
            )
        # Before the handler, so a view with no page to draw the calendar on
        # is an error before anything is written.
        urls = self._urls_for(request, self._served())
        bound = BoundCalendar(
            self, asked, [], today, urls, others, formats, keys_in(context.shortcuts)
        )
        # On for this response too, whichever it is: the host that answers a
        # fragment replaces the page's, and a dialog that was cancelled makes
        # no request of its own to switch them back on.
        switch_on(self, bound.shortcuts)

        csrf_token: str = context.csrf_token
        if action == DIALOG:
            shown = prefilled(body, asked, self.layers)
            return self._shown(bound, shown, {}, HTTPStatus.OK, csrf_token)
        if action == OVERLAPS:
            return await self._checked(request, bound, body)
        if action == SAVE and self.save is not None:
            return await self._saved(request, bound, body, self.save, csrf_token)
        if action == MOVE and self.save is not None:
            return await self._moved(request, bound, body, self.save)
        if self.delete is None:  # pragma: no cover - only served with one
            raise AssertionError(action)
        # Undone by saving the event back as events() had it, series and
        # all, without the id, so an undone delete is a new event.
        was = await self._router._run_sync(
            self._find, request, bound.state, body.id, body.occurrence, formats
        )
        return await self._changed(
            request,
            bound,
            self.delete,
            body.id,
            "Delete",
            body=body,
            undo=lambda _: undo_delete(bound, was),
        )

    def _shown(
        self,
        bound: BoundCalendar,
        posted: Posted,
        errors: Mapping[str, str],
        status: HTTPStatus,
        csrf_token: str,
    ) -> HueResponse:
        """
        The dialog over the posted fields, in the slot.
        """
        return HueResponse(
            component=event_dialog(bound, posted, errors, csrf_token=csrf_token),
            target=slot_id(self.key),
            status_code=status,
        )

    async def _saved(
        self,
        request: Any,
        bound: BoundCalendar,
        body: Posted,
        save: Callable[..., Any],
        csrf_token: str,
    ) -> Any:
        """
        The calendar once the dialog's fields are saved, or the dialog again
        over them when they could not be: a field error, or a handler that
        failed or refused, so nothing typed is lost. A failed duplicate is
        the calendar again, since nothing was typed.
        """
        formats = bound.formats
        draft, errors = self._draft(body, formats)
        if draft is None:
            return self._shown(
                bound, body, errors, HTTPStatus.UNPROCESSABLE_ENTITY, csrf_token
            )
        kept = "What you entered is still in the dialog."
        # A failed save answers with the dialog over what was posted.
        refused = partial(self._shown, bound, body, {}, csrf_token=csrf_token)
        if draft.id is None:
            # Undone by deleting what save made, which it has to name:
            # without an id back, a create has no undo.
            return await self._changed(
                request,
                bound,
                save,
                draft,
                "Create",
                body=body,
                undo=lambda made: undo_create(bound, draft, id_of(made)),
                lands=draft if body.undo else None,
                # A duplicate has no dialog to keep a failure in.
                description="The calendar is shown as it is now."
                if body.copy
                else kept,
                refused=None if body.copy else refused,
            )
        if body.undo:
            # Put back as it was: a series from its first occurrence.
            return await self._changed(
                request,
                bound,
                save,
                draft,
                "Save",
                body=body,
                lands=draft,
            )
        was = await self._router._run_sync(
            self._find, request, bound.state, draft.id, body.occurrence, formats
        )
        if was is None:
            toast.danger("Save failed", description="The event is no longer there.")
            return refused(HTTPStatus.NOT_FOUND)
        edited = draft
        if draft.repeat:
            series = series_times(was, draft.starts, draft.ends, formats)
            if series is None:
                errors = {"starts_time": SERIES_SKIPPED}
                status = HTTPStatus.UNPROCESSABLE_ENTITY
                return self._shown(bound, body, errors, status, csrf_token)
            edited = replace(draft, starts=series[0], ends=series[1])
        return await self._changed(
            request,
            bound,
            save,
            edited,
            "Save",
            body=body,
            undo=lambda _: undo_save(bound, was),
            description=kept,
            refused=refused,
        )

    async def _moved(
        self,
        request: Any,
        bound: BoundCalendar,
        body: Posted,
        save: Callable[..., Any],
    ) -> Any:
        """
        The event the browser dragged or stepped, saved at the posted
        times with every other field as events() has it. The browser knows
        the id and the times and nothing else, so the rest is looked up,
        and a save handler is enough.
        """
        formats = bound.formats
        was = await self._router._run_sync(
            self._find, request, bound.state, body.id, body.occurrence, formats
        )
        if was is None and body.undo:
            # An Undo names the occurrence where the series landed, which
            # its rule may skip: a weekday series dropped on a Saturday. It
            # posts the times it goes back to, so any occurrence will do.
            was = await self._router._run_sync(
                self._find, request, bound.state, body.id, "", formats
            )
        if was is None:
            return await self._failed(
                request,
                bound,
                "Move",
                "The event is no longer there.",
                HTTPStatus.NOT_FOUND,
            )
        errors: dict[str, str] = {}
        # Timed or whole days as it is, whatever the body says.
        posted = replace(body, all_day="" if was.timed else "1")
        starts, ends = when_posted(posted, errors, zone_of(formats))
        if errors or starts is None or ends is None:
            why = next(iter(errors.values()), "Enter a time.")
            return await self._failed(
                request, bound, "Move", why, HTTPStatus.UNPROCESSABLE_ENTITY
            )
        landed = replace(was, starts=starts, ends=ends)
        # An Undo posts the series where it began, saved as posted.
        if not body.undo:
            series = series_times(was, starts, ends, formats)
            if series is None:
                return await self._failed(
                    request,
                    bound,
                    "Move",
                    SERIES_SKIPPED,
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                )
            starts, ends = series
        moved = replace(was, starts=starts, ends=ends)
        resized = stamps(was, formats)[0] == stamps(landed, formats)[0]
        verb = "Resize" if resized else "Move"
        return await self._changed(
            request,
            bound,
            save,
            moved,
            verb,
            body=body,
            undo=lambda _: undo_move(bound, was, landed),
            lands=landed,
        )

    async def _checked(self, request: Any, bound: BoundCalendar, body: Posted) -> Any:
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
            component=overlap_warning(found, bound.formats),
            target=overlap_id(self.key),
        )

    async def _changed(
        self,
        request: Any,
        bound: BoundCalendar,
        handler: Callable[..., Any],
        given: Event | str,
        verb: str,
        *,
        body: Posted,
        undo: Callable[[Any], Undo | None] | None = None,
        lands: Event | None = None,
        description: str = "The calendar is shown as it is now.",
        refused: Callable[[HTTPStatus], Any] | None = None,
    ) -> Any:
        """
        The calendar after a handler has run, with a toast saying what
        happened and offering to undo it, or saying what failed.

        undo is given what the handler returned and says which action puts
        things back and with what fields, or None when nothing can; left
        out, nothing is offered. One level: the request an Undo makes
        carries the undo flag, and the toast it earns offers none. lands is
        the event focus goes to once the calendar is back, named by the id
        save returns when it has none; an undone create sends it to New
        event. refused answers a failure instead of the calendar, as the
        dialog does over what was typed.
        """
        focus: Event | Literal["new"] | None = None
        status, made = await self._run(
            request, handler, given, label=verb, description=description
        )
        if status != HTTPStatus.OK and refused is not None:
            return refused(status)
        if status == HTTPStatus.OK:
            # Named by the title the popover or the dialog posts beside the id.
            named = (
                given.title if isinstance(given, Event) else body.title.strip()
            ) or "the event"
            series = bool(given.repeat if isinstance(given, Event) else body.repeat)
            back = None if body.undo or undo is None else undo(made)
            # Only through a route that is served: a create is undone by a
            # delete, and a delete by a save, which the other may lack.
            if back is not None and back.action not in bound.urls.act:
                back = None
            toast.success(
                toast_title(verb, named, series, undone=bool(body.undo)),
                action=render_if(back, lambda it: undo_button(bound, it)),
            )
            if body.undo and verb == "Delete":
                focus = "new"
            elif lands is not None:
                focus = lands if lands.id else replace(lands, id=id_of(made))
        return await self._redrawn(request, bound, status, focus)

    async def _failed(
        self,
        request: Any,
        bound: BoundCalendar,
        verb: str,
        why: str,
        status: HTTPStatus,
    ) -> Any:
        toast.danger(f"{verb} failed", description=why)
        return await self._redrawn(request, bound, status)

    async def _redrawn(
        self,
        request: Any,
        bound: BoundCalendar,
        status: HTTPStatus,
        focus: Event | Literal["new"] | None = None,
    ) -> Any:
        """
        Drawn after the change, because the events have just moved under
        it. The whole thing, with an empty slot: the response targets the
        slot, which closes the dialog, and the synced parts refresh.
        """
        events = await self._router._run_sync(self._fetch, request, bound.state)
        redrawn = replace(bound, events=events)
        if isinstance(focus, Event):
            focus = landing(redrawn, focus)
        return HueResponse(
            component=self._drawn(Calendar(), replace(redrawn, focus=focus)),
            status_code=status,
        )


# What a view calls, at class scope, to declare a calendar.
build_calendar_state = _Declaration
