"""
Curated showcases for ScatterChart.

It has no axis to toggle: what changes the drawing is the data, such as a
second series.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        variants=[
            variant(
                "Two series",
                """
                (
                    ScatterChart()
                    .series(
                        [(12, 0.18), (25, 0.22), (31, 0.35), (44, 0.41), (58, 0.47)],
                        label="Online",
                    )
                    .series(
                        [(9, 0.12), (20, 0.15), (36, 0.21), (47, 0.26)],
                        label="In store",
                    )
                    .x_label("Basket size")
                    .y_label("Margin")
                    .x_format("currency", currency="EUR")
                    .y_format("percent")
                    .description("Margin grows with basket size, faster online.")
                )
                """,
            ),
        ],
    ),
]
