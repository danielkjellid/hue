"""
Curated showcases for the TimeInput molecule.

The auto-grid starts every field empty. These start with a value, so the
list opens on it.
"""

from __future__ import annotations

from datetime import time

from hue_docs.showcase import Showcase, variant

_NAMES = {"time": time}

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Type 14:30, 1430, 2:30 pm or 9a, or pick from the list with the "
            "arrow keys, Home and End."
        ),
        variants=[
            variant(
                "With a value",
                """
                TimeInput().name("reminder").label("Reminder").value(time(14, 30))
                """,
                _NAMES,
            ),
            variant(
                "Every five minutes",
                """
                TimeInput().name("alarm").label("Alarm").step(5)
                """,
            ),
        ],
    ),
]
