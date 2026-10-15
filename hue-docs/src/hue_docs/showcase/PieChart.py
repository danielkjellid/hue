"""
Curated showcases for PieChart.

It has no axis to toggle, and the grouping of small slices is the part
worth seeing.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        variants=[
            variant(
                "Pie",
                """
                (
                    PieChart()
                    .slices([
                        ("Paid", 92), ("Pending", 31), ("Draft", 14), ("Declined", 8)
                    ])
                    .description("Most invoices this month are paid: 92 of 145.")
                )
                """,
            ),
        ],
    ),
    Showcase(
        title="More slices than colours",
        description=(
            "The palette has six colours. Past six slices, the five largest "
            "are drawn and the rest share one slice called Other; the table "
            "a screen reader is given still lists all of them."
        ),
        variants=[
            variant(
                "Eight regions",
                """
                (
                    PieChart()
                    .slices([
                        ("North", 340), ("South", 280), ("East", 190),
                        ("West", 160), ("Central", 90), ("Islands", 30),
                        ("Coast", 20), ("Valley", 12),
                    ])
                    .value_format("currency", currency="EUR")
                    .description("North and South bring in over half of it.")
                )
                """,
            ),
        ],
    ),
]
