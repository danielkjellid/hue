"""
Curated showcases for the DateInput molecule.

The auto-grid has the modes, sizes and states, each empty. These start
with a value or a refusal, so each one opens on what it is about.
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
            "Type a day and press Enter, or open the month with the button or "
            "the down arrow. Each one reads 2026-10-20, 20.10.2026, "
            "20 Oct 2026 and today, and keeps its value when the text is "
            "not a day it can read."
        ),
        variants=[
            variant(
                "A single day",
                """
                (
                    DateInput().name("due")
                    .label("Due date")
                    .hint("Any day from today.")
                    .min(date(2026, 10, 20))
                    .value(date(2026, 10, 30))
                )
                """,
                _NAMES,
            ),
            variant(
                "A range with presets",
                """
                (
                    DateInput().name("period")
                    .label("Reporting period")
                    .mode("range", presets=True)
                    .value(date(2026, 10, 14), date(2026, 10, 20))
                )
                """,
                _NAMES,
            ),
            variant(
                "Several days",
                """
                (
                    DateInput().name("blackout")
                    .label("Blackout dates")
                    .mode("multiple")
                    .value(date(2026, 10, 23), date(2026, 10, 30))
                )
                """,
                _NAMES,
            ),
            variant(
                "Weekdays in a booking window",
                """
                (
                    DateInput().name("visit")
                    .label("Visit date")
                    .hint("A weekday from 20 October to 18 December.")
                    .required()
                    .min(date(2026, 10, 20))
                    .max(date(2026, 12, 18))
                    .unavailable("saturday", "sunday")
                    .value(date(2026, 10, 21))
                )
                """,
                _NAMES,
            ),
            variant(
                "Invalid",
                """
                (
                    DateInput().name("expires")
                    .label("Expires")
                    .value(date(2026, 10, 1))
                    .error("Choose a date on or after 2026-10-20.")
                )
                """,
                _NAMES,
            ),
            variant(
                "Disabled and read-only",
                """
                Stack().content(
                    DateInput().name("locked").label("Locked")
                    .value(date(2026, 10, 20)).disabled(),
                    DateInput().name("signed").label("Signed on")
                    .value(date(2026, 10, 2)).readonly(),
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
                        DateInput().name("new_day")
                        .label("New day")
                        .value(date(2026, 10, 22)),
                        DateTimeInput().name("new_start")
                        .label("Starts"),
                    )
                )
                """,
                _NAMES,
            ),
        ],
    ),
    Showcase(
        title="In a form",
        layout="stack",
        description=(
            "What a form submits is ISO text under each field's name: one "
            "field for a day, two for a range, one per day of several."
        ),
        variants=[
            variant(
                "Submitted as ISO",
                """
                (
                    Form().action("#").content(
                        DateInput().name("trip")
                        .label("Trip")
                        .mode("range")
                        .value(date(2026, 11, 2), date(2026, 11, 6)),
                        DateInput().name("rest_days")
                        .label("Rest days")
                        .mode("multiple")
                        .value(date(2026, 11, 4)),
                        TimeInput().name("pickup").label("Pickup"),
                        Button().type("submit").content("Book"),
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
            "x_model binds the value as a list of ISO dates in every mode, "
            "whether it was picked or typed."
        ),
        variants=[
            variant(
                "Read back as you pick",
                """
                (
                    Stack().x_data({"days": []}).content(
                        DateInput().name("bound_days")
                        .label("Days off")
                        .mode("multiple")
                        .x_model(unsafe("days")),
                        Text().x_text(unsafe("'Picked: ' + days.join(', ')")),
                    )
                )
                """,
            ),
        ],
    ),
]
