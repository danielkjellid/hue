"""
Curated showcases for LineChart, which has no axis to toggle: what
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
                    LineChart()
                    .labels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
                    .series([212, 240, 198, 260, 251, 305, 330], label="This week")
                    .compare([190, 205, 201, 222, 230, 260, 270], label="Last week")
                    .description("Sign-ups rose from 212 to 330, above last week.")
                )
                """,
            ),
            variant(
                "One series, as percentages",
                """
                (
                    LineChart()
                    .labels(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])
                    .series([0.92, 0.94, 0.91, 0.96, 0.97, 0.98], label="Uptime")
                    .y_format("percent")
                    .description("Uptime climbed from 92% to 98% over six months.")
                )
                """,
            ),
        ],
    ),
]
