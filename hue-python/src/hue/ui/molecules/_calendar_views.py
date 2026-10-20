"""
The views of a Calendar: the time grid of a day or a week, the month, the
year and the agenda, each a function over the one Draw a rendering holds,
which owns the words, the links and the events they share. VIEWS at the
foot is the one place a view is defined.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal

from htmy import Context, html

from hue.formats import Formats
from hue.types.core import Component, ComponentType
from hue.ui._styles import (
    DASH,
    FOCUS_RING,
    FOCUS_RING_INSET,
    STEP,
    STEP_IDLE,
    STEP_SPENT,
)
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.molecules._days import (
    Event,
    EventColor,
    Placed,
    Slot,
    add_months,
    minutes,
    month_grid,
    pack,
    place,
    starts_on,
    week_of,
    weekend,
)
from hue.ui.molecules.date_picker import Weekday
from hue.ui.molecules.empty import Empty
from hue.ui.molecules.popover import Popover
from hue.ui.molecules.tabs import Tab, Tabs
from hue.ui.navigation import swap
from hue.utils import classnames, render_if, render_when

type CalendarView = Literal["day", "week", "month", "year", "agenda"]
type Href = Callable[[date, CalendarView], str]
type Actions = Callable[[Event], Iterable[ComponentType]]

_AGENDA_DAYS = 30

# The days a calendar can be around. A grid reaches into the weeks either
# side of its range, so the years at the ends of what a date can hold
# would overflow; a date outside is moved in, and no step leads out.
FIRST = date(2, 1, 1)
LAST = date(9998, 12, 31)


# Keyed by the Literal so mypy keeps them exhaustive. An event is a tint of
# its colour with a bar of it down the start edge; the text stays the
# foreground, so a tint never has to clear contrast on its own.
_TINT: dict[EventColor, str] = {
    1: "border-chart-1 bg-chart-1/15 hover:bg-chart-1/25",
    2: "border-chart-2 bg-chart-2/15 hover:bg-chart-2/25",
    3: "border-chart-3 bg-chart-3/15 hover:bg-chart-3/25",
    4: "border-chart-4 bg-chart-4/15 hover:bg-chart-4/25",
    5: "border-chart-5 bg-chart-5/15 hover:bg-chart-5/25",
    6: "border-chart-6 bg-chart-6/15 hover:bg-chart-6/25",
}
_SOLID: dict[EventColor, str] = {
    1: "bg-chart-1",
    2: "bg-chart-2",
    3: "bg-chart-3",
    4: "bg-chart-4",
    5: "bg-chart-5",
    6: "bg-chart-6",
}

_TOOLBAR = (
    "flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-border px-3 py-2"
)
_TITLE = "min-w-0 flex-1 truncate font-ui text-md font-semibold tabular-nums"
# The number of a day, a disc so today can be filled. It is marked on the
# link itself in a grid cell and on the header around it in the time grid.
_NUMBER = (
    "relative inline-flex size-7 items-center justify-center rounded-full font-ui "
    "text-sm font-semibold tabular-nums no-underline"
)
_NUMBER_TODAY = "aria-[current=date]:bg-accent aria-[current=date]:text-accent-fg"
_NUMBER_LINK = "hover:bg-surface-hover aria-[current=date]:hover:bg-accent-hover"

_EVENT = (
    "w-full min-w-0 cursor-pointer rounded-sm border-s-[3px] px-1.5 text-start "
    "text-xs font-medium text-fg"
)
_CHIP = "block h-5 truncate leading-5"
# A timed event in a list is a dot, its time and its title, with no fill.
_DOTTED = (
    "flex w-full cursor-pointer items-center gap-1.5 rounded-sm px-1 text-start "
    "text-xs font-medium leading-5 text-fg hover:bg-surface-hover"
)
_DOT = "size-2 flex-none rounded-full"
_TIME = "flex-none text-2xs tabular-nums text-fg-muted"
_REPEAT = "ms-1 inline size-3 align-[-2px] text-fg-muted"


# One hour of the time grid, in pixels, and where the grid opens: 07:30,
# just before most days start.
_HOUR = 48
_OPENS_AT = int(7.5 * _HOUR)
# The space between two events that follow each other, and the least box a
# line of text fits in. The least time an event is packed as is the time
# that box and its space cover, so one drawn taller than it lasts still
# pushes the next one along beside it rather than under it.
_GAP = 2
_LEAST_HEIGHT = 18
_LEAST = -(-(_LEAST_HEIGHT + _GAP) * 60 // _HOUR)
# Under this many minutes an event is one line, title then time; over this
# many pixels its title may wrap.
_SHORT = 45
_TALL = 70
# A month cell shows this many events, or one fewer and how many more.
_PER_CELL = 3
_HEAD = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-muted"
_NUMBER_IN_TODAY = (
    "group-aria-[current=date]:bg-accent group-aria-[current=date]:text-accent-fg"
)
_WEEKEND = "bg-canvas-subtle"
# The hour and half-hour rules of a column, drawn as a background so they
# cost no elements. The sizes are the hour height above.
_HOUR_LINES = (
    "background-image: linear-gradient(var(--color-border) 1px, transparent 1px), "
    "linear-gradient(color-mix(in oklab, var(--color-border) 50%, transparent) "
    "1px, transparent 1px); "
    f"background-size: 100% {_HOUR}px; background-position: 0 0, 0 {_HOUR // 2}px"
)


class EventButton(ChainableComponent):
    """
    The control that opens an event's popover, in whichever shape a view
    draws it. A component rather than an element because Popover wires its
    state onto the trigger's attributes.
    """

    category = None

    def __init__(self, event: Event, name: str) -> None:
        super().__init__()
        self._attrs["aria_label"] = name
        # What a script that moves or resizes events reads it by.
        if event.id is not None:
            self._attrs["data-event-id"] = event.id
        self._attrs["data-starts"] = event.starts.isoformat()
        self._attrs["data-ends"] = (event.ends or event.starts).isoformat()
        if not event.timed:
            self._attrs["data-all-day"] = ""

    def _render(self, context: Context) -> Component:
        return html.button(
            *self._children,
            type="button",
            class_=self._get_prop("class_"),
            **self._get_base_html_attrs(),
        )


@dataclass(frozen=True)
class Draw:
    """
    One rendering of a calendar: what every view, every link and every
    event reads, and the parts the views share. The views themselves are
    functions over it, below.
    """

    formats: Formats
    cursor: date
    view: CalendarView
    today: date | None
    start: Weekday
    weekdays: bool
    events: list[Event]
    href: Href | None
    actions: Actions | None
    own_id: str | None
    # An event's popover content by the event's identity, built once however
    # many days or cells the event is drawn in.
    panels: dict[int, ComponentType] = field(default_factory=dict, compare=False)

    @property
    def region(self) -> str | None:
        """
        The id of what the links swap: the toolbar and the view, under the
        frame, so the status outside them stays to be refreshed.
        """
        return self._stable("view")

    # ------------------------------------------------------------------
    # Words
    # ------------------------------------------------------------------

    def between(self, first: date, last: date) -> str:
        """
        12 to 18 October 2026, 28 September to 4 October 2026, or 28
        December 2026 to 3 January 2027, with a dash between: as little of
        the start as tells it apart from the end.
        """
        names = self.formats.month_names_in_date
        end = f"{last.day} {names[last.month - 1]} {last.year}"
        if (first.year, first.month) == (last.year, last.month):
            return f"{first.day} {DASH} {end}"
        if first.year == last.year:
            return f"{first.day} {names[first.month - 1]} {DASH} {end}"
        return f"{first.day} {names[first.month - 1]} {first.year} {DASH} {end}"

    def clock(self, moment: datetime | time) -> str:
        return self.formats.write(self.formats.time, moment)

    def name(self, event: Event) -> str:
        """
        The whole of an event in words, for the control that opens it: a
        chip's place in a grid says nothing to a screen reader, so the
        name says the time and the day as well as the title.
        """
        formats = self.formats
        if event.timed:
            starts = event.moments(formats)[0]
            text = f"{event.title}, {formats.day(starts.date())}, "
            text += self.times(event, "to")
        else:
            first, last = event.span(formats)
            text = f"{event.title}, all day, {formats.day(first)}"
            if last != first:
                text += f" to {formats.day(last)}"
        return f"{text}, repeats" if event.repeat else text

    def times(self, event: Event, to: str = DASH, *, end_day: bool = True) -> str:
        """
        A timed event by the clock: 13:00 to 14:30, with the end's day after
        its time when the event ends on another day and end_day asks for it,
        or 09:30 alone when it has no end.
        """
        starts, ends = event.moments(self.formats)
        if event.ends is None:
            return self.clock(starts)
        text = f"{self.clock(starts)} {to} {self.clock(ends)}"
        if end_day and ends.date() != starts.date():
            text += f" {self.formats.day(ends.date())}"
        return text

    def when(self, event: Event) -> str:
        formats = self.formats
        if event.timed:
            starts = event.moments(formats)[0]
            return f"{formats.day(starts.date())} · {self.times(event)}"
        first, last = event.span(formats)
        days = formats.day(first)
        if last != first:
            days += f" {DASH} {formats.day(last)}"
        return f"{days} · All day"

    def day_name(self, day: date) -> str:
        name = self.formats.day(day)
        return f"{name}, today" if day == self.today else name

    # ------------------------------------------------------------------
    # Links
    # ------------------------------------------------------------------

    def link(
        self,
        day: date,
        view: CalendarView,
        *content: ComponentType,
        label: str | None = None,
        classes: str = "",
        link_classes: str = "",
        current: bool = False,
        stable_id: str | None = None,
    ) -> ComponentType:
        """
        A link to a view on a day, or the content alone where there is
        nothing to link to.
        """
        current_date = "date" if current else None
        if self.href is None:
            return html.span(*content, aria_current=current_date, class_=classes)
        return html.a(
            *content,
            href=self.href(day, view),
            id=stable_id,
            aria_label=label,
            aria_current=current_date,
            class_=classnames(classes, link_classes, FOCUS_RING),
            **swap(self.region),
        )

    def toolbar(self, title: str) -> ComponentType:
        return html.div(
            render_when(self.href is not None, self._steps()),
            # Where focus lands after a swap that took the link it was on.
            html.h2(
                title,
                tabindex=None if self.region is None else "-1",
                class_=classnames(_TITLE, "outline-none"),
            ),
            render_if(self.href, self._switcher),
            class_=_TOOLBAR,
        )

    def _steps(self) -> ComponentType:
        return html.nav(
            self._step(-1, "Previous", "chevron-left"),
            render_if(
                self.today,
                lambda day: self.link(
                    day,
                    self.view,
                    "Today",
                    classes=classnames(STEP, STEP_IDLE),
                    stable_id=self._stable("today"),
                ),
            ),
            self._step(1, "Next", "chevron-right"),
            aria_label="Calendar",
            class_="flex items-center gap-1",
        )

    def _step(self, count: int, label: str, icon: str) -> ComponentType:
        glyph = HueIcon(icon).class_("size-3.5")
        day = VIEWS[self.view].step(self.cursor, count)
        if not FIRST <= day <= LAST:
            return html.span(
                glyph,
                aria_label=label,
                aria_disabled="true",
                class_=classnames(STEP, STEP_SPENT),
            )
        return self.link(
            day,
            self.view,
            glyph,
            label=label,
            classes=classnames(STEP, STEP_IDLE),
            stable_id=self._stable(label.lower()),
        )

    def _stable(self, name: str) -> str | None:
        """
        An id a part keeps across swaps (a step, the switcher, the region),
        so focus and the swap find it again after the swap replaced it.
        """
        return None if self.own_id is None else f"{self.own_id}-{name}"

    def _switcher(self, href: Href) -> ComponentType:
        tabs = Tabs().segmented().label("View")
        if self.region is not None and (views := self._stable("views")):
            tabs.id(views).target(self.region, sync=False)
        return tabs.content(
            *(
                Tab()
                .href(href(self.cursor, view))
                .current(view == self.view)
                .content(each.label)
                for view, each in VIEWS.items()
            )
        )

    def number(self, day: date, events: int = 0) -> ComponentType:
        """
        A day's number, a link to its day view, filled when it is today. The
        year view counts its events, with a dot under it when there are any.
        """
        label = self.day_name(day)
        if events:
            label += f", {events} event" if events == 1 else f", {events} events"
        return self.link(
            day,
            "day",
            html.time(str(day.day), datetime=day.isoformat()),
            render_when(
                events > 0,
                html.span(
                    aria_hidden="true",
                    class_="absolute bottom-0.5 size-1 rounded-full bg-current",
                ),
            ),
            label=label,
            classes=classnames(_NUMBER, _NUMBER_TODAY),
            link_classes=_NUMBER_LINK,
            current=day == self.today,
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def event(self, event: Event, button: EventButton) -> ComponentType:
        """
        The button and the popover it opens, titled by the event.
        """
        return (
            Popover()
            .title(event.title)
            # Fixed: in the time grid the popover opens inside a scroll
            # container, which would clip one positioned on the page.
            .placement("bottom-start", fixed=True)
            .trigger(button)
            .class_("h-full w-full")
            .content(self._panel(event))
        )

    def _panel(self, event: Event) -> ComponentType:
        """
        When, whether it repeats, where and notes, then the app's actions and
        a link to the event itself when it has one.
        """
        if id(event) in self.panels:
            return self.panels[id(event)]
        actions = list(self.actions(event)) if self.actions is not None else []
        rows = (
            self._row("When", "clock", self.when(event)),
            render_when(
                bool(event.repeat), self._row("Repeats", "repeat", "Part of a series")
            ),
            render_if(
                event.location, lambda text: self._row("Location", "map-pin", text)
            ),
            render_if(
                event.notes,
                lambda text: self._row(
                    "Notes", "text", html.span(text, class_="whitespace-pre-line")
                ),
            ),
        )
        foot = (
            *actions,
            render_if(
                event.href,
                lambda href: html.a(
                    "Open",
                    href=href,
                    class_=classnames(
                        "ms-auto rounded-sm font-ui text-sm font-semibold "
                        "text-accent-text underline-offset-[3px] hover:underline",
                        FOCUS_RING,
                    ),
                ),
            ),
        )
        panel = html.div(
            html.dl(*rows, class_="flex flex-col gap-2 text-sm"),
            render_when(
                bool(actions) or event.href is not None,
                html.div(
                    *foot,
                    class_="flex flex-wrap items-center gap-2 border-t "
                    "border-border pt-3",
                ),
            ),
            class_="flex flex-col gap-3.5",
        )
        self.panels[id(event)] = panel
        return panel

    def _row(self, term: str, icon: str, detail: ComponentType) -> ComponentType:
        return html.div(
            html.dt(term, class_="sr-only"),
            HueIcon(icon).class_("mt-0.5 size-4 flex-none text-fg-muted"),
            html.dd(detail, class_="min-w-0"),
            class_="flex items-start gap-2.5",
        )

    def title_of(self, event: Event) -> tuple[ComponentType, ...]:
        """
        A title with the repeat mark after it when the event repeats.
        """
        return (
            event.title,
            render_when(bool(event.repeat), HueIcon("repeat").class_(_REPEAT)),
        )

    def chip(self, event: Event, before: bool, after: bool) -> ComponentType:
        """
        An all-day event in a list: a filled bar, squared off at an end it
        continues past.
        """
        button = (
            EventButton(event, self.name(event))
            .class_(
                classnames(
                    _EVENT,
                    _CHIP,
                    _TINT[event.tone],
                    FOCUS_RING_INSET,
                    {"rounded-s-none": before, "rounded-e-none": after},
                )
            )
            .content(
                *self.title_of(event),
                # The squared corner is what a sighted reader sees of a bar
                # that goes on; this is what a screen reader hears of it.
                render_when(
                    before or after, html.span(" (continues)", class_="sr-only")
                ),
            )
        )
        return self.event(event, button)

    def dotted(self, placed: Placed) -> ComponentType:
        """
        A timed event in a list: a dot in its colour, its start time and
        its title.
        """
        event = placed.event
        starts = starts_on(placed, self.formats)
        button = (
            EventButton(event, self.name(event))
            .class_(classnames(_DOTTED, FOCUS_RING_INSET))
            .content(
                html.span(
                    aria_hidden="true", class_=classnames(_DOT, _SOLID[event.tone])
                ),
                html.span(self.clock(starts), class_=_TIME),
                html.span(*self.title_of(event), class_="min-w-0 truncate"),
            )
        )
        return self.event(event, button)

    def item(self, placed: Placed) -> ComponentType:
        return html.li(
            self.dotted(placed)
            if placed.event.timed
            else self.chip(
                placed.event, placed.continues_before, placed.continues_after
            ),
            # A flex item rather than a line box, so the chip inside sits
            # flush with no descender gap under it.
            class_="flex",
        )

    def week(self) -> list[date]:
        return self.shown(week_of(self.cursor, self.start))

    def shown(self, days: Iterable[date]) -> list[date]:
        return [day for day in days if not (self.weekdays and weekend(day))]


@dataclass(frozen=True)
class _Bar:
    """
    An all-day event across the columns of a week, from the first it covers
    to the last, and whether it goes on past either end.
    """

    event: Event
    first: int
    last: int
    before: bool
    after: bool


# Day and week


def time_grid(draw: Draw, days: list[date]) -> ComponentType:
    """
    A column per day over twenty-four hours, with the all-day events in
    a row above and the hours down the side.
    """
    placed = place(draw.events, days[0], days[-1], draw.formats)
    columns = f"grid-template-columns: 3.5rem repeat({len(days)}, minmax(0, 1fr))"
    bars = _bars(days, placed)
    return html.div(
        html.div(
            html.div(),
            *(_day_head(draw, day) for day in days),
            class_="grid border-b border-border",
            style=columns,
        ),
        html.div(
            html.div(
                "All day",
                class_=classnames(_HEAD, "flex items-center justify-end pe-2"),
            ),
            render_when(
                bool(bars),
                html.ul(
                    *(_bar(draw, bar) for bar in bars),
                    class_="grid gap-y-0.5 border-s border-border py-1",
                    style=(
                        f"grid-column: 2 / -1; grid-template-columns: "
                        f"repeat({len(days)}, minmax(0, 1fr)); "
                        "grid-auto-flow: row dense; grid-auto-rows: 1.25rem"
                    ),
                ),
                html.div(class_="min-h-7 border-s border-border"),
            ),
            class_="grid border-b border-border",
            style=columns,
        ),
        html.div(
            html.div(
                _hours(draw),
                *(_column(draw, day, placed.get(day, [])) for day in days),
                class_="grid",
                style=f"{columns}; height: {24 * _HOUR}px",
            ),
            class_="max-h-[42rem] overflow-y-auto",
            **{"x-init": f"$el.scrollTop = {_OPENS_AT}"},
        ),
        class_="flex flex-col",
    )


def _day_head(draw: Draw, day: date) -> ComponentType:
    return draw.link(
        day,
        "day",
        html.span(draw.formats.day_abbreviations[day.weekday()], class_=_HEAD),
        html.span(str(day.day), class_=classnames(_NUMBER, _NUMBER_IN_TODAY)),
        label=draw.day_name(day),
        classes="group flex h-13 items-center justify-center gap-2 border-s "
        "border-border no-underline",
        link_classes="hover:bg-surface-hover",
        current=day == draw.today,
    )


def _bars(days: list[date], placed: dict[date, list[Placed]]) -> list[_Bar]:
    """
    Each all-day event once, across every shown day it covers. Keyed by
    identity: two events alike in every field are still two events.
    """
    found: dict[int, _Bar] = {}
    for index, day in enumerate(days):
        for each in placed.get(day, []):
            if each.event.timed:
                continue
            known = found.get(id(each.event))
            found[id(each.event)] = _Bar(
                each.event,
                index if known is None else known.first,
                index,
                each.continues_before if known is None else known.before,
                each.continues_after,
            )
    return list(found.values())


def _bar(draw: Draw, bar: _Bar) -> ComponentType:
    return html.li(
        draw.chip(bar.event, bar.before, bar.after),
        class_=classnames("flex", {"ms-0.5": not bar.before, "me-0.5": not bar.after}),
        style=f"grid-column: {bar.first + 1} / {bar.last + 2}",
    )


def _hours(draw: Draw) -> ComponentType:
    """
    The gutter. Decoration: every event says its own time.
    """
    return html.div(
        *(
            html.span(
                draw.clock(time(hour)),
                class_="absolute end-2 -translate-y-1/2 text-2xs tabular-nums "
                "text-fg-muted",
                style=f"top: {hour * _HOUR}px",
            )
            for hour in range(1, 24)
        ),
        aria_hidden="true",
        class_="relative",
    )


def _column(draw: Draw, day: date, items: list[Placed]) -> ComponentType:
    timed = [each for each in items if each.event.timed]
    spans = [minutes(each, draw.formats, _LEAST) for each in timed]
    slots = pack(spans)
    return html.div(
        render_when(
            bool(timed),
            html.ul(
                *(
                    _timed(draw, each, span, slot)
                    for each, span, slot in zip(timed, spans, slots, strict=True)
                ),
                class_="absolute inset-0",
            ),
        ),
        render_when(day == draw.today, _now()),
        data_date=day.isoformat(),
        class_=classnames("relative border-s border-border", {_WEEKEND: weekend(day)}),
        style=_HOUR_LINES,
    )


def _timed(
    draw: Draw, placed: Placed, span: tuple[int, int], slot: Slot
) -> ComponentType:
    event = placed.event
    start, end = span
    starts = starts_on(placed, draw.formats)
    height = (end - start) * _HOUR // 60 - _GAP
    short = end - start < _SHORT
    if short:
        title_classes, time_classes = "min-w-0 truncate", "flex-none"
    elif height > _TALL:
        title_classes, time_classes = "line-clamp-3", "block truncate"
    else:
        title_classes, time_classes = "block truncate", "block truncate"
    button = (
        EventButton(event, draw.name(event))
        .class_(
            classnames(
                _EVENT,
                _TINT[event.tone],
                FOCUS_RING_INSET,
                "h-full overflow-hidden py-0.5 leading-4",
                "flex items-baseline gap-1.5" if short else "block",
                # Squared where it runs on from the day before or into the
                # next, as an all-day bar is where the week cuts it.
                {
                    "rounded-t-none": placed.continues_before,
                    "rounded-b-none": placed.continues_after,
                },
            )
        )
        .content(
            html.span(
                *draw.title_of(event),
                class_=classnames("font-semibold", title_classes),
            ),
            html.span(
                draw.clock(starts) if short else draw.times(event, end_day=False),
                class_=classnames("tabular-nums text-fg-muted", time_classes),
            ),
        )
    )
    return html.li(
        draw.event(event, button),
        class_="absolute flex",
        style=(
            f"top: {start * _HOUR // 60}px; "
            f"height: {height}px; "
            f"left: calc({slot.column} / {slot.columns} * 100% + 2px); "
            f"width: calc(100% / {slot.columns} - 4px)"
        ),
    )


def _now() -> ComponentType:
    """
    The line at the time it is, moved every minute by the browser, which
    is the one clock that knows the reader's now.
    """
    # Assumes the browser's timezone is the one Formats moves events
    # into; where they differ, the line and the events disagree.
    return html.div(
        aria_hidden="true",
        class_="pointer-events-none absolute inset-x-0 z-10 h-0.5 bg-danger "
        "before:absolute before:-start-1 before:-top-[3px] before:size-2 "
        "before:rounded-full before:bg-danger",
        **{
            "x-data": (
                "{ minute: 0, timer: null, tick() { const now = new Date(); "
                "this.minute = now.getHours() * 60 + now.getMinutes() }, "
                "destroy() { clearInterval(this.timer) } }"
            ),
            "x-init": "tick(); timer = setInterval(() => tick(), 60000)",
            ":style": f"'top: ' + minute * {_HOUR} / 60 + 'px'",
        },
    )


# Month


def month(draw: Draw) -> ComponentType:
    """
    A table with a column per weekday and six rows of weeks. A table
    rather than a grid widget: every event is a control to read and
    open, and browse-mode table navigation already announces the
    weekday with each cell.
    """
    formats = draw.formats
    rows = [draw.shown(row) for row in month_grid(draw.cursor, draw.start)]
    placed = place(draw.events, rows[0][0], rows[-1][-1], formats)
    return html.table(
        html.caption(formats.month(draw.cursor), class_="sr-only"),
        html.thead(
            html.tr(
                *(
                    html.th(
                        formats.day_abbreviations[day.weekday()],
                        scope="col",
                        abbr=formats.day_names[day.weekday()],
                        class_=classnames(_HEAD, "border-b border-border py-2"),
                    )
                    for day in rows[0]
                )
            )
        ),
        html.tbody(
            *(
                html.tr(
                    *(_cell(draw, day, placed.get(day, [])) for day in row),
                    class_="border-b border-border last:border-b-0",
                )
                for row in rows
            ),
        ),
        class_="w-full table-fixed border-collapse",
    )


def _cell(draw: Draw, day: date, items: list[Placed]) -> ComponentType:
    outside = (day.year, day.month) != (draw.cursor.year, draw.cursor.month)
    shown = items if len(items) <= _PER_CELL else items[: _PER_CELL - 1]
    return html.td(
        draw.number(day),
        render_when(
            bool(shown),
            html.ul(
                *(draw.item(each) for each in shown),
                class_="mt-1 flex flex-col gap-0.5",
            ),
        ),
        render_when(len(shown) < len(items), _more(draw, day, items[len(shown) :])),
        data_date=day.isoformat(),
        class_=classnames(
            "h-28 overflow-hidden border-e border-border p-1 align-top last:border-e-0",
            {
                _WEEKEND: outside or weekend(day),
                "text-fg-subtle": outside,
            },
        ),
    )


def _more(draw: Draw, day: date, hidden: list[Placed]) -> ComponentType:
    """
    The events a cell had no room for, in a popover headed by the day.
    """
    name = draw.formats.day(day)
    count = len(hidden)
    return (
        Popover()
        .title(name)
        .placement("bottom-start", fixed=True)
        .trigger(
            Button()
            .variant("ghost")
            .size("xs")
            .aria_label(f"+{count} more, {name}")
            .class_("mt-0.5")
            .content(f"+{count} more")
        )
        .content(
            html.ul(
                *(draw.item(each) for each in hidden),
                class_="flex flex-col gap-0.5",
            )
        )
    )


# Year


def year(draw: Draw) -> ComponentType:
    year = draw.cursor.year
    placed = place(draw.events, date(year, 1, 1), date(year, 12, 31), draw.formats)
    return html.div(
        *(_mini(draw, date(year, month, 1), placed) for month in range(1, 13)),
        class_="grid grid-cols-[repeat(auto-fill,minmax(14rem,1fr))] gap-x-8 "
        "gap-y-6 p-4",
    )


def _mini(draw: Draw, month: date, placed: dict[date, list[Placed]]) -> ComponentType:
    """
    One small month: its days as links to their day view, each with a
    dot when something is on.
    """
    formats = draw.formats
    rows = [
        row
        for row in month_grid(month, draw.start)
        if any(day.month == month.month for day in row)
    ]
    return html.table(
        html.caption(
            formats.month_names[month.month - 1],
            class_="pb-1 text-start font-ui text-sm font-semibold",
        ),
        html.thead(
            html.tr(
                *(
                    html.th(
                        formats.day_abbreviations[day.weekday()][0],
                        scope="col",
                        abbr=formats.day_names[day.weekday()],
                        class_=classnames(_HEAD, "pb-1 text-center"),
                    )
                    for day in rows[0]
                )
            )
        ),
        html.tbody(
            *(
                html.tr(
                    *(
                        html.td(
                            render_when(
                                day.month == month.month,
                                draw.number(day, len(placed.get(day, []))),
                            ),
                            class_="p-0 text-center",
                        )
                        for day in row
                    )
                )
                for row in rows
            )
        ),
        class_="w-full table-fixed border-collapse",
    )


# Agenda


def agenda(draw: Draw) -> ComponentType:
    """
    The next thirty days with something on, each day a heading over
    its list; an Empty when none of them has.
    """
    formats = draw.formats
    first = draw.cursor
    last = _agenda_last(draw)
    placed = place(draw.events, first, last, formats)
    days = sorted(placed)
    if not days:
        return (
            Empty()
            .title("Nothing scheduled")
            .description(f"{formats.day(first)} to {formats.day(last)}.")
        )
    return html.div(
        *(_agenda_day(draw, day, placed[day]) for day in days),
        class_="flex flex-col divide-y divide-border px-4",
    )


def _agenda_day(draw: Draw, day: date, items: list[Placed]) -> ComponentType:
    formats = draw.formats
    return html.section(
        html.div(
            draw.number(day),
            html.span(
                formats.day_abbreviations[day.weekday()],
                html.br(),
                formats.month(day),
                class_="text-xs leading-tight text-fg-muted",
            ),
            class_="flex items-center gap-2 self-start",
        ),
        html.ul(
            *(html.li(_agenda_row(draw, each), class_="flex") for each in items),
            class_="flex flex-col gap-0.5",
        ),
        data_date=day.isoformat(),
        class_="grid grid-cols-[7.5rem_minmax(0,1fr)] gap-4 py-3",
    )


def _agenda_row(draw: Draw, placed: Placed) -> ComponentType:
    event = placed.event
    formats = draw.formats
    if event.timed:
        when = draw.times(event, end_day=False)
    else:
        first, last = event.span(formats)
        total = (last - first).days + 1
        nth = (placed.day - first).days + 1
        when = "All day" if total == 1 else f"Day {nth} of {total}"
    button = (
        EventButton(event, draw.name(event))
        .class_(
            classnames(
                "grid w-full cursor-pointer grid-cols-[6.5rem_auto_minmax(0,1fr)] "
                "items-center gap-3 rounded-md px-2.5 py-2 text-start text-sm "
                "text-fg hover:bg-surface-hover",
                FOCUS_RING_INSET,
            )
        )
        .content(
            html.span(when, class_="text-xs tabular-nums text-fg-muted"),
            html.span(aria_hidden="true", class_=classnames(_DOT, _SOLID[event.tone])),
            html.span(
                html.span(*draw.title_of(event), class_="font-semibold"),
                render_if(
                    event.location,
                    lambda text: html.span(text, class_="ms-2 text-fg-muted"),
                ),
                class_="min-w-0 truncate",
            ),
        )
    )
    return draw.event(event, button)


@dataclass(frozen=True)
class _View:
    label: str
    # The day the previous or the next page of this view is around.
    step: Callable[[date, int], date]
    title: Callable[[Draw], str]
    render: Callable[[Draw], ComponentType]


def _agenda_last(draw: Draw) -> date:
    return draw.cursor + timedelta(days=_AGENDA_DAYS - 1)


VIEWS: dict[CalendarView, _View] = {
    "day": _View(
        "Day",
        lambda day, count: day + timedelta(days=count),
        lambda draw: draw.formats.day(draw.cursor),
        lambda draw: time_grid(draw, [draw.cursor]),
    ),
    "week": _View(
        "Week",
        lambda day, count: day + timedelta(weeks=count),
        lambda draw: draw.between(draw.week()[0], draw.week()[-1]),
        lambda draw: time_grid(draw, draw.week()),
    ),
    "month": _View(
        "Month",
        add_months,
        lambda draw: draw.formats.month(draw.cursor),
        month,
    ),
    "year": _View(
        "Year",
        lambda day, count: add_months(day, 12 * count),
        lambda draw: str(draw.cursor.year),
        year,
    ),
    "agenda": _View(
        "Agenda",
        lambda day, count: day + timedelta(days=_AGENDA_DAYS * count),
        lambda draw: draw.between(draw.cursor, _agenda_last(draw)),
        agenda,
    ),
}
