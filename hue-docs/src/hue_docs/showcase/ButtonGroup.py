"""
Curated showcases for the ButtonGroup molecule.

The group has no axes, so the auto-grid has nothing to vary - and nothing to
put inside it, which is the whole component.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Buttons that happen to sit together, each still doing its own "
            "thing. Only the geometry is shared, so every button keeps the "
            "variant it was given and they should all be given the same one. "
            "ghost and link are rejected: the group is made of its buttons' "
            "borders, and those variants have none."
        ),
        variants=[
            variant(
                "A split button",
                """
                (
                    ButtonGroup().content(
                        Button().variant("outline").size("sm").content("Export"),
                        Button()
                        .variant("outline")
                        .size("sm")
                        .icon_only("Export options")
                        .content("v"),
                    )
                )
                """,
            ),
            variant(
                "Three actions",
                """
                (
                    ButtonGroup()
                    .label("Row actions")
                    .content(
                        Button().variant("outline").size("sm").content("Edit"),
                        Button().variant("outline").size("sm").content("Duplicate"),
                        Button()
                        .variant("danger-outline")
                        .size("sm")
                        .content("Delete"),
                    )
                )
                """,
            ),
        ],
    ),
]
