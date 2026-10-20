"""
The calendar declaration, end to end against a Django view.

The page reads its state off the URL, every link carries the rest of the
query along, and the one route answers the dialog, the overlap check, a
save and a delete with the calendar in the state it was in.
"""

import asyncio
import re
from collections import Counter
from datetime import date, datetime
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, QueryDict
from django.test import Client, override_settings
from django.urls import clear_url_caches, include, path, resolve
from hue import calendar as declared
from hue import html
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
        # Mounted again, the new view takes the old one's place.
        view = _view(**given)
        urlpatterns_[:] = [path(MOUNT, include(view.urls))]
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


def _ids(html: str) -> Counter[str]:
    return Counter(re.findall(r'\sid="([^"]+)"', html))


def _act(action: str, **posted: str) -> Any:
    return Client().post(f"/{MOUNT}events/{action}/", posted, **_AJAX)


def _fields(**changed: str) -> dict[str, str]:
    """
    The dialog's fields as it posts them, under the key, for an hour and a
    half on Thursday, with any of them changed.
    """
    whole = {
        "title": "Pairing",
        "starts": "2026-10-15",
        "starts_time": "11:00",
        "ends": "2026-10-15",
        "ends_time": "12:30",
        "layer": "home",
        **changed,
    }
    return {f"events-{name}": value for name, value in whole.items()}


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


# The dialog


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


def test_the_dialogs_controls_are_named_and_identified_under_the_key(mounted):
    mounted(repeats={"weekly": "Every week"})
    html = _act("dialog").content.decode()
    for name in (
        "title",
        "all_day",
        "starts",
        "starts_time",
        "ends",
        "ends_time",
        "layer",
        "repeat",
        "location",
        "notes",
    ):
        assert f'name="events-{name}"' in html, name
        assert f'id="events-{name}"' in html, name
        assert f'for="events-{name}"' in html, name
    assert 'id="title"' not in html
    assert "x-autofocus" in re.search(r'<input[^>]*id="events-title"[^>]*>', html)[0]


def test_an_existing_event_can_be_deleted_from_its_dialog(mounted):
    mounted()
    html = _act("dialog", **_fields(id="7")).content.decode()
    assert "Edit event" in html
    assert 'name="events-id" value="7"' in html
    delete = re.search(r'<button[^>]*formaction="/planning/events/delete/"[^>]*>', html)
    assert delete and 'form="events-form"' in delete[0]
    # A new event has nothing to delete, and neither has a calendar
    # without a delete.
    assert "/planning/events/delete/" not in _act("dialog").content.decode()
    mounted(delete=None)
    assert (
        "/planning/events/delete/"
        not in _act("dialog", **_fields(id="7")).content.decode()
    )


def test_the_repeat_and_calendar_selects_are_there_when_declared(mounted):
    mounted(repeats={"weekly": "Every week"})
    html = _act("dialog").content.decode()
    assert re.search(r'<select[^>]*name="events-repeat"', html)
    assert "Does not repeat" in html and "Every week" in html
    assert re.search(r'<select[^>]*name="events-layer"', html)
    mounted(repeats=None, layers=[])
    html = _act("dialog").content.decode()
    assert 'name="events-repeat"' not in html
    assert 'name="events-layer"' not in html


@pytest.mark.parametrize(
    ("changed", "wrong"),
    [
        ({"title": "  "}, "Give the event a title."),
        ({"starts": "14.10.2026"}, "Enter a date."),
        ({"ends_time": "2pm"}, "Enter a time."),
        ({"ends_time": "10:00"}, "Ends before it starts."),
        ({"ends_time": "11:00"}, "Starts and ends at the same time."),
        ({"all_day": "on", "ends": "2026-10-14"}, "Ends before it starts."),
        ({"ends": "2027-10-17"}, "Ends more than a year after it starts."),
        ({"layer": ""}, "Choose a calendar."),
        ({"repeat": "yearly"}, "Choose how it repeats."),
    ],
)
def test_a_field_that_cannot_be_read_comes_back_on_the_dialog(mounted, changed, wrong):
    mounted(repeats={"weekly": "Every week"})
    response = _act("save", **_fields(**changed))
    assert response.status_code == 422
    html = response.content.decode()
    assert wrong in html
    assert 'aria-invalid="true"' in html
    assert _SAVED == []


def test_a_time_the_clocks_skip_is_refused_under_a_timezone(mounted):
    mounted()
    # Oslo goes forward at 02:00 on 29 March 2026, so 02:30 is no time.
    # Made aware it would be 03:30, the same instant the event ends at.
    with override_settings(TIME_ZONE="Europe/Oslo"):
        day = {"starts": "2026-03-29", "ends": "2026-03-29"}
        refused = _act("save", **_fields(**day, starts_time="02:30", ends_time="03:30"))
        allowed = _act("save", **_fields(**day, starts_time="03:30", ends_time="04:30"))
    assert refused.status_code == 422
    html = refused.content.decode()
    assert "That time is skipped when the clocks go forward." in html
    assert allowed.status_code == 200
    assert [event.starts for event in _SAVED] == [datetime(2026, 3, 29, 3, 30)]


def test_a_save_reaches_the_handler_and_redraws_the_calendar_with_a_toast(mounted):
    mounted()
    response = _act(
        "save", **_fields(), **{"events-view": "day", "events-date": "2026-10-15"}
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
    assert re.search(r'<div id="events-dialog"[^>]*></div>', html)
    assert "Thursday 15 October 2026" in html


def test_the_fields_become_the_event_the_handler_is_handed(mounted):
    mounted(repeats={"weekly": "Every week"})
    _act("save", **_fields(id="7", repeat="weekly", location=" Room 3B ", notes=""))
    assert _SAVED == [
        Event(
            "Pairing",
            datetime(2026, 10, 15, 11),
            datetime(2026, 10, 15, 12, 30),
            id="7",
            location="Room 3B",
            repeat="weekly",
            layer="home",
        )
    ]
    # A whole day is a pair of dates, which may be the same day, and a
    # calendar without layers asks for none.
    mounted(layers=[])
    _act("save", **_fields(all_day="on", layer="", ends="2026-10-15"))
    assert _SAVED == [Event("Pairing", date(2026, 10, 15), date(2026, 10, 15))]


def test_a_delete_reaches_the_handler(mounted):
    mounted()
    response = _act("delete", **{"events-id": "1", "events-title": "Review"})
    assert response.status_code == 200
    assert _DELETED == ["1"]
    assert "Deleted" in response.content.decode()
    assert _act("delete").status_code == 404


def test_the_overlap_check_answers_in_the_dialogs_own_region(mounted):
    mounted()
    response = _act(
        "overlaps",
        **_fields(
            starts="2026-10-14",
            starts_time="13:30",
            ends="2026-10-14",
            ends_time="14:30",
        ),
    )
    html = response.content.decode()
    assert html.startswith('<div id="events-overlap">')
    assert "Overlaps Review (13:00 to 14:00)." in html
    cleared = _act("overlaps", **_fields(all_day="on")).content.decode()
    assert re.fullmatch(r'<div id="events-overlap">\s*</div>', cleared.strip())


def test_the_overlap_check_asks_for_the_drafts_days_in_every_layer_unsearched(
    mounted,
):
    asked: list[Any] = []

    def events(request: Any, state: CalendarState) -> list[Event]:
        asked.append((state.first, state.last, state.query, state.layers))
        return []

    mounted(events=events)
    # The view is on March, with a search and a hidden layer; the draft
    # is far away from both. Only its own day is asked for, in every layer
    # and with no search, or a far draft reads thousands of days a
    # keystroke and a clash the reader cannot see goes unmentioned.
    _act(
        "overlaps",
        **_fields(starts="9998-12-30", ends="9998-12-30"),
        **{"events-date": "2026-03-02", "events-q": "re", "events-hide": "home"},
    )
    assert asked == [(date(9998, 12, 30), date(9998, 12, 30), "", ("work", "home"))]


def test_the_overlap_warning_names_two_counts_the_rest_and_skips_itself(mounted):
    def events(request: Any, state: CalendarState) -> list[Event]:
        return [
            Event(name, datetime(2026, 10, 15, 11), datetime(2026, 10, 15, 12), id=i)
            for i, name in (("1", "A"), ("2", "B"), ("3", "C"))
        ]

    mounted(events=events)
    html = _act("overlaps", **_fields()).content.decode()
    assert "Overlaps A (11:00 to 12:00) and B (11:00 to 12:00) and 1 more." in html
    # The event being edited is not in its own way.
    html = _act("overlaps", **_fields(id="3")).content.decode()
    assert "Overlaps A (11:00 to 12:00) and B (11:00 to 12:00)." in html


def test_a_handler_that_fails_says_so_on_the_page(mounted):
    def fail(request: Any, event: Event) -> None:
        raise RuntimeError("down")

    mounted(save=fail)
    response = _act("save", **_fields())
    assert response.status_code == 500
    assert "Create failed" in response.content.decode()


@pytest.mark.parametrize(
    ("refusal", "status"), [(PermissionDenied, 403), (Http404, 404)]
)
def test_a_refusal_from_the_handler_keeps_its_status_and_answers_on_the_page(
    mounted, refusal, status
):
    # A stale edit, or one the reader may not make. Django's own page has
    # no slot for the browser to put it in, so the calendar answers, with
    # the dialog closed and a toast, and the status Django would give.
    def refuse(request: Any, event: Event) -> None:
        raise refusal

    mounted(save=refuse)
    response = _act("save", **_fields())
    assert response.status_code == status
    html = response.content.decode()
    assert "Create failed" in html
    assert re.search(r'<div id="events-dialog"[^>]*></div>', html)


def test_the_dialogs_form_carries_the_csrf_token_for_a_plain_submit(mounted):
    mounted()
    html = _act("dialog").content.decode()
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    assert token and len(token[1]) == 64
    # Posted back, it is the framework's and not something a link carries.
    page = _act("dialog", csrfmiddlewaretoken=token[1]).content.decode()
    assert 'name="csrfmiddlewaretoken" form=' not in page
    assert page.count('name="csrfmiddlewaretoken"') == 1


def test_an_action_that_is_not_one_is_not_found_and_the_route_wants_ajax(mounted):
    mounted()
    assert _act("archive").status_code == 404
    assert Client().post(f"/{MOUNT}events/save/", _fields()).status_code == 400


def test_without_handlers_there_is_no_route(mounted):
    view = mounted(save=None, delete=None)
    assert [route.path for route in view.router.routes] == []


def test_two_calendars_on_one_page_keep_their_own_routes_states_and_ids(urlpatterns_):
    class TwoView(HueView):
        router = Router[HttpRequest]()
        rooms = build_calendar_state(
            router, key="rooms", events=_events, save=lambda r, e: None
        )
        desks = build_calendar_state(
            router, key="desks", events=_events, save=lambda r, e: None
        )

        async def index(self, request: Any, context: Any) -> Any:
            return Page(
                title="Two",
                body=html.div(
                    Calendar.from_state(self.rooms), Calendar.from_state(self.desks)
                ),
            )

    urlpatterns_.append(path(MOUNT, include(TwoView.urls)))
    clear_url_caches()
    assert [(r.path, r.name) for r in TwoView.router.routes] == [
        ("rooms/<str:action>/", "rooms_act"),
        ("desks/<str:action>/", "desks_act"),
    ]
    page = Client().get(f"/{MOUNT}", {"rooms-view": "month", "desks-view": "year"})
    rooms_html = page.content.decode()
    assert "October 2026" in rooms_html and ">2026<" in rooms_html
    # Each carries the other's state unchanged.
    request = _request(**{"desks-view": "year"})
    rooms = _render(Calendar.from_state(TwoView.rooms), request)
    assert "desks-view=year" in _hrefs(rooms.replace("rooms-", "events-"))["next"]
    # Nothing on the page, the two dialogs included, shares an id. A dialog
    # arrives inside its slot, which the page already holds.
    dialogs = "".join(
        Client()
        .post(f"/{MOUNT}{key}/dialog/", {}, **_AJAX)
        .content.decode()
        .removeprefix(f'<div id="{key}-dialog">')
        for key in ("rooms", "desks")
    )
    repeated = {name for name, n in _ids(rooms_html + dialogs).items() if n > 1}
    assert repeated == set()
    assert {"rooms-title", "desks-title"} <= set(_ids(dialogs))
