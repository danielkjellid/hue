from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date, datetime
from typing import Any, ClassVar, Protocol

from htmy import Context, html
from typing_extensions import Self

from hue.formats import Formats
from hue.js import Expression
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import Awaited, ChainableComponent
from hue.ui.molecules._days import (
    Event,
    EventVariant,
    Weekday,
    day_number,
    event_item,
    first_of,
    place,
    shift,
    weekday_head,
    weeks,
)
from hue.ui.navigation import swap
from hue.utils import classes_if_else, classnames, render_if, render_when

__all__ = ["Calendar", "Event", "EventVariant"]


class _Declaration(Protocol):
    """
    What from_state() takes: something that draws a calendar for the
    request in the context. hue.calendar's declaration is the one there is,
    and it imports this module, so it is named by shape rather than imported.
    """

    async def draw(self, calendar: Calendar, context: Context) -> Component: ...


_CAPTION = "pb-3 text-start font-ui text-base font-semibold text-fg-strong"
# A day is a cell of a ruled grid, tall enough to hold a few events.
_CELL = "h-24 border border-border p-1 align-top"
_IN_MONTH = "text-fg"
_OUTSIDE = "bg-canvas-subtle text-fg-subtle"
_EVENTS = "mt-1 flex flex-col gap-0.5"
# The month steps sit where a Pagination step would, and look the same.
_STEP = (
    "inline-flex h-control-sm min-w-[var(--spacing-control-sm)] items-center "
    "justify-center rounded-md px-2 font-ui text-sm font-medium text-fg-muted "
    "no-underline hover:bg-surface-hover hover:text-fg"
)


class Calendar(ChainableComponent):
    """
    A month of events, as a table with a column per weekday.

    month() picks the month and events() fills it; today() marks a day and
    week_start() moves the first column. An event is a link when it has an
    href. href() adds links to the months either side and, with today(),
    back to this one. Opening a day is what a declaration adds:
    Calendar.from_state().
    """

    category: ClassVar[str | None] = "Data"

    def __init__(self) -> None:
        super().__init__()
        # Preset rather than defaulted in _render, because the declaration
        # reads it before drawing to work out which days are shown.
        self._props["week_start"] = "monday"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .month(date(2026, 10, 1))
            .today(date(2026, 10, 14))
            .events(
                [
                    Event("Design review", datetime(2026, 10, 14, 9, 30), href="#"),
                    Event(
                        "Offsite",
                        date(2026, 10, 19),
                        date(2026, 10, 21),
                        variant="info",
                    ),
                    Event("Release", date(2026, 10, 29), variant="success"),
                ]
            )
        )

    @classmethod
    def from_state(cls, declaration: _Declaration) -> Self:
        """
        The calendar a declaration describes, for the month the page's URL
        asks for, with the links to the months either side and, when the
        declaration has one, the day action.
        """
        calendar = cls()
        calendar._props["declaration"] = declaration
        return calendar

    def month(self, value: date) -> Self:
        """
        The month shown; any day in it will do.
        """
        self._props["month"] = first_of(value)
        return self

    def events(self, value: Iterable[Event]) -> Self:
        self._props["events"] = list(value)
        return self

    def today(self, value: date) -> Self:
        """
        The day to mark as today. Told rather than read off the clock, so a
        page renders the same for everyone in one timezone and the docs
        render the same every day. A declaration tells it the reader's today.
        """
        self._props["today"] = value
        return self

    def week_start(self, value: Weekday) -> Self:
        self._props["week_start"] = value
        return self

    def href(self, value: Callable[[date], str]) -> Self:
        """
        Where a month lives, given its first day. With one, the calendar
        draws links to the previous and next months, and to today's month
        when today() is set. With an id, the links swap the calendar in
        place; without one they are plain links.
        """
        self._props["href"] = value
        return self

    def _day_action(self, label: str, expression: Callable[[date], Expression]) -> Self:
        """
        Make each day's number a button named label plus the day, running the
        expression the day gives (the declaration's ajax() to its day route).
        The fragment lands in a slot under the grid, named from the id.
        """
        self._props["day_action"] = (label, expression)
        return self

    def _undeclared(self) -> Calendar:
        calendar = Calendar()
        calendar._props = {k: v for k, v in self._props.items() if k != "declaration"}
        calendar._attrs = dict(self._attrs)
        calendar._children = self._children
        return calendar

    def _render(self, context: Context) -> Component:
        declaration: _Declaration | None = self._get_prop("declaration")
        if declaration is not None:
            # A copy without the declaration goes in, or drawing it would
            # hand it straight back to the declaration again.
            undeclared = self._undeclared()
            return Awaited(lambda context: declaration.draw(undeclared, context))

        month: date | None = self._get_prop("month")
        if month is None:
            raise ValueError("Calendar needs a month(); any day in it will do.")
        own_id: str | None = self._attrs.get("id")
        action: tuple[str, Callable[[date], Expression]] | None = self._get_prop(
            "day_action"
        )
        if action is not None and own_id is None:
            raise ValueError(
                "A Calendar with a day action needs an id() of its own: the "
                "slot a day's fragment lands in is named from it."
            )
        formats = Formats.from_context(context)
        start: Weekday = self._props["week_start"]
        today: date | None = self._get_prop("today")
        rows = weeks(month, start)
        placed = place(self._get_prop("events", []), rows[0][0], rows[-1][-1], formats)

        def cell(day: date) -> ComponentType:
            button: dict[str, Any] | None = None
            if action is not None:
                label, expression = action
                button = {
                    "aria_label": f"{label}, {formats.day(day)}",
                    "x-on:click": expression(day),
                }
            items = placed.get(day, [])
            return html.td(
                day_number(
                    day, month=month, today=today, formats=formats, button=button
                ),
                render_when(
                    bool(items),
                    html.ul(
                        *(event_item(one, formats) for one in items), class_=_EVENTS
                    ),
                ),
                class_=classnames(
                    _CELL,
                    classes_if_else(
                        (day.year, day.month) == (month.year, month.month),
                        [_IN_MONTH],
                        [_OUTSIDE],
                    ),
                ),
            )

        return html.div(
            render_if(self._get_prop("href"), lambda to: self._nav(to, month, today)),
            html.table(
                html.caption(formats.month(month), class_=_CAPTION),
                weekday_head(formats, start),
                html.tbody(*(html.tr(*(cell(day) for day in row)) for row in rows)),
                class_="w-full table-fixed border-collapse",
            ),
            render_when(action is not None, html.div(id=f"{own_id}-day")),
            class_=classnames("relative", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )

    def _nav(
        self, to: Callable[[date], str], month: date, today: date | None
    ) -> ComponentType:
        """
        The links to the months either side and to today's, swapping the
        calendar itself when it has an id. Stable ids on each, so focus
        finds the link again after the swap replaced it.
        """
        own_id: str | None = self._attrs.get("id")

        def step(
            name: str, label: str, target: date | None, icon: str | None = None
        ) -> ComponentType:
            if target is None:
                # Past either end of the years a grid can draw.
                return ""
            return html.a(
                HueIcon(icon) if icon else label,
                href=to(target),
                id=f"{own_id}-{name}" if own_id else None,
                aria_label=label if icon else None,
                class_=classnames(_STEP, FOCUS_RING),
                **swap(own_id),
            )

        return html.nav(
            step("previous", "Previous month", shift(month, -1), "chevron-left"),
            render_if(today, lambda day: step("today", "Today", first_of(day))),
            step("next", "Next month", shift(month, 1), "chevron-right"),
            aria_label="Months",
            class_="absolute end-0 top-0 flex items-center gap-1",
        )
