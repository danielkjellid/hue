"""
The state a declared calendar reads off a request, on its own. The routes
and the drawing are tested against a real Django view in hue-django.
"""

from datetime import date
from typing import Any

import pytest

from hue.calendar import CalendarState, DayAction, build_calendar_state


def test_first_and_last_cover_the_whole_weeks_the_month_touches():
    monday = CalendarState(date(2026, 10, 1))
    assert (monday.first, monday.last) == (date(2026, 9, 28), date(2026, 11, 1))
    sunday = CalendarState(date(2026, 10, 1), "sunday")
    assert (sunday.first, sunday.last) == (date(2026, 9, 27), date(2026, 10, 31))


def test_the_month_is_its_first_day():
    with pytest.raises(ValueError, match="first of the month"):
        CalendarState(date(2026, 10, 14))


class _Router:
    """
    Just enough router to build a declaration against.
    """

    def __init__(self) -> None:
        self.registered: list[tuple[str, str]] = []

    def fragment_get(self, path: str, *, name: str | None = None) -> Any:
        self.registered.append((path, name or ""))
        return lambda view_func: view_func

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {}

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        return "/"

    async def _run_sync(self, func: Any, /, *args: Any) -> Any:
        return func(*args)


def _declared(**given: Any) -> Any:
    return build_calendar_state(
        _Router(), key="bookings", events=lambda request, shown: [], **given
    )


_TODAY = date(2026, 10, 14)


@pytest.mark.parametrize(
    "typed",
    [
        None,
        "",
        "2026-13",
        "2026-00",
        "2026-1",
        "2026-10-14",
        "0001-01",
        "9999-12",
        "abc",
    ],
)
def test_a_month_that_is_not_one_is_todays(typed):
    values = {} if typed is None else {"bookings-month": [typed]}
    month, _ = _declared()._read(values, _TODAY)
    assert month == date(2026, 10, 1)


def test_a_month_that_is_one_is_read_and_the_last_value_wins():
    month, _ = _declared()._read({"bookings-month": ["2026-01", "2027-03"]}, _TODAY)
    assert month == date(2027, 3, 1)


def test_everything_else_in_the_query_rides_along_in_order():
    _, others = _declared()._read(
        {"tab": ["a", "b"], "bookings-month": ["2026-03"], "other-month": ["x"]},
        _TODAY,
    )
    assert others == (("tab", "a"), ("tab", "b"), ("other-month", "x"))


def test_a_key_is_required():
    with pytest.raises(ValueError, match="key"):
        build_calendar_state(_Router(), key="", events=lambda request, shown: [])


def test_a_day_action_needs_a_label():
    with pytest.raises(ValueError, match="blank label"):
        _declared(day=DayAction("  ", lambda request, day: ""))


def test_the_day_route_is_registered_only_with_a_day_action():
    router = _Router()
    build_calendar_state(router, key="bookings", events=lambda r, s: [])
    assert router.registered == []
    build_calendar_state(
        router,
        key="rooms",
        events=lambda r, s: [],
        day=DayAction("Book", lambda request, day: ""),
    )
    assert router.registered == [("rooms/day/", "rooms_day")]
