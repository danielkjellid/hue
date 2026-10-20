"""
How a value with more than one spelling is written out.

A date has no one right way to be read: 2026-03-01, 01.03.2026 and
1 Mar 2026 are all the same day to someone. The formats live in the
context, so a framework integration can fill them from its settings once
and every component that writes a value reads the same answer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any

from htmy import Context

# The fields below are called date and datetime, which hides the types by
# those names inside the class.
type _Moment = datetime
type _Day = date


@dataclass(frozen=True, slots=True)
class Formats:
    """
    The strftime formats for dates and times, ISO 8601 by default because it
    is the one spelling no reader gets wrong, and the names of the months and
    the days, English by default.

    localize turns an aware datetime into the reader's time before it is
    written, as a framework's templates would. Without one, an aware
    datetime is written in its own timezone.

    The names are plain sequences rather than strftime's %A and %B, which
    read the process locale: a framework fills them per request from its
    own translations, the way it fills the patterns from its settings. Days
    are Monday first, as date.weekday() counts them. month_names_in_date is
    the month as written inside a date, which some languages decline: Polish
    has "październik" alone but "14 października" in a date.
    """

    date: str = "%Y-%m-%d"
    datetime: str = "%Y-%m-%d %H:%M"
    time: str = "%H:%M"
    localize: Callable[[_Moment], _Moment] | None = None
    month_names: tuple[str, ...] = (
        "January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December",
    )  # fmt: skip
    month_names_in_date: tuple[str, ...] = month_names
    day_names: tuple[str, ...] = (
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
        "Sunday",
    )  # fmt: skip
    day_abbreviations: tuple[str, ...] = (
        "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
    )  # fmt: skip

    def __post_init__(self) -> None:
        # A framework's config is the one boundary. Everything after indexes
        # these by month and weekday and trusts the lengths.
        for name, wanted in (
            ("month_names", 12),
            ("month_names_in_date", 12),
            ("day_names", 7),
            ("day_abbreviations", 7),
        ):
            if len(getattr(self, name)) != wanted:
                raise ValueError(
                    f"Formats.{name} needs {wanted} names, January or Monday first."
                )

    def text(self, value: Any) -> str | None:
        """
        The value as text, or None when it is not something with a spelling
        of its own here.
        """
        # datetime before date: every datetime is a date too.
        if isinstance(value, datetime):
            return self.moment(value).strftime(self.datetime)
        if isinstance(value, date):
            return value.strftime(self.date)
        if isinstance(value, time):
            return value.strftime(self.time)
        return None

    def moment(self, value: _Moment) -> _Moment:
        """
        An aware datetime in the reader's time, when there is a localize. A
        calendar uses it to put an event on the reader's day.
        """
        if value.tzinfo is not None and self.localize is not None:
            return self.localize(value)
        return value

    # date-picker.js writes month() and day() again, in this word order.
    def month(self, value: _Day) -> str:
        """
        October 2026: a month's caption.
        """
        return f"{self.month_names[value.month - 1]} {value.year}"

    def day(self, value: _Day) -> str:
        """
        Wednesday 14 October 2026: a day's accessible name, in one word order
        for every language.
        """
        return (
            f"{self.day_names[value.weekday()]} {value.day} "
            f"{self.month_names_in_date[value.month - 1]} {value.year}"
        )

    @classmethod
    def from_context(cls, context: Context) -> Formats:
        found = context.get(cls)
        return found if isinstance(found, cls) else cls()
