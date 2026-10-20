"""
Days, and how an event sits on one: the arithmetic every calendar view
draws with.

Nothing here knows about markup. A week view's columns, a month's cells and
an agenda's list are new compositions of the same answers: which days a
range covers, which events land on each of them, and how timed events that
overlap share a column.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Literal, get_args

from hue.formats import Formats

# The three days a week starts on anywhere: ISO's Monday, the Americas'
# Sunday, the Middle East's Saturday.
type WeekStart = Literal["monday", "saturday", "sunday"]

# As date.weekday() counts them.
_WEEKDAY: dict[WeekStart, int] = {"monday": 0, "saturday": 5, "sunday": 6}

# One of the chart tokens, which stay apart from each other in both themes
# and under every simulated colour-vision deficiency. 1 is the accent.
type EventColor = Literal[1, 2, 3, 4, 5, 6]

_COLORS: tuple[int, ...] = get_args(EventColor.__value__)

# The minutes in a day, where a timed event that runs past midnight is cut.
MIDNIGHT = 24 * 60

# A timed event takes at least this much of a column, so two that start
# together still read as side by side when one of them is a moment long.
_LEAST = 15


@dataclass(frozen=True, slots=True)
class Event:
    """
    Something on the calendar.

    A date is a whole day, and ends is the last day it covers, so an offsite
    from Monday to Wednesday ends on Wednesday. A datetime is a moment, and
    ends is when it is over. Without ends it is one day, or one moment.

    id is what a route names it by. href makes the detail popover offer a
    link to it; recurring draws the repeat mark, and expanding the rule into
    occurrences is the app's job. color picks one of the six chart tokens.

        Event("Offsite", date(2026, 10, 19), date(2026, 10, 21), color=4)
        Event("Standup", datetime(2026, 10, 14, 9, 30), id="12", recurring=True)
    """

    title: str
    starts: date | datetime
    ends: date | datetime | None = None
    id: str | None = None
    location: str | None = None
    notes: str | None = None
    recurring: bool = False
    href: str | None = None
    color: EventColor = 1

    def __post_init__(self) -> None:
        # Refused here rather than misdrawn later: a date and a datetime
        # mean different things by ends, and an end before the start covers
        # no day at all. The title is every control's accessible name.
        if not self.title:
            raise ValueError("An Event needs a title; it is what the event is called.")
        if self.color not in _COLORS:
            raise ValueError(
                f"{self.title!r} has color {self.color!r}; it is one of 1 to 6."
            )
        if self.ends is None:
            return
        if isinstance(self.starts, datetime) != isinstance(self.ends, datetime):
            raise ValueError(
                f"{self.title!r} starts with a {type(self.starts).__name__} and "
                f"ends with a {type(self.ends).__name__}. An event is either whole "
                f"days, both dates, or a stretch of time, both datetimes."
            )
        try:
            backwards = self.ends < self.starts
        except TypeError:
            raise ValueError(
                f"{self.title!r} mixes a naive datetime with an aware one, and "
                f"the two cannot be compared. Give both a timezone, or neither."
            ) from None
        if backwards:
            raise ValueError(f"{self.title!r} ends before it starts.")

    @property
    def timed(self) -> bool:
        return isinstance(self.starts, datetime)

    def moments(self, formats: Formats) -> tuple[datetime, datetime]:
        """
        When a timed event starts and ends, in the reader's time.
        """
        if not isinstance(self.starts, datetime):
            raise TypeError(f"{self.title!r} is a whole-day event.")
        starts = formats.moment(self.starts)
        ends = formats.moment(self.ends) if isinstance(self.ends, datetime) else starts
        return starts, ends

    def span(self, formats: Formats) -> tuple[date, date]:
        """
        The first and last day it covers, inclusive, in the reader's time.
        A timed event that ends at midnight does not cover the next day.
        """
        if not isinstance(self.starts, datetime):
            return self.starts, self.ends or self.starts
        starts, ends = self.moments(formats)
        first = starts.date()
        # The end is exclusive, so the last day is the one the final
        # instant falls in. A zero-length event at midnight keeps its day.
        last = (ends - timedelta(microseconds=1)).date()
        return first, max(first, last)


def week_of(day: date, start: WeekStart) -> tuple[date, ...]:
    """
    The seven days of the week day falls in, from the start day on.
    """
    offset = (day.weekday() - _WEEKDAY[start]) % 7
    first = day - timedelta(days=offset)
    return tuple(first + timedelta(days=n) for n in range(7))


def month_grid(month: date, start: WeekStart) -> tuple[tuple[date, ...], ...]:
    """
    Six weeks from the one the month starts in. Always six, so the grid is
    the same height for every month and nothing under it moves when the
    month changes.
    """
    first = week_of(month.replace(day=1), start)[0]
    return tuple(
        tuple(first + timedelta(days=7 * row + n) for n in range(7)) for row in range(6)
    )


def add_months(day: date, count: int) -> date:
    """
    The same day of the month count months on, or the last day of that
    month when it is shorter: 31 January and one month is 28 February.
    """
    index = day.year * 12 + day.month - 1 + count
    year, month = divmod(index, 12)
    first = date(year, month + 1, 1)
    last = (first + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    return first.replace(day=min(day.day, last.day))


@dataclass(frozen=True, slots=True)
class Placed:
    """
    One event on one day. A multi-day event is placed once on every day it
    covers; continues_before and continues_after are what square off its
    ends so the days read as one bar.
    """

    event: Event
    day: date
    continues_before: bool
    continues_after: bool


def place(
    events: Iterable[Event], first: date, last: date, formats: Formats
) -> dict[date, list[Placed]]:
    """
    Every event on every day it covers between first and last, each day's
    list in reading order: what spans days and all-day events, then timed
    ones by start time.

    Aware datetimes are moved into the reader's time first, because the day
    a 23:30 UTC event falls on depends on who is looking.
    """
    found: dict[date, list[tuple[tuple[Any, ...], Placed]]] = {}
    for event in events:
        a, b = event.span(formats)
        order = _order(event, a, b, formats)
        day = max(a, first)
        while day <= min(b, last):
            found.setdefault(day, []).append(
                (order, Placed(event, day, day > a, day < b))
            )
            day += timedelta(days=1)
    return {
        day: [placed for _, placed in sorted(items, key=lambda pair: pair[0])]
        for day, items in found.items()
    }


def _order(event: Event, first: date, last: date, formats: Formats) -> tuple[Any, ...]:
    # Timed events after the all-day ones, by start time; among the all-day
    # ones the longest first, so a bar sits above the single days under it.
    if event.timed:
        return (1, 0, event.moments(formats)[0].time())
    return (0, (first - last).days, time.min)


def minutes(placed: Placed, formats: Formats) -> tuple[int, int]:
    """
    Where a timed event sits on the day it is placed on, in minutes from
    midnight: from the start of the day when it began earlier, to midnight
    when it ends later. One shorter than a quarter of an hour is widened to
    one, so it still has a box to be seen in.
    """
    starts, ends = placed.event.moments(formats)
    start = starts.hour * 60 + starts.minute if starts.date() == placed.day else 0
    end = ends.hour * 60 + ends.minute if ends.date() == placed.day else MIDNIGHT
    return start, max(end, start + _LEAST)


@dataclass(frozen=True, slots=True)
class Slot:
    """
    Which column of how many a timed event takes among the ones it overlaps.
    """

    column: int
    columns: int


def pack(spans: Sequence[tuple[int, int]]) -> list[Slot]:
    """
    Lay overlapping spans out side by side, one slot per span in the order
    given.

    Spans that touch, directly or through others, form a cluster that shares
    its columns equally; a span takes the first column that is free when it
    starts. Two spans that never overlap each get the whole width.
    """
    slots = [Slot(0, 1)] * len(spans)
    cluster: list[tuple[int, int]] = []
    ends: list[int] = []
    reach = 0

    def flush() -> None:
        for index, column in cluster:
            slots[index] = Slot(column, len(ends))
        cluster.clear()
        ends.clear()

    # Earliest first, and the longer of two that start together first, so
    # it takes the leftmost column and the shorter ones tuck in beside it.
    for index in sorted(range(len(spans)), key=lambda i: (spans[i][0], -spans[i][1])):
        start, end = spans[index]
        if cluster and start >= reach:
            flush()
        column = next((n for n, free_at in enumerate(ends) if free_at <= start), None)
        if column is None:
            column = len(ends)
            ends.append(end)
        else:
            ends[column] = end
        cluster.append((index, column))
        reach = max(reach, end)
    flush()
    return slots
