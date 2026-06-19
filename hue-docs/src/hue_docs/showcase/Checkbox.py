"""
Curated showcases for the Checkbox atom.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "A native checkbox with a styled box. Use .checked() for the initial "
            "state, .indeterminate() for a mixed state, and .help_text() / "
            ".error_text() for supporting copy (error_text marks it invalid)."
        ),
        variants=[
            variant("Basic", 'Checkbox().name("terms").label("I accept the terms")'),
            variant(
                "Checked",
                """
                (
                    Checkbox()
                    .name("news")
                    .label("Subscribe to the newsletter")
                    .checked()
                )
                """,
            ),
            variant(
                "Indeterminate",
                'Checkbox().name("all").label("Select all").indeterminate()',
            ),
            variant(
                "With helper text",
                """
                (
                    Checkbox()
                    .name("marketing")
                    .label("Marketing emails")
                    .help_text("You can unsubscribe at any time.")
                )
                """,
            ),
            variant(
                "Required",
                'Checkbox().name("tos").label("I agree to the terms").required()',
            ),
            variant(
                "Disabled",
                'Checkbox().name("locked").label("Unavailable option").disabled()',
            ),
            variant(
                "Error",
                """
                (
                    Checkbox()
                    .name("consent")
                    .label("I consent")
                    .error_text("This field is required.")
                )
                """,
            ),
        ],
    ),
]
