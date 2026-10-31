from datetime import UTC, date, datetime, time, timedelta, timezone

import pytest

from hue.formats import Formats

_OSLO = timezone(timedelta(hours=1))
_LOCAL = Formats(localize=lambda moment: moment.astimezone(_OSLO))


@pytest.mark.parametrize(
    ("formats", "value", "expected"),
    [
        (_LOCAL, datetime(2026, 3, 1, 12, 0, tzinfo=UTC), "2026-03-01 13:00"),
        # Only an aware datetime has a zone to convert from.
        (_LOCAL, datetime(2026, 3, 1, 12, 0), "2026-03-01 12:00"),
        (Formats(), datetime(2026, 3, 1, 12, 0, tzinfo=UTC), "2026-03-01 12:00"),
        (Formats(time="%I:%M %p"), time(14, 5), "02:05 PM"),
        (Formats(), object(), None),
    ],
    ids=["localized", "naive", "own zone", "time", "no spelling"],
)
def test_text_spells_a_value(formats, value, expected):
    assert formats.text(value) == expected


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
    aware = datetime(2026, 3, 1, 23, 30, tzinfo=UTC)
    assert _LOCAL.moment(aware).day == 2
    # A naive datetime has no zone to convert from.
    assert _LOCAL.moment(datetime(2026, 3, 1, 23, 30)).day == 1
    assert Formats().moment(aware) is aware
