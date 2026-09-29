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
from datetime import date, datetime
from typing import Any

from htmy import Context

# The fields below are called date and datetime, which hides the types by
# those names inside the class.
type _Moment = datetime


@dataclass(frozen=True, slots=True)
class Formats:
    """
    The strftime formats for dates and for dates with a time, ISO 8601 by
    default because it is the one spelling no reader gets wrong.

    localize turns an aware datetime into the reader's time before it is
    written, as a framework's templates would. Without one, an aware
    datetime is written in its own timezone.
    """

    date: str = "%Y-%m-%d"
    datetime: str = "%Y-%m-%d %H:%M"
    localize: Callable[[_Moment], _Moment] | None = None

    def text(self, value: Any) -> str | None:
        """
        The value as text, or None when it is not something with a spelling
        of its own here.
        """
        # datetime before date: every datetime is a date too.
        if isinstance(value, datetime):
            if value.tzinfo is not None and self.localize is not None:
                value = self.localize(value)
            return value.strftime(self.datetime)
        if isinstance(value, date):
            return value.strftime(self.date)
        return None

    @classmethod
    def from_context(cls, context: Context) -> Formats:
        found = context.get(cls)
        return found if isinstance(found, cls) else cls()
