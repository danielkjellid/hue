"""
Curated showcases for the Progress atom.

The auto-grid covers the variants, sizes and the indeterminate toggle. These
show the shapes it cannot build, where the value and the label carry the point.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "indeterminate() is for work whose length is unknown: the bar "
            "sweeps and announces no position, because an aria-valuenow of 0 "
            'would say "0 percent", which reads as stalled rather than '
            "unknown."
        ),
        variants=[
            variant("Labelled", 'Progress().value(64).label("Uploading archive.zip")'),
            variant("Bare", "Progress().value(32)"),
            variant("Indeterminate", 'Progress().indeterminate().label("Exporting")'),
            variant("Nearly full", 'Progress().value(92).variant("warning")'),
        ],
    ),
]
