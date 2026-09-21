"""
Curated showcases for the Tabs molecule.

The auto-grid toggles the variant on one set of tabs; what it cannot show is
a tab carrying a count, or one that cannot be reached.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "The arrow keys walk the row and the panel follows, which is what "
            "the tab role promises; only the selected tab is a tab stop, so "
            "Tab moves past the row rather than through it. The segmented "
            "variant wears the same track as SegmentedControl - they look "
            "alike and mean different things, one a set of toggles and this a "
            "list of panels."
        ),
        variants=[
            variant(
                "Underline",
                """
                (
                    Tabs()
                    .value("overview")
                    .content(
                        TabList()
                        .label("Invoice sections")
                        .content(
                            Tab().value("overview").label("Overview"),
                            Tab()
                            .value("lines")
                            .label("Line items")
                            .badge(Badge().content("3")),
                            Tab().value("history").label("History"),
                            Tab().value("disputes").label("Disputes").disabled(),
                        ),
                        TabPanel()
                        .value("overview")
                        .content("Paid 12 Sep 2026 by Northwind Traders."),
                        TabPanel()
                        .value("lines")
                        .content("Three lines, totalling $1,200.00."),
                        TabPanel()
                        .value("history")
                        .content("Sent, viewed twice, paid."),
                        TabPanel().value("disputes").content("Nothing to see."),
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
                    .value("week")
                    .content(
                        TabList()
                        .label("Date range")
                        .content(
                            Tab().value("day").label("Day"),
                            Tab().value("week").label("Week"),
                            Tab().value("month").label("Month"),
                        ),
                        TabPanel().value("day").content("Today so far."),
                        TabPanel().value("week").content("The last seven days."),
                        TabPanel().value("month").content("September."),
                    )
                )
                """,
            ),
        ],
    ),
]
