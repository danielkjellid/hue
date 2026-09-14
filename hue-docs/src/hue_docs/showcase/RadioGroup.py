"""
Curated showcases for the RadioGroup atom.

The auto-grid can toggle the axes but has no options to put inside, which is
most of what a radio group is.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "A fieldset with a legend, so the question is announced with each "
            'option - "Region, Europe" rather than "Europe" on its own. The '
            "group owns the name and the selection; an option carries its "
            "value and its text."
        ),
        variants=[
            variant(
                "Inline",
                """
                (
                    RadioGroup("region")
                    .legend("Region")
                    .value("eu")
                    .content(
                        Radio().value("eu").label("Europe"),
                        Radio().value("us").label("North America"),
                        Radio().value("ap").label("Asia Pacific"),
                    )
                )
                """,
            ),
            variant(
                "With descriptions",
                """
                (
                    RadioGroup("plan")
                    .legend("Plan")
                    .value("team")
                    .content(
                        Radio()
                        .value("solo")
                        .label("Solo")
                        .description("One seat, no shared workspaces."),
                        Radio()
                        .value("team")
                        .label("Team")
                        .description("Up to 20 seats and shared billing."),
                    )
                )
                """,
            ),
            variant(
                "As cards",
                """
                (
                    RadioGroup("plan")
                    .legend("Plan")
                    .variant("card")
                    .value("team")
                    .content(
                        Radio()
                        .value("solo")
                        .label("Solo")
                        .description("One seat, no shared workspaces."),
                        Radio()
                        .value("team")
                        .label("Team")
                        .description("Up to 20 seats and shared billing."),
                    )
                )
                """,
            ),
            variant(
                "Invalid",
                """
                (
                    RadioGroup("region")
                    .legend("Region")
                    .required()
                    .error("Pick a region to continue.")
                    .content(
                        Radio().value("eu").label("Europe"),
                        Radio().value("us").label("North America"),
                    )
                )
                """,
            ),
        ],
    ),
]
