"""
The state a declared calendar reads off a request, the event it reads off
the dialog, and what it draws around the calendar. The route itself is
tested against a real Django view in hue-django.
"""

import asyncio
from datetime import date, datetime
from typing import Any

import pytest

from hue import calendar as declared
from hue.calendar import CalendarState, Layer, _Posted, build_calendar_state
from hue.context import HueContextArgs
from hue.formats import Formats
from hue.renderer import render_tree
from hue.ui import Calendar, Event
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

_TODAY = date(2026, 10, 14)
_LAYERS = [Layer("work", "Work"), Layer("home", "Home", color=3)]


class _Router:
    """
    Just enough router to declare against: the query it is told, and URLs
    spelled out, since there is nothing to reverse them against.
    """

    def __init__(self) -> None:
        self.registered: list[str] = []
        self.query: dict[str, list[str]] = {}

    def fragment_post(self, path: str) -> Any:
        self.registered.append(path)
        return lambda view_func: view_func

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return self.query

    def _get_form_values(self, request: Any) -> dict[str, list[str]]:
        return {}

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        return f"/events/{params['action']}/" if params else "/events/"

    def _passes_through(self, error: Exception) -> bool:
        return False

    def _form_fields(self) -> frozenset[str]:
        return frozenset()

    async def _run_sync(self, func: Any, /, *args: Any) -> Any:
        return func(*args)


def _events(request: Any, asked: CalendarState) -> list[Event]:
    return [
        Event("Review", datetime(2026, 10, 14, 13), datetime(2026, 10, 14, 14), id="1"),
        Event("Offsite", date(2026, 10, 19), date(2026, 10, 21), id="2", layer="home"),
    ]


def _declared(router: _Router | None = None, **given: Any) -> Any:
    given.setdefault("events", _events)
    return build_calendar_state(router or _Router(), key="events", **given)


def _posted(**fields: str) -> _Posted:
    whole = {
        "title": "Review",
        "starts": "2026-10-14",
        "starts_time": "13:00",
        "ends": "2026-10-14",
        "ends_time": "14:00",
    }
    return _Posted(**{**whole, **fields})


@pytest.fixture(autouse=True)
def _october(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(declared, "_today", lambda formats: _TODAY)


async def _html(component: Any, context_args: Any) -> str:
    return await render_tree(component, context_args=context_args)


def _bound(declaration: Any, **query: str) -> Any:
    declaration._router.query = {name: [value] for name, value in query.items()}
    asked, others = declaration._read(declaration._router.query, _TODAY)
    return asyncio.run(declaration._bind(None, asked, others, _TODAY, Formats()))


# The state


@pytest.mark.parametrize(
    ("view", "shown"),
    [
        ("day", (date(2026, 10, 14), date(2026, 10, 14))),
        ("week", (date(2026, 10, 12), date(2026, 10, 18))),
        ("month", (date(2026, 9, 28), date(2026, 11, 8))),
        ("year", (date(2026, 1, 1), date(2026, 12, 31))),
        ("agenda", (date(2026, 10, 14), date(2026, 11, 12))),
    ],
)
def test_each_view_shows_its_own_days(view, shown):
    assert CalendarState(_TODAY, view=view).days == shown


def test_first_and_last_cover_the_view_and_the_month_the_picker_shows():
    # A week asks for the six weeks around it, for the picker's marks; an
    # agenda runs past them.
    week = CalendarState(_TODAY, view="week")
    assert (week.first, week.last) == (date(2026, 9, 28), date(2026, 11, 8))
    agenda = CalendarState(_TODAY, view="agenda")
    assert (agenda.first, agenda.last) == (date(2026, 9, 28), date(2026, 11, 12))


@pytest.mark.parametrize(
    "typed",
    [
        {},
        {"events-view": ["weekly"], "events-date": ["14-10-2026"]},
        {"events-date": ["2026-13-01"], "events-start": ["tuesday"]},
        {"events-date": ["0001-01-01"], "events-weekdays": ["yes"]},
    ],
)
def test_what_is_not_a_state_is_the_default(typed):
    asked, _ = _declared()._read(typed, _TODAY)
    expected = CalendarState(date(2, 1, 1) if "0001" in str(typed) else _TODAY)
    assert asked == expected


def test_the_state_is_read_under_the_key_and_the_rest_rides_along():
    asked, others = _declared(layers=_LAYERS)._read(
        {
            "events-view": ["month"],
            "events-date": ["2026-03-02"],
            "events-q": [" planning "],
            "events-hide": ["home,gone"],
            "events-start": ["sunday"],
            "events-weekdays": ["1"],
            "tab": ["a", "b"],
            "other-view": ["day"],
            # The dialog's own fields, posted beside the state, which no
            # link may carry on.
            "title": ["Review"],
            "starts_time": ["13:00"],
        },
        _TODAY,
    )
    assert asked == CalendarState(
        date(2026, 3, 2),
        view="month",
        query="planning",
        hidden=("home",),
        week_start="sunday",
        weekdays=True,
        layers=("work",),
    )
    assert others == (("tab", "a"), ("tab", "b"), ("other-view", "day"))


def test_links_carry_only_what_differs_from_the_defaults():
    bound = _bound(_declared(week_start="sunday"), tab="all")
    assert bound.href() == "/events/?tab=all"
    assert bound.href(date=date(2026, 10, 21), view="month") == (
        "/events/?tab=all&events-view=month&events-date=2026-10-21"
    )
    assert bound.href(week_start="monday", weekdays=True) == (
        "/events/?tab=all&events-start=monday&events-weekdays=1"
    )


def test_events_is_asked_for_the_days_and_the_layers_shown():
    asked: list[CalendarState] = []

    def events(request: Any, state: CalendarState) -> list[Event]:
        asked.append(state)
        return []

    _bound(_declared(events=events, layers=_LAYERS), **{"events-hide": "work"})
    assert asked[0].layers == ("home",)
    assert (asked[0].first, asked[0].last) == (date(2026, 9, 28), date(2026, 11, 8))


def test_an_event_takes_its_layers_colour_unless_it_chose_one():
    bound = _bound(_declared(layers=_LAYERS))
    assert [event.color for event in bound.events] == [None, 3]
    chosen = _bound(
        _declared(
            layers=_LAYERS,
            events=lambda r, s: [Event("Own", _TODAY, layer="home", color=5)],
        )
    )
    assert chosen.events[0].color == 5


def test_something_that_is_not_an_event_is_refused_by_name():
    with pytest.raises(TypeError, match="events"):
        _bound(_declared(events=lambda r, s: [{"title": "Offsite"}]))


# The declaration


def test_the_route_is_registered_only_when_there_is_something_to_post():
    router = _Router()
    _declared(router)
    assert router.registered == []
    _declared(router, save=lambda r, e: None)
    assert router.registered == ["events/<str:action>/"]


@pytest.mark.parametrize(
    ("given", "complaint"),
    [
        ({"key": ""}, "key"),
        ({"layers": [Layer("a", "A"), Layer("a", "B")]}, "two layers"),
        ({"layers": [Layer("a,b", "A")]}, "comma"),
        ({"repeats": {"weekly": "Weekly"}}, "no save"),
    ],
)
def test_a_declaration_that_cannot_work_is_refused(given, complaint):
    given = {"key": "events", "events": _events, **given}
    with pytest.raises(ValueError, match=complaint):
        build_calendar_state(_Router(), **given)


# The dialog's fields


def test_the_fields_become_an_event_in_the_readers_time():
    event, errors = _declared(
        layers=_LAYERS, save=lambda r, e: None, repeats={"weekly": "Weekly"}
    )._draft(
        _posted(id="7", layer="home", repeat="weekly", location=" Room 3B ", notes="")
    )
    assert errors == {}
    assert event == Event(
        "Review",
        datetime(2026, 10, 14, 13),
        datetime(2026, 10, 14, 14),
        id="7",
        location="Room 3B",
        repeat="weekly",
        layer="home",
    )


def test_a_whole_day_event_is_a_pair_of_dates_that_may_be_the_same_day():
    event, errors = _declared()._draft(
        _posted(all_day="on", starts_time="", ends_time="")
    )
    assert errors == {}
    assert (event.starts, event.ends) == (date(2026, 10, 14), date(2026, 10, 14))


@pytest.mark.parametrize(
    ("fields", "wrong"),
    [
        ({"title": "  "}, {"title": "Give the event a title."}),
        ({"starts": "14.10.2026"}, {"starts": "Enter a date."}),
        ({"ends_time": "2pm"}, {"ends_time": "Enter a time."}),
        ({"ends_time": "12:00"}, {"ends_time": "Ends before it starts."}),
        ({"ends_time": "13:00"}, {"ends_time": "Starts and ends at the same time."}),
        (
            {"all_day": "on", "ends": "2026-10-13"},
            {"ends": "Ends before it starts."},
        ),
        ({"repeat": "yearly"}, {"repeat": "Choose how it repeats."}),
    ],
)
def test_what_cannot_be_read_is_an_error_on_its_field(fields, wrong):
    event, errors = _declared(save=lambda r, e: None)._draft(_posted(**fields))
    assert event is None
    assert errors == wrong


def test_a_layer_is_required_when_there_are_layers():
    assert _declared(layers=_LAYERS)._draft(_posted())[1] == {
        "layer": "Choose a calendar."
    }
    assert _declared()._draft(_posted())[1] == {}


def test_the_overlap_check_names_the_timed_events_that_share_a_moment():
    found = _declared()._overlapping(
        None,
        CalendarState(_TODAY),
        Event("New", datetime(2026, 10, 14, 13, 30), datetime(2026, 10, 14, 15)),
        Formats(),
    )
    assert [event.title for event in found] == ["Review"]
    # Not the event being edited, and not a whole-day one.
    itself = Event(
        "Review", datetime(2026, 10, 14, 13), datetime(2026, 10, 14, 15), id="1"
    )
    assert (
        _declared()._overlapping(None, CalendarState(_TODAY), itself, Formats()) == []
    )


# What is drawn


class TestDrawn:
    @pytest.mark.asyncio
    async def test_the_sidebar_the_toolbar_and_the_calendar_hang_off_the_key(
        self, context_args
    ):
        html = await _html(
            Calendar.from_state(_declared(layers=_LAYERS, search="Search events")),
            context_args,
        )
        assert_attr(html, "aside#events-side", "x-sync")
        assert_attr(html, "#events-view", "x-sync")
        assert_selector(html, "#events-dialog")
        assert_attr(html, "form#events-search input[name=events-q]", "type", "search")
        assert_attr(html, "#events-matches", "role", "status")
        assert_selector(html, "form#events-options input[name=events-start]", count=3)
        # The picker marks the days with something on, and submits under
        # the date's name.
        picker = select(html, "#events-picker")[0]
        assert (
            '"markers": ["2026-10-14", "2026-10-19", "2026-10-20", "2026-10-21"]'
            in (picker["x-data"])
        )
        assert_attr(html, "#events-picker input[type=hidden]", "name", "events-date")
        # The whole state, for the script that opens the dialog from a click.
        assert_selector(html, "#events-state")

    @pytest.mark.asyncio
    async def test_a_hidden_layer_is_unticked_and_the_forms_carry_the_rest(
        self, context_args
    ):
        declaration = _declared(layers=_LAYERS, search="Search events")
        declaration._router.query = {"events-hide": ["home"], "events-view": ["month"]}
        html = await _html(Calendar.from_state(declaration), context_args)
        assert_attr(html, "#events-show-work", "checked")
        assert "checked" not in select(html, "#events-show-home")[0].attrs
        carried = select(html, "input[form=events-search]")
        assert {(one["name"], one["value"]) for one in carried} == {
            ("events-hide", "home"),
            ("events-view", "month"),
        }

    @pytest.mark.asyncio
    async def test_the_search_says_how_many_it_found_among_the_days_shown(
        self, context_args
    ):
        declaration = _declared(search="Search events")
        declaration._router.query = {"events-q": ["re"]}
        html = await _html(Calendar.from_state(declaration), context_args)
        assert select(html, "#events-matches")[0].get_text() == '1 event matches "re".'

    @pytest.mark.asyncio
    async def test_without_a_save_there_is_nothing_to_create_or_edit_with(
        self, context_args
    ):
        html = await _html(Calendar.from_state(_declared()), context_args)
        assert_no_selector(html, "#events-new")
        assert_no_selector(html, "[aria-label='Delete event']")
        assert "@click" not in select(html, "#events")[0].attrs

    @pytest.mark.asyncio
    async def test_with_handlers_the_popover_posts_the_event_back(self, context_args):
        html = await _html(
            Calendar.from_state(
                _declared(save=lambda r, e: None, delete=lambda r, i: None)
            ),
            context_args,
        )
        assert_attr(html, "#events-new", "@click", "create()")
        assert_attr(html, "#events", "@click", "slot($event)")
        edits = [
            b
            for b in select(html, "button")
            if "/events/dialog/" in b.get("@click", "")
        ]
        # One event is in the week; the offsite is the week after.
        assert len(edits) == 1
        assert '"starts_time": "13:00"' in edits[0]["@click"]
        assert_selector(html, "[aria-label='Delete event']", count=1)

    @pytest.mark.asyncio
    async def test_two_calendars_on_one_page_keep_their_own_ids(self, context_args):
        rooms = build_calendar_state(_Router(), key="rooms", events=_events)
        desks = build_calendar_state(_Router(), key="desks", events=_events)
        html = await render_tree(
            Calendar.from_state(rooms),
            Calendar.from_state(desks),
            context_args=context_args,
        )
        assert_selector(html, "#rooms-side")
        assert_selector(html, "#desks-side")
        assert_selector(html, "#rooms-picker")
        assert_selector(html, "#desks-picker")


class TestDialog:
    async def _dialog(
        self, declaration: Any, posted: _Posted, errors: dict[str, str]
    ) -> Any:
        asked, others = declaration._read({}, _TODAY)
        bound = await declaration._bind(None, asked, others, _TODAY, Formats())
        return declaration._dialog(bound, posted, errors)

    @pytest.mark.asyncio
    async def test_a_new_event_has_the_fields_and_posts_the_state(self, context_args):
        declaration = _declared(
            layers=_LAYERS, save=lambda r, e: None, repeats={"weekly": "Every week"}
        )
        html = await _html(await self._dialog(declaration, _posted(), {}), context_args)
        assert_attr(html, "[role=dialog]", "aria-modal", "true")
        assert "New event" in html
        form = select(html, "form#events-form")[0]
        assert form["action"] == "/events/save/"
        assert form["x-target"] == "events-dialog"
        assert "novalidate" in form.attrs
        for name in ("title", "all_day", "starts", "starts_time", "ends", "ends_time"):
            assert_selector(html, f"#events-form [name={name}]")
        assert_attr(html, "input[name=title]", "x-autofocus")
        assert [
            o.get_text(strip=True) for o in select(html, "select[name=layer] option")
        ] == [
            "Work",
            "Home",
        ]
        assert [
            o.get_text(strip=True) for o in select(html, "select[name=repeat] option")
        ] == [
            "Does not repeat",
            "Every week",
        ]
        assert_attr(html, "#events-overlap", "role", "status")
        assert_no_selector(html, "[formaction='/events/delete/']")

    @pytest.mark.asyncio
    async def test_an_existing_event_can_be_deleted_from_its_dialog(self, context_args):
        declaration = _declared(save=lambda r, e: None, delete=lambda r, i: None)
        html = await _html(
            await self._dialog(declaration, _posted(id="7"), {}), context_args
        )
        assert "Edit event" in html
        assert_attr(html, "input[name=id]", "value", "7")
        assert_attr(html, "[formaction='/events/delete/']", "form", "events-form")
        assert_no_selector(html, "select[name=layer]")
        assert_no_selector(html, "select[name=repeat]")

    @pytest.mark.asyncio
    async def test_errors_land_on_their_fields(self, context_args):
        declaration = _declared(save=lambda r, e: None)
        html = await _html(
            await self._dialog(
                declaration,
                _posted(title=""),
                {
                    "title": "Give the event a title.",
                    "ends_time": "Ends before it starts.",
                },
            ),
            context_args,
        )
        assert_attr(html, "input[name=title]", "aria-invalid", "true")
        assert "Give the event a title." in html
        assert "Ends before it starts." in html


def test_the_overlap_warning_names_two_and_counts_the_rest():
    found = [
        Event("A", datetime(2026, 10, 14, 13), datetime(2026, 10, 14, 14)),
        Event("B", datetime(2026, 10, 14, 13), datetime(2026, 10, 14, 15)),
        Event("C", datetime(2026, 10, 14, 13), datetime(2026, 10, 14, 16)),
    ]
    html = asyncio.run(
        render_tree(
            declared._overlap_warning(found, Formats()),
            context_args=HueContextArgs(request=None, csrf_token=""),
        )
    )
    assert "Overlaps A (13:00 to 14:00) and B (13:00 to 15:00) and 1 more." in html
    assert declared._overlap_warning([], Formats()) == ""
