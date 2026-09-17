"""
Curated showcases for the Tooltip molecule.

The auto-grid can place the bubble but has no trigger to hang it on, which is
most of what a tooltip is.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="row",
        description=(
            "Hover or focus the trigger. It opens on focus as well, because a "
            "keyboard never hovers - and a touch device gets neither, so what "
            "a tooltip says can never be the only place that information "
            "lives. Never put a link or a button inside one: there is no way "
            "to reach it. The bubble is the page inverted in light mode, which "
            "is what a tooltip looks like - and a lifted surface in dark, "
            "where inverting again would put a white card on a dark page."
        ),
        variants=[
            variant(
                "On an icon button",
                """
                (
                    Tooltip()
                    .content("Dismiss")
                    .trigger(
                        Button()
                        .variant("ghost")
                        .icon_only("Dismiss")
                        .content(HueIcon("x"))
                    )
                )
                """,
            ),
            variant(
                "With a shortcut",
                """
                (
                    Tooltip()
                    .content("Search")
                    .shortcut("⌘K")
                    .trigger(
                        Button()
                        .variant("ghost")
                        .icon_only("Search")
                        .content(HueIcon("search"))
                    )
                )
                """,
            ),
            variant(
                "Below the trigger",
                """
                (
                    Tooltip()
                    .content("Appears underneath")
                    .placement("bottom")
                    .trigger(Button().variant("secondary").size("sm").content("Below"))
                )
                """,
            ),
        ],
    ),
]
