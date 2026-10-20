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
        {"month_abbreviations": ("Jan",) * 13},
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


def test_names_are_written_from_formats_not_the_process_locale():
    french = Formats(
        month_abbreviations=(
            "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août",
            "sept.", "oct.", "nov.", "déc.",
        ),
        day_abbreviations=("lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."),
        date="%a %e %b %Y",
    )  # fmt: skip
    assert french.text(date(2026, 7, 5)) == "dim.  5 juil. 2026"


def test_every_directive_is_written_the_same_on_every_platform():
    moment = datetime(2026, 3, 5, 0, 7)
    written = Formats().write("%d %-d %e %m %-m %Y %H %M %I %-I %p %%", moment)
    assert written == "05 5  5 03 3 2026 00 07 12 12 AM %"
    assert Formats().write("%Y %B %A", date(26, 10, 1)) == "0026 October Thursday"


@pytest.mark.parametrize(
    ("field", "pattern", "directive"),
    [
        ("date", "%d/%m/%y", "%y"),
        ("date", "%Y-%m-%d %H:%M", "%H"),
        ("time", "%Y %H:%M", "%Y"),
        ("datetime", "%j %H:%M", "%j"),
    ],
)
def test_a_pattern_a_field_cannot_read_back_is_refused(field, pattern, directive):
    with pytest.raises(ValueError, match=f"Formats.{field} uses {directive}"):
        Formats(**{field: pattern})
