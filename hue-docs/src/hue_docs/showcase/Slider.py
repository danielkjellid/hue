"""
Curated showcases for the Slider atom.

A slider is a track, a readout and the labels under it working together, and
none of those are axes the auto-grid can build.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Always paired with the number it is setting. A slider on its own "
            "cannot say what it has landed on, and for anything billable the "
            "exact value is the whole point - so the readout is on by default "
            "and sits in the label row, where a textarea puts its counter."
        ),
        variants=[
            variant(
                "With ticks",
                """
                (
                    Slider()
                    .name("seats")
                    .label("Team seats")
                    .min(1)
                    .max(50)
                    .value(12)
                    .ticks("1", "25", "50")
                )
                """,
            ),
            variant(
                "A unit on the number",
                """
                (
                    Slider()
                    .name("budget")
                    .label("Monthly budget cap")
                    .min(0)
                    .max(2000)
                    .step(50)
                    .value(600)
                    .prefix("$")
                    .hint("Billing pauses when the cap is reached.")
                )
                """,
            ),
            variant(
                "No readout",
                """
                (
                    Slider()
                    .name("volume")
                    .label("Volume")
                    .value(70)
                    .show_value(False)
                )
                """,
            ),
            variant(
                "Disabled",
                """
                (
                    Slider()
                    .name("locked")
                    .label("Managed by your plan")
                    .value(25)
                    .disabled()
                )
                """,
            ),
        ],
    ),
]
