"""
Curated showcases for the Skeleton atom.

The auto-grid shows each shape at its default size, which says nothing about
how to change it - the question the component actually raises.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Sizing",
        layout="stack",
        description=(
            "Every shape carries the size it usually stands in for, so most "
            "skeletons are one call. width() and height() replace either when "
            "the real content differs, and they are the same two controls for "
            "every shape. lines() is the one exception: it stacks text bars "
            "into a "
            "paragraph, and the other shapes reject it, since three circles on "
            "top of each other stand in for nothing."
        ),
        variants=[
            variant("Default size", 'Skeleton().shape("circle")'),
            variant(
                "Larger",
                'Skeleton().shape("circle").width("w-16").height("h-16")',
            ),
            variant("Shorter card", 'Skeleton().shape("card").height("h-20")'),
            variant("Half width", 'Skeleton().shape("rect").width("w-1/2")'),
            variant("A paragraph", 'Skeleton().shape("text").lines(3)'),
        ],
    ),
    Showcase(
        title="Standing in for content",
        layout="stack",
        description=(
            "The shape is the whole point: a skeleton has to occupy the same "
            "box as the content it is waiting for, or the page jumps when the "
            "data arrives - which is worse than having shown nothing at all."
        ),
        variants=[
            variant(
                "A list row",
                """
                (
                    Stack()
                    .horizontal()
                    .spacing("sm")
                    .align_items("items-center")
                    .content(
                        Skeleton().shape("circle"),
                        Skeleton().shape("text").lines(2).class_("flex-1"),
                    )
                )
                """,
            ),
            variant(
                "A card",
                """
                (
                    Stack()
                    .spacing("sm")
                    .content(
                        Skeleton().shape("card").height("h-24"),
                        Skeleton().shape("text").lines(2),
                    )
                )
                """,
            ),
        ],
    ),
]
