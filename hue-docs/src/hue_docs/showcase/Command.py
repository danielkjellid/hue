"""
Curated showcases for the Command molecule.

The example has four plain items. These show what a palette in an app looks
like: icons and shortcuts, a description under a label, recent records with
an amount at the end, items that run something rather than go somewhere, and
keywords that find an item by another name.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Open one and type: an item stays when its label or a keyword "
            "contains what was typed, and one whose label starts with it moves "
            "to the top of its group, since the first result is the one Enter "
            "runs. Escape clears what was typed, and a second Escape closes."
        ),
        variants=[
            variant(
                "Navigation, actions and recent records",
                """
                (
                    Command()
                    .trigger(Button().variant("outline").content("Search"))
                    .content(
                        CommandGroup().label("Navigate").content(
                            CommandItem().label("Go to Billing")
                            .icon(HueIcon("credit-card"))
                            .shortcut("g", "b")
                            .href("#billing"),
                            CommandItem().label("Go to Members")
                            .icon(HueIcon("users"))
                            .shortcut("g", "m")
                            .href("#members"),
                        ),
                        CommandGroup().label("Actions").content(
                            CommandItem().label("Create invoice")
                            .icon(HueIcon("file-text"))
                            .shortcut("alt+n")
                            .action(toast.js.success("Invoice created")),
                            CommandItem().label("Copy invoice link")
                            .icon(HueIcon("copy"))
                            .keywords("share", "url")
                            .action(toast.js.success("Link copied")),
                            CommandItem().label("Delete workspace")
                            .icon(HueIcon("trash-2"))
                            .disabled(),
                        ),
                        CommandGroup().label("Recent").content(
                            CommandItem().label("INV-2048 Northwind Traders")
                            .icon(HueIcon("file-text"))
                            .meta("$1,200.00")
                            .href("#inv-2048"),
                            CommandItem().label("INV-2049 Contoso Ltd")
                            .icon(HueIcon("file-text"))
                            .meta("$840.00")
                            .href("#inv-2049"),
                        ),
                    )
                )
                """,
            ),
            variant(
                "With descriptions",
                """
                (
                    Command()
                    .placeholder("Search people")
                    .empty_message("Nobody by that name.")
                    .trigger(Button().variant("outline").content("Find a person"))
                    .content(
                        CommandItem().label("Ada Lovelace")
                        .icon(HueIcon("user"))
                        .description("Engineering · ada@example.com")
                        .href("#ada"),
                        CommandItem().label("Grace Hopper")
                        .icon(HueIcon("user"))
                        .description("Platform · grace@example.com")
                        .href("#grace"),
                        CommandItem().label("Edsger Dijkstra")
                        .icon(HueIcon("user"))
                        .description("Research · edsger@example.com")
                        .keywords("algorithms")
                        .href("#edsger"),
                    )
                )
                """,
            ),
        ],
    ),
]
