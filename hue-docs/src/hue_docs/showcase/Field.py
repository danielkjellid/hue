"""
Curated showcases for the Field molecule.

The auto-grid covers the layouts and the toggles. What it cannot show is the
thing Field is for: wrapping a control hue does not ship.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="States",
        layout="stack",
        description=(
            "hue's own controls build a Field for themselves, so these are "
            "written against TextInput. An error replaces the hint rather "
            "than joining it, and is announced when it appears - it usually "
            "shows up after a submit, when nothing else would prompt a "
            "screen reader to look again."
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
    Showcase(
        title="Around your own control",
        layout="stack",
        description=(
            "Field on its own, for a control hue does not ship. html_for() "
            "has to name the control's id: that is what ties the label and "
            "the messages to it. CONTROL_SHELL is the box every hue input "
            "wears, so a bespoke one can match without copying classes."
        ),
        variants=[
            variant(
                "A native select",
                """
                (
                    Field()
                    .label("Time zone")
                    .html_for("tz")
                    .hint("Affects report boundaries.")
                    .content(
                        html.select(
                            html.option("Europe/Oslo (UTC+2)"),
                            html.option("UTC"),
                            id="tz",
                            class_=CONTROL_SHELL,
                        )
                    )
                )
                """,
            ),
        ],
    ),
]
