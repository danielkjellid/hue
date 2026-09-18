"""
Curated showcases for the TableOfContents molecule.

There is nothing to toggle: what there is to see is the rail, which is drawn
from the shape of the list rather than from any modifier.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

_NESTED = (
    '[Heading("introduction", "Introduction"), '
    'Heading("core-concepts", "Core Concepts"), '
    'Heading("architecture", "Architecture", 3), '
    'Heading("data-flow", "Data Flow", 3), '
    'Heading("components", "Components"), '
    'Heading("utilities", "Utilities")]'
)

_FLAT = (
    '[Heading("introduction", "Introduction"), '
    'Heading("components", "Components"), '
    'Heading("utilities", "Utilities"), '
    'Heading("deployment", "Deployment")]'
)

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="grid",
        description=(
            "A nav around an ordered list of in-page links, with a rail drawn "
            "beside it. The rail bends to follow the nesting and fills in as "
            "far as the heading being read - which on a real page follows the "
            "scroll, and here holds at whatever current() named, because "
            "none of these headings are on this one. aria-current is "
            '"location" rather than "page": every entry points at the page '
            "you are already on, and what is marked is where in it you have "
            "got to."
        ),
        variants=[
            variant(
                "Nested headings",
                f"TableOfContents().items({_NESTED})"
                '.current("data-flow").class_("max-w-60")',
            ),
            variant(
                "A flat page",
                f"TableOfContents().items({_FLAT})"
                '.current("components").class_("max-w-60")',
            ),
        ],
    ),
]
