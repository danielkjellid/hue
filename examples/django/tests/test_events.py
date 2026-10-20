"""
The declared calendar against a real table: the occurrences a series
gives the days shown, what the search and the layers narrow, and what
the dialog's route writes.
"""

import re
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client

from example.events.models import Entry, _aware
from example.events.repeats import occurrences

_AJAX = {"HTTP_X_ALPINE_REQUEST": "true"}
_OSLO = ZoneInfo("Europe/Oslo")
# The week of 12 October 2026 in the URL, so the seeded entries are always on it.
_WEEK = {"events-date": "2026-10-14", "events-view": "week"}


def _at(*clock: int) -> datetime:
    return datetime(*clock, tzinfo=_OSLO)


@pytest.fixture
def entries(db: None) -> dict[str, Entry]:
    made = [
        Entry(title="Standup", layer="eng", starts=_at(2026, 9, 28, 9),
              ends=_at(2026, 9, 28, 9, 15), repeat="weekdays", location="Huddle room"),
        Entry(title="Design review", layer="product", starts=_at(2026, 10, 14, 13),
              ends=_at(2026, 10, 14, 14, 30), notes="Walk the matrix."),
        Entry(title="Release freeze", layer="eng", all_day=True,
              starts=_at(2026, 10, 16), ends=_at(2026, 10, 17)),
        Entry(title="Dentist", layer="personal", starts=_at(2026, 10, 15, 15),
              ends=_at(2026, 10, 15, 15, 45)),
    ]  # fmt: skip
    Entry.objects.bulk_create(made)
    return {entry.title: entry for entry in Entry.objects.all()}


def _titles(html: str) -> list[str]:
    return sorted(set(re.findall(r'aria-label="([^",]+),', html)))


def _read(**params: str) -> str:
    response = Client().get("/events/", {**_WEEK, **params}, **_AJAX)
    assert response.status_code == 200
    return response.content.decode()


def _act(action: str, **posted: Any) -> Any:
    """
    One of the route's actions, with the dialog's fields posted under the
    key as the dialog posts them.
    """
    fields = {f"events-{name}": value for name, value in posted.items()}
    return Client().post(f"/events/events/{action}/", {**_WEEK, **fields}, **_AJAX)


def test_the_page_draws_the_week_with_a_series_expanded_onto_its_days(entries):
    html = _read()
    assert "Design review" in html and "Dentist" in html and "Release freeze" in html
    # Five standups, Monday to Friday, from a series that began weeks before.
    assert html.count('aria-label="Standup,') == 5
    assert 'aria-label="Standup, Saturday' not in html


def test_the_search_and_the_layers_narrow_what_is_drawn(entries):
    assert _titles(_read(**{"events-q": "matrix"})) == ["Design review"]
    assert "Standup" not in _read(**{"events-hide": "eng"})
    assert "Dentist" in _read(**{"events-hide": "eng"})


def test_a_save_writes_an_aware_entry_and_the_dialog_edits_it(entries):
    response = _act(
        "save",
        title="Pairing",
        starts="2026-10-15",
        starts_time="11:00",
        ends="2026-10-15",
        ends_time="12:30",
        layer="eng",
        repeat="weekly",
    )
    assert response.status_code == 200
    made = Entry.objects.get(title="Pairing")
    assert made.starts == _at(2026, 10, 15, 11)
    assert made.repeat == "weekly"
    assert 'aria-label="Pairing,' in response.content.decode()

    review = entries["Design review"]
    moved = _act(
        "save",
        id=str(review.pk),
        title="Design review",
        starts="2026-10-16",
        starts_time="09:00",
        ends="2026-10-16",
        ends_time="10:00",
        layer="product",
    )
    assert moved.status_code == 200
    review.refresh_from_db()
    assert review.starts == _at(2026, 10, 16, 9)


def test_a_move_keeps_what_the_browser_never_had_and_undo_puts_it_back(entries):
    review = entries["Design review"]
    moved = _act(
        "move",
        id=str(review.pk),
        occurrence="2026-10-14T13:00",
        starts="2026-10-15",
        starts_time="09:00",
        ends="2026-10-15",
        ends_time="10:30",
    )
    assert moved.status_code == 200
    review.refresh_from_db()
    assert (review.starts, review.ends) == (
        _at(2026, 10, 15, 9),
        _at(2026, 10, 15, 10, 30),
    )
    assert review.notes == "Walk the matrix."
    # The toast's Undo posts a move back, which lands where it was.
    html = moved.content.decode()
    back = re.search(r'"events-starts_time": "(\d\d:\d\d)"[^}]*"events-undo"', html)
    assert back and back[1] == "13:00"
    _act(
        "move",
        id=str(review.pk),
        occurrence="2026-10-15T09:00",
        starts="2026-10-14",
        starts_time="13:00",
        ends="2026-10-14",
        ends_time="14:30",
        undo="1",
    )
    review.refresh_from_db()
    assert review.starts == _at(2026, 10, 14, 13)


def test_a_create_is_undone_by_the_key_save_returns(entries):
    made = _act("save", title="Pairing", starts="2026-10-15", starts_time="11:00",
                ends="2026-10-15", ends_time="12:30", layer="eng")  # fmt: skip
    pk = Entry.objects.get(title="Pairing").pk
    assert f'"events-id": "{pk}"' in made.content.decode()
    assert _act("delete", id=str(pk), undo="1").status_code == 200
    assert not Entry.objects.filter(title="Pairing").exists()


def test_the_calendars_keys_are_bound_on_the_page(entries):
    html = _read()
    assert 'id="hue-shortcuts"' in html
    assert "events-switch-month" in html and 'id="events-help"' in html


def test_a_field_that_cannot_be_read_is_an_error_and_writes_nothing(entries):
    response = _act("save", title="", starts="2026-10-15", ends="2026-10-15")
    assert response.status_code == 422
    assert "Give the event a title." in response.content.decode()
    assert Entry.objects.count() == 4


def test_a_delete_removes_the_entry_and_a_key_that_is_not_one_is_not_found(entries):
    assert _act("delete", id=str(entries["Dentist"].pk)).status_code == 200
    assert not Entry.objects.filter(title="Dentist").exists()
    assert _act("delete", id="abc").status_code == 404
    assert _act("delete", id="999999").status_code == 404


def test_a_stale_edit_is_not_found_and_says_so_on_the_page(entries):
    # The row went while the dialog was open: the dialog comes back over
    # what was typed, with a toast, rather than Django's 404 page.
    response = _act(
        "save",
        id="999999",
        title="Gone",
        starts="2026-10-15",
        starts_time="11:00",
        ends="2026-10-15",
        ends_time="12:30",
        layer="eng",
    )
    assert response.status_code == 404
    html = response.content.decode()
    assert "Save failed" in html and 'value="Gone"' in html
    assert not Entry.objects.filter(title="Gone").exists()


def test_a_series_that_began_years_ago_still_lands_on_the_days_asked_for(entries):
    standup = entries["Standup"]
    # Counted from near the week asked for rather than walked from 2026.
    found = list(occurrences(standup, date(9998, 12, 28), date(9999, 1, 3)))
    assert [event.starts.date() for event in found] == [
        date(9998, 12, 28) + timedelta(days=n) for n in range(5)
    ]
    # A long whole-day entry that started before the first day still counts.
    freeze = entries["Release freeze"]
    freeze.repeat = "weekly"
    found = list(occurrences(freeze, date(2026, 10, 17), date(2026, 10, 17)))
    assert [event.starts for event in found] == [date(2026, 10, 16)]


def test_a_monthly_series_from_two_years_ago_lands_on_its_day(entries):
    review = entries["Design review"]
    review.repeat = "monthly"
    review.starts, review.ends = _at(2024, 10, 14, 13), _at(2024, 10, 14, 14)
    found = list(occurrences(review, date(2026, 10, 12), date(2026, 10, 18)))
    assert [event.starts.date() for event in found] == [date(2026, 10, 14)]


def test_a_time_the_clocks_skip_is_refused_rather_than_moved(db):
    # Oslo goes forward at 02:00 on 29 March 2026.
    assert _aware(datetime(2026, 3, 29, 3, 30)) == _at(2026, 3, 29, 3, 30)
    with pytest.raises(ValueError, match="02:30 is skipped"):
        _aware(datetime(2026, 3, 29, 2, 30))
