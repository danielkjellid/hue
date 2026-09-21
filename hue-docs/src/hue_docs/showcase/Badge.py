"""
Curated showcases for the Badge atom.

The auto-grid covers the tones one at a time. These show them doing the job
they exist for: labelling status in a row, where the comparison between them is
the whole point.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Status",
        layout="stack",
        description=(
            "Colour never carries the meaning on its own. Every badge has a "
            "text label, and the dot repeats what the label already says - at "
            "12px that pairing reads faster than a fully tinted pill, which is "
            "why it is the usual choice in a table."
        ),
        variants=[
            variant("Paid", 'Badge().variant("success").dot().content("Paid")'),
            variant("Pending", 'Badge().variant("warning").dot().content("Pending")'),
            variant("Declined", 'Badge().variant("danger").dot().content("Declined")'),
            variant("Draft", 'Badge().dot().content("Draft")'),
        ],
    ),
    Showcase(
        title="Counts",
        layout="stack",
        description=(
            "numeric() lines the figures up on a shared width so a column of "
            "counts stays scannable; without it the digits drift."
        ),
        variants=[
            variant("Count", 'Badge().numeric().content("128")'),
            variant("Pill", 'Badge().pill().numeric().content("9")'),
            variant("Large", 'Badge().size("lg").variant("accent").content("Pro")'),
            variant("Solid", 'Badge().variant("solid").content("New")'),
        ],
    ),
]
