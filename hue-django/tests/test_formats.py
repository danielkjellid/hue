from django.test import RequestFactory, override_settings

from hue_django.router import Router


def _formats():
    return Router()._get_context_args(RequestFactory().get("/"))["formats"]


def test_dates_are_iso_until_a_setting_says_otherwise():
    assert (_formats().date, _formats().datetime) == ("%Y-%m-%d", "%Y-%m-%d %H:%M")


@override_settings(HUE_DATE_FORMAT="%d.%m.%Y", HUE_DATETIME_FORMAT="%d.%m.%Y %H:%M")
def test_the_settings_reach_every_request():
    assert (_formats().date, _formats().datetime) == ("%d.%m.%Y", "%d.%m.%Y %H:%M")
