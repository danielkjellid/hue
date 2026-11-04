"""
Days, and how an event sits on one: the arithmetic every calendar view
draws with.

Nothing here knows about markup. A week view's columns, a month's cells and
an agenda's list are new compositions of the same answers: which days a
range covers, which events land on each of them, and how timed events that
overlap share a column.
"""

from __future__ import annotations

from calendar import monthrange
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from typing import Any, Literal, get_args

from hue.formats import Formats
from hue.ui.molecules.date_picker import WEEKDAYS, Weekday

# One of the chart tokens, which stay apart from each other in both themes
# and under every simulated colour-vision deficiency. 1 is the accent.
type EventColor = Literal[1, 2, 3, 4, 5, 6]

_COLORS: tuple[int, ...] = get_args(EventColor.__value__)

# The minutes in a day, where a timed event that runs past midnight is cut.
MIDNIGHT = 24 * 60
_DAY = timedelta(days=1)

# How a timed event drawn as a bar meets its first and last day: across the
# whole of every day it touches, from and to its times, or over the nights
# it covers, which leaves the day it ends on free.
type Spans = Literal["days", "times", "nights"]


@dataclass(frozen=True, slots=True)
class Event:
    """
    Something on the calendar.

    A date is a whole day, and ends is the last day it covers, so an offsite
    from Monday to Wednesday ends on Wednesday. A datetime is a moment, and
    ends is when it is over. Without ends it is one day, or one moment.

    id is what a route names it by. href makes the detail popover offer a
    link to it. repeat is the key of the rule it repeats by, which draws the
    repeat mark; expanding the rule into occurrences is the app's job. layer
    names the calendar it belongs to, under a declaration. color picks one of
    the six chart tokens, the first unless its layer says otherwise.
    series_starts is when the first occurrence of the series it belongs to
    starts, which an editable calendar needs from every occurrence it is
    handed: moving one occurrence moves the series from there.

        Event("Offsite", date(2026, 10, 19), date(2026, 10, 21), color=4)
        Event("Standup", datetime(2026, 10, 14, 9, 30), id="12", repeat="weekly")
    """

    title: str
    starts: date | datetime
    ends: date | datetime | None = None
    id: str | None = None
    location: str | None = None
    notes: str | None = None
    repeat: str | None = None
    layer: str | None = None
    href: str | None = None
    color: EventColor | None = None
    series_starts: date | datetime | None = None

    def __post_init__(self) -> None:
        # Refused here rather than misdrawn later: a date and a datetime
        # mean different things by ends, and an end before the start covers
        # no day at all. The title is every control's accessible name.
        if not self.title:
            raise ValueError("An Event needs a title; it is what the event is called.")
        if self.color is not None and self.color not in _COLORS:
            raise ValueError(
                f"{self.title!r} has color {self.color!r}; it is one of 1 to 6."
            )
        if self.series_starts is not None and isinstance(
            self.series_starts, datetime
        ) != isinstance(self.starts, datetime):
            raise ValueError(
                f"{self.title!r} and the series it belongs to start with "
                f"different kinds of value. Both are dates, or both datetimes."
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

    @property
    def tone(self) -> EventColor:
        """
        The chart token it is drawn in: its own, or the first.
        """
        return 1 if self.color is None else self.color

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


def week_of(day: date, start: Weekday) -> tuple[date, ...]:
    """
    The seven days of the week day falls in, from the start day on.
    """
    offset = (day.weekday() - WEEKDAYS.index(start)) % 7
    first = day - timedelta(days=offset)
    return tuple(first + timedelta(days=n) for n in range(7))


def weekend(day: date) -> bool:
    """
    Saturday and Sunday, whichever day the week starts on: a week that
    starts on Sunday still ends its working days on Friday.
    """
    return day.weekday() >= 5


def month_grid(month: date, start: Weekday) -> tuple[tuple[date, ...], ...]:
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
    return date(year, month + 1, min(day.day, monthrange(year, month + 1)[1]))


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
        day = max(a, first)
        while day <= min(b, last):
            placed = Placed(event, day, day > a, day < b)
            found.setdefault(day, []).append((_order(placed, a, b, formats), placed))
            day += timedelta(days=1)
    return {
        day: [placed for _, placed in sorted(items, key=lambda pair: pair[0])]
        for day, items in found.items()
    }


def starts_on(placed: Placed, formats: Formats) -> datetime:
    """
    When a timed event starts on the day it is placed on, in the reader's
    time: midnight when it began the day before.
    """
    moment = placed.event.moments(formats)[0]
    if placed.continues_before:
        return datetime.combine(placed.day, time.min, moment.tzinfo)
    return moment


def _order(
    placed: Placed, first: date, last: date, formats: Formats
) -> tuple[Any, ...]:
    # Timed events after the all-day ones, by when they start on the day;
    # among the all-day ones the longest first, so a bar sits above the
    # single days under it.
    if placed.event.timed:
        # Naive, so an aware event and a naive one never compare.
        return (1, 0, starts_on(placed, formats).time())
    return (0, (first - last).days, time.min)


def minutes(placed: Placed, formats: Formats, least: int) -> tuple[int, int]:
    """
    Where a timed event sits on the day it is placed on, in minutes from
    midnight: from the start of the day when it began earlier, to midnight
    when it ends later. One shorter than least is widened to it, the time
    its box is drawn over, and moved up when that would take it past
    midnight.
    """
    starts = starts_on(placed, formats)
    ends = placed.event.moments(formats)[1]
    start = starts.hour * 60 + starts.minute
    end = ends.hour * 60 + ends.minute if ends.date() == placed.day else MIDNIGHT
    end = min(max(end, start + least), MIDNIGHT)
    return min(start, end - least), end


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


def long(event: Event, formats: Formats) -> bool:
    """
    A timed event of a day or more, which is drawn as a bar among the
    whole-day events rather than through the hours.
    """
    if not event.timed:
        return False
    starts, ends = event.moments(formats)
    return ends - starts >= _DAY


def barred(event: Event, formats: Formats) -> bool:
    """
    Drawn as a bar: every whole-day event, and a timed one of a day or more.
    """
    return not event.timed or long(event, formats)


@dataclass(frozen=True, slots=True)
class Reach:
    """
    The days a bar runs over, and how far into the first it starts and into
    the last it ends, as a share of the day: 0 is the midnight a day starts
    at and 1 the midnight it ends at.
    """

    first: date
    last: date
    enters: float = 0.0
    leaves: float = 1.0


def reach(event: Event, formats: Formats, spans: Spans) -> Reach:
    """
    Where a bar runs. A whole-day event fills its days whatever spans says;
    spans decides only for a timed one.
    """
    first, last = event.span(formats)
    if not event.timed or spans == "days":
        return Reach(first, last)
    starts, ends = event.moments(formats)
    if spans == "nights":
        # The end down to the midnight before it, so the day it ends on is
        # free unless it ends exactly at midnight, which is the same day.
        return Reach(first, max(first, ends.date() - _DAY))
    enters = (starts.hour * 60 + starts.minute) / MIDNIGHT
    # The end is the midnight after last when the event ends on one.
    leaves = (ends.hour * 60 + ends.minute) / MIDNIGHT if ends.date() == last else 1.0
    return Reach(first, last, enters, leaves)


@dataclass(frozen=True, slots=True)
class Run:
    """
    One bar across one row of shown days: the columns it covers, how far
    into the first and last, whether it goes on past either end of the row,
    and the line of the row it is drawn on.
    """

    event: Event
    first: int
    last: int
    enters: float
    leaves: float
    before: bool
    after: bool
    lane: int = 0


def runs(
    events: Iterable[Event], days: Sequence[date], formats: Formats, spans: Spans
) -> list[Run]:
    """
    Every barred event across the row of shown days it touches, each on the
    first line free where it runs, so a bar never jumps between lines from
    one day to the next. One that comes on from the row before goes first,
    then the longest of those that start together. A line is free from where
    the bar before ends, so a stay that leaves at 11:00 and one that arrives
    at 15:00 share a line on the day between when drawn by their times.

    A bar that starts or ends on a day the row does not show, such as a
    weekend left out, is squared off there and fills the day next to it.
    """
    found: list[Run] = []
    for event in events:
        if not barred(event, formats):
            continue
        at = reach(event, formats, spans)
        columns = [n for n, day in enumerate(days) if at.first <= day <= at.last]
        if not columns:
            continue
        first, last = columns[0], columns[-1]
        before = days[first] != at.first
        after = days[last] != at.last
        found.append(
            Run(
                event,
                first,
                last,
                0.0 if before else at.enters,
                1.0 if after else at.leaves,
                before,
                after,
            )
        )
    found.sort(key=lambda run: (run.first, not run.before, run.first - run.last))
    # Where each line is taken to, in columns and shares of a day.
    taken: list[float] = []
    laid: list[Run] = []
    for run in found:
        starts = run.first + run.enters
        lane = next((n for n, end in enumerate(taken) if end <= starts), len(taken))
        if lane == len(taken):
            taken.append(0.0)
        taken[lane] = run.last + run.leaves
        laid.append(replace(run, lane=lane))
    return laid
