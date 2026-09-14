"""
Curated showcases for the Skeleton atom.

The auto-grid covers the shapes in isolation. This shows them assembled into
the box of a real component, which is the only thing that matters about a
skeleton and the one thing the grid cannot demonstrate.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Standing in for content",
        layout="stack",
        description=(
            "A skeleton has to occupy the same box as the content it is "
            "waiting for, or the page jumps when the data arrives - which is "
            "worse than having shown nothing at all. Size it with class_() "
            "when the default shape does not match."
        ),
        variants=[
            variant("Paragraph", 'Skeleton().shape("text").lines(3)'),
            variant("Avatar", 'Skeleton().shape("circle")'),
            variant("Card", 'Skeleton().shape("card")'),
            variant(
                "A list row",
                """
                (
                    Stack()
                    .direction("horizontal")
                    .spacing("sm")
                    .align_items("items-center")
                    .content(
                        Skeleton().shape("circle"),
                        Skeleton().shape("text").lines(2).class_("flex-1"),
                    )
                )
                """,
            ),
        ],
    ),
]
