"""
Curated showcases for the Empty molecule.

The three kinds differ mostly in their copy, which no axis can express, so they
are shown here written out.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="The three kinds",
        layout="stack",
        description=(
            "Nothing here yet, nothing matched, and we could not load this. "
            "Collapsing them is the usual mistake: an error rendered as "
            '"no results" tells the user to change their search when the '
            "server is actually down. Each one needs a way forward, and a "
            "no-results state should echo the query back."
        ),
        variants=[
            variant(
                "First use",
                """
                (
                    Empty()
                    .title("No invoices yet")
                    .description("Invoices appear here once your first order is paid.")
                    .actions(Button().content("Create invoice"))
                )
                """,
            ),
            variant(
                "No results",
                """
                (
                    Empty()
                    .compact()
                    .title('No results for "refund q3"')
                    .description("Try clearing the Declined filter.")
                    .actions(
                        Button().variant("outline").size("sm").content("Clear filters")
                    )
                )
                """,
            ),
            variant(
                "Could not load",
                """
                (
                    Empty()
                    .variant("danger")
                    .compact()
                    .title("Couldn't load invoices")
                    .description("Billing service didn't respond. Last tried 12s ago.")
                    .actions(
                        Button().variant("outline").size("sm").content("Try again"),
                        Button().variant("ghost").size("sm").content("Contact support"),
                    )
                )
                """,
            ),
        ],
    ),
]
