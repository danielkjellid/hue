from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs

import pytest
from playwright.sync_api import Page

from hue.calendar import build_calendar_state
from hue.ui import Calendar, Event
from tests.browser.conftest import ORIGIN, Show

_STAY = Event("Lise", datetime(2026, 10, 16, 15), datetime(2026, 10, 19, 11))


def _box(page: Page, selector: str) -> dict[str, float]:
    box = page.locator(selector).first.bounding_box()
    assert box is not None, selector
    return box


def _edges(page: Page, selector: str, rtl: bool) -> tuple[float, float]:
    """
    Where something starts and ends along the line of reading, from the
    page's start edge.
    """
    box = _box(page, selector)
    width = page.evaluate("document.documentElement.clientWidth")
    if rtl:
        return width - box["x"] - box["width"], width - box["x"]
    return box["x"], box["x"] + box["width"]


def test_a_bar_runs_unbroken_across_the_cells_of_its_week(show: Show) -> None:
    offsite = Event("Offsite", date(2026, 10, 12), date(2026, 10, 20))
    page = show(Calendar().view("month").date(date(2026, 10, 14)).events([offsite]))
    first = page.locator("button[aria-label^='Offsite,']")
    assert first.count() == 2
    bar = first.nth(0).bounding_box()
    monday = _box(page, "td[data-date='2026-10-12']")
    sunday = _box(page, "td[data-date='2026-10-18']")
    assert bar is not None
    # From inside Monday's padding to Sunday's far edge, over every rule
    # between, since it goes on into the next week.
    assert abs(bar["x"] - (monday["x"] + 4)) <= 1.5
    assert abs(bar["x"] + bar["width"] - (sunday["x"] + sunday["width"])) <= 1.5
    # The next week's bar starts at its row's edge and stops inside Tuesday.
    after = first.nth(1).bounding_box()
    next_monday = _box(page, "td[data-date='2026-10-19']")
    tuesday = _box(page, "td[data-date='2026-10-20']")
    assert after is not None
    assert abs(after["x"] - next_monday["x"]) <= 1.5
    inside_tuesday = tuesday["x"] + tuesday["width"] - 4
    assert abs(after["x"] + after["width"] - inside_tuesday) <= 1.5


@pytest.mark.parametrize(("width", "direction"), [(1280, "ltr"), (320, "rtl")])
def test_a_bar_by_its_times_starts_and_ends_that_far_into_its_days(
    show: Show, width: int, direction: str
) -> None:
    calendar = Calendar().view("month").date(date(2026, 10, 14))
    page = show(
        calendar.events([_STAY]).spans("times"),
        width=width,
        dir=direction,
    )
    rtl = direction == "rtl"
    start, _ = _edges(page, "button[aria-label^='Lise,'] >> nth=0", rtl)
    friday, saturday = (
        _edges(page, f"td[data-date='2026-10-{day}']", rtl)[0] for day in (16, 17)
    )
    # 15:00 is five eighths of the way from Friday's edge to Saturday's.
    assert abs(start - (friday + (saturday - friday) * 15 / 24)) <= 1.5
    _, end = _edges(page, "button[aria-label^='Lise,'] >> nth=1", rtl)
    monday, tuesday = (
        _edges(page, f"td[data-date='2026-10-{day}']", rtl)[0] for day in (19, 20)
    )
    assert abs(end - (monday + (tuesday - monday) * 11 / 24)) <= 1.5


def test_a_bar_by_its_times_sits_that_far_into_its_week_columns(show: Show) -> None:
    calendar = Calendar().view("week").date(date(2026, 10, 14))
    page = show(calendar.events([_STAY]).spans("times"))
    start, _ = _edges(page, "button[aria-label^='Lise,']", rtl=False)
    friday, saturday = (
        _edges(page, f"[data-timed][data-date='2026-10-{day}']", rtl=False)[0]
        for day in (16, 17)
    )
    # Along the all-day row, out of the hours, from 15:00 on Friday.
    assert page.locator("[data-all-day-row] button[aria-label^='Lise,']").count() == 1
    assert abs(start - (friday + (saturday - friday) * 15 / 24)) <= 1.5


class _Router:
    """
    Just enough router to declare a calendar that moves its events: its
    route is the one the test answers.
    """

    def fragment_post(self, path: str) -> Any:
        return lambda handler: handler

    def _path_param(self, name: str) -> str:
        return f"<{name}>"

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {"events-view": ["month"]}

    def _get_form_values(self, request: Any) -> dict[str, list[str]]:
        return {}

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        return f"/events/{params['action']}/" if params else "/"

    def _refusal(self, error: Exception) -> None:
        return None

    def _csrf_field(self) -> None:
        return None

    async def _run_sync(self, func: Any, /, *args: Any) -> Any:
        return func(*args)


def test_a_bar_moves_by_the_days_from_where_it_was_taken_hold_of(show: Show) -> None:
    monday = date.today() - timedelta(days=date.today().weekday())
    tuesday, thursday, friday = (monday + timedelta(days=n) for n in (1, 3, 4))
    bar = Event("Offsite", tuesday, friday, id="7")
    declared = build_calendar_state(
        _Router(), key="events", events=lambda r, s: [bar], save=lambda r, e: None
    )
    page = show(Calendar.from_state(declared))
    page.route(
        f"{ORIGIN}/events/move/",
        lambda route: route.fulfill(
            body='<div id="events-dialog"></div>', content_type="text/html"
        ),
    )
    held = page.locator("button[aria-label^='Offsite,']").bounding_box()
    assert held is not None
    y = held["y"] + held["height"] / 2

    def middle(day: date) -> float:
        cell = page.locator(f"td[data-drop][data-date='{day}']").bounding_box()
        assert cell is not None
        return cell["x"] + cell["width"] / 2

    # Taken hold of on Thursday, over the bar's own cell, and let go on
    # Friday, where the bar still lies: one day on.
    page.mouse.move(middle(thursday), y)
    page.mouse.down()
    page.mouse.move(middle(thursday) + 12, y, steps=3)
    page.mouse.move(middle(friday), y, steps=6)
    with page.expect_request(f"{ORIGIN}/events/move/") as posted:
        page.mouse.up()
    moved = parse_qs(posted.value.post_data or "")
    assert moved["events-starts"] == [(tuesday + timedelta(days=1)).isoformat()]
