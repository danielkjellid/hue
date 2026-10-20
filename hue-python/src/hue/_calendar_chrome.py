"""
The parts a declared calendar draws around the Calendar itself: the frame,
the sidebar, the band above it, the help dialog and the keys.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, timedelta
from typing import ClassVar

from htmy import Context, html

from hue._calendar_state import (
    _DATE,
    _DIALOG,
    _HIDE,
    _MOVE,
    _QUERY,
    _START,
    _WEEKDAYS,
    BoundCalendar,
    Layer,
    _new,
    _side,
    _slot,
    _state,
    _timezone,
    _view_options,
)
from hue._declared import bound_from, carried, search_form, search_id
from hue.js import Expression, call, close, unsafe
from hue.shortcuts import Shortcut, ShortcutRegistry
from hue.types.core import Component, ComponentType
from hue.ui import _shortcut
from hue.ui._styles import PANEL_LABEL
from hue.ui.atoms.button import Button
from hue.ui.atoms.checkbox import Checkbox
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.kbd import Kbd
from hue.ui.atoms.radio import Radio, RadioGroup
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _calendar_views as views
from hue.ui.molecules.date_picker import WEEKDAYS, DatePicker
from hue.ui.molecules.dialog import Dialog
from hue.ui.molecules.popover import Popover
from hue.ui.navigation import SYNC, swap
from hue.utils import classnames, render_if, render_when


def _press(element_id: str) -> Expression:
    return _on(element_id, "click")


def _on(element_id: str, method: str) -> Expression:
    """
    Press or focus the control with this id, when it is on the page.
    """
    return unsafe(f"document.getElementById({json.dumps(element_id)})?.{method}()")


def _open(element_id: str) -> Expression:
    """
    Tell the dialog with this id to open. It listens for hue:open on its
    root, which is outside the scope of whatever presses the keys.
    """
    return unsafe(
        f"document.getElementById({json.dumps(element_id)})"
        "?.dispatchEvent(new CustomEvent('hue:open'))"
    )


def _keys_in(
    registry: type[ShortcutRegistry] | None,
) -> type[ShortcutRegistry] | None:
    """
    The app's registry when it inherits the calendar's keys, else None:
    switching on a shortcut a registry does not have is an error, so an
    app that has not opted in gets no keys.
    """
    if registry is not None and CalendarShortcuts.calendar_today in registry.shortcuts:
        return registry
    return None


class CalendarShortcuts(ShortcutRegistry):
    """
    The keys a declared calendar answers to, for an app's registry to
    inherit: class Shortcuts(CalendarShortcuts). Each is scoped, so it is
    on only where a calendar is drawn, and each presses the control that
    does the same thing, so the keys and the clicks cannot drift apart.
    The design's bare arrow keys are left out: on their own they move
    through a date picker and a listbox, and the registry refuses them.
    """

    calendar_today = Shortcut("Go to today", "t", scoped=True, group="Calendar")
    calendar_previous = Shortcut("Previous", "j", scoped=True, group="Calendar")
    calendar_next = Shortcut("Next", "k", scoped=True, group="Calendar")
    calendar_day = Shortcut("Day view", "d", scoped=True, group="Calendar")
    calendar_week = Shortcut("Week view", "w", scoped=True, group="Calendar")
    calendar_month = Shortcut("Month view", "m", scoped=True, group="Calendar")
    calendar_year = Shortcut("Year view", "y", scoped=True, group="Calendar")
    calendar_agenda = Shortcut("Agenda view", "a", scoped=True, group="Calendar")
    calendar_new = Shortcut("New event", "n", scoped=True, group="Calendar")
    calendar_search = Shortcut("Search events", "/", scoped=True, group="Calendar")
    calendar_help = Shortcut("Keyboard shortcuts", "?", scoped=True, group="Calendar")


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
            "move": bound.urls.act.get(_MOVE),
            "key": bound.key,
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
            render_when(bound.shortcuts is not None, _Help(bound)),
            class_="flex flex-col gap-4 lg:flex-row lg:items-start",
            **{"x-data": call("hueCalendar", config)},
        )


class _Help(ChainableComponent):
    """
    The keyboard shortcuts, in a dialog the ? key and the view options
    open: every shortcut on for this request, which is the app's own as
    well as the calendar's, and the keys that move the focused event,
    which are the event's rather than the page's and so are not shortcuts.
    """

    category: ClassVar[str | None] = None

    def __init__(self, bound: BoundCalendar) -> None:
        super().__init__()
        self._bound = bound

    def _render(self, context: Context) -> Component:
        bound = self._bound
        assert bound.shortcuts is not None
        rows = [
            _help_row(item.shortcut.label, _shortcut.keys(item.shortcut.steps))
            for item in bound.shortcuts.active()
        ]
        if bound.declaration.save is not None:
            rows += [
                _help_row(
                    "Move the focused event a quarter hour",
                    *_either(("alt",), "up", "down"),
                ),
                _help_row("Move it a day", *_either(("alt",), "left", "right")),
                _help_row(
                    "Change its end by a quarter hour",
                    *_either(("alt", "shift"), "up", "down"),
                ),
                _help_row(
                    "Change an all-day end by a day",
                    *_either(("alt", "shift"), "left", "right"),
                ),
            ]
        rows.append(_help_row("Close a popover or a dialog", Kbd("esc")))
        return (
            Dialog()
            .id(f"{bound.key}-help")
            .title("Keyboard shortcuts")
            .size("sm")
            .x_on("hue:open", unsafe("open = true"))
            .content(html.ul(*rows, class_="flex flex-col divide-y divide-border"))
        )


def _either(
    held: tuple[str, ...], first: str, second: str
) -> tuple[ComponentType, ...]:
    """
    Keys held with one of two others, written once: alt + up / down.
    """
    return (
        Kbd(*held),
        html.span("+", class_="text-fg-subtle"),
        Kbd(first),
        html.span(
            html.span("/", aria_hidden="true"),
            html.span("or", class_="sr-only"),
            class_="text-fg-subtle",
        ),
        Kbd(second),
    )


def _help_row(label: str, *keys: ComponentType) -> ComponentType:
    # The keys wrap under a label they would crowd, rather than squeeze it.
    return html.li(
        html.span(label, class_="min-w-0 flex-auto"),
        html.span(*keys, class_="ms-auto flex flex-none items-center gap-1.5"),
        class_="flex flex-wrap items-center gap-x-4 gap-y-1.5 py-2 text-sm",
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
                .x_autofocus(bound.focus == "new")
                .content(HueIcon("plus"), "New event")
                .x_on("click", unsafe("calendarCreate()")),
            ),
            html.form(
                DatePicker()
                .name(declared.param(_DATE))
                .id(f"{key}-picker")
                .label("Go to a day")
                .hidden_label()
                .size("sm")
                .value(state.date)
                .week_start(state.week_start)
                .markers(*_marked(bound))
                # Named so nothing in the picker's own scope, which has a
                # day() of its own, can stand in for it.
                .x_model(unsafe("pickedDay")),
                *carried(bound.query(picked, without={_DATE})),
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
                        *carried(bound.query(bound.state, without={_HIDE})),
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
                *carried(bound.query(state, without={_QUERY}), form=search_id(key)),
                *carried(
                    bound.query(state, without={_START, _WEEKDAYS}),
                    form=_view_options(key),
                ),
                html.div(*carried(bound.query(state)), id=_state(key)),
                hidden=True,
            ),
            id=_side(key),
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
            .aria_controls(_side(key))
            .content(HueIcon("panel-left"))
            .x_on("click", unsafe("calendarSide = !calendarSide"))
            .x_bind("aria-expanded", unsafe("calendarSide")),
            render_when(
                declared.search is not None,
                search_form(
                    bound,
                    param=_QUERY,
                    label=declared.search or "",
                    value=bound.state.query,
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
                id=_view_options(key),
                method="get",
                action=bound.urls.read,
                class_="flex w-52 flex-col gap-4",
                **swap(views.region_id(key)),
                **{"@change": "$el.requestSubmit()"},
            ),
            # The visible way to the help, for anyone who has not been
            # told there is a ? to press.
            render_when(
                bound.shortcuts is not None,
                Button()
                .variant("ghost")
                .size("sm")
                .class_("mt-3 w-full justify-between")
                .content("Keyboard shortcuts", Kbd("?"))
                .x_on("click", unsafe(f"{close()}; {_open(f'{key}-help')}")),
            ),
        )
    )
