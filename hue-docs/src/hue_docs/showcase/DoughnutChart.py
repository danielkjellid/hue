"""
Curated showcases for DoughnutChart, which has no axis to toggle.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        variants=[
            variant(
                "Payment methods",
                """
                (
                    DoughnutChart()
                    .slices([("Card", 412), ("Invoice", 191), ("Transfer", 107)])
                    .description("Card is the most used way to pay, at 58%.")
                )
                """,
            ),
        ],
    ),
]
