"""
The parts a declared calendar draws besides the Calendar itself: the frame
around it, the help dialog and the keys, the tools a page hands its
toolbar, and the sidebar MiniCalendar draws wherever the page puts it.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, ClassVar

from htmy import Context, html

from hue._calendar_state import (
    DATE,
    DIALOG,
    HIDE,
    MOVE,
    QUERY,
    START,
    WEEKDAYS_ONLY,
    BoundCalendar,
    Layer,
    help_id,
    new_id,
    side_id,
    slot_id,
    state_id,
    timezone_name,
    view_options_id,
)
from hue._declared import (
    bound_from,
    carried,
    filter_form,
    filters_id,
    search_form,
    search_id,
)
from hue.js import Expression, call, close, unsafe
from hue.shortcuts import Shortcut, ShortcutRegistry, shortcuts
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
from hue.ui.molecules._calendar_views import CalendarView
from hue.ui.molecules.date_picker import WEEKDAYS, DatePicker
from hue.ui.molecules.dialog import Dialog
from hue.ui.molecules.popover import Popover
from hue.ui.navigation import SYNC, swap
from hue.utils import classnames, render_if, render_when

if TYPE_CHECKING:
    from hue.calendar import _Declaration


def _on(element_id: str, method: str) -> Expression:
    """
    Press or focus the control with this id, when it is on the page.
    """
    return unsafe(f"document.getElementById({json.dumps(element_id)})?.{method}()")


def _open(element_id: str) -> Expression:
    """
    Tell the dialog with this id to open, from outside its scope.
    """
    return unsafe(
        f"document.getElementById({json.dumps(element_id)})"
        "?.dispatchEvent(new CustomEvent('hue:open'))"
    )


def keys_in(
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


# The key that presses each view's tab, keyed by the Literal so mypy keeps
# it whole.
_VIEW_KEYS: dict[CalendarView, Shortcut] = {
    "day": CalendarShortcuts.calendar_day,
    "week": CalendarShortcuts.calendar_week,
    "month": CalendarShortcuts.calendar_month,
    "year": CalendarShortcuts.calendar_year,
    "agenda": CalendarShortcuts.calendar_agenda,
}

# Minutes a drag snaps to and an arrow key moves an event by, which the
# script is handed and the help says.
_SNAP = 15
_SNAPPED = "a quarter hour" if _SNAP == 15 else f"{_SNAP} minutes"

# What the calendar hears to drag and move its events, under the internal
# keys like the slot's click, so the page's own handlers are kept beside
# them.
DRAGS = {
    "x-on:pointerdown": "calendarPress($event)",
    "x-on:pointermove": "calendarStretch($event)",
    "x-on:pointerup": "calendarRelease()",
    "x-on:pointercancel": "calendarCancel()",
    # After pointerup as well, by when there is no drag left.
    "x-on:lostpointercapture": "calendarCancel()",
    "x-on:keydown": "calendarKeys($event)",
    "x-on:click.capture": "calendarSwallow($event)",
}


def switch_on(
    declared: _Declaration,
    registry: type[ShortcutRegistry] | None,
    tools: frozenset[str],
) -> None:
    """
    The calendar's keys, on for this response when the app's registry has
    them. Each one presses the control that does the same thing, so a key
    and a click are the one code path, and the one for a tool is on only
    when the page drew that tool.
    """
    if registry is None:
        return
    key = declared.key
    pressed = {
        CalendarShortcuts.calendar_today: views.control_id(key, "today"),
        CalendarShortcuts.calendar_previous: views.control_id(key, "previous"),
        CalendarShortcuts.calendar_next: views.control_id(key, "next"),
        **{
            shortcut: views.switch_id(key, view)
            for view, shortcut in _VIEW_KEYS.items()
        },
    }
    if CalendarNewEvent.name in tools and CalendarNewEvent.declared_by(declared):
        pressed[CalendarShortcuts.calendar_new] = new_id(key)
    for shortcut, target in pressed.items():
        shortcuts.use(shortcut, action=_on(target, "click"))
    if CalendarSearch.name in tools and CalendarSearch.declared_by(declared):
        shortcuts.use(
            CalendarShortcuts.calendar_search,
            action=_on(declared.param(QUERY), "focus"),
        )
    shortcuts.use(CalendarShortcuts.calendar_help, action=_open(help_id(key)))


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


class Frame(ChainableComponent):
    """
    The Calendar inside, with the slot the dialog lands in, the help for
    the keys and the state a click posts.

    Its x-data is hueCalendar, configured here: the click on an empty slot,
    New event, and the drags and keys that move an event, which the
    Calendar inside listens for. The slot says where focus goes when the
    dialog closes under it: New event, which every response that closes
    the dialog draws again, where what opened the dialog may be gone.
    """

    category: ClassVar[str | None] = None

    def __init__(self, bound: BoundCalendar) -> None:
        super().__init__()
        self._bound = bound

    def htmy_context(self) -> Context:
        # The tools in the Calendar's toolbar read the binding from here.
        return {BoundCalendar: self._bound}

    def _render(self, context: Context) -> Component:
        bound = self._bound
        key = bound.key
        config = {
            "url": bound.urls.act.get(DIALOG),
            "move": bound.urls.act.get(MOVE),
            "key": key,
            "target": slot_id(key),
            # Where the state is read from at the click, since this root
            # is drawn once and the state moves under it.
            "state": state_id(key),
            "region": views.region_id(key),
            # The tabs a week on a phone is fitted with.
            "weekTab": views.switch_id(key, "week"),
            "dayTab": views.switch_id(key, "day"),
            "hour": views._HOUR,
            "snap": _SNAP,
        }
        # New event when the toolbar has it, else the view's heading, which
        # is always drawn.
        heading = views.control_id(key, "heading")
        refocus = (
            f"{new_id(key)} {heading}" if bound.declaration.save is not None else None
        )
        return html.div(
            *self._children,
            html.div(id=slot_id(key), **{"data-hue-refocus": refocus}),
            # Synced, so the help comes with whichever calendar's answer
            # takes the keys, also on a page where another one drew them.
            html.div(
                render_if(bound.shortcuts, lambda keys: _help(bound, keys)),
                id=f"{key}-shortcuts",
                **SYNC,
            ),
            # The whole state, for the script that opens the dialog from a
            # click, read at the click since it moves under this root.
            html.div(
                *carried(bound.posted()),
                id=state_id(key),
                hidden=True,
                **SYNC,
            ),
            carried_by_tools(bound),
            class_="min-w-0",
            **{"x-data": call("hueCalendar", config)},
        )


def new_event(bound: BoundCalendar) -> ComponentType:
    """
    New event, which opens the dialog empty. Synced, so the response that
    sends focus back to it draws it again with x-autofocus.
    """
    return (
        Button()
        .variant("primary")
        .size("sm")
        .id(new_id(bound.key))
        .x_sync()
        .x_autofocus(bound.focus == "new")
        .content(HueIcon("plus"), "New event")
        .x_on("click", unsafe("calendarCreate()"))
    )


def _help(bound: BoundCalendar, keys: type[ShortcutRegistry]) -> ComponentType:
    """
    The keyboard shortcuts, in a dialog the ? key and the view options
    open: every shortcut on for this request, which is the app's own as
    well as the calendar's, and the keys that move the focused event,
    which are the event's rather than the page's and so are not shortcuts.
    """
    rows = [
        _help_row(item.shortcut.label, _shortcut.keys(item.shortcut.steps))
        for item in keys.active()
    ]
    if bound.declaration.save is not None:
        rows += [
            _help_row(
                f"Move the focused event {_SNAPPED}",
                *_either(("alt",), "up", "down"),
            ),
            _help_row("Move it a day", *_either(("alt",), "left", "right")),
            _help_row(
                f"Change its end by {_SNAPPED}",
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
        .id(help_id(bound.key))
        .title("Keyboard shortcuts")
        .size("sm")
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


def side(
    bound: BoundCalendar,
    classes: str | None = None,
    attrs: Mapping[str, Any] | None = None,
) -> ComponentType:
    """
    What MiniCalendar draws: a picker to jump by, the calendars to show and
    hide, and which timezone the times are in.

    Everything inside is synced, so every response refreshes it: the
    picker's marks and the state its forms carry both live there. The page's
    classes and attributes go on the aside around it, which no response
    replaces, so they outlast a change.
    """
    declared, state, key = bound.declaration, bound.state, bound.key
    formats = bound.formats
    view = views.region_id(key)
    # Picking a day in the year view goes to that day; elsewhere the view
    # stays and moves to it.
    picked = replace(state, view="day" if state.view == "year" else state.view)
    inside = html.div(
        html.form(
            DatePicker()
            .name(declared.param(DATE))
            .id(f"{key}-picker")
            .label("Go to a day")
            .hidden_label()
            .size("sm")
            .value(state.date)
            .week_start(state.week_start)
            .markers(*_marked(bound))
            # Named so nothing in the picker's own scope, which has a day()
            # of its own, can stand in for it.
            .x_model(unsafe("pickedDay")),
            *carried(bound.query(picked, without={DATE})),
            method="get",
            action=bound.urls.read,
            **swap(view),
            **{
                "x-data": f"{{ pickedDay: {json.dumps([state.date.isoformat()])} }}",
                # After the tick, so the picker's hidden field holds the new
                # day before the form reads it.
                "x-init": (
                    "$watch('pickedDay', () => $nextTick(() => $el.requestSubmit()))"
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
                # The boxes sit outside the form, so they are read and never
                # submitted: a box can only submit itself while it is
                # ticked, and what the URL wants is the ones that are not.
                # One hidden field carries those, left out of the URL while
                # there are none.
                html.form(
                    html.input_(
                        type="hidden",
                        name=declared.param(HIDE),
                        **{
                            ":value": "hiddenLayers.join(',')",
                            ":disabled": "!hiddenLayers.length",
                        },
                    ),
                    *carried(bound.query(bound.state, without={HIDE})),
                    method="get",
                    action=bound.urls.read,
                    hidden=True,
                    **swap(view),
                    **{"x-ref": "form"},
                ),
                class_="flex flex-col gap-2",
                **{"x-data": f"{{ hiddenLayers: {json.dumps(list(state.hidden))} }}"},
            ),
        ),
        render_if(
            timezone_name(formats),
            lambda name: html.p(
                HueIcon("clock").class_("size-3.5 flex-none"),
                f"Times in {name.replace('_', ' ')}",
                class_="flex items-center gap-1.5 text-xs text-fg-muted",
            ),
        ),
        id=side_id(key),
        class_="flex flex-col gap-5",
        **SYNC,
    )
    return html.aside(
        inside, class_=classes, **{"aria_label": "Calendar tools", **(attrs or {})}
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


def matches(bound: BoundCalendar) -> ComponentType:
    """
    How many events the search found, synced so a change refreshes it.
    """
    return html.span(
        _matches(bound),
        id=f"{bound.key}-matches",
        role="status",
        class_="text-sm tabular-nums text-fg-muted",
        **SYNC,
    )


def carried_by_tools(bound: BoundCalendar) -> ComponentType:
    """
    What the search, the filters and the view options each send besides
    their own part, tied to each by id. Here rather than in the forms, which
    no response replaces, so they always send the state the calendar is in.
    """
    declared, state, key = bound.declaration, bound.state, bound.key
    filtered = {f.name for f in declared.filters}
    return html.div(
        *(
            carried(bound.query(state, without={QUERY}), form=search_id(key))
            if declared.search is not None
            else ()
        ),
        *(
            carried(bound.query(state, without=filtered), form=filters_id(key))
            if declared.filters
            else ()
        ),
        *carried(
            bound.query(state, without={START, WEEKDAYS_ONLY}),
            form=view_options_id(key),
        ),
        id=f"{key}-carried",
        hidden=True,
        **SYNC,
    )


class _Tool(ChainableComponent):
    """
    A control for a declared calendar's toolbar, handed to Calendar's
    tools() and bound to the calendar it is drawn in. It draws into the
    toolbar's row through a wrapper with no box of its own, so an id or a
    data attribute set on it lands there and a layout class has nothing to
    act on.
    """

    category: ClassVar[str | None] = None
    # What the binding and every post call it.
    name: ClassVar[str]
    # What the declaration has to have for it, as an error would say it, or
    # None when it draws for any calendar.
    needs: ClassVar[str | None] = None

    @classmethod
    def declared_by(cls, declaration: _Declaration) -> bool:
        return True

    @classmethod
    def synced(cls, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        """
        Its parts a response after a change refreshes by id.
        """
        return ()

    def _render(self, context: Context) -> Component:
        bound = bound_from(context, BoundCalendar, self, "Calendar")
        if not self.declared_by(bound.declaration):
            raise ValueError(
                f"{type(self).__name__} needs {self.needs} on the declaration "
                f"of {bound.key!r}. Give build_calendar_state {self.needs}, or "
                f"leave {type(self).__name__} out of tools()."
            )
        return html.div(
            *self._drawn(bound),
            class_=classnames("contents", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )

    def _drawn(self, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        raise NotImplementedError


class CalendarSearch(_Tool):
    """
    The search box of a declared calendar, and how many events it found.
    The declaration's search is its label, and with it drawn the / key
    focuses it.
    """

    name = "search"
    needs = "a search"

    @classmethod
    def declared_by(cls, declaration: _Declaration) -> bool:
        return declaration.search is not None

    @classmethod
    def synced(cls, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        return (matches(bound),)

    def _drawn(self, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        return (
            search_form(
                bound,
                param=QUERY,
                label=bound.declaration.search or "",
                value=bound.state.query,
                target=views.region_id(bound.key),
            ),
            matches(bound),
        )


class CalendarFilters(_Tool):
    """
    The Filter button of a declared calendar, with its panel and a chip
    for each answer, for the filters the declaration names.
    """

    name = "filters"
    needs = "filters"

    @classmethod
    def declared_by(cls, declaration: _Declaration) -> bool:
        return bool(declaration.filters)

    def _drawn(self, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        declared = bound.declaration
        target = views.region_id(bound.key)
        return (
            filter_form(bound, declared.filters, bound.state.filters, target=target),
        )


class CalendarViewOptions(_Tool):
    """
    The view options of a declared calendar: which day the week starts on
    and whether to leave the weekend out, behind one button.
    """

    name = "options"

    def _drawn(self, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        return (_options(bound),)


class CalendarNewEvent(_Tool):
    """
    New event, which opens a declared calendar's dialog empty, and which
    the n key presses. It needs a save to make the event with.
    """

    name = "new"
    needs = "a save"

    @classmethod
    def declared_by(cls, declaration: _Declaration) -> bool:
        return declaration.save is not None

    @classmethod
    def synced(cls, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        return (new_event(bound),)

    def _drawn(self, bound: BoundCalendar) -> tuple[ComponentType, ...]:
        return (new_event(bound),)


# Every tool by the name the binding and the posts know it by.
TOOLS_BY_NAME: dict[str, type[_Tool]] = {
    tool.name: tool
    for tool in (CalendarSearch, CalendarFilters, CalendarViewOptions, CalendarNewEvent)
}


def drawn_tools(tools: Iterable[object]) -> frozenset[str]:
    """
    The names of the tools a Calendar was handed.
    """
    return frozenset(tool.name for tool in tools if isinstance(tool, _Tool))


def known_tools(posted: str) -> frozenset[str]:
    """
    The tools a post names, less any name that is not a tool, since anyone
    can post anything.
    """
    return frozenset(name for name in posted.split() if name in TOOLS_BY_NAME)


def refreshed(bound: BoundCalendar) -> tuple[ComponentType, ...]:
    """
    The synced parts of the tools the page drew, for a response after a
    change, which the page merges by id.
    """
    return tuple(
        part
        for name in sorted(bound.tools)
        if TOOLS_BY_NAME[name].declared_by(bound.declaration)
        for part in TOOLS_BY_NAME[name].synced(bound)
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
                .name(declared.param(START))
                .id(f"{key}-{START}")
                .legend("Week starts on")
                .value(state.week_start)
                .content(
                    *(
                        Radio().value(day).label(names[WEEKDAYS.index(day)])
                        for day in WEEKDAYS
                    )
                ),
                Checkbox()
                .name(declared.param(WEEKDAYS_ONLY))
                .id(f"{key}-{WEEKDAYS_ONLY}")
                .value("1")
                .label("Weekdays only")
                .checked(state.weekdays),
                id=view_options_id(key),
                method="get",
                action=bound.urls.read,
                class_="flex flex-col gap-4",
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
                .x_on("click", unsafe(f"{close()}; {_open(help_id(key))}")),
            ),
        )
    )
