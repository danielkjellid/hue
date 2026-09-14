"""
Curated showcases for the Item molecule.

The auto-grid can toggle Item's bools but has nothing to put in its slots, and
the slots are what the component is.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "The shape behind list rows, menu entries, combobox options and "
            "settings rows. Title and description truncate rather than wrap: "
            "one row growing to two lines shifts everything below it, which is "
            "what makes a long list feel unruly."
        ),
        variants=[
            variant(
                "A list row",
                """
                (
                    Item()
                    .variant("bordered")
                    .title("Ada Lovelace")
                    .description("ada@example.com · Owner")
                )
                """,
            ),
            variant(
                "Interactive",
                """
                (
                    Item()
                    .variant("bordered")
                    .href("/people/ada")
                    .title("Ada Lovelace")
                    .description("Opens in the same tab, like a real link")
                )
                """,
            ),
            variant(
                "Selected",
                """
                (
                    Item()
                    .variant("bordered")
                    .selected()
                    .title("Pro")
                    .description("$49 / month")
                )
                """,
            ),
            variant(
                "Disabled",
                """
                (
                    Item()
                    .variant("bordered")
                    .disabled()
                    .title("Government")
                    .description("Join the waitlist")
                )
                """,
            ),
            variant(
                "With actions",
                """
                (
                    Item()
                    .variant("bordered")
                    .title("Grace Hopper")
                    .description("grace@example.com · Admin")
                    .actions(Button().variant("ghost").size("xs").content("Manage"))
                )
                """,
            ),
        ],
    ),
]
