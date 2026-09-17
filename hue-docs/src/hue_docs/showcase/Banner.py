"""
Curated showcases for the Banner molecule.

Everything an Alert can do, in the shape a page-level message takes - so the
examples here are about where it sits rather than about what it can hold.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "An Alert underneath, so every variant, action and announcement "
            "rule is the same. Squared off with no side borders, because a "
            "message about the whole page belongs to the frame rather than to "
            "the content inside it."
        ),
        variants=[
            variant(
                "Scheduled work",
                """
                (
                    Banner()
                    .variant("info")
                    .title("Scheduled maintenance on Sunday")
                    .description("The API is read-only between 02:00 and 04:00 UTC.")
                )
                """,
            ),
            variant(
                "Needs an answer",
                """
                (
                    Banner()
                    .variant("warning")
                    .title("Your trial ends on Friday")
                    .actions(
                        Button().variant("outline").size("sm").content("Add billing")
                    )
                    .dismissible()
                )
                """,
            ),
        ],
    ),
]
