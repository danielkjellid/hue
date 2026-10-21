"""
Every view over one set of events, a weekdays-only month, and an empty agenda.
"""

from __future__ import annotations

from datetime import date, datetime

from hue_docs.showcase import Showcase, variant

_NS = {"date": date, "datetime": datetime}

_EVENTS = """
        [
            Event(
                "Standup",
                datetime(2026, 10, 12, 9),
                datetime(2026, 10, 12, 9, 15),
                id="1",
                recurring=True,
                location="Huddle room",
                color=6,
            ),
            Event(
                "Design review",
                datetime(2026, 10, 14, 13),
                datetime(2026, 10, 14, 14, 30),
                id="2",
                location="Room 3B",
                notes="Walk the range state matrix and the contrast audit.",
                href="#design-review",
            ),
            Event(
                "Contrast audit",
                datetime(2026, 10, 15, 10),
                datetime(2026, 10, 15, 12),
                id="3",
                color=2,
            ),
            Event(
                "Pairing: range selection",
                datetime(2026, 10, 15, 11),
                datetime(2026, 10, 15, 12, 30),
                id="4",
                color=2,
            ),
            Event(
                "Token naming workshop",
                datetime(2026, 10, 15, 11, 30),
                datetime(2026, 10, 15, 12, 15),
                id="5",
                color=3,
            ),
            Event(
                "Dentist",
                datetime(2026, 10, 15, 15),
                datetime(2026, 10, 15, 15, 45),
                id="6",
                color=5,
            ),
            Event(
                "Release 2.4 freeze",
                date(2026, 10, 16),
                date(2026, 10, 17),
                id="7",
                color=4,
            ),
            Event(
                "Quarterly planning",
                date(2026, 10, 8),
                date(2026, 10, 9),
                id="8",
                color=4,
            ),
            Event(
                "Time off",
                date(2026, 10, 26),
                date(2026, 10, 30),
                id="9",
                color=5,
            ),
            Event(
                "Deploy window",
                datetime(2026, 10, 16, 22),
                datetime(2026, 10, 17, 2),
                id="10",
                color=2,
            ),
        ]
"""


def _calendar(key: str, view: str, day: str, extra: str = "") -> str:
    return f"""
    (
        Calendar()
        .id("cal-{key}")
        .view("{view}")
        .date({day})
        .today(date(2026, 10, 14))
        .href(lambda day, view: f"#{{view}}/{{day}}"){extra}
        .events({_EVENTS.strip()}
        )
    )
    """


SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "The same events in each view. href() is a function from a day "
            "and a view to a URL; everything that navigates is a link to it, "
            "so the calendar works without JavaScript, and with an id the "
            "links swap the calendar in place. An event opens a popover with "
            "its details. Times follow Formats.time from the context, so a "
            "12-hour clock is a setting rather than an option here."
        ),
        variants=[
            variant("Week", _calendar("week", "week", "date(2026, 10, 14)"), _NS),
            variant("Day", _calendar("day", "day", "date(2026, 10, 15)"), _NS),
            variant("Month", _calendar("month", "month", "date(2026, 10, 1)"), _NS),
            variant(
                "Weekdays only",
                _calendar(
                    "weekdays", "month", "date(2026, 10, 1)", "\n        .weekdays()"
                ),
                _NS,
            ),
            variant("Year", _calendar("year", "year", "date(2026, 10, 1)"), _NS),
            variant("Agenda", _calendar("agenda", "agenda", "date(2026, 10, 12)"), _NS),
            variant(
                "Nothing scheduled",
                """
                (
                    Calendar()
                    .id("cal-empty")
                    .view("agenda")
                    .date(date(2026, 12, 1))
                    .href(lambda day, view: f"#{view}/{day}")
                )
                """,
                _NS,
            ),
        ],
    ),
]
