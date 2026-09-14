"""
Curated showcases for the Switch atom.

The auto-grid has the sizes and the toggles; what it cannot show is the pair
of states side by side, which is the whole point of a switch.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            'role="switch" rather than a checkbox, so it is announced as on '
            "or off rather than checked or unchecked. A switch takes effect "
            "as it is flipped; pending() covers the round trip when that means "
            "a request, so the delay is visible rather than the switch just "
            "refusing to move."
        ),
        variants=[
            variant("Off", 'Switch("notify").label("Email notifications")'),
            variant(
                "On",
                'Switch("notify").label("Email notifications").checked()',
            ),
            variant(
                "With a description",
                """
                (
                    Switch("digest")
                    .label("Weekly digest")
                    .description("A summary of everything that changed, every Monday.")
                    .checked()
                )
                """,
            ),
            variant(
                "Saving",
                """
                (
                    Switch("sso")
                    .label("Enforce SSO")
                    .checked()
                    .pending()
                )
                """,
            ),
            variant(
                "Disabled",
                'Switch("locked").label("Managed by your administrator").disabled()',
            ),
        ],
    ),
]
