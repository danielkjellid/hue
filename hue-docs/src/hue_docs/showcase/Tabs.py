"""
Curated showcases for the Tabs molecule.

The auto-grid toggles the variant on one row; what it cannot show is a tab
carrying a count, or a section there is nothing in yet.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "A row of links to the sections of one thing. Tabs navigate, so "
            "each one is a real link to a real URL - it opens in a new tab, "
            "sends to somebody and answers the back button, and what it "
            "shows is whatever that page renders. The page you are on is "
            "given once, and the tab that leads there marks itself, "
            "including on the pages inside it. The segmented variant wears "
            "the same track as SegmentedControl - they look alike and mean "
            "different things, one a set of choices and this a set of "
            "places."
        ),
        variants=[
            variant(
                "Underline",
                """
                (
                    Tabs()
                    .label("Invoice sections")
                    .current("/invoices/2050/lines")
                    .content(
                        Tab().href("/invoices/2050").exact().content("Overview"),
                        Tab()
                        .href("/invoices/2050/lines")
                        .content("Line items", Badge().content("3")),
                        Tab().href("/invoices/2050/history").content("History"),
                        Tab().href("/invoices/2050/disputes").disabled().content(
                            "Disputes"
                        ),
                    )
                )
                """,
            ),
            variant(
                "Segmented",
                """
                (
                    Tabs()
                    .variant("segmented")
                    .label("Date range")
                    .current("/reports/week")
                    .content(
                        Tab().href("/reports/day").content("Day"),
                        Tab().href("/reports/week").content("Week"),
                        Tab().href("/reports/month").content("Month"),
                    )
                )
                """,
            ),
        ],
    ),
]
