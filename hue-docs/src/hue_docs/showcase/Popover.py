"""
Curated showcases for the Popover molecule.

The auto-grid has the placements, but a popover is a trigger and something
worth opening, and it can assemble neither.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="row",
        description=(
            "Non-modal: the page behind stays live and focus is not trapped, "
            "so the panel follows the trigger in the tab order and a form "
            "inside one is a form on the page. Escape closes it and puts "
            "focus back on the trigger; a click outside closes it and leaves "
            "focus where the click landed. Anything in the panel can close it "
            "by calling close()."
        ),
        variants=[
            variant(
                "Interactive content",
                """
                (
                    Popover()
                    .title("Share Route planner")
                    .description("Anyone with the link can view. Members can edit.")
                    .trigger(Button().variant("outline").content("Share project"))
                    .content(
                        TextInput()
                        .name("share_link")
                        .label("Share link")
                        .hidden_label()
                        .value("hue.app/p/9f2Kd8")
                        .readonly()
                        .action(Button().variant("outline").content("Copy")),
                        Checkbox().name("allow_comments").label("Allow comments"),
                    )
                )
                """,
            ),
            variant(
                "A definition",
                """
                (
                    Popover()
                    .placement("bottom-end")
                    .title("Monthly recurring revenue")
                    .description(
                        "Normalised monthly value of all active subscriptions. "
                        "Annual plans are divided by 12."
                    )
                    .trigger(
                        Button()
                        .variant("ghost")
                        .icon_only("What is MRR?")
                        .content(HueIcon("circle-info"))
                    )
                    .content(
                        Button()
                        .variant("link")
                        .content("Read the full definition")
                        .on_click(close())
                    )
                )
                """,
            ),
        ],
    ),
]
