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
            "The variant decides how loudly it arrives: danger interrupts "
            'the screen reader with role="alert", the rest wait for a gap '
            'with role="status". Nothing is announced twice - a live region '
            "that exists with its content already in it is never announced, "
            "so one rendered with the page is simply read in order. Actions "
            "pair one solid or outline button with a ghost: two ghosts side "
            "by side read as floating text rather than as things to press."
        ),
        variants=[
            variant(
                "With a way out",
                """
                (
                    Alert()
                    .variant("danger")
                    .title("We could not charge your card")
                    .content("The bank declined the payment. Nothing was lost.")
                    .actions(
                        Button().variant("danger").size("sm").content("Try again"),
                        Button()
                        .variant("ghost")
                        .size("sm")
                        .content("Use another card"),
                    )
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
                    .content("You can invite people from the members page.")
                    .dismissible()
                )
                """,
            ),
            variant(
                "Anything under the title",
                """
                (
                    Alert()
                    .variant("warning")
                    .title("Two invoices are overdue")
                    .content(
                        Stack()
                        .direction("horizontal")
                        .justify_content("justify-between")
                        .align_items("items-center")
                        .content(
                            Text().variant("body").content("INV-2050 and INV-2051"),
                            Button().variant("outline").size("sm").content("Pay both"),
                        )
                    )
                )
                """,
            ),
            variant(
                "Title only",
                'Alert().variant("warning").title("Two invoices are overdue")',
            ),
        ],
    ),
]
