"""
Curated showcases for the Panel molecule.

The auto-grid toggles padding and sunken but has nothing to frame, and framing
something is the entire point of the component.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "The bar appears only when it has something to say, so a panel "
            "with neither a label nor a hint is a plain bordered frame. "
            'padding("none") is for content that brings its own edges, such '
            "as a table, and sunken() tints the body so whatever sits on it "
            "reads as raised."
        ),
        variants=[
            variant(
                "Labelled",
                """
                (
                    Panel()
                    .label("Control heights")
                    .hint("36px is the default")
                    .content("Everything lines up on a shared baseline.")
                )
                """,
            ),
            variant("Label only", 'Panel().label("Variants").content("One per row.")'),
            variant("No bar", 'Panel().content("A plain bordered frame.")'),
            variant(
                "Sunken",
                """
                (
                    Panel()
                    .label("Elevation")
                    .sunken()
                    .content("Tinted, so a raised surface reads against it.")
                )
                """,
            ),
        ],
    ),
]
