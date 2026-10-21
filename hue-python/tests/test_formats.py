from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest

from hue.formats import Formats


def test_an_aware_moment_is_localized_when_told_how():
    oslo = timezone(timedelta(hours=1))
    formats = Formats(localize=lambda moment: moment.astimezone(oslo))
    assert formats.text(datetime(2026, 3, 1, 12, 0, tzinfo=UTC)) == "2026-03-01 13:00"
    # Only an aware datetime has a zone to convert from.
    assert formats.text(datetime(2026, 3, 1, 12, 0)) == "2026-03-01 12:00"


def test_an_aware_moment_keeps_its_own_zone_otherwise():
    assert Formats().text(datetime(2026, 3, 1, 12, 0, tzinfo=UTC)) == "2026-03-01 12:00"


def test_a_time_is_written_in_the_time_format():
    assert Formats(time="%I:%M %p").text(time(14, 5)) == "02:05 PM"


def test_anything_else_has_no_spelling_here():
    assert Formats().text(object()) is None


@pytest.mark.parametrize(
    "wrong",
    [
        {"month_names": ("January",)},
        {"month_names_in_date": ("January",) * 13},
        {"day_names": ("Monday",) * 8},
        {"day_abbreviations": ()},
    ],
)
def test_a_name_list_of_the_wrong_length_is_refused(wrong):
    with pytest.raises(ValueError, match=next(iter(wrong))):
        Formats(**wrong)


def test_a_month_and_a_day_are_named_in_words():
    assert Formats().month(date(2026, 10, 14)) == "October 2026"
    assert Formats().day(date(2026, 10, 14)) == "Wednesday 14 October 2026"


def test_a_day_names_its_month_as_written_inside_a_date():
    # Polish writes "październik" alone but "14 października" in a date.
    formats = Formats(month_names_in_date=("x",) * 9 + ("października", "y", "z"))
    assert formats.day(date(2026, 10, 14)).endswith("14 października 2026")
    assert formats.month(date(2026, 10, 14)) == "October 2026"


def test_a_moment_is_moved_into_the_readers_time_only_when_it_can_be():
    oslo = timezone(timedelta(hours=1))
    formats = Formats(localize=lambda moment: moment.astimezone(oslo))
    aware = datetime(2026, 3, 1, 23, 30, tzinfo=UTC)
    assert formats.moment(aware).day == 2
    # A naive datetime has no zone to convert from.
    assert formats.moment(datetime(2026, 3, 1, 23, 30)).day == 1
    assert Formats().moment(aware) is aware
