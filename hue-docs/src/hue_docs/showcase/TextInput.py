"""
Curated showcases for the text inputs.

The auto-grid toggles one input's axes at a time. What it cannot show is the
supporting copy around a control, or the two layouts it can sit in - both of
which come from the Field the input builds for itself.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="States",
        layout="stack",
        description=(
            "An error replaces the hint rather than joining it, and is "
            "announced when it appears - it usually shows up after a submit, "
            "when nothing else would prompt a screen reader to look again."
        ),
        variants=[
            variant(
                "Hint",
                """
                (
                    EmailInput("email")
                    .label("Email address")
                    .hint("We only use it for receipts.")
                )
                """,
            ),
            variant(
                "Error",
                """
                (
                    EmailInput("email")
                    .label("Email address")
                    .required()
                    .value("ada@example")
                    .error("Add a domain, like ada@example.com")
                )
                """,
            ),
            variant(
                "Read-only",
                """
                (
                    TextInput("account")
                    .label("Account ID")
                    .value("acct_9f2Kd81mQ")
                    .readonly()
                    .hint("Still focusable and copyable.")
                )
                """,
            ),
        ],
    ),
    Showcase(
        title="Horizontal",
        layout="stack",
        description=(
            "For a settings page, where a 180px label column gives every row "
            "one edge. The hint joins the label there rather than sitting "
            "under the control, where it would fall into the next row's space."
        ),
        variants=[
            variant(
                "Settings row",
                """
                (
                    TextInput("url")
                    .label("Workspace URL")
                    .hint("Used in every share link.")
                    .value("northwind")
                    .layout("horizontal")
                )
                """,
            ),
        ],
    ),
]
