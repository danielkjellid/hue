"""
The declared calendar against a real table: the occurrences a series
gives the days shown, what the search and the layers narrow, and what
the dialog's route writes.
"""

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from django.test import Client

from example.events.models import Entry

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
    return Client().post(f"/events/events/{action}/", {**_WEEK, **posted}, **_AJAX)


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
