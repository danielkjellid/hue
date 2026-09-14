"""
Curated showcases for the ProgressRing atom.

The auto-grid shows every variant at one value, which is the wrong axis for a
ring - what it looks like at 28, 64 and 100 percent is the thing to see.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Filling up",
        layout="row",
        description=(
            "For a card or a table cell, where a bar would not fit. "
            "show_value() prints the figure in the middle for a ring standing "
            "on its own; leave it off where the number is already beside it. "
            "A screen reader is told the percentage either way."
        ),
        variants=[
            variant(
                "28%",
                'ProgressRing().value(28).show_value().label("Storage used")',
            ),
            variant(
                "64%",
                'ProgressRing().value(64).show_value().label("Storage used")',
            ),
            variant(
                "100%",
                "(\n"
                "    ProgressRing()\n"
                "    .value(100)\n"
                '    .variant("success")\n'
                "    .show_value()\n"
                '    .label("Storage used")\n'
                ")",
            ),
            variant("Bare", 'ProgressRing().value(64).label("Storage used")'),
        ],
    ),
]
