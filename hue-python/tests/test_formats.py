from datetime import UTC, datetime, timedelta, timezone

from hue.formats import Formats


def test_an_aware_moment_is_localized_when_told_how():
    oslo = timezone(timedelta(hours=1))
    formats = Formats(localize=lambda moment: moment.astimezone(oslo))
    assert formats.text(datetime(2026, 3, 1, 12, 0, tzinfo=UTC)) == "2026-03-01 13:00"
    # Only an aware datetime has a zone to convert from.
    assert formats.text(datetime(2026, 3, 1, 12, 0)) == "2026-03-01 12:00"


def test_an_aware_moment_keeps_its_own_zone_otherwise():
    assert Formats().text(datetime(2026, 3, 1, 12, 0, tzinfo=UTC)) == "2026-03-01 12:00"


def test_anything_else_has_no_spelling_here():
    assert Formats().text(object()) is None
