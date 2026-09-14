"""
Curated showcases for the ProgressRing atom.

The auto-grid shows every variant at one value, which is the wrong axis for a
ring - what it looks like at 28, 64 and 100 percent is the thing to see. The
percentage is the caption here, as it is in the design guide: the ring itself
draws no number, so a page using one has to put the figure beside it.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Filling up",
        layout="row",
        description=(
            "For a card or a table cell, where a bar would not fit. The ring "
            "draws no figure of its own, so pair it with the number it stands "
            "for - the label only reaches a screen reader, which is told the "
            "percentage either way."
        ),
        variants=[
            variant("28%", 'ProgressRing().value(28).label("Storage used")'),
            variant("64%", 'ProgressRing().value(64).label("Storage used")'),
            variant(
                "100%",
                'ProgressRing().value(100).variant("success").label("Storage used")',
            ),
        ],
    ),
]
