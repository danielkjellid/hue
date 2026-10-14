"""
Days, and how an event sits on one: the parts every calendar view draws
with.

The month view is the only view today. A week view's all-day row, its hour
columns and an agenda list are new compositions of what is here, and the
month view never learns they exist. A date picker shares the date math and
the header.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Literal

from htmy import html

from hue.formats import Formats
from hue.types.core import ComponentType
from hue.ui._styles import FOCUS_RING, FOCUS_RING_INSET
from hue.utils import classnames, render_when

type Weekday = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]  # fmt: skip

# Monday first, as date.weekday() and Formats.day_names count.
WEEKDAYS: tuple[Weekday, ...] = (
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
)  # fmt: skip

# The years a month grid can draw without a leading or trailing day falling
# off the end of date. A month from a URL outside them is no month at all.
FIRST_YEAR = date.min.year + 1
LAST_YEAR = date.max.year - 1

# The shared tone vocabulary, spelled as Badge spells it.
type EventVariant = Literal["neutral", "info", "success", "warning", "danger"]


@dataclass(frozen=True, slots=True)
class Event:
    """
    Something on the calendar.

    A date is a whole day, and ends is the last day it covers, so an offsite
    from Monday to Wednesday ends on Wednesday. A datetime is a moment, and
    ends is when it is over. Without ends it is one day, or one moment. href
    makes it a link; variant colours it in the shared tones.

        Event("Offsite", date(2026, 10, 19), date(2026, 10, 21), variant="info")
        Event("Standup", datetime(2026, 10, 14, 9, 30), href="/events/12/")
    """

    title: str
    starts: date | datetime
    ends: date | datetime | None = None
    href: str | None = None
    variant: EventVariant = "neutral"

    def __post_init__(self) -> None:
        # Refused here rather than misdrawn later: a date and a datetime
        # mean different things by ends, and an end before the start covers
        # no day at all.
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

    def span(self, formats: Formats) -> tuple[date, date]:
        """
        The first and last day it covers, inclusive, in the reader's time.
        A timed event that ends at midnight does not cover the next day.
        """
        if not isinstance(self.starts, datetime):
            return self.starts, self.ends or self.starts
        first = formats.moment(self.starts).date()
        if not isinstance(self.ends, datetime):
            return first, first
        # The end is exclusive, so the last day is the one the final
        # instant falls in. A zero-length event at midnight keeps its day.
        last = (formats.moment(self.ends) - timedelta(microseconds=1)).date()
        return first, max(first, last)


def week_of(day: date, start: Weekday) -> tuple[date, ...]:
    """
    The seven days of the week day falls in, from the start day on.
    """
    offset = (day.weekday() - WEEKDAYS.index(start)) % 7
    first = day - timedelta(days=offset)
    return tuple(first + timedelta(days=n) for n in range(7))


def weeks(month: date, start: Weekday) -> tuple[tuple[date, ...], ...]:
    """
    Every week a month touches, whole: four to six rows, with the days of
    the months either side that complete the first and the last.
    """
    first = first_of(month)
    last = (first + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    rows: list[tuple[date, ...]] = []
    day = first
    while day <= last:
        row = week_of(day, start)
        rows.append(row)
        day = row[-1] + timedelta(days=1)
    return tuple(rows)


def first_of(month: date) -> date:
    return month.replace(day=1)


def shift(month: date, by: int) -> date | None:
    """
    The first of the month by months away, or None past either end of the
    years a grid can draw, which leaves that link out.
    """
    index = month.year * 12 + month.month - 1 + by
    year, number = divmod(index, 12)
    if not FIRST_YEAR <= year <= LAST_YEAR:
        return None
    return date(year, number + 1, 1)


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
    if isinstance(event.starts, datetime):
        return (1, 0, formats.moment(event.starts).time())
    return (0, (first - last).days, time.min)


# ----------------------------------------------------------------------
# Markup
# ----------------------------------------------------------------------

_HEAD_CELL = (
    "py-2 text-center font-ui text-2xs font-bold uppercase tracking-[0.05em] "
    "text-fg-muted"
)

# The number at the top of a day, a disc so today can be filled.
_DAY_NUMBER = (
    "inline-flex size-7 items-center justify-center rounded-full font-ui "
    "text-sm font-medium tabular-nums "
    "aria-[current=date]:bg-accent aria-[current=date]:text-accent-fg"
)
_DAY_BUTTON = "cursor-pointer hover:bg-surface-hover"

_EVENT = "flex items-center gap-1.5 rounded-sm px-1.5 py-0.5 text-xs font-medium"
_LINK = "no-underline hover:underline"
# Inherits the chip's text colour, so one tone map colours both looks.
_DOT = "size-1.5 flex-none rounded-full bg-current"

# Keyed by the Literal so mypy keeps it exhaustive. An all-day event is a
# filled bar; a timed one is a dot and text in the same tone.
_TONES: dict[EventVariant, str] = {
    "neutral": "bg-surface-sunken text-fg",
    "info": "bg-info-subtle text-info-text",
    "success": "bg-success-subtle text-success-text",
    "warning": "bg-warning-subtle text-warning-text",
    "danger": "bg-danger-subtle text-danger-text",
}
_TEXT_TONES: dict[EventVariant, str] = {
    "neutral": "text-fg",
    "info": "text-info-text",
    "success": "text-success-text",
    "warning": "text-warning-text",
    "danger": "text-danger-text",
}


def weekday_head(formats: Formats, start: Weekday) -> ComponentType:
    """
    The header row: abbreviated names, with the full one in abbr, which is
    what a screen reader announces as the column header (the APG date picker
    does the same). Shared by the events grid and the picker.
    """
    first = WEEKDAYS.index(start)
    return html.thead(
        html.tr(
            *(
                html.th(
                    formats.day_abbreviations[i],
                    scope="col",
                    abbr=formats.day_names[i],
                    class_=_HEAD_CELL,
                )
                for i in ((first + n) % 7 for n in range(7))
            )
        )
    )


def day_number(
    day: date,
    *,
    month: date,
    today: date | None,
    formats: Formats,
    button: Mapping[str, Any] | None = None,
) -> ComponentType:
    """
    The number at the top of a day: a time element, today marked with
    aria-current="date", and a day outside the shown month carrying its
    month name for a screen reader (the column header and caption say the
    rest). With button attributes, the number is a button wearing them,
    which is how a declaration's day click gets in without this module
    knowing about routes.
    """
    outside = (day.year, day.month) != (month.year, month.month)
    number = html.time(
        str(day.day),
        render_when(
            outside,
            html.span(f" {formats.month_names[day.month - 1]}", class_="sr-only"),
        ),
        datetime=day.isoformat(),
    )
    current = "date" if day == today else None
    if button is None:
        return html.span(number, aria_current=current, class_=_DAY_NUMBER)
    return html.button(
        number,
        type="button",
        aria_current=current,
        class_=classnames(_DAY_NUMBER, _DAY_BUTTON, FOCUS_RING),
        **button,
    )


def event_item(placed: Placed, formats: Formats) -> ComponentType:
    """
    One event in a day's list: an li holding a link when it has an href and
    plain text when it does not. A timed event leads with its start time in
    a time element; an all-day one is a filled bar in its tone. The single
    place an event is drawn, for every view.
    """
    event = placed.event
    if isinstance(event.starts, datetime):
        moment = formats.moment(event.starts)
        lead: ComponentType = html.span(
            html.span(class_=_DOT, aria_hidden="true"),
            html.time(
                moment.strftime(formats.time),
                datetime=moment.isoformat(timespec="minutes"),
                class_="tabular-nums text-fg-muted",
            ),
            class_="flex flex-none items-center gap-1.5",
        )
        tone = _TEXT_TONES[event.variant]
    else:
        lead = ""
        tone = _TONES[event.variant]
    continues = placed.continues_before or placed.continues_after
    content = (
        lead,
        html.span(event.title, class_="truncate"),
        # The flattened corner is what a sighted reader sees of a bar that
        # goes on; this is what a screen reader hears of it.
        render_when(continues, html.span(" (continues)", class_="sr-only")),
    )
    classes = classnames(
        _EVENT,
        tone,
        {
            "rounded-s-none": placed.continues_before,
            "rounded-e-none": placed.continues_after,
        },
    )
    if event.href is None:
        return html.li(html.span(*content, class_=classes))
    return html.li(
        html.a(
            *content,
            href=event.href,
            class_=classnames(classes, _LINK, FOCUS_RING_INSET),
        )
    )
