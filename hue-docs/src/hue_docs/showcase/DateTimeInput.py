"""
Curated showcases for the DateTimeInput molecule.

The auto-grid starts every field empty. These start with a value, so the
time list opens on it.
"""

from __future__ import annotations

from datetime import date, datetime

from hue_docs.showcase import Showcase, variant

_NAMES = {"date": date, "datetime": datetime}

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Type a day and a time, as in 2026-10-21 09:30 or "
            "tomorrow 2:30 pm, or pick them. Now picks the next time in "
            "the list."
        ),
        variants=[
            variant(
                "With a value",
                """
                (
                    DateTimeInput().name("publish_at")
                    .label("Publish at")
                    .value(datetime(2026, 10, 21, 9, 30))
                )
                """,
                _NAMES,
            ),
            variant(
                "Half hours from today",
                """
                (
                    DateTimeInput().name("call_at")
                    .label("Call at")
                    .step(30)
                    .min(date(2026, 10, 20))
                )
                """,
                _NAMES,
            ),
        ],
    ),
]
