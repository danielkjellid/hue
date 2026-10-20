"""
Curated showcases for the DatePicker molecule.

The auto-grid starts every picker on today with nothing selected, which
shows no range, no markers and no refused days. These start with a value,
so each one opens on the month it is about.
"""

from __future__ import annotations

from datetime import date

from hue_docs.showcase import Showcase, variant

_NAMES = {"date": date}

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Click a day or move to it with the arrow keys and press Enter. "
            "Page Up and Page Down change the month, with Shift the year, and "
            "the month's title jumps to a month or a year."
        ),
        variants=[
            variant(
                "A range over two months",
                """
                (
                    DatePicker().name("stay")
                    .label("Stay")
                    .mode("range")
                    .months(2)
                    .value(date(2026, 10, 27), date(2026, 11, 3))
                )
                """,
                _NAMES,
            ),
            variant(
                "Several days",
                """
                (
                    DatePicker().name("shifts")
                    .label("Shifts")
                    .mode("multiple")
                    .value(date(2026, 10, 6), date(2026, 10, 8), date(2026, 10, 13))
                )
                """,
                _NAMES,
            ),
            variant(
                "Weekends and a holiday refused",
                """
                (
                    DatePicker().name("delivery")
                    .label("Delivery day")
                    .min(date(2026, 12, 1))
                    .max(date(2026, 12, 31))
                    .unavailable("saturday", "sunday", date(2026, 12, 25))
                    .value(date(2026, 12, 3))
                )
                """,
                _NAMES,
            ),
            variant(
                "Small, with markers",
                """
                (
                    DatePicker().name("agenda_day")
                    .label("Agenda")
                    .size("sm")
                    .week_start("sunday")
                    .markers(date(2026, 10, 2), date(2026, 10, 14), date(2026, 10, 19))
                    .value(date(2026, 10, 19))
                )
                """,
                _NAMES,
            ),
            variant(
                "Inside a dialog",
                """
                (
                    Dialog()
                    .title("Reschedule")
                    .trigger(Button().variant("secondary").content("Reschedule"))
                    .content(
                        DatePicker().name("new_day")
                        .label("New day")
                        .value(date(2026, 10, 22))
                    )
                )
                """,
                _NAMES,
            ),
        ],
    ),
    Showcase(
        title="Binding the value",
        layout="stack",
        description=(
            "x_model binds the selection as a list of ISO dates in every mode: "
            "one for a single day, the start and the end for a range."
        ),
        variants=[
            variant(
                "Read back as you pick",
                """
                (
                    Stack().x_data({"days": []}).content(
                        DatePicker().name("bound_range")
                        .label("Trip")
                        .mode("range")
                        .x_model(unsafe("days")),
                        Text().x_text(unsafe("'Picked: ' + days.join(' to ')")),
                    )
                )
                """,
            ),
        ],
    ),
]
