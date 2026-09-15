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
            "as it is flipped, so unlike the rest of the form group it has a "
            "round trip to report on. submission_state() covers it: "
            '"pending" also holds the switch still, and the two finished '
            "states clear themselves after a couple of seconds so a row is "
            'not left wearing an outcome from minutes ago. layout("horizontal") '
            "puts the text first and the switch at the far end, which is the "
            "order a settings list reads in."
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
                    .submission_state("pending")
                )
                """,
            ),
            variant(
                "Saved",
                """
                (
                    Switch("sso")
                    .label("Enforce SSO")
                    .checked()
                    .submission_state("success")
                )
                """,
            ),
            variant(
                "Could not save",
                """
                (
                    Switch("sso")
                    .label("Enforce SSO")
                    .submission_state("error")
                )
                """,
            ),
            variant(
                "In a settings list",
                """
                (
                    Switch("twofactor")
                    .label("Two-factor authentication")
                    .description(
                        "Require a code from your authenticator at every sign-in."
                    )
                    .layout("horizontal")
                    .checked()
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
