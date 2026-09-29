from datetime import UTC, datetime

from django.test import RequestFactory, override_settings

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
