"""
Curated showcases for BarChart, which has no axis to toggle: what
changes the drawing is the data, a highlighted bar or a comparison.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        variants=[
            variant(
                "One bar highlighted",
                """
                (
                    BarChart()
                    .labels(["Paid", "Pending", "Draft", "Declined", "Refunded"])
                    .series([92, 31, 14, 8, 3], label="Invoices")
                    .highlight("Paid")
                    .description("Most invoices in September are paid: 92 of 148.")
                )
                """,
            ),
            variant(
                "Against last year",
                """
                (
                    BarChart()
                    .labels(["Q1", "Q2", "Q3", "Q4"])
                    .series([48, 52, 61, 70], label="2026")
                    .compare([41, 45, 50, 58], label="2025")
                    .description("Every quarter of 2026 beat the same quarter of 2025.")
                )
                """,
            ),
        ],
    ),
]
