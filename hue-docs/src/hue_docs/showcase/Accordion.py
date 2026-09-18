"""
Curated showcases for the Accordion molecule.

The auto-grid toggles the axes on one accordion; what it cannot show is the
pair side by side, which is the whole difference between the modes.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Each trigger is a real button inside a heading, which is how a "
            "screen reader jumps between sections, and each panel is named by "
            "the heading that opens it. Hover tints the label rather than the "
            "row: the row's fill is already carrying open and closed."
        ),
        variants=[
            variant(
                "One at a time",
                """
                (
                    Accordion()
                    .mode("single")
                    .content(
                        AccordionItem()
                        .title("How is usage calculated?")
                        .open()
                        .content(
                            "Metered per API call, aggregated hourly and billed "
                            "monthly in arrears. Failed requests that return 4xx "
                            "are not counted."
                        ),
                        AccordionItem()
                        .title("Can I change plans mid-cycle?")
                        .content(
                            "Upgrades take effect immediately and we prorate the "
                            "difference. Downgrades apply at the start of your "
                            "next billing period."
                        ),
                        AccordionItem()
                        .title("What happens if a payment fails?")
                        .content(
                            "We retry three times over eight days and email the "
                            "billing contact each time."
                        ),
                    )
                )
                """,
            ),
            variant(
                "Independent panels",
                """
                (
                    Accordion()
                    .variant("boxed")
                    .mode("multiple")
                    .content(
                        AccordionItem()
                        .title("Request headers")
                        .open()
                        .content(
                            "Authorization: Bearer <token> is required on every "
                            "endpoint. Idempotency-Key is optional but strongly "
                            "recommended on writes."
                        ),
                        AccordionItem()
                        .title("Rate limits")
                        .content(
                            "600 requests per minute per key, bursting to 1,000. "
                            "Exceeding it returns 429 with a Retry-After header."
                        ),
                        AccordionItem()
                        .title("Pagination")
                        .content(
                            "Cursor-based. Pass the next_cursor from the previous "
                            "response; offsets are not supported above 10,000 "
                            "records."
                        ),
                    )
                )
                """,
            ),
        ],
    ),
]
