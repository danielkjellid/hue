"""
Expanding a series into the occurrences a stretch of days holds.

hue draws what it is handed and says an event repeats; which days that
means is the app's own rule, and this is a small one: every day, every
weekday, the same day each week, or the same day of the month.
"""

from calendar import monthrange
from collections.abc import Iterator
from datetime import date, datetime, timedelta

from django.utils import timezone
from hue.ui import Event

from example.events.models import Entry


def occurrences(entry: Entry, first: date, last: date) -> Iterator[Event]:
    """
    Every occurrence of entry that touches a day from first to last.
    """
    starts, ends = timezone.localtime(entry.starts), timezone.localtime(entry.ends)
    length = ends - starts
    for begins in _starts(starts, entry.repeat, first - length, last):
        if (begins + length).date() >= first:
            yield entry.event(begins, begins + length)


# The fewest days between two occurrences of a rule. Counting from there
# rather than from the series' first day keeps a series that began years
# ago from being walked day by day to reach the week asked for.
_STEPS = {
    Entry.Repeat.DAILY: 1,
    Entry.Repeat.WEEKDAYS: 1,
    Entry.Repeat.WEEKLY: 7,
    Entry.Repeat.MONTHLY: 28,
}


def _starts(
    anchor: datetime, repeat: str, first: date, last: date
) -> Iterator[datetime]:
    """
    When each occurrence begins, from the last one before first until the
    day after last.
    """
    if not repeat:
        yield anchor
        return
    count = max(0, ((first - anchor.date()).days - 1) // _STEPS[Entry.Repeat(repeat)])
    while True:
        begins = _nth(anchor, repeat, count)
        count += 1
        if begins.date() > last:
            return
        if repeat == Entry.Repeat.WEEKDAYS and begins.weekday() >= 5:
            continue
        yield begins


def _nth(anchor: datetime, repeat: str, count: int) -> datetime:
    if repeat == Entry.Repeat.WEEKLY:
        return anchor + timedelta(weeks=count)
    if repeat == Entry.Repeat.MONTHLY:
        # The 31st in a shorter month is that month's last day.
        index = anchor.year * 12 + anchor.month - 1 + count
        year, month = divmod(index, 12)
        day = min(anchor.day, monthrange(year, month + 1)[1])
        return anchor.replace(year=year, month=month + 1, day=day)
    return anchor + timedelta(days=count)
