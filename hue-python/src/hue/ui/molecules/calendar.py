from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import TYPE_CHECKING

from htmy import Context, html
from typing_extensions import Self

from hue.formats import Formats
from hue.types.core import Component
from hue.ui._styles import LOADING
from hue.ui.base import ChainableComponent, declared
from hue.ui.molecules._calendar_views import (
    FIRST,
    LAST,
    VIEWS,
    Actions,
    CalendarView,
    Draw,
    Href,
)
from hue.ui.molecules._days import Event, EventColor
from hue.ui.molecules.date_picker import Weekday
from hue.ui.navigation import SYNC
from hue.utils import classnames, render_if

if TYPE_CHECKING:
    from hue.calendar import _Declaration

__all__ = ["Calendar", "CalendarView", "Event", "EventColor"]

# date() is a modifier below, which hides the type by that name inside the
# class, as Formats' fields do.
type _Day = date

_FRAME = (
    "flex w-full flex-col rounded-lg border border-border bg-surface text-base text-fg"
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
    def from_state(cls, declaration: _Declaration) -> Self:
        """
        The calendar a declaration describes, bound to the request of the
        page it is rendered on, with the sidebar, the search and the event
        dialog around it.
        """
        declaration.claim_keys()
        calendar = cls()
        calendar._props["declaration"] = declaration
        return calendar

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
                        repeat="weekly",
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

    def week_start(self, value: Weekday) -> Self:
        self._props["week_start"] = value
        return self

    def weekdays(self, value: bool = True) -> Self:
        """
        Leave Saturday and Sunday out of the week and the month.
        """
        self._props["weekdays"] = value
        return self

    def href(self, value: Href) -> Self:
        """
        Where a view on a day lives. Given one, Previous, Today and Next,
        the view switcher and every day are links to it; without one the
        calendar is a picture of its events.
        """
        self._props["href"] = value
        return self

    def actions(self, value: Actions) -> Self:
        """
        The buttons at the foot of an event's popover, given the event:
        Edit, Duplicate, Delete, or whatever the app does with one.
        """
        self._props["actions"] = value
        return self

    def _render(self, context: Context) -> Component:
        if (declaration := self._get_prop("declaration")) is not None:
            declaration.keys_on(context)
        if (drawn := declared(self)) is not None:
            return drawn

        cursor: date | None = self._get_prop("date")
        if cursor is None:
            raise ValueError("Calendar needs a date(): the day its view is around.")
        cursor = min(max(cursor, FIRST), LAST)
        view: CalendarView = self._get_prop("view", "week")
        attrs = self._get_base_html_attrs()
        own_id: str | None = attrs.pop("id", None)
        draw = Draw(
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
            movable=self._get_prop("movable", False),
            focus=self._get_prop("focus"),
        )
        title = VIEWS[view].title(draw)

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
                VIEWS[view].render(draw),
                id=draw.region,
                class_=LOADING,
                # A swap that took the control focus was on, a day or a
                # view tab, hands focus to the new view's heading.
                **({**SYNC, "data-hue-refocus": draw.heading} if own_id else {}),
            ),
            id=own_id,
            class_=classnames(_FRAME, self._get_prop("class_")),
            **attrs,
        )
