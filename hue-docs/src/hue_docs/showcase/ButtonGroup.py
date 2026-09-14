"""
Curated showcases for the ButtonGroup molecule.

The auto-grid can toggle the variant but has no buttons to put inside, and the
buttons are what makes the two variants read as different things.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "An attached group is buttons that happen to sit together, each "
            "doing its own thing. A segmented group is a choice where exactly "
            "one option is on - a radio group in a button costume - so it needs "
            "a label and an aria-pressed on each option. Do not reach for "
            "aria-selected there; that belongs to tabs and listbox options."
        ),
        variants=[
            variant(
                "Attached",
                """
                (
                    ButtonGroup().content(
                        Button().variant("outline").size("sm").content("Export"),
                        Button()
                        .variant("outline")
                        .size("sm")
                        .icon_only("Export options")
                        .content("v"),
                    )
                )
                """,
            ),
            variant(
                "Segmented",
                """
                (
                    ButtonGroup()
                    .variant("segmented")
                    .label("Date range")
                    .content(
                        Button().variant("ghost").size("sm").content("Day"),
                        Button().variant("ghost").size("sm").content("Week"),
                        Button().variant("ghost").size("sm").content("Month"),
                    )
                )
                """,
            ),
        ],
    ),
]
