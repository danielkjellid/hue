"""
Curated showcases for BubbleChart, which has no axis to toggle: what
changes the drawing is the data.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        variants=[
            variant(
                "Teams",
                """
                (
                    BubbleChart()
                    .series(
                        [(2, 40, 120), (5, 55, 340), (8, 48, 90), (11, 70, 410)],
                        label="Teams",
                    )
                    .x_label("Engineers")
                    .y_label("Deploys per week")
                    .size_label("Incidents fixed")
                    .description("Larger teams deploy more and fix more incidents.")
                )
                """,
            ),
        ],
    ),
]
