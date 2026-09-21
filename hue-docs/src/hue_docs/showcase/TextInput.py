"""
Curated showcases for the text inputs.

The auto-grid toggles one input's axes at a time. What it cannot show is the
supporting copy around a control, the two layouts it can sit in - both of which
come from the Field the input builds for itself - or anything attached to the
control, which hands its frame over to a group.
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
                    EmailInput()
                    .name("email")
                    .label("Email address")
                    .hint("We only use it for receipts.")
                )
                """,
            ),
            variant(
                "Error",
                """
                (
                    EmailInput()
                    .name("billing_email")
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
                    TextInput()
                    .name("account")
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
                    TextInput()
                    .name("workspace_url")
                    .label("Workspace URL")
                    .hint("Used in every share link.")
                    .value("northwind")
                    .horizontal()
                )
                """,
            ),
        ],
    ),
    Showcase(
        title="With something attached",
        layout="stack",
        description=(
            "prefix(), suffix(), leading_icon() and action() wrap the input in "
            "a group. The border, the fill and the focus halo move up to that "
            "group, because a square segment inside a rounded box pokes past "
            "the corner and reads as a broken border."
        ),
        variants=[
            variant(
                "Prefix",
                """
                (
                    TextInput()
                    .name("url")
                    .label("Workspace URL")
                    .prefix("hue.app/")
                    .value("northwind")
                    .hint("Used in every share link.")
                )
                """,
            ),
            variant(
                "Suffix",
                """
                (
                    NumberInput()
                    .name("rate")
                    .label("API rate limit")
                    .suffix("req/min")
                    .value("600")
                )
                """,
            ),
            variant(
                "Attached action",
                """
                (
                    TextInput()
                    .name("api_key")
                    .label("API key")
                    .value("sk_live_51H8xK2eZv")
                    .readonly()
                    .action(Button().variant("outline").content("Copy"))
                )
                """,
            ),
            variant(
                "Leading icon",
                """
                (
                    TextInput()
                    .name("q")
                    .label("Search invoices")
                    .hidden_label()
                    .leading_icon(HueIcon("search"))
                    .placeholder("Search invoices")
                )
                """,
            ),
        ],
    ),
]
