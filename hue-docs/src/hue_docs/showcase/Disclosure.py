"""
Curated showcases for the Disclosure molecule.

The auto-grid toggles one of these; what it cannot show is a run of them
folding a long form into sections, which is what they are for.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Sections of a form",
        layout="stack",
        description=(
            "Each one answers to nothing else on the page, so any number can "
            "be open at once - that is the difference from an Accordion, "
            "which exists to agree on how many stay open. The trigger is a "
            "button inside a heading rather than a link: a link that toggles "
            "something tells a screen reader the wrong thing about what "
            "pressing it does."
        ),
        variants=[
            variant(
                "A long form, folded",
                """
                Stack().spacing("lg").align_items("items-stretch").content(
                    Disclosure()
                    .title("General")
                    .open()
                    .content(
                        Stack().spacing("md").align_items("items-stretch").content(
                            TextInput()
                            .name("product_name")
                            .label("Name")
                            .required()
                            .hint("Give your product a short and clear name."),
                            Textarea()
                            .name("product_description")
                            .label("Description")
                            .rows(3)
                            .hint("120-160 characters reads well in search results."),
                        )
                    ),
                    Disclosure()
                    .title("Pricing")
                    .content(
                        Stack().spacing("md").align_items("items-stretch").content(
                            NumberInput()
                            .name("price")
                            .label("Price")
                            .prefix("$")
                            .value("49"),
                            Switch()
                            .name("subscription")
                            .label("Bill monthly")
                            .description("Charge the customer every 30 days."),
                        )
                    ),
                    Disclosure()
                    .title("Search engines")
                    .content(
                        TextInput()
                        .name("slug")
                        .label("URL slug")
                        .prefix("northwind.com/")
                        .value("acoustic-guitar")
                    ),
                )
                """,
            ),
        ],
    ),
]
