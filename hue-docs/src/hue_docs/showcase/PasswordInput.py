"""
Curated showcases for the PasswordInput atom.

revealable() is the only thing this input has that the others do not, and it
is behaviour rather than an axis, so the auto-grid has nothing to show for it.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "revealable() attaches a toggle that swaps the input's type. It "
            'keeps one name - "Show password" - and reports its state '
            'through aria-pressed, rather than renaming itself to "Hide '
            'password": a control whose label changes is announced as a '
            "different control every time it is pressed."
        ),
        variants=[
            variant(
                "Plain",
                """
                (
                    PasswordInput()
                    .name("current_password")
                    .label("Password")
                )
                """,
            ),
            variant(
                "Revealable",
                """
                (
                    PasswordInput()
                    .name("password")
                    .label("Password")
                    .value("hunter2")
                    .revealable()
                )
                """,
            ),
            variant(
                "New password, with a hint",
                """
                (
                    PasswordInput()
                    .name("new_password")
                    .label("New password")
                    .autocomplete("new-password")
                    .hint("At least 12 characters.")
                    .revealable()
                )
                """,
            ),
        ],
    ),
]
