"""
Curated showcases for the Avatar atom.

The auto-grid covers sizes, shapes and statuses one at a time. These show the
combinations that actually appear in a product.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Initials are the default rather than the fallback: most people "
            "have no photo, and a grid of identical grey silhouettes says "
            "nothing. The status dot is visual only, so it folds into the "
            'avatar\'s own label - "Grace Hopper, online" - instead of sitting '
            "alongside as a second thing to announce."
        ),
        variants=[
            variant("Initials", 'Avatar().name("Ada Lovelace")'),
            variant(
                "With a picture",
                'Avatar().name("Ada Lovelace").src("https://i.pravatar.cc/128?img=5")',
            ),
            variant("Online", 'Avatar().name("Grace Hopper").status("online")'),
            variant("Busy", 'Avatar().name("Alan Turing").size("lg").status("busy")'),
            variant(
                "Square",
                'Avatar().name("Northwind Ltd").shape("square").size("lg")',
            ),
        ],
    ),
    Showcase(
        title="Groups",
        layout="stack",
        description=(
            "A group is one image with one summary label. Six separately "
            "announced sets of initials is noise, so members are hidden from "
            "assistive tech and the group speaks for them. The group's size "
            "reaches its members, so only one call sets it."
        ),
        variants=[
            variant(
                "With overflow",
                """
                (
                    AvatarGroup()
                    .label("Ada Lovelace, Grace Hopper, Alan Turing and 3 others")
                    .more(3)
                    .content(
                        Avatar().name("Ada Lovelace"),
                        Avatar().name("Grace Hopper"),
                        Avatar().name("Alan Turing"),
                    )
                )
                """,
            ),
            variant(
                "Small",
                """
                (
                    AvatarGroup()
                    .label("Ada Lovelace and Grace Hopper")
                    .size("sm")
                    .content(
                        Avatar().name("Ada Lovelace"),
                        Avatar().name("Grace Hopper"),
                    )
                )
                """,
            ),
        ],
    ),
]
