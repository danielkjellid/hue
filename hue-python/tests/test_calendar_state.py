"""
The state a declared calendar reads off a request and what it draws around
the calendar, through the page a view renders: the state is what events()
is handed, and the links are what comes back. The route itself is tested
against a real Django view in hue-django.
"""

import re
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from hue import calendar as declared
from hue import html, scope
from hue.calendar import CalendarShortcuts, CalendarState, Layer, build_calendar_state
from hue.context import HueContextArgs
from hue.formats import Formats
from hue.js import unsafe
from hue.pages import create_page_base
from hue.renderer import render_tree
from hue.shortcuts import ShortcutRegistry, shortcuts
from hue.ui import Calendar, Event
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

_TODAY = date(2026, 10, 14)
_Page = create_page_base(css_url="/s.css", js_url="/a.js", html_title_factory=str)
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

    def _refusal(self, error: Exception) -> None:
        return None

    def _csrf_field(self) -> None:
        return None

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


@pytest.fixture(autouse=True)
def _october(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(declared, "today_in", lambda formats: _TODAY)


async def _drawn(declaration: Any, context_args: Any, **query: str) -> str:
    """
    The page a view renders for this query.
    """
    declaration._router.query = {name: [value] for name, value in query.items()}
    page = Calendar.from_state(declaration)
    return await render_tree(page, context_args=context_args)


async def _asked(context_args: Any, **query: str) -> CalendarState:
    """
    The state events() is handed for a page with this query, which is the
    one public reading of what the URL said.
    """
    seen: list[CalendarState] = []

    def events(request: Any, asked: CalendarState) -> list[Event]:
        seen.append(asked)
        return []

    await _drawn(_declared(events=events, layers=_LAYERS), context_args, **query)
    return seen[0]


def _href(html: str, element_id: str) -> str:
    return select(html, f"#{element_id}")[0]["href"]


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "typed",
    [
        {},
        {"events-view": "weekly", "events-date": "14-10-2026"},
        {"events-date": "2026-13-01", "events-start": "someday"},
        {"events-date": "0001-01-01", "events-weekdays": "yes"},
    ],
)
async def test_what_is_not_a_state_is_the_default(context_args, typed):
    cursor = date(2, 1, 1) if "0001" in str(typed) else _TODAY
    assert await _asked(context_args, **typed) == CalendarState(
        cursor, layers=("work", "home")
    )


@pytest.mark.asyncio
async def test_the_state_is_read_under_the_key(context_args):
    asked = await _asked(
        context_args,
        **{
            "events-view": "month",
            "events-date": "2026-03-02",
            "events-q": " planning ",
            "events-hide": "home,gone",
            "events-start": "wednesday",
            "events-weekdays": "1",
            "other-view": "day",
        },
    )
    assert asked == CalendarState(
        date(2026, 3, 2),
        view="month",
        query="planning",
        hidden=("home",),
        week_start="wednesday",
        weekdays=True,
        layers=("work",),
    )


@pytest.mark.asyncio
async def test_the_rest_of_the_query_rides_along_and_the_dialogs_fields_do_not(
    context_args,
):
    # A page parameter that happens to share a name with one of the
    # dialog's fields is the page's; the field under the key is not.
    html = await _drawn(
        _declared(),
        context_args,
        **{"tab": "a", "title": "Report", "events-title": "Review"},
    )
    assert _href(html, "events-next") == (
        "/events/?tab=a&title=Report&events-date=2026-10-21"
    )


@pytest.mark.asyncio
async def test_links_carry_only_what_differs_from_the_defaults(context_args):
    html = await _drawn(_declared(week_start="sunday"), context_args, tab="all")
    assert _href(html, "events-today") == "/events/?tab=all"
    assert _href(html, "events-next") == "/events/?tab=all&events-date=2026-10-21"
    # Back to Monday is a change from this calendar's default, so it is said.
    html = await _drawn(
        _declared(week_start="sunday"),
        context_args,
        **{"events-start": "monday", "events-weekdays": "1"},
    )
    assert _href(html, "events-today") == (
        "/events/?events-start=monday&events-weekdays=1"
    )


@pytest.mark.asyncio
async def test_events_is_asked_for_the_days_and_the_layers_shown(context_args):
    asked = await _asked(context_args, **{"events-hide": "work"})
    assert asked.layers == ("home",)
    assert (asked.first, asked.last) == (date(2026, 9, 28), date(2026, 11, 8))


@pytest.mark.asyncio
async def test_an_event_takes_its_layers_colour_unless_it_chose_one(context_args):
    html = await _drawn(
        _declared(
            layers=_LAYERS,
            events=lambda r, s: [
                Event("Own", _TODAY, layer="home", color=5),
                Event("Home", _TODAY, layer="home"),
            ],
        ),
        context_args,
    )
    own, home = (
        select(html, f"#events-view button[aria-label^='{title},']")[0]["class"]
        for title in ("Own", "Home")
    )
    assert "border-chart-5" in own
    assert "border-chart-3" in home


@pytest.mark.asyncio
async def test_something_that_is_not_an_event_is_refused_by_name(context_args):
    with pytest.raises(TypeError, match="events"):
        await _drawn(
            _declared(events=lambda r, s: [{"title": "Offsite"}]), context_args
        )


@pytest.mark.asyncio
async def test_a_part_drawn_outside_its_calendar_says_what_it_belongs_to(
    context_args,
):
    with pytest.raises(ValueError, match=r"part of a Calendar bound to a request"):
        await render_tree(declared.Side(), context_args=context_args)


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


# What is drawn


class TestDrawn:
    @pytest.mark.asyncio
    async def test_the_sidebar_the_toolbar_and_the_calendar_hang_off_the_key(
        self, context_args
    ):
        html = await _drawn(
            _declared(layers=_LAYERS, search="Search events"), context_args
        )
        assert_attr(html, "aside#events-side", "x-sync")
        assert_attr(html, "#events-view", "x-sync")
        assert_selector(html, "#events-dialog")
        assert_attr(html, "form#events-search input[name=events-q]", "type", "search")
        assert_attr(html, "#events-matches", "role", "status")
        assert_selector(html, "form#events-options input[name=events-start]", count=7)
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
    async def test_without_a_search_there_is_no_box_and_no_count(self, context_args):
        html = await _drawn(_declared(), context_args)
        assert_no_selector(html, "#events-search")
        assert_no_selector(html, "#events-matches")

    @pytest.mark.asyncio
    async def test_a_hidden_layer_is_unticked_and_the_forms_carry_the_rest(
        self, context_args
    ):
        html = await _drawn(
            _declared(layers=_LAYERS, search="Search events"),
            context_args,
            **{"events-hide": "home", "events-view": "month"},
        )
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
        html = await _drawn(
            _declared(search="Search events"), context_args, **{"events-q": "re"}
        )
        assert select(html, "#events-matches")[0].get_text() == '1 event matches "re".'

    @pytest.mark.asyncio
    async def test_the_sidebar_names_the_timezone_when_the_framework_sets_one(self):
        oslo = ZoneInfo("Europe/Oslo")
        args = HueContextArgs(
            request=None,
            csrf_token="tok",
            formats=Formats(localize=lambda moment: moment.astimezone(oslo)),
        )
        html = await _drawn(_declared(), args)
        assert "Times in Europe/Oslo" in select(html, "#events-side")[0].get_text()
        # Without one the times are shown as given, and nothing is claimed.
        html = await _drawn(_declared(), HueContextArgs(request=None, csrf_token="t"))
        assert "Times in" not in html

    @pytest.mark.asyncio
    async def test_without_a_save_there_is_nothing_to_create_or_edit_with(
        self, context_args
    ):
        html = await _drawn(_declared(), context_args)
        assert_no_selector(html, "#events-new")
        assert_no_selector(html, "[aria-label='Delete event']")
        assert "x-on:click" not in select(html, "#events")[0].attrs
        assert "data-hue-refocus" not in select(html, "#events-dialog")[0].attrs

    @pytest.mark.asyncio
    async def test_with_handlers_the_popover_posts_the_event_back_under_the_key(
        self, context_args
    ):
        html = await _drawn(
            _declared(save=lambda r, e: None, delete=lambda r, i: None), context_args
        )
        assert_attr(html, "#events-new", "@click", "calendarCreate()")
        assert_attr(html, "#events", "x-on:click", "calendarSlot($event)")
        # Where focus goes when the dialog closes under it.
        assert_attr(html, "#events-dialog", "data-hue-refocus", "events-new")
        edits = [
            b
            for b in select(html, "button")
            if "/events/dialog/" in b.get("@click", "")
        ]
        # One event is in the week; the offsite is the week after.
        assert len(edits) == 1
        assert '"events-starts_time": "13:00"' in edits[0]["@click"]
        # Marked, so a failed copy redraws the calendar rather than opening
        # a dialog the reader never opened.
        copies = [b for b in select(html, "button") if "Duplicate" in b.get_text()]
        assert '"events-copy": "1"' in copies[0]["@click"]
        assert_selector(html, "[aria-label='Delete event']", count=1)

    @pytest.mark.asyncio
    async def test_a_click_handler_of_the_pages_own_is_kept(self, context_args):
        editable = _declared(save=lambda r, e: None)
        html = await render_tree(
            Calendar.from_state(editable).x_on("click", unsafe("mine()")),
            context_args=context_args,
        )
        assert_attr(html, "#events", "@click", "mine()")
        assert_attr(html, "#events", "x-on:click", "calendarSlot($event)")

    @pytest.mark.asyncio
    async def test_the_script_is_told_where_to_post_a_move_only_with_a_save(
        self, context_args
    ):
        html = await _drawn(_declared(save=lambda r, e: None), context_args)
        frame = select(html, "[x-data^=hueCalendar]")[0]["x-data"]
        assert '"move": "/events/move/"' in frame
        # The help's "a quarter hour" and the drag's snap are the one number.
        assert '"snap": 15' in frame
        assert select(html, "#events [data-resize]")
        assert_attr(html, "#events", "x-on:pointerdown", "calendarPress($event)")
        # Delete alone has no save to hand a moved event to.
        html = await _drawn(_declared(delete=lambda r, i: None), context_args)
        assert '"move": null' in select(html, "[x-data^=hueCalendar]")[0]["x-data"]
        assert_no_selector(html, "#events [data-resize]")
        assert_no_selector(html, "#events[x-on\\:pointerdown]")

    @pytest.mark.asyncio
    async def test_the_view_switcher_is_named_under_the_key(self, context_args):
        html = await _drawn(_declared(), context_args)
        assert _href(html, "events-switch-month") == "/events/?events-view=month"

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


# The keys


class _Keys(CalendarShortcuts):
    pass


class _Other(ShortcutRegistry):
    pass


class TestKeys:
    @pytest.fixture
    def _request(self):
        with scope.request_scope():
            yield

    @pytest.mark.asyncio
    async def test_the_keys_are_on_and_listed_when_the_registry_inherits_them(
        self, _request
    ):
        args = HueContextArgs(request=None, csrf_token="t", shortcuts=_Keys)
        html = await _drawn(_declared(save=lambda r, e: None, search="Search"), args)
        used = {item.shortcut.name: item.action for item in shortcuts.used()}
        assert used["calendar_today"] == (
            'document.getElementById("events-today")?.click()'
        )
        assert used["calendar_month"] == (
            'document.getElementById("events-switch-month")?.click()'
        )
        assert used["calendar_new"] == 'document.getElementById("events-new")?.click()'
        assert used["calendar_search"] == 'document.getElementById("events-q")?.focus()'
        assert "hue:open" in used["calendar_help"]
        # The help names each of them and the keys that move an event.
        help_ = select(html, "#events-help")[0]
        # Every control a key presses, focuses or opens is on the page.
        for action in used.values():
            for target in re.findall(r'getElementById\("([^"]+)"\)', action):
                assert select(html, f"#{target}"), target
        text = help_.get_text(" ", strip=True)
        assert "Go to today" in text and "Move it a day" in text
        assert (
            "Keyboard shortcuts" in select(html, "#events-options")[0].parent.get_text()
        )

    @pytest.mark.asyncio
    async def test_without_a_save_or_a_search_those_keys_stay_off(self, _request):
        args = HueContextArgs(request=None, csrf_token="t", shortcuts=_Keys)
        html = await _drawn(_declared(), args)
        names = {item.shortcut.name for item in shortcuts.used()}
        assert "calendar_today" in names
        assert not {"calendar_new", "calendar_search"} & names
        assert "Move it a day" not in select(html, "#events-help")[0].get_text()

    @pytest.mark.asyncio
    async def test_a_registry_without_the_keys_gets_none_and_no_help(self, _request):
        args = HueContextArgs(request=None, csrf_token="t", shortcuts=_Other)
        html = await _drawn(_declared(save=lambda r, e: None), args)
        assert shortcuts.used() == []
        assert_no_selector(html, "#events-help")
        assert "Keyboard shortcuts" not in html

    @pytest.mark.asyncio
    async def test_a_calendar_inside_an_async_component_still_binds_its_keys(
        self, _request
    ):
        class Late:
            def __init__(self, child: Any) -> None:
                self.child = child

            async def htmy(self, context: Any) -> Any:
                return self.child

        args = HueContextArgs(request=None, csrf_token="t", shortcuts=_Keys)
        page = _Page(title="Events", body=Late(Late(Calendar.from_state(_declared()))))
        rendered = await render_tree(page, context_args=args)
        assert_selector(rendered, "#hue-shortcuts button[x-on\\:click*='events-today']")

    @pytest.mark.asyncio
    async def test_of_two_calendars_on_a_page_the_first_drawn_has_the_keys(
        self, _request
    ):
        args = HueContextArgs(request=None, csrf_token="t", shortcuts=_Keys)
        rooms = build_calendar_state(_Router(), key="rooms", events=_events)
        page = _Page(
            title="Two",
            body=html.div(Calendar.from_state(_declared()), Calendar.from_state(rooms)),
        )
        rendered = await render_tree(page, context_args=args)
        today = [
            item.action
            for item in shortcuts.used()
            if item.shortcut is CalendarShortcuts.calendar_today
        ]
        assert today == ['document.getElementById("events-today")?.click()']
        # Only the one the keys drive offers their help.
        assert_selector(rendered, "#events-help")
        assert_no_selector(rendered, "#rooms-help")
