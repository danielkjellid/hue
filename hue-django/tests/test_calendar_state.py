"""
The calendar declaration, end to end against a Django view.

The page reads its state off the URL, every link carries the rest of the
query along, and the one route answers the dialog, the overlap check, a
save and a delete with the calendar in the state it was in.
"""

import asyncio
import re
from datetime import date, datetime
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, QueryDict
from django.test import Client
from django.urls import clear_url_caches, include, path, resolve
from hue import calendar as declared
from hue.calendar import CalendarState, Layer, build_calendar_state
from hue.context import HueContextArgs
from hue.renderer import render_tree
from hue.ui import Calendar, Event

from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueView

MOUNT = "planning/"
_AJAX = {"HTTP_X_ALPINE_REQUEST": "true"}
_TODAY = date(2026, 10, 14)

_SAVED: list[Event] = []
_DELETED: list[str] = []


def _events(request: Any, asked: CalendarState) -> list[Event]:
    return [
        Event(
            "Review",
            datetime(2026, 10, 14, 13),
            datetime(2026, 10, 14, 14),
            id="1",
            layer="work",
        )
    ]


def _view(**given: Any) -> Any:
    _SAVED.clear()
    _DELETED.clear()
    given.setdefault("events", _events)
    given.setdefault("layers", [Layer("work", "Work"), Layer("home", "Home", color=3)])
    given.setdefault("save", lambda request, event: _SAVED.append(event))
    given.setdefault("delete", lambda request, id: _DELETED.append(id))

    class EventsView(HueView):
        router = Router[HttpRequest]()

        events = build_calendar_state(router, key="events", **given)

        async def index(self, request: Any, context: Any) -> Any:
            return Page(title="Events", body=Calendar.from_state(self.events))

    return EventsView


@pytest.fixture
def mounted(urlpatterns_: list[Any]) -> Any:
    def build(**given: Any) -> Any:
        view = _view(**given)
        urlpatterns_.append(path(MOUNT, include(view.urls)))
        clear_url_caches()
        return view

    return build


@pytest.fixture(autouse=True)
def _october(monkeypatch: pytest.MonkeyPatch) -> None:
    # The clock held still, so today and its week are known.
    monkeypatch.setattr(declared, "_today", lambda formats: _TODAY)


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
        name = re.search(r'id="events-(previous|today|next)"', tag)
        href = re.search(r'href="([^"]*)"', tag)
        if name and href:
            found[name[1]] = href[1]
    return found


def _act(action: str, **posted: str) -> Any:
    return Client().post(f"/{MOUNT}events/{action}/", posted, **_AJAX)


_FIELDS = {
    "title": "Pairing",
    "starts": "2026-10-15",
    "starts_time": "11:00",
    "ends": "2026-10-15",
    "ends_time": "12:30",
    "layer": "home",
}


def test_the_page_draws_the_state_the_url_asks_for(mounted):
    mounted()
    response = Client().get(
        f"/{MOUNT}", {"events-view": "month", "events-date": "2026-03-02"}
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "March 2026" in html
    assert 'id="events"' in html
    assert re.search(r'<p id="events-status"[^>]*x-sync[^>]*>March 2026</p>', html)


def test_the_links_keep_the_rest_of_the_query_and_todays_drops_the_date(mounted):
    html = _render(
        Calendar.from_state(mounted().events),
        _request(**{"events-date": "2026-10-21", "events-view": "day", "tab": "all"}),
    )
    assert _hrefs(html) == {
        "previous": "/planning/?tab=all&amp;events-view=day&amp;events-date=2026-10-20",
        "today": "/planning/?tab=all&amp;events-view=day",
        "next": "/planning/?tab=all&amp;events-view=day&amp;events-date=2026-10-22",
    }
    assert 'x-target.push="events-view"' in html


def test_events_is_asked_for_the_days_shown_off_the_event_loop(mounted):
    asked: list[Any] = []

    def events(request: Any, state: CalendarState) -> list[Event]:
        asked.append((state.first, state.last, state.layers, _on_the_loop()))
        return []

    _render(Calendar.from_state(mounted(events=events).events), _request())
    assert asked == [(date(2026, 9, 28), date(2026, 11, 8), ("work", "home"), False)]


def _on_the_loop() -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def test_the_dialog_opens_in_the_slot_with_the_state_and_a_time_filled_in(mounted):
    mounted()
    response = _act("dialog", **{"events-view": "month", "events-date": "2026-10-21"})
    assert response.status_code == 200
    html = response.content.decode()
    assert html.startswith('<div id="events-dialog">')
    assert 'role="dialog"' in html
    # A new event starts at nine on the day the view is around, and the
    # form posts the state back so the calendar comes back as it was.
    assert 'value="2026-10-21"' in html
    assert 'value="09:00"' in html and 'value="10:00"' in html
    assert 'name="events-view" value="month"' in html


def test_a_field_that_cannot_be_read_comes_back_on_the_dialog(mounted):
    mounted()
    response = _act("save", **{**_FIELDS, "title": "", "ends_time": "10:00"})
    assert response.status_code == 422
    html = response.content.decode()
    assert "Give the event a title." in html
    assert "Ends before it starts." in html
    assert _SAVED == []


def test_a_save_reaches_the_handler_and_redraws_the_calendar_with_a_toast(mounted):
    mounted()
    response = _act(
        "save", **{**_FIELDS, "events-view": "day", "events-date": "2026-10-15"}
    )
    assert response.status_code == 200
    assert _SAVED == [
        Event(
            "Pairing",
            datetime(2026, 10, 15, 11),
            datetime(2026, 10, 15, 12, 30),
            layer="home",
        )
    ]
    html = response.content.decode()
    assert "Created &quot;Pairing&quot;" in html or 'Created "Pairing"' in html
    assert '<div id="events-dialog"></div>' in html
    assert "Thursday 15 October 2026" in html


def test_a_delete_reaches_the_handler(mounted):
    mounted()
    response = _act("delete", id="1", title="Review")
    assert response.status_code == 200
    assert _DELETED == ["1"]
    assert "Deleted" in response.content.decode()
    assert _act("delete").status_code == 404


def test_the_overlap_check_answers_in_the_dialogs_own_region(mounted):
    mounted()
    response = _act(
        "overlaps",
        **{
            **_FIELDS,
            "starts": "2026-10-14",
            "starts_time": "13:30",
            "ends": "2026-10-14",
            "ends_time": "14:30",
        },
    )
    html = response.content.decode()
    assert html.startswith('<div id="events-overlap">')
    assert "Overlaps Review (13:00 to 14:00)." in html
    cleared = _act("overlaps", **{**_FIELDS, "all_day": "on"}).content.decode()
    assert re.fullmatch(r'<div id="events-overlap">\s*</div>', cleared.strip())


def test_a_handler_that_fails_says_so_on_the_page(mounted):
    def fail(request: Any, event: Event) -> None:
        raise RuntimeError("down")

    mounted(save=fail)
    response = _act("save", **_FIELDS)
    assert response.status_code == 500
    assert "Create failed" in response.content.decode()


def test_a_refusal_from_the_handler_is_djangos_own_answer(mounted):
    def refuse(request: Any, event: Event) -> None:
        raise PermissionDenied

    mounted(save=refuse)
    assert _act("save", **_FIELDS).status_code == 403


def test_an_action_that_is_not_one_is_not_found_and_the_route_wants_ajax(mounted):
    mounted()
    assert _act("archive").status_code == 404
    assert Client().post(f"/{MOUNT}events/save/", _FIELDS).status_code == 400


def test_without_handlers_there_is_no_route(mounted):
    view = mounted(save=None, delete=None)
    assert [route.path for route in view.router.routes] == []


def test_two_calendars_on_one_view_keep_their_own_routes_and_states(urlpatterns_):
    class TwoView(HueView):
        router = Router[HttpRequest]()
        rooms = build_calendar_state(
            router, key="rooms", events=_events, save=lambda r, e: None
        )
        desks = build_calendar_state(
            router, key="desks", events=_events, save=lambda r, e: None
        )

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

    urlpatterns_.append(path(MOUNT, include(TwoView.urls)))
    clear_url_caches()
    assert [(r.path, r.name) for r in TwoView.router.routes] == [
        ("rooms/<str:action>/", "rooms_act"),
        ("desks/<str:action>/", "desks_act"),
    ]
    request = MagicMock()
    request.GET = QueryDict("rooms-view=month&desks-view=year")
    request.resolver_match = resolve(f"/{MOUNT}")
    rooms = _render(Calendar.from_state(TwoView.rooms), request)
    desks = _render(Calendar.from_state(TwoView.desks), request)
    assert "October 2026" in rooms and ">2026<" in desks
    # Each carries the other's state unchanged.
    assert "desks-view=year" in _hrefs(rooms.replace("rooms-", "events-"))["next"]
    assert "rooms-view=month" in _hrefs(desks.replace("desks-", "events-"))["next"]
