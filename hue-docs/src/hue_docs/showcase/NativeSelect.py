"""
Curated showcases for the NativeSelect atom.

The auto-grid has the sizes; what it cannot build is a select with options in
it, which is most of what there is to look at.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

_ZONES = '[("oslo", "Europe/Oslo (UTC+2)"), ("utc", "UTC"), ("ny", "America/New_York")]'

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "The browser's own control, so the phone picker, type-ahead and "
            "every assistive-tech behaviour come for free. Reach for Select "
            "instead when an option needs more than a line of text."
        ),
        variants=[
            variant(
                "With a value",
                f"""
                (
                    NativeSelect().name("tz")
                    .label("Time zone")
                    .options({_ZONES})
                    .value("oslo")
                    .hint("Affects report boundaries.")
                )
                """,
            ),
            variant(
                "Nothing picked yet",
                f"""
                (
                    NativeSelect().name("tz_default")
                    .label("Time zone")
                    .placeholder("Select a time zone")
                    .options({_ZONES})
                )
                """,
            ),
            variant(
                "Invalid",
                f"""
                (
                    NativeSelect().name("tz_required")
                    .label("Time zone")
                    .required()
                    .placeholder("Select a time zone")
                    .options({_ZONES})
                    .error("Pick a time zone to continue.")
                )
                """,
            ),
        ],
    ),
]
