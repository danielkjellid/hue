"""
Curated showcases for the Progress atom.

The auto-grid covers the variants and sizes. These show the two shapes it takes
that the grid cannot build: the labelled row, and the indeterminate bar.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Leave value() unset for work whose length is unknown and the bar "
            "animates instead, with no position announced - aria-valuenow of 0 "
            'would say "0 percent", which reads as stalled rather than '
            "unknown. Past ten seconds a determinate bar needs a way out next "
            "to it; progress with no exit is just a nicer spinner."
        ),
        variants=[
            variant("Labelled", 'Progress().value(64).label("Uploading archive.zip")'),
            variant("Bare", "Progress().value(32)"),
            variant("Indeterminate", 'Progress().label("Exporting")'),
            variant("Nearly full", 'Progress().value(92).variant("warning")'),
        ],
    ),
]
