from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.formats import Formats
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING, FOCUS_RING_INSET
from hue.ui.atoms.button import Button
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.molecules._days import (
    Event,
    EventColor,
    Placed,
    Slot,
    WeekStart,
    add_months,
    minutes,
    month_grid,
    pack,
    place,
    week_of,
)
from hue.ui.molecules.empty import Empty
from hue.ui.molecules.popover import Popover
from hue.ui.molecules.tabs import Tab, Tabs
from hue.ui.navigation import SYNC, swap
from hue.utils import classnames, render_if, render_when

__all__ = ["Calendar", "CalendarView", "Event", "EventColor", "WeekStart"]

type CalendarView = Literal["day", "week", "month", "year", "agenda"]

# date() is a modifier below, which hides the type by that name inside the
# class, as Formats' fields do.
type _Day = date
type _Href = Callable[[date, CalendarView], str]
type _Actions = Callable[[Event], Iterable[ComponentType]]

_AGENDA_DAYS = 30

#: The range separator. An en dash, which is what a range takes.
_DASH = "\u2013"


@dataclass(frozen=True)
class _View:
    label: str
    # The day the previous or the next page of this view is around.
    step: Callable[[date, int], date]


_VIEWS: dict[CalendarView, _View] = {
    "day": _View("Day", lambda day, count: day + timedelta(days=count)),
    "week": _View("Week", lambda day, count: day + timedelta(weeks=count)),
    "month": _View("Month", add_months),
    "year": _View("Year", lambda day, count: add_months(day, 12 * count)),
    "agenda": _View(
        "Agenda", lambda day, count: day + timedelta(days=_AGENDA_DAYS * count)
    ),
}

# One hour of the time grid, in pixels, and where the grid opens: 07:30,
# just before most days start.
_HOUR = 48
_OPENS_AT = int(7.5 * _HOUR)
# Under this many minutes an event is one line, title then time; over this
# many pixels its title may wrap.
_SHORT = 45
_TALL = 70
# A month cell shows this many events, or one fewer and how many more.
_PER_CELL = 3

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

_FRAME = (
    "flex w-full flex-col rounded-lg border border-border bg-surface text-base text-fg"
)
# Alpine AJAX marks what it is about to replace aria-busy while the request
# runs, as it does for a Table.
_LOADING = (
    "transition-opacity duration-150 aria-busy:opacity-60 aria-busy:cursor-progress"
)
_TOOLBAR = (
    "flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-border px-3 py-2"
)
_TITLE = "min-w-0 flex-1 truncate font-ui text-md font-semibold tabular-nums"
# A step is what a Pagination step is, so the two read as one control.
_STEP = (
    "inline-flex h-control-sm min-w-[var(--spacing-control-sm)] items-center "
    "justify-center rounded-md px-2 font-ui text-sm font-medium text-fg-muted "
    "no-underline hover:bg-surface-hover hover:text-fg"
)
_HEAD = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-muted"
# The number of a day, a disc so today can be filled. It is marked on the
# link itself in a grid cell and on the header around it in the time grid.
_NUMBER = (
    "inline-flex size-7 items-center justify-center rounded-full font-ui "
    "text-sm font-semibold tabular-nums no-underline"
)
_NUMBER_TODAY = "aria-[current=date]:bg-accent aria-[current=date]:text-accent-fg"
_NUMBER_IN_TODAY = (
    "group-aria-[current=date]:bg-accent group-aria-[current=date]:text-accent-fg"
)
_NUMBER_LINK = "hover:bg-surface-hover aria-[current=date]:hover:bg-accent-hover"
_WEEKEND = "bg-canvas-subtle"

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

# The hour and half-hour rules of a column, drawn as a background so they
# cost no elements. The sizes are the hour height above.
_HOUR_LINES = (
    "background-image: linear-gradient(var(--color-border) 1px, transparent 1px), "
    "linear-gradient(color-mix(in oklab, var(--color-border) 50%, transparent) "
    "1px, transparent 1px); "
    f"background-size: 100% {_HOUR}px; background-position: 0 0, 0 {_HOUR // 2}px"
)


class Calendar(ChainableComponent):
    """
    Events on a day, a week, a month, a year or the next thirty days, drawn
    the way Table draws the rows it is handed.

    date() is the day the view is around and view() which view; events()
    fills it and today() marks a day. href() takes a function from a day
    and a view to its URL, which makes the navigation, the view switcher
    and every day a link, and with an id the links swap the calendar in
    place. actions() fills the buttons of an event's popover.
    """

    category = "Data"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .date(date(2026, 10, 14))
            .today(date(2026, 10, 14))
            .href(lambda day, view: f"#{view}/{day}")
            .events(
                [
                    Event(
                        "Design review",
                        datetime(2026, 10, 14, 13),
                        datetime(2026, 10, 14, 14, 30),
                        id="1",
                        location="Room 3B",
                        notes="Walk the range state matrix.",
                    ),
                    Event(
                        "Contrast audit",
                        datetime(2026, 10, 15, 10),
                        datetime(2026, 10, 15, 12),
                        id="2",
                        color=2,
                    ),
                    Event(
                        "Pairing",
                        datetime(2026, 10, 15, 11),
                        datetime(2026, 10, 15, 12, 30),
                        id="3",
                        color=3,
                    ),
                    Event(
                        "Release freeze",
                        date(2026, 10, 16),
                        date(2026, 10, 17),
                        id="4",
                        color=4,
                    ),
                    Event(
                        "Standup",
                        datetime(2026, 10, 12, 9),
                        datetime(2026, 10, 12, 9, 15),
                        id="5",
                        recurring=True,
                        color=6,
                        href="#standup",
                    ),
                ]
            )
        )

    def view(self, value: CalendarView) -> Self:
        self._props["view"] = value
        return self

    def date(self, value: _Day) -> Self:
        """
        The day the view is around: the day itself, or any day of the week,
        the month or the year shown, or the first of the agenda's thirty.
        """
        self._props["date"] = value
        return self

    def events(self, value: Iterable[Event]) -> Self:
        self._props["events"] = list(value)
        return self

    def today(self, value: _Day) -> Self:
        """
        The day to mark as today. Told rather than read off the clock, so a
        page renders the same for everyone in one timezone and the docs
        render the same every day. The Today link leads to it.
        """
        self._props["today"] = value
        return self

    def week_start(self, value: WeekStart) -> Self:
        self._props["week_start"] = value
        return self

    def weekdays(self, value: bool = True) -> Self:
        """
        Leave Saturday and Sunday out of the week and the month.
        """
        self._props["weekdays"] = value
        return self

    def href(self, value: _Href) -> Self:
        """
        Where a view on a day lives. Given one, Previous, Today and Next,
        the view switcher and every day are links to it; without one the
        calendar is a picture of its events.
        """
        self._props["href"] = value
        return self

    def actions(self, value: _Actions) -> Self:
        """
        The buttons at the foot of an event's popover, given the event:
        Edit, Duplicate, Delete, or whatever the app does with one.
        """
        self._props["actions"] = value
        return self

    def _render(self, context: Context) -> Component:
        cursor: date | None = self._get_prop("date")
        if cursor is None:
            raise ValueError("Calendar needs a date(): the day its view is around.")
        view: CalendarView = self._get_prop("view", "week")
        attrs = self._get_base_html_attrs()
        own_id: str | None = attrs.pop("id", None)
        draw = _Draw(
            formats=Formats.from_context(context),
            cursor=cursor,
            view=view,
            today=self._get_prop("today"),
            start=self._get_prop("week_start", "monday"),
            weekdays=self._get_prop("weekdays", False),
            events=self._get_prop("events", []),
            href=self._get_prop("href"),
            actions=self._get_prop("actions"),
            own_id=own_id,
        )
        title = draw.title()
        body: Callable[[], ComponentType] = {
            "day": lambda: draw.time_grid([cursor]),
            "week": lambda: draw.time_grid(draw.week()),
            "month": draw.month,
            "year": draw.year,
            "agenda": draw.agenda,
        }[view]

        return html.div(
            # Outside the region the links swap and refreshed by SYNC, so
            # its text changes in place and is announced, where a live
            # region that arrived with the new markup would not be.
            render_if(
                own_id,
                lambda frame: html.p(
                    title,
                    id=f"{frame}-status",
                    role="status",
                    class_="sr-only",
                    **SYNC,
                ),
            ),
            html.div(
                draw.toolbar(title),
                body(),
                id=draw.region,
                class_=_LOADING,
                **(SYNC if own_id else {}),
            ),
            id=own_id,
            class_=classnames(_FRAME, self._get_prop("class_")),
            **attrs,
        )


class _EventButton(ChainableComponent):
    """
    The control that opens an event's popover, in whichever shape a view
    draws it. A component rather than an element because Popover wires its
    state onto the trigger's attributes.
    """

    category = None

    def __init__(self, event: Event, name: str, classes: str) -> None:
        super().__init__()
        self._props["classes"] = classes
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
            class_=self._props["classes"],
            **self._get_base_html_attrs(),
        )


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


@dataclass(frozen=True)
class _Draw:
    """
    One rendering of a calendar: what every view, every link and every
    event reads. Held once rather than handed down, because the parts are
    the same from the toolbar to the deepest chip.
    """

    formats: Formats
    cursor: date
    view: CalendarView
    today: date | None
    start: WeekStart
    weekdays: bool
    events: list[Event]
    href: _Href | None
    actions: _Actions | None
    own_id: str | None

    @property
    def region(self) -> str | None:
        """
        The id of what the links swap: the toolbar and the view, under the
        frame, so the status outside them stays to be refreshed.
        """
        return None if self.own_id is None else f"{self.own_id}-view"

    # ------------------------------------------------------------------
    # Words
    # ------------------------------------------------------------------

    def title(self) -> str:
        formats, cursor = self.formats, self.cursor
        if self.view == "day":
            return formats.day(cursor)
        if self.view == "month":
            return formats.month(cursor)
        if self.view == "year":
            return str(cursor.year)
        if self.view == "week":
            days = week_of(cursor, self.start)
            return self._range(days[0], days[-1])
        return self._range(cursor, cursor + timedelta(days=_AGENDA_DAYS - 1))

    def _range(self, first: date, last: date) -> str:
        """
        12 to 18 October 2026, 28 September to 4 October 2026, or 28
        December 2026 to 3 January 2027, with a dash between: as little of
        the start as tells it apart from the end.
        """
        names = self.formats.month_names
        end = f"{last.day} {names[last.month - 1]} {last.year}"
        if (first.year, first.month) == (last.year, last.month):
            return f"{first.day} {_DASH} {end}"
        if first.year == last.year:
            return f"{first.day} {names[first.month - 1]} {_DASH} {end}"
        return f"{first.day} {names[first.month - 1]} {first.year} {_DASH} {end}"

    def clock(self, moment: datetime | time) -> str:
        return moment.strftime(self.formats.time)

    def name(self, event: Event) -> str:
        """
        The whole of an event in words, for the control that opens it: a
        chip's place in a grid says nothing to a screen reader, so the
        name says the time and the day as well as the title.
        """
        formats = self.formats
        if event.timed:
            starts, ends = event.moments(formats)
            if ends.date() == starts.date():
                when = f"{self.clock(starts)} to {self.clock(ends)}, "
                when += formats.day(starts.date())
            else:
                when = f"{self.clock(starts)} {formats.day(starts.date())} to "
                when += f"{self.clock(ends)} {formats.day(ends.date())}"
            text = f"{event.title}, {when}"
        else:
            first, last = event.span(formats)
            text = f"{event.title}, all day, {formats.day(first)}"
            if last != first:
                text += f" to {formats.day(last)}"
        return f"{text}, repeats" if event.recurring else text

    def when(self, event: Event) -> str:
        formats = self.formats
        if event.timed:
            starts, ends = event.moments(formats)
            if ends.date() == starts.date():
                span = f"{self.clock(starts)} {_DASH} {self.clock(ends)}"
            else:
                span = (
                    f"{self.clock(starts)} {_DASH} {self.clock(ends)} "
                    f"{formats.day(ends.date())}"
                )
            return f"{formats.day(starts.date())} · {span}"
        first, last = event.span(formats)
        days = formats.day(first)
        if last != first:
            days += f" {_DASH} {formats.day(last)}"
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
            html.h2(title, class_=_TITLE),
            render_if(self.href, self._switcher),
            class_=_TOOLBAR,
        )

    def _steps(self) -> ComponentType:
        return html.nav(
            self._step("previous", -1, "Previous", "chevron-left"),
            render_if(
                self.today,
                lambda day: self.link(
                    day,
                    self.view,
                    "Today",
                    classes=_STEP,
                    stable_id=self._stable("today"),
                ),
            ),
            self._step("next", 1, "Next", "chevron-right"),
            aria_label="Calendar",
            class_="flex items-center gap-1",
        )

    def _step(self, name: str, count: int, label: str, icon: str) -> ComponentType:
        try:
            day = _VIEWS[self.view].step(self.cursor, count)
        except (OverflowError, ValueError):
            # Past either end of the years a date can hold.
            return ""
        return self.link(
            day,
            self.view,
            HueIcon(icon).class_("size-3.5"),
            label=label,
            classes=_STEP,
            stable_id=self._stable(name),
        )

    def _stable(self, name: str) -> str | None:
        """
        An id a step keeps across swaps, so focus finds it again after the
        swap replaced it.
        """
        return None if self.own_id is None else f"{self.own_id}-{name}"

    def _switcher(self, href: _Href) -> ComponentType:
        tabs = Tabs().segmented().label("View")
        if self.region is not None:
            tabs.id(f"{self.own_id}-views").target(self.region)
        return tabs.content(
            *(
                Tab()
                .href(href(self.cursor, view))
                .current(view == self.view)
                .content(each.label)
                for view, each in _VIEWS.items()
            )
        )

    def number(self, day: date) -> ComponentType:
        """
        A day's number, a link to its day view, filled when it is today.
        """
        return self.link(
            day,
            "day",
            html.time(str(day.day), datetime=day.isoformat()),
            label=self.day_name(day),
            classes=classnames(_NUMBER, _NUMBER_TODAY),
            link_classes=_NUMBER_LINK,
            current=day == self.today,
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def event(self, event: Event, button: _EventButton) -> ComponentType:
        """
        The button and the popover it opens: colour, title, when, whether
        it repeats, where, notes, then the app's actions and a link to the
        event itself when it has one.
        """
        actions = list(self.actions(event)) if self.actions is not None else []
        rows = (
            self._row("When", "clock", self.when(event)),
            render_when(event.recurring, self._row("Repeats", "repeat", "Repeats")),
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
        return (
            Popover()
            .label(event.title)
            # Fixed: in the time grid the popover opens inside a scroll
            # container, which would clip one positioned on the page.
            .placement("bottom-start", fixed=True)
            .trigger(button)
            .class_("h-full w-full")
            .content(
                html.div(
                    html.span(
                        aria_hidden="true",
                        class_=classnames(
                            "mt-1 size-3 flex-none rounded-xs", _SOLID[event.color]
                        ),
                    ),
                    html.div(
                        html.p(
                            event.title,
                            class_="font-ui text-base font-bold leading-[1.35]",
                        ),
                        html.p(
                            self.when(event),
                            class_="mt-0.5 text-sm tabular-nums text-fg-muted",
                        ),
                        class_="min-w-0",
                    ),
                    class_="flex items-start gap-2.5",
                ),
                html.dl(*rows, class_="flex flex-col gap-2 text-sm"),
                render_when(
                    bool(actions) or event.href is not None,
                    html.div(
                        *foot,
                        class_="flex flex-wrap items-center gap-2 border-t "
                        "border-border pt-3",
                    ),
                ),
            )
        )

    def _row(self, term: str, icon: str, detail: ComponentType) -> ComponentType:
        return html.div(
            html.dt(term, class_="sr-only"),
            HueIcon(icon).class_("mt-0.5 size-4 flex-none text-fg-muted"),
            html.dd(detail, class_="min-w-0"),
            class_="flex items-start gap-2.5",
        )

    def _title_of(self, event: Event) -> tuple[ComponentType, ...]:
        """
        A title with the repeat mark after it when the event repeats.
        """
        return (
            event.title,
            render_when(event.recurring, HueIcon("repeat").class_(_REPEAT)),
        )

    def chip(self, event: Event, before: bool, after: bool) -> ComponentType:
        """
        An all-day event in a list: a filled bar, squared off at an end it
        continues past.
        """
        button = _EventButton(
            event,
            self.name(event),
            classnames(
                _EVENT,
                _CHIP,
                _TINT[event.color],
                FOCUS_RING_INSET,
                {"rounded-s-none": before, "rounded-e-none": after},
            ),
        ).content(
            *self._title_of(event),
            # The squared corner is what a sighted reader sees of a bar
            # that goes on; this is what a screen reader hears of it.
            render_when(before or after, html.span(" (continues)", class_="sr-only")),
        )
        return self.event(event, button)

    def dotted(self, placed: Placed) -> ComponentType:
        """
        A timed event in a list: a dot in its colour, its start time and
        its title.
        """
        event = placed.event
        starts = event.moments(self.formats)[0]
        button = _EventButton(
            event, self.name(event), classnames(_DOTTED, FOCUS_RING_INSET)
        ).content(
            html.span(aria_hidden="true", class_=classnames(_DOT, _SOLID[event.color])),
            html.span(self.clock(starts), class_=_TIME),
            html.span(*self._title_of(event), class_="min-w-0 truncate"),
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

    # ------------------------------------------------------------------
    # Day and week
    # ------------------------------------------------------------------

    def week(self) -> list[date]:
        days = week_of(self.cursor, self.start)
        return [day for day in days if not self.weekdays or day.weekday() < 5]

    def time_grid(self, days: list[date]) -> ComponentType:
        """
        A column per day over twenty-four hours, with the all-day events in
        a row above and the hours down the side.
        """
        placed = place(self.events, days[0], days[-1], self.formats)
        columns = f"grid-template-columns: 3.5rem repeat({len(days)}, minmax(0, 1fr))"
        bars = self._bars(days, placed)
        return html.div(
            html.div(
                html.div(),
                *(self._day_head(day) for day in days),
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
                        *(self._bar(bar) for bar in bars),
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
                    self._hours(),
                    *(self._column(day, placed.get(day, [])) for day in days),
                    class_="grid",
                    style=f"{columns}; height: {24 * _HOUR}px",
                ),
                class_="max-h-[42rem] overflow-y-auto",
                **{"x-init": f"$el.scrollTop = {_OPENS_AT}"},
            ),
            class_="flex flex-col",
        )

    def _day_head(self, day: date) -> ComponentType:
        return self.link(
            day,
            "day",
            html.span(self.formats.day_abbreviations[day.weekday()], class_=_HEAD),
            html.span(str(day.day), class_=classnames(_NUMBER, _NUMBER_IN_TODAY)),
            label=self.day_name(day),
            classes="group flex h-13 items-center justify-center gap-2 border-s "
            "border-border no-underline",
            link_classes="hover:bg-surface-hover",
            current=day == self.today,
        )

    def _bars(self, days: list[date], placed: dict[date, list[Placed]]) -> list[_Bar]:
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

    def _bar(self, bar: _Bar) -> ComponentType:
        return html.li(
            self.chip(bar.event, bar.before, bar.after),
            class_=classnames(
                "flex", {"ms-0.5": not bar.before, "me-0.5": not bar.after}
            ),
            style=f"grid-column: {bar.first + 1} / {bar.last + 2}",
        )

    def _hours(self) -> ComponentType:
        """
        The gutter. Decoration: every event says its own time.
        """
        return html.div(
            *(
                html.span(
                    self.clock(time(hour)),
                    class_="absolute end-2 -translate-y-1/2 text-2xs tabular-nums "
                    "text-fg-muted",
                    style=f"top: {hour * _HOUR}px",
                )
                for hour in range(1, 24)
            ),
            aria_hidden="true",
            class_="relative",
        )

    def _column(self, day: date, items: list[Placed]) -> ComponentType:
        # An event that began the day before is drawn where it started
        # and cut at midnight.
        timed = [
            each for each in items if each.event.timed and not each.continues_before
        ]
        spans = [minutes(each, self.formats) for each in timed]
        slots = pack(spans)
        return html.div(
            render_when(
                bool(timed),
                html.ul(
                    *(
                        self._timed(each, span, slot)
                        for each, span, slot in zip(timed, spans, slots, strict=True)
                    ),
                    class_="absolute inset-0",
                ),
            ),
            render_when(day == self.today, self._now()),
            data_date=day.isoformat(),
            class_=classnames(
                "relative border-s border-border", {_WEEKEND: day.weekday() >= 5}
            ),
            style=_HOUR_LINES,
        )

    def _timed(
        self, placed: Placed, span: tuple[int, int], slot: Slot
    ) -> ComponentType:
        event = placed.event
        start, end = span
        starts, ends = event.moments(self.formats)
        height = max((end - start) * _HOUR // 60 - 2, 18)
        short = end - start < _SHORT
        if short:
            title_classes, time_classes = "min-w-0 truncate", "flex-none"
        elif height > _TALL:
            title_classes, time_classes = "line-clamp-3", "block truncate"
        else:
            title_classes, time_classes = "block truncate", "block truncate"
        button = _EventButton(
            event,
            self.name(event),
            classnames(
                _EVENT,
                _TINT[event.color],
                FOCUS_RING_INSET,
                "h-full overflow-hidden py-0.5 leading-4",
                "flex items-baseline gap-1.5" if short else "block",
            ),
        ).content(
            html.span(
                *self._title_of(event),
                class_=classnames("font-semibold", title_classes),
            ),
            html.span(
                self.clock(starts)
                if short
                else f"{self.clock(starts)} {_DASH} {self.clock(ends)}",
                class_=classnames("tabular-nums text-fg-muted", time_classes),
            ),
        )
        return html.li(
            self.event(event, button),
            class_="absolute flex",
            style=(
                f"top: {start * _HOUR // 60}px; height: {height}px; "
                f"left: calc({slot.column} / {slot.columns} * 100% + 2px); "
                f"width: calc(100% / {slot.columns} - 4px)"
            ),
        )

    def _now(self) -> ComponentType:
        """
        The line at the time it is, moved every minute by the browser, which
        is the one clock that knows the reader's now.
        """
        return html.div(
            aria_hidden="true",
            class_="pointer-events-none absolute inset-x-0 z-10 h-0.5 bg-danger "
            "before:absolute before:-start-1 before:-top-[3px] before:size-2 "
            "before:rounded-full before:bg-danger",
            **{
                "x-data": (
                    "{ minute: 0, tick() { const now = new Date(); "
                    "this.minute = now.getHours() * 60 + now.getMinutes() } }"
                ),
                "x-init": "tick(); setInterval(() => tick(), 60000)",
                ":style": f"'top: ' + minute * {_HOUR} / 60 + 'px'",
            },
        )

    # ------------------------------------------------------------------
    # Month
    # ------------------------------------------------------------------

    def month(self) -> ComponentType:
        """
        A table with a column per weekday and six rows of weeks. A table
        rather than a grid widget: every event is a control to read and
        open, and browse-mode table navigation already announces the
        weekday with each cell.
        """
        formats = self.formats
        rows = month_grid(self.cursor, self.start)
        if self.weekdays:
            rows = tuple(tuple(day for day in row if day.weekday() < 5) for row in rows)
        placed = place(self.events, rows[0][0], rows[-1][-1], formats)
        return html.table(
            html.caption(formats.month(self.cursor), class_="sr-only"),
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
                    html.tr(*(self._cell(day, placed.get(day, [])) for day in row))
                    for row in rows
                ),
                class_="[&_tr:last-child_td]:border-b-0",
            ),
            class_="w-full table-fixed border-collapse",
        )

    def _cell(self, day: date, items: list[Placed]) -> ComponentType:
        outside = (day.year, day.month) != (self.cursor.year, self.cursor.month)
        shown = items if len(items) <= _PER_CELL else items[: _PER_CELL - 1]
        more = len(items) - len(shown)
        return html.td(
            self.number(day),
            render_when(
                bool(shown),
                html.ul(
                    *(self.item(each) for each in shown),
                    class_="mt-1 flex flex-col gap-0.5",
                ),
            ),
            render_when(more > 0, self._more(day, items, more)),
            data_date=day.isoformat(),
            class_=classnames(
                "h-28 overflow-hidden border-e border-b border-border p-1 align-top "
                "last:border-e-0",
                {
                    _WEEKEND: outside or day.weekday() >= 5,
                    "text-fg-subtle": outside,
                },
            ),
        )

    def _more(self, day: date, items: list[Placed], count: int) -> ComponentType:
        """
        The rest of a day's events, in a popover headed by the day.
        """
        name = self.formats.day(day)
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
                    *(self.item(each) for each in items),
                    class_="flex flex-col gap-0.5",
                )
            )
        )

    # ------------------------------------------------------------------
    # Year
    # ------------------------------------------------------------------

    def year(self) -> ComponentType:
        year = self.cursor.year
        placed = place(self.events, date(year, 1, 1), date(year, 12, 31), self.formats)
        return html.div(
            *(self._mini(date(year, month, 1), placed) for month in range(1, 13)),
            class_="grid grid-cols-[repeat(auto-fill,minmax(14rem,1fr))] gap-x-8 "
            "gap-y-6 p-4",
        )

    def _mini(self, month: date, placed: dict[date, list[Placed]]) -> ComponentType:
        """
        One small month: its days as links to their day view, each with a
        dot when something is on.
        """
        formats = self.formats
        rows = [
            row
            for row in month_grid(month, self.start)
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
                                    self._year_day(day, len(placed.get(day, []))),
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

    def _year_day(self, day: date, count: int) -> ComponentType:
        label = self.day_name(day)
        if count:
            label += f", {count} event" if count == 1 else f", {count} events"
        return self.link(
            day,
            "day",
            html.time(str(day.day), datetime=day.isoformat()),
            render_when(
                count > 0,
                html.span(
                    aria_hidden="true",
                    class_="absolute bottom-0.5 size-1 rounded-full bg-current",
                ),
            ),
            label=label,
            classes=classnames(_NUMBER, _NUMBER_TODAY, "relative"),
            link_classes=_NUMBER_LINK,
            current=day == self.today,
        )

    # ------------------------------------------------------------------
    # Agenda
    # ------------------------------------------------------------------

    def agenda(self) -> ComponentType:
        """
        The next thirty days with something on, each day a heading over
        its list; an Empty when none of them has.
        """
        formats = self.formats
        first = self.cursor
        last = first + timedelta(days=_AGENDA_DAYS - 1)
        placed = place(self.events, first, last, formats)
        days = sorted(placed)
        if not days:
            return (
                Empty()
                .title("Nothing scheduled")
                .description(f"{formats.day(first)} to {formats.day(last)}.")
            )
        return html.div(
            *(self._agenda_day(day, placed[day]) for day in days),
            class_="flex flex-col divide-y divide-border px-4",
        )

    def _agenda_day(self, day: date, items: list[Placed]) -> ComponentType:
        formats = self.formats
        return html.section(
            html.div(
                self.number(day),
                html.span(
                    formats.day_abbreviations[day.weekday()],
                    html.br(),
                    f"{formats.month_names[day.month - 1]} {day.year}",
                    class_="text-xs leading-tight text-fg-muted",
                ),
                class_="flex items-center gap-2 self-start",
            ),
            html.ul(
                *(html.li(self._agenda_row(each), class_="flex") for each in items),
                class_="flex flex-col gap-0.5",
            ),
            data_date=day.isoformat(),
            class_="grid grid-cols-[7.5rem_minmax(0,1fr)] gap-4 py-3",
        )

    def _agenda_row(self, placed: Placed) -> ComponentType:
        event = placed.event
        formats = self.formats
        if event.timed:
            starts, ends = event.moments(formats)
            when = f"{self.clock(starts)} {_DASH} {self.clock(ends)}"
        else:
            first, last = event.span(formats)
            total = (last - first).days + 1
            nth = (placed.day - first).days + 1
            when = "All day" if total == 1 else f"Day {nth} of {total}"
        button = _EventButton(
            event,
            self.name(event),
            classnames(
                "grid w-full cursor-pointer grid-cols-[6.5rem_auto_minmax(0,1fr)] "
                "items-center gap-3 rounded-md px-2.5 py-2 text-start text-sm "
                "text-fg hover:bg-surface-hover",
                FOCUS_RING_INSET,
            ),
        ).content(
            html.span(when, class_="text-xs tabular-nums text-fg-muted"),
            html.span(aria_hidden="true", class_=classnames(_DOT, _SOLID[event.color])),
            html.span(
                html.span(*self._title_of(event), class_="font-semibold"),
                render_if(
                    event.location,
                    lambda text: html.span(text, class_="ms-2 text-fg-muted"),
                ),
                class_="min-w-0 truncate",
            ),
        )
        return self.event(event, button)
