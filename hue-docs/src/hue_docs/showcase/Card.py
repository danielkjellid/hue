"""
Curated showcases for the Card molecule.

Card is assembled from slots rather than driven by axes, so the auto-grid has
only the variants to show and nothing to put inside them.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Cards sit flat on the canvas with a hairline border. Elevation is "
            "reserved for things that genuinely float, so reach for raised "
            "only when the card really is above the page - if everything "
            "lifts, nothing does."
        ),
        variants=[
            variant(
                "Bordered",
                """
                (
                    Card().content(
                        CardHeader()
                        .title("Monthly revenue")
                        .description("Last 30 days")
                        .content(Text().variant("body").muted().content("+12.4%")),
                        CardBody().content("$48,290"),
                    )
                )
                """,
            ),
            variant(
                "With a footer",
                """
                (
                    Card().content(
                        CardHeader()
                        .title("Invite teammates")
                        .description("They will get an email with a join link."),
                        CardBody().content("Anyone with the link can request access."),
                        CardFooter().content(
                            Button().variant("ghost").content("Cancel"),
                            Button().content("Send invites"),
                        ),
                    )
                )
                """,
            ),
            variant(
                "Every piece",
                """
                (
                    Card().content(
                        CardMedia().content(
                            html.img(src="/assets/cover.svg", alt="")
                        ),
                        CardHeader()
                        .title("Q3 revenue report")
                        .description("Published 14 September")
                        .content(Badge().content("New")),
                        CardBody().content(
                            "Revenue grew 12.4% against a flat quarter last year."
                        ),
                        CardFooter().content(
                            Button().variant("ghost").content("Dismiss"),
                            Button().content("Open report"),
                        ),
                    )
                )
                """,
            ),
            variant(
                "Flat",
                """
                (
                    Card()
                    .variant("flat")
                    .content(CardBody().content("Grouped inside another container."))
                )
                """,
            ),
        ],
    ),
    Showcase(
        title="Interactive",
        layout="stack",
        description=(
            "href() turns the title into a link and interactive() into a "
            "button, stretched over the card so a click anywhere on it lands. "
            "The title is the one tab stop and the name a screen reader "
            "reads, and a button of the card's own still works on top of it "
            "rather than nested inside it."
        ),
        variants=[
            variant(
                "As a link",
                """
                (
                    Card()
                    .href("/invoices/2050")
                    .content(
                        CardHeader()
                        .title("INV-2050")
                        .description("Contoso Ltd - $2,190.00"),
                    )
                )
                """,
            ),
            variant(
                "With its own actions",
                """
                (
                    Card()
                    .href("/reports/q3")
                    .content(
                        CardHeader()
                        .title("Q3 revenue report")
                        .description("Published 14 September"),
                        CardFooter().content(
                            Button().variant("ghost").content("Archive"),
                        ),
                    )
                )
                """,
            ),
        ],
    ),
]
