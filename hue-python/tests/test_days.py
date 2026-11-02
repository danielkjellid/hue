"""
The arithmetic every calendar view is drawn from, on its own: which days a
week and a month cover, which days an event lands on, and how timed events
that overlap share a column.
"""

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from hue.formats import Formats
from hue.ui.molecules._days import (
    Event,
    Placed,
    Slot,
    add_months,
    minutes,
    month_grid,
    pack,
    place,
    week_of,
)

_OSLO = Formats(localize=lambda moment: moment.astimezone(timezone(timedelta(hours=2))))


def test_a_week_runs_from_the_start_day_through_the_one_asked_for():
    wednesday = date(2026, 10, 14)
    assert week_of(wednesday, "monday")[0] == date(2026, 10, 12)
    assert week_of(wednesday, "sunday")[0] == date(2026, 10, 11)
    assert week_of(wednesday, "saturday")[0] == date(2026, 10, 10)
    assert len(week_of(wednesday, "monday")) == 7


def test_a_month_grid_is_always_six_weeks_from_the_week_of_the_first():
    # October 2026 starts on a Thursday; June 2026 on a Monday.
    october = month_grid(date(2026, 10, 14), "monday")
    assert october[0][0] == date(2026, 9, 28)
    assert len(october) == 6
    assert october[-1][-1] == date(2026, 11, 8)
    june = month_grid(date(2026, 6, 1), "monday")
    assert june[0][0] == date(2026, 6, 1)
    assert len(june) == 6


def test_a_month_on_clamps_the_day_to_the_shorter_month():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 10, 14), -12) == date(2025, 10, 14)
    assert add_months(date(9999, 11, 30), 1) == date(9999, 12, 30)
    assert add_months(date(2026, 12, 5), 1) == date(2027, 1, 5)


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
    later = Event("Party", datetime(2026, 10, 14, 20), datetime(2026, 10, 15, 0, 30))
    placed = place([later], date(2026, 10, 1), date(2026, 10, 31), Formats())
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


def test_minutes_cut_an_event_at_midnight_and_widen_a_moment():
    day = date(2026, 10, 14)
    late = Event("Late", datetime(2026, 10, 14, 23), datetime(2026, 10, 15, 1))
    assert minutes(Placed(late, day, False, True), Formats(), 15) == (23 * 60, 24 * 60)
    after = Placed(late, date(2026, 10, 15), True, False)
    assert minutes(after, Formats(), 15) == (0, 60)
    moment = Event("Moment", datetime(2026, 10, 14, 9, 5))
    assert minutes(Placed(moment, day, False, False), Formats(), 15) == (545, 560)
    aware = Event("Deploy", datetime(2026, 10, 14, 7, tzinfo=UTC))
    assert minutes(Placed(aware, day, False, False), _OSLO, 15)[0] == 9 * 60


def test_a_moment_widened_at_the_end_of_the_day_moves_up_instead():
    day = date(2026, 10, 14)
    tiny = Event("Tiny", datetime(2026, 10, 14, 23, 55), datetime(2026, 10, 14, 23, 59))
    assert minutes(Placed(tiny, day, False, False), Formats(), 15) == (1425, 1440)


def test_overlapping_spans_share_the_width_and_separate_ones_take_it_all():
    # 10:00-12:00, 11:00-12:30 and 11:30-12:15 form one cluster of three
    # columns; 15:00-16:00 stands alone.
    assert pack([(600, 720), (660, 750), (690, 735), (900, 960)]) == [
        Slot(0, 3),
        Slot(1, 3),
        Slot(2, 3),
        Slot(0, 1),
    ]


def test_a_span_takes_the_first_column_that_has_come_free():
    # 09:00-10:00 and 09:30-11:00 overlap; 10:00-11:00 fits under the first
    # again, so the cluster stays two columns wide.
    assert pack([(540, 600), (570, 660), (600, 660)]) == [
        Slot(0, 2),
        Slot(1, 2),
        Slot(0, 2),
    ]


def test_slots_come_back_in_the_order_the_spans_were_given():
    assert pack([(660, 720), (600, 720)]) == [Slot(1, 2), Slot(0, 2)]
    assert pack([]) == []


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


def test_an_event_needs_a_title_and_one_of_the_six_colours():
    with pytest.raises(ValueError, match="title"):
        Event("", date(2026, 10, 14))
    with pytest.raises(ValueError, match="one of 1 to 6"):
        Event("Loud", date(2026, 10, 14), color=7)  # type: ignore[arg-type]
    assert Event("Open", date(2026, 10, 14)).ends is None
    assert Event("Moment", datetime(2026, 10, 14, 9)).timed is True
