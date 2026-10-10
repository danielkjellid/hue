"""
Curated showcases for the DropdownMenu molecule.

The auto-grid has the placements, but a menu is a trigger and a list of
things to do, and it can assemble neither.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="row",
        description=(
            "Arrow keys move between items and wrap, Home and End jump to the "
            "ends, Escape closes the menu and puts focus back on the trigger. "
            "A disabled item stays in the menu and in the tab order, because "
            "an action that disappears when it cannot be used leaves nothing "
            "to explain why. Destructive items go last, after a separator, "
            "and are the only coloured thing in the menu."
        ),
        variants=[
            variant(
                "Project actions",
                """
                (
                    DropdownMenu()
                    .label("Project actions")
                    .trigger(
                        Button()
                        .variant("outline")
                        .content("Project actions", HueIcon("chevron-down"))
                    )
                    .content(
                        MenuLabel().content("Project"),
                        MenuItem()
                        .icon(HueIcon("copy"))
                        .shortcut(Kbd("mod", "D"))
                        .content("Duplicate"),
                        MenuItem().icon(HueIcon("file-text")).content("Export as CSV"),
                        MenuSeparator(),
                        MenuLabel().content("Sharing"),
                        MenuItem().checkable().checked().content("Public link"),
                        MenuItem().checkable().content("Allow comments"),
                        MenuSeparator(),
                        MenuItem()
                        .disabled()
                        .icon(HueIcon("users"))
                        .content("Transfer ownership"),
                        MenuItem()
                        .variant("danger")
                        .icon(HueIcon("trash-2"))
                        .content("Delete project"),
                    )
                )
                """,
            ),
            variant(
                "An account menu",
                """
                (
                    DropdownMenu()
                    .label("Account")
                    .placement("bottom-end")
                    .trigger(
                        Button()
                        .variant("ghost")
                        .icon_only("Account")
                        .content(HueIcon("ellipsis"))
                    )
                    .content(
                        MenuItem().href("/profile").icon(HueIcon("user")).content("Profile"),
                        MenuItem()
                        .href("/billing")
                        .icon(HueIcon("credit-card"))
                        .content("Billing"),
                        MenuSeparator(),
                        MenuItem().icon(HueIcon("log-out")).content("Sign out"),
                    )
                )
                """,
            ),
        ],
    ),
]
