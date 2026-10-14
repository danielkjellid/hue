"""
The declared calendar on a real view: the page, and the dialog a day opens.
"""

from django.test import Client

_AJAX = {"HTTP_X_ALPINE_REQUEST": "true"}


def test_the_page_draws_the_month_asked_for():
    response = Client().get("/events/", {"events-month": "2026-10"})
    assert response.status_code == 200
    html = response.content.decode()
    assert "October 2026" in html
    assert "Offsite" in html and "Release" in html
    assert 'id="events-next"' in html


def test_a_day_opens_the_new_event_dialog():
    response = Client().get("/events/events/day/", {"day": "2026-10-14"}, **_AJAX)
    assert response.status_code == 200
    html = response.content.decode()
    assert 'id="events-day"' in html
    assert "New event on 14 October 2026" in html
    assert 'value="2026-10-14"' in html
    assert 'id="starts-picker"' in html
