"""
Curated showcases for the SegmentedControl molecule.

Its options are children, which the auto-grid cannot supply.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "A radio group wearing a button costume, so the control owns how "
            "its options look and marks the one matching value(). The label "
            "names the whole control, which is what tells a screen reader what "
            "is being chosen. Leave value() unset when something client-side "
            "decides, as ThemeSwitcher does."
        ),
        variants=[
            variant(
                "Date range",
                """
                (
                    SegmentedControl()
                    .label("Date range")
                    .value("week")
                    .content(
                        SegmentedOption().value("day").content("Day"),
                        SegmentedOption().value("week").content("Week"),
                        SegmentedOption().value("month").content("Month"),
                    )
                )
                """,
            ),
            variant(
                "Large",
                """
                (
                    SegmentedControl()
                    .label("Billing period")
                    .value("annual")
                    .size("lg")
                    .content(
                        SegmentedOption().value("monthly").content("Monthly"),
                        SegmentedOption().value("annual").content("Annual"),
                    )
                )
                """,
            ),
        ],
    ),
]
