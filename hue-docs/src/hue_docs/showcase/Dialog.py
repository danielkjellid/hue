"""
Curated showcases for the Dialog molecule.

The auto-grid has the sizes and the toggles, but a dialog is a trigger, a
question and a way to answer it, and it can assemble none of those.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="row",
        description=(
            "Focus is trapped inside while it is up and returns to whatever "
            "opened it; the page behind cannot be scrolled or tabbed into. "
            "Escape always closes, dismissible or not - a modal with no way "
            "out is a trap whatever the question was. The footer actions are "
            "the other way out, and the only one when the dialog cannot be "
            "dismissed: each calls close(). Below sm every dialog docks to "
            "the bottom edge as a sheet - narrow the window to see it."
        ),
        variants=[
            variant(
                "With a footer",
                """
                (
                    Dialog()
                    .title("Invite teammates")
                    .description("They will get an email with a join link.")
                    .trigger(Button().content("Invite"))
                    .content(
                        TextInput()
                        .name("emails")
                        .label("Email addresses")
                        .placeholder("ada@example.com")
                    )
                    .footer(
                        Button()
                        .variant("ghost")
                        .content("Cancel")
                        .on_click(close()),
                        Button().content("Send invites").on_click(close()),
                    )
                )
                """,
            ),
            variant(
                "Destructive",
                """
                (
                    Dialog()
                    .size("sm")
                    .destructive()
                    .title("Delete this project?")
                    .description("Everything in it goes too. This cannot be undone.")
                    .trigger(Button().variant("danger").content("Delete project"))
                    .footer(
                        Button()
                        .variant("ghost")
                        .content("Keep it")
                        .on_click(close()),
                        Button()
                        .variant("danger")
                        .content("Delete")
                        .on_click(close()),
                    )
                )
                """,
            ),
            variant(
                "Must be answered",
                """
                (
                    Dialog()
                    .size("sm")
                    .dismissible(False)
                    .title("Accept the new terms")
                    .description("You need to accept these before continuing.")
                    .trigger(Button().variant("outline").content("Review terms"))
                    .footer(Button().content("Accept").on_click(close()))
                )
                """,
            ),
        ],
    ),
]
