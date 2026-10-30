"""
Curated showcases for AreaChart, which has no axis to toggle: what
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
                "Against last week",
                """
                (
                    AreaChart()
                    .labels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
                    .series(
                        [3100, 3400, 3200, 4100, 3900, 4600, 4829], label="This week"
                    )
                    .compare(
                        [2900, 3000, 2800, 3300, 3100, 3600, 3700], label="Last week"
                    )
                    .y_format("currency", currency="USD")
                    .description("Revenue rose from 3,100.00 USD to 4,829.00 USD.")
                )
                """,
            ),
        ],
    ),
]
