"""
The date math every calendar view is drawn from, on its own: which weeks
a month touches, and which days an event lands on.
"""

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from hue.formats import Formats
from hue.ui.molecules._days import Event, place, week_of, weeks

_OSLO = Formats(localize=lambda moment: moment.astimezone(timezone(timedelta(hours=2))))


def test_a_month_that_starts_on_the_week_start_has_no_leading_days():
    # June 2026 starts on a Monday.
    rows = weeks(date(2026, 6, 1), "monday")
    assert rows[0][0] == date(2026, 6, 1)
    assert len(rows) == 5
    assert rows[-1][-1] == date(2026, 7, 5)


def test_the_days_of_the_month_before_complete_the_first_week():
    # October 2026 starts on a Thursday.
    rows = weeks(date(2026, 10, 14), "monday")
    assert rows[0] == tuple(date(2026, 9, 28) + timedelta(days=n) for n in range(7))
    assert all(len(row) == 7 for row in rows)
    assert rows[-1][-1] == date(2026, 11, 1)


def test_a_sunday_start_moves_the_first_column():
    rows = weeks(date(2026, 10, 1), "sunday")
    assert rows[0][0] == date(2026, 9, 27)
    assert rows[0][0].weekday() == 6
    assert week_of(date(2026, 10, 14), "sunday")[0] == date(2026, 10, 11)


def test_february_can_be_exactly_four_rows():
    # February 2027 starts on a Monday and has 28 days.
    assert len(weeks(date(2027, 2, 1), "monday")) == 4


def test_a_whole_day_event_is_placed_on_every_day_it_covers():
    offsite = Event("Offsite", date(2026, 10, 19), date(2026, 10, 21))
    placed = place([offsite], date(2026, 9, 28), date(2026, 11, 1), Formats())
    assert sorted(placed) == [date(2026, 10, 19) + timedelta(days=n) for n in range(3)]
    first, middle, last = (placed[day][0] for day in sorted(placed))
    assert (first.continues_before, first.continues_after) == (False, True)
    assert (middle.continues_before, middle.continues_after) == (True, True)
    assert (last.continues_before, last.continues_after) == (True, False)


def test_a_timed_event_ending_at_midnight_does_not_cover_the_next_day():
    party = Event("Party", datetime(2026, 10, 14, 20), datetime(2026, 10, 15, 0))
    assert sorted(place([party], date(2026, 10, 1), date(2026, 10, 31), Formats())) == [
        date(2026, 10, 14)
    ]


def test_a_timed_event_ending_after_midnight_does():
    party = Event("Party", datetime(2026, 10, 14, 20), datetime(2026, 10, 15, 0, 30))
    placed = place([party], date(2026, 10, 1), date(2026, 10, 31), Formats())
    assert sorted(placed) == [date(2026, 10, 14), date(2026, 10, 15)]
    assert placed[date(2026, 10, 14)][0].continues_after is True


def test_an_aware_event_lands_on_the_readers_day():
    late = Event("Deploy", datetime(2026, 10, 14, 23, 30, tzinfo=UTC))
    assert list(place([late], date(2026, 10, 1), date(2026, 10, 31), _OSLO)) == [
        date(2026, 10, 15)
    ]
    assert list(place([late], date(2026, 10, 1), date(2026, 10, 31), Formats())) == [
        date(2026, 10, 14)
    ]


def test_events_outside_the_range_are_dropped_and_ones_across_it_are_cut():
    before = Event("Before", date(2026, 9, 1))
    across = Event("Across", date(2026, 9, 25), date(2026, 10, 2))
    placed = place([before, across], date(2026, 9, 28), date(2026, 11, 1), Formats())
    assert sorted(placed) == [date(2026, 9, 28) + timedelta(days=n) for n in range(5)]
    # Cut by the range, the first shown day still reads as a continuation.
    assert placed[date(2026, 9, 28)][0].continues_before is True


def test_a_day_reads_the_long_bars_first_then_the_timed_events_by_start():
    day = date(2026, 10, 14)
    events = [
        Event("Standup", datetime(2026, 10, 14, 9, 30)),
        Event("Release", day),
        Event("Early", datetime(2026, 10, 14, 8)),
        Event("Offsite", date(2026, 10, 13), date(2026, 10, 15)),
    ]
    placed = place(events, day, day, Formats())
    assert [p.event.title for p in placed[day]] == [
        "Offsite",
        "Release",
        "Early",
        "Standup",
    ]


@pytest.mark.parametrize(
    ("starts", "ends", "message"),
    [
        (date(2026, 10, 14), datetime(2026, 10, 14, 9), "both dates"),
        (datetime(2026, 10, 14, 9), datetime(2026, 10, 14, 9, tzinfo=UTC), "naive"),
        (date(2026, 10, 14), date(2026, 10, 13), "ends before it starts"),
    ],
)
def test_an_event_that_cannot_be_drawn_is_refused(starts, ends, message):
    with pytest.raises(ValueError, match=message):
        Event("Broken", starts, ends)


def test_an_event_can_end_when_it_starts_or_not_say():
    assert Event("Moment", date(2026, 10, 14), date(2026, 10, 14)).ends is not None
    assert Event("Open", date(2026, 10, 14)).ends is None
    assert Event("Moment", datetime(2026, 10, 14, 9)).timed is True
