"""
Curated showcases for the Sidebar molecule.

The auto-grid has nothing to toggle: a sidebar is its parts, and the parts
only make sense assembled.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="A whole sidebar",
        layout="stack",
        description=(
            "A header and a footer that stay, a nav between them that "
            "scrolls, and a spacer that pushes the last section to the "
            "bottom without pinning it there. The page you are on is marked "
            "twice - a tint for the eye and a bar in the gutter for the "
            "glance - and the accent is spent on that and nothing else, "
            'because this is the one place where "where am I" has to '
            "survive a squint."
        ),
        variants=[
            variant(
                "Assembled",
                """
                html.div(
                    Sidebar()
                    .current("/events")
                    .content(
                        SidebarHeader().content(
                            SidebarItem()
                            .icon(HueIcon("house"))
                            .content(SidebarLabel().content("Northwind")),
                            SidebarItem()
                            .icon(HueIcon("search"))
                            .content(SidebarLabel().content("Search")),
                        ),
                        SidebarBody().content(
                            SidebarSection().content(
                                SidebarItem()
                                .href("/")
                                .icon(HueIcon("house"))
                                .content(SidebarLabel().content("Home")),
                                SidebarItem()
                                .href("/events")
                                .icon(HueIcon("file-text"))
                                .content(SidebarLabel().content("Events")),
                                SidebarItem()
                                .href("/orders")
                                .icon(HueIcon("credit-card"))
                                .content(
                                    SidebarLabel().content("Orders"),
                                    Badge().content("3"),
                                ),
                            ),
                            SidebarDivider(),
                            SidebarSection().content(
                                SidebarHeading().content("Upcoming"),
                                SidebarItem()
                                .href("/events/bear-hug")
                                .content(SidebarLabel().content("Bear Hug: Live")),
                                SidebarItem()
                                .href("/events/six-more")
                                .content(SidebarLabel().content("Six More Weeks")),
                            ),
                            SidebarSpacer(),
                            SidebarSection().content(
                                SidebarItem()
                                .href("/support")
                                .icon(HueIcon("circle-info"))
                                .content(SidebarLabel().content("Support")),
                            ),
                        ),
                        SidebarFooter().content(
                            SidebarItem().content(
                                Avatar().name("Erica Meyers").size("sm"),
                                SidebarLabel().content("Erica"),
                            )
                        ),
                    ),
                    class_="h-[620px] overflow-hidden rounded-lg border border-border",
                )
                """,
            ),
        ],
    ),
]
