"""
Curated showcases for the Alert molecule.

The auto-grid has the variants, but an alert is a title, a description and
sometimes a way out of the situation - none of which it can assemble.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            'role="alert" is not the default. An alert already on the page '
            "when it loads is read in order like any other text, and a live "
            "region would have it said a second time; live() is for one that "
            "arrives in response to something the user just did."
        ),
        variants=[
            variant(
                "With a way out",
                """
                (
                    Alert()
                    .variant("danger")
                    .title("We could not charge your card")
                    .description("The bank declined the payment. Nothing was lost.")
                    .actions(
                        Button().variant("ghost").size("sm").content("Try again"),
                        Button()
                        .variant("ghost")
                        .size("sm")
                        .content("Use another card"),
                    )
                    .live()
                )
                """,
            ),
            variant(
                "Dismissible",
                """
                (
                    Alert()
                    .variant("success")
                    .title("Workspace created")
                    .description("You can invite people from the members page.")
                    .dismissible()
                )
                """,
            ),
            variant(
                "Title only",
                'Alert().variant("warning").title("Two invoices are overdue")',
            ),
            variant(
                "As a page banner",
                """
                (
                    Alert()
                    .variant("info")
                    .title("Scheduled maintenance on Sunday")
                    .description("The API is read-only between 02:00 and 04:00 UTC.")
                    .banner()
                )
                """,
            ),
        ],
    ),
]
