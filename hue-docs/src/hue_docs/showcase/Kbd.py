"""
Curated showcases for the Kbd atom.

Kbd has no enum or bool axes - its whole surface is the keys it is given - so
the auto-grid has nothing to show.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Modifier names become their glyphs and carry a spoken name, so a "
            'screen reader announces "Command" rather than the glyph\'s Unicode '
            'name. "mod" is the command key on Apple platforms and control '
            "everywhere else, which only the browser can decide."
        ),
        variants=[
            variant("Shortcut", 'Kbd("mod", "K")'),
            variant("Three keys", 'Kbd("shift", "mod", "P")'),
            variant("Single key", 'Kbd("esc")'),
            variant("Arrows", 'Kbd("up", "down")'),
            variant("Literal key", 'Kbd("F5")'),
        ],
    ),
]
