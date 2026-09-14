"""
Curated showcases for the Button atom.

The auto-grid covers variant, size and shape. These are the states it cannot
reach: icon_only() takes a label rather than a flag, so it is not an axis at
all, and the bool axes are pushed out of the playground by the combination cap.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="States",
        layout="stack",
        description=(
            "Every state is designed, not inherited. A button that only has a "
            "resting state is unfinished. loading() keeps the button's width "
            "and its accessible name, announces aria-busy, and disables it so "
            "the action cannot be submitted twice."
        ),
        variants=[
            variant("Default", 'Button().content("Publish")'),
            variant("Loading", 'Button().loading().content("Publish")'),
            variant("Disabled", 'Button().disabled().content("Publish")'),
            variant(
                "Loading, secondary",
                'Button().variant("outline").loading().content("Export")',
            ),
        ],
    ),
    Showcase(
        title="Icon only",
        layout="stack",
        description=(
            "An icon carries no accessible name, so icon_only() takes the "
            "label as an argument: there is no way to render an unnamed one. "
            "The button goes square at whatever size it is set to."
        ),
        variants=[
            variant(
                "Small",
                'Button().variant("outline").size("sm").icon_only("Add project")'
                '.content("+")',
            ),
            variant(
                "Default",
                'Button().variant("outline").icon_only("Add project").content("+")',
            ),
            variant(
                "Ghost",
                'Button().variant("ghost").icon_only("More actions").content("...")',
            ),
        ],
    ),
    Showcase(
        title="Width",
        layout="stack",
        description=(
            "Buttons size to their content by default, so a button sitting in "
            "a row of buttons does not have to opt out of filling the row. "
            "fluid() is for mobile primaries and form submits."
        ),
        variants=[
            variant("Content width", 'Button().content("Save changes")'),
            variant("Fluid", 'Button().fluid().content("Save changes")'),
        ],
    ),
]
