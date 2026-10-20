from datetime import UTC, date, datetime, time

import pytest
from django.test import RequestFactory, override_settings
from django.utils import translation

from hue_django.router import Router


def _formats():
    return Router()._get_context_args(RequestFactory().get("/"))["formats"]


def test_dates_are_iso_until_a_setting_says_otherwise():
    assert (_formats().date, _formats().datetime) == ("%Y-%m-%d", "%Y-%m-%d %H:%M")


@override_settings(HUE_DATE_FORMAT="%d.%m.%Y", HUE_DATETIME_FORMAT="%d.%m.%Y %H:%M")
def test_the_settings_reach_every_request():
    assert (_formats().date, _formats().datetime) == ("%d.%m.%Y", "%d.%m.%Y %H:%M")


@override_settings(USE_TZ=True, TIME_ZONE="Europe/Oslo")
def test_an_aware_datetime_is_written_in_local_time():
    # The ORM hands it over in UTC; a template would show it in Oslo time.
    assert _formats().text(datetime(2026, 3, 1, 12, tzinfo=UTC)) == "2026-03-01 13:00"


@override_settings(USE_TZ=False)
def test_without_timezones_a_moment_is_written_as_it_is():
    assert _formats().localize is None


@override_settings(HUE_TIME_FORMAT="%I:%M %p")
def test_the_time_format_is_a_setting_too():
    assert _formats().text(time(14, 5)) == "02:05 PM"


def test_the_names_are_django_s_translations():
    # Keyed from Monday and January, which is how Formats indexes them.
    with translation.override("nb"):
        formats = _formats()
    assert formats.day_names[0] == "mandag"
    assert formats.day_abbreviations[0] == "man"
    assert formats.month_names[9] == "oktober"
    assert formats.month_abbreviations[9] == "Okt"
    assert _formats().day_names[0] == "Monday"


@pytest.mark.parametrize(
    ("language", "in_date"),
    [
        # Polish declines the month inside a date.
        ("pl", "14 października 2026"),
        # Here Django's in-date form is the plain name with its case flipped.
        ("fr", "14 octobre 2026"),
        ("nb", "14 oktober 2026"),
        ("tg", "14 октябр 2026"),
    ],
)
def test_a_month_inside_a_date_takes_its_in_date_form(language, in_date):
    with translation.override(language):
        formats = _formats()
    assert formats.day(date(2026, 10, 14)).endswith(in_date)


@override_settings(HUE_DATETIME_FORMAT="%Y-%m-%d %H:%M:%S")
def test_a_format_with_seconds_reaches_every_request():
    assert _formats().text(datetime(2026, 3, 1, 12, 0, 5)) == "2026-03-01 12:00:05"
