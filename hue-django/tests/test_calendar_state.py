"""
The calendar declaration, end to end against a Django view.

The page reads its month off the URL, every link carries the rest of the
query along, and the day route answers an AJAX request with the handler's
fragment in the slot the calendar left for it.
"""

import asyncio
import re
from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from django.http import HttpRequest, QueryDict
from django.test import Client
from django.urls import clear_url_caches, include, path, resolve
from hue import calendar as declared
from hue import html
from hue.calendar import DayAction, build_calendar_state
from hue.context import HueContextArgs
from hue.renderer import render_tree
from hue.ui import Calendar, Event

from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueView

MOUNT = "bookings/"


def _events(request: Any, shown: Any) -> list[Event]:
    return [Event("Offsite", shown.month, href="/offsite/")]


def _open(request: Any, day: date) -> Any:
    return html.p(f"New booking on {day.isoformat()}")


def _view(**given: Any) -> Any:
    class BookingsView(HueView):
        router = Router[HttpRequest]()

        bookings = build_calendar_state(
            router,
            key="bookings",
            events=given.pop("events", _events),
            day=given.pop("day", DayAction("New booking", _open)),
        )

        async def index(self, request: Any, context: Any) -> Any:
            return Page(title="Bookings", body=Calendar.from_state(self.bookings))

    return BookingsView


@pytest.fixture
def mounted(urlpatterns_: list[Any]) -> Any:
    def build(**given: Any) -> Any:
        view = _view(**given)
        urlpatterns_.append(path(MOUNT, include(view.urls)))
        clear_url_caches()
        return view

    return build


@pytest.fixture
def october(monkeypatch: pytest.MonkeyPatch) -> date:
    # The clock held still, so "today" and its month are known.
    monkeypatch.setattr(
        declared, "_now", lambda: datetime(2026, 10, 14, 12, tzinfo=UTC)
    )
    return date(2026, 10, 14)


def _request(**params: str) -> Any:
    request = MagicMock()
    request.GET = QueryDict(urlencode(params, doseq=True))
    request.resolver_match = resolve(f"/{MOUNT}")
    return request


def _render(component: Any, request: Any) -> str:
    return asyncio.run(
        render_tree(
            component,
            context_args=HueContextArgs(request=request, csrf_token="t"),
        )
    )


def _hrefs(html: str) -> dict[str, str]:
    found = {}
    for tag in re.findall(r"<a [^>]*>", html):
        name = re.search(r'id="bookings-(previous|today|next)"', tag)
        href = re.search(r'href="([^"]*)"', tag)
        if name and href:
            found[name[1]] = href[1]
    return found


def test_the_page_draws_the_month_the_url_asks_for(mounted, october):
    mounted()
    response = Client().get(f"/{MOUNT}", {"bookings-month": "2026-03"})
    assert response.status_code == 200
    html = response.content.decode()
    assert "March 2026" in html
    assert 'id="bookings"' in html
    assert re.search(r'<p id="bookings-status"[^>]*x-sync[^>]*>March 2026</p>', html)


@pytest.mark.parametrize("typed", ["2026-13", "2026-1", "nonsense", "0001-01"])
def test_a_month_that_is_not_one_is_this_month(mounted, october, typed):
    html = _render(
        Calendar.from_state(mounted().bookings), _request(**{"bookings-month": typed})
    )
    assert "October 2026" in html
    assert 'aria-current="date"' in html


def test_the_links_keep_the_rest_of_the_query_and_todays_drops_the_month(
    mounted, october
):
    html = _render(
        Calendar.from_state(mounted().bookings),
        _request(**{"bookings-month": "2026-03", "tab": "all"}),
    )
    assert _hrefs(html) == {
        "previous": "/bookings/?tab=all&amp;bookings-month=2026-02",
        "today": "/bookings/?tab=all",
        "next": "/bookings/?tab=all&amp;bookings-month=2026-04",
    }
    assert 'x-target.push="bookings"' in html


def test_events_is_asked_for_the_days_shown_off_the_event_loop(mounted, october):
    asked: list[Any] = []

    def events(request: Any, shown: Any) -> list[Event]:
        asked.append((shown.first, shown.last, _on_the_loop()))
        return []

    _render(Calendar.from_state(mounted(events=events).bookings), _request())
    assert asked == [(date(2026, 9, 28), date(2026, 11, 1), False)]


def _on_the_loop() -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def test_something_that_is_not_an_event_is_refused_by_name(mounted, october):
    view = mounted(events=lambda request, shown: [{"title": "Offsite"}])
    with pytest.raises(TypeError, match="bookings"):
        _render(Calendar.from_state(view.bookings), _request())


def test_a_day_opens_the_handlers_fragment_in_the_calendars_slot(mounted):
    mounted()
    response = Client().get(
        f"/{MOUNT}bookings/day/", {"day": "2026-10-14"}, HTTP_X_ALPINE_REQUEST="true"
    )
    assert response.status_code == 200
    assert re.search(
        r'<div id="bookings-day">\s*<p[^>]*>New booking on 2026-10-14</p>',
        response.content.decode(),
    )


@pytest.mark.parametrize("typed", ["2026-10-32", "14-10-2026", "", "2026-10-14T09"])
def test_a_day_that_is_not_one_is_not_found(mounted, typed):
    mounted()
    response = Client().get(
        f"/{MOUNT}bookings/day/", {"day": typed}, HTTP_X_ALPINE_REQUEST="true"
    )
    assert response.status_code == 404


def test_the_day_route_answers_only_ajax(mounted):
    mounted()
    assert (
        Client().get(f"/{MOUNT}bookings/day/", {"day": "2026-10-14"}).status_code == 400
    )


def test_without_a_day_action_there_is_no_route_and_no_button(mounted, october):
    view = mounted(day=None)
    assert [route.path for route in view.router.routes] == []
    html = _render(Calendar.from_state(view.bookings), _request())
    assert "<button" not in html
    assert "bookings-day" not in html


def test_the_day_buttons_fetch_the_mounted_route(mounted, october):
    html = _render(Calendar.from_state(mounted().bookings), _request())
    assert (
        'x-on:click=\'$ajax("/bookings/bookings/day/?day=2026-10-14", '
        '{"method": "get", "target": "bookings-day", "sync": true})\'' in html
    )
    assert 'aria-label="New booking, Wednesday 14 October 2026"' in html


def test_two_calendars_on_one_view_keep_their_own_routes_and_months(
    urlpatterns_, october
):
    class TwoView(HueView):
        router = Router[HttpRequest]()
        rooms = build_calendar_state(
            router, key="rooms", events=_events, day=DayAction("Book", _open)
        )
        desks = build_calendar_state(
            router, key="desks", events=_events, day=DayAction("Reserve", _open)
        )

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

    urlpatterns_.append(path(MOUNT, include(TwoView.urls)))
    clear_url_caches()
    assert [(r.path, r.name) for r in TwoView.router.routes] == [
        ("rooms/day/", "rooms_day"),
        ("desks/day/", "desks_day"),
    ]
    request = MagicMock()
    request.GET = QueryDict("rooms-month=2026-03&desks-month=2026-05")
    request.resolver_match = resolve(f"/{MOUNT}")
    rooms = _render(Calendar.from_state(TwoView.rooms), request)
    desks = _render(Calendar.from_state(TwoView.desks), request)
    assert "March 2026" in rooms and "May 2026" in desks
    # Each carries the other's month unchanged.
    assert 'href="/bookings/?desks-month=2026-05&amp;rooms-month=2026-04"' in rooms
    assert 'href="/bookings/?rooms-month=2026-03&amp;desks-month=2026-06"' in desks
