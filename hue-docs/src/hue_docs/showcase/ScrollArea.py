"""
Curated showcases for the ScrollArea atom.

The auto-grid can toggle fade(), but not show what the two are for: one is a
box with a border around a list, the other is prose running past an edge.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

_ZONES = [
    ("Europe/Oslo", "UTC+2 · Central European Summer Time"),
    ("Europe/London", "UTC+1 · British Summer Time"),
    ("America/New_York", "UTC-4 · Eastern Daylight Time"),
    ("America/Los_Angeles", "UTC-7 · Pacific Daylight Time"),
    ("Asia/Tokyo", "UTC+9 · Japan Standard Time"),
    ("Asia/Singapore", "UTC+8 · Singapore Standard Time"),
    ("Australia/Sydney", "UTC+10 · Australian Eastern Standard Time"),
]

_ROWS = ", ".join(
    f'html.div(html.div("{name}", class_="font-medium text-fg"), '
    f'html.div("{offset}", class_="text-xs text-fg-muted"), '
    f'class_="rounded-md px-2 py-1.5 hover:bg-surface-hover")'
    for name, offset in _ZONES
)

_NOTES = [
    "4.2.0 — Usage-based billing is now available on Pro and Scale. "
    "Invoices show a per-endpoint breakdown.",
    "4.1.3 — Fixed a rounding error in multi-currency invoices where the "
    "total could be off by one minor unit.",
    "4.1.0 — Added cursor pagination to the transactions endpoint. Offset "
    "pagination is deprecated above 10,000 records.",
    "4.0.1 — Webhook retries now use exponential backoff instead of a fixed "
    "60-second interval.",
    "4.0.0 — New API version. Bearer tokens replace the legacy key-and-secret pair.",
]

_PROSE = ", ".join(f'html.p("{note}")' for note in _NOTES)

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="grid",
        description=(
            "The scrolling is the browser's and only the bar is themed: a "
            "scrollbar written in JavaScript loses the momentum, the platform "
            "conventions and the accessibility of the real one. "
            "overscroll-contain keeps a list that has hit its end from "
            "carrying on into the page behind it. Both are focusable and "
            "named, because a keyboard has no other way to scroll a box."
        ),
        variants=[
            variant(
                "A list in a box",
                'ScrollArea().label("Time zones").max_height("max-h-48")'
                '.class_("rounded-md border border-border p-2")'
                f".content({_ROWS})",
            ),
            variant(
                "Prose, with the edges faded",
                'ScrollArea().label("Release notes").max_height("max-h-48")'
                '.fade().class_("[&_p]:mb-3 [&_p]:last:mb-0")'
                f".content({_PROSE})",
            ),
        ],
    ),
]
