"""
Curated showcases for the Drawer molecule.

The auto-grid has the sides and the sizes, but a drawer is a trigger, a
panel's worth of content and a way to answer it, and it can assemble none of
those.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="row",
        description=(
            "Narrow the window below md and both of these become the same "
            "bottom sheet: a 420px panel on a 375px screen is a dialog with a "
            "worse animation. Focus is trapped while one is up and returns to "
            "the trigger when it closes; Escape always closes. The footer "
            "actions call close(), like a dialog's."
        ),
        variants=[
            variant(
                "A filter panel",
                """
                (
                    Drawer()
                    .title("Filters")
                    .description("3 filters applied, 148 of 2,481 records")
                    .trigger(Button().variant("outline").content("Open side drawer"))
                    .content(
                        Stack().spacing("lg").content(
                            RadioGroup()
                            .name("drawer_status")
                            .legend("Status")
                            .value("paid")
                            .content(
                                Radio().value("paid").label("Paid (1,904)"),
                                Radio().value("pending").label("Pending (412)"),
                                Radio().value("refunded").label("Refunded (118)"),
                            ),
                            Slider()
                            .name("drawer_amount")
                            .label("Amount")
                            .min(0)
                            .max(5000)
                            .step(50)
                            .value(600)
                            .show_value()
                            .hint("Minimum transaction amount."),
                            NativeSelect()
                            .name("drawer_period")
                            .label("Period")
                            .options(
                                [
                                    ("30", "Last 30 days"),
                                    ("90", "Last 90 days"),
                                    ("ytd", "Year to date"),
                                ]
                            ),
                        )
                    )
                    .footer(
                        Button().variant("ghost").content("Reset all"),
                        Button()
                        .content("Show 148 records")
                        .x_on("click", "close()"),
                    )
                )
                """,
            ),
            variant(
                "A bottom sheet",
                """
                (
                    Drawer()
                    .side("bottom")
                    .title("INV-2048")
                    .description("$1,200.00 - paid 12 Sep 2026")
                    .trigger(Button().variant("outline").content("Open bottom sheet"))
                    .content(
                        Table().content(
                            TableBody().content(
                                TableRow().content(
                                    TableCell().content("Customer"),
                                    TableCell().content("Northwind Traders"),
                                ),
                                TableRow().content(
                                    TableCell().content("Payment method"),
                                    TableCell().content("Visa ending 4242"),
                                ),
                                TableRow().content(
                                    TableCell().content("Status"),
                                    TableCell().content(
                                        Badge().variant("success").dot().content("Paid")
                                    ),
                                ),
                            )
                        )
                    )
                    .footer(
                        Button()
                        .variant("outline")
                        .content("Close")
                        .x_on("click", "close()"),
                        Button().content("Download PDF"),
                    )
                )
                """,
            ),
        ],
    ),
]
