"""
Curated showcases for the Spinner atom.

The auto-grid covers the sizes. This shows the labelled shape, which is the one
worth reaching for and which the grid cannot build.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Nothing under 300ms, a Skeleton from 300ms to 2s, a labelled "
            "spinner from 2s to 10s, and a determinate Progress with a way out "
            "beyond that. A spinner alone says something is happening but not "
            "what, so give it a label once the wait is long enough to see."
        ),
        variants=[
            variant("Labelled", 'Spinner().label("Loading payments")'),
            variant("Muted", 'Spinner().size("sm").muted().label("Searching")'),
            variant("Bare", "Spinner()"),
            variant("Large", 'Spinner().size("lg")'),
        ],
    ),
]
