"""
Curated showcases for the Textarea atom.

The counter and the overage state are the parts worth seeing, and neither is
an axis the auto-grid can build.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "max_length() counts rather than enforces: the counter turns red "
            "and the control marks itself invalid, but the text is still "
            "accepted. A hard maxlength drops the keystroke silently, which "
            "reads as a broken keyboard rather than as a limit."
        ),
        variants=[
            variant(
                "Empty",
                """
                (
                    Textarea().name("description")
                    .label("Description")
                    .placeholder("What does this workspace do?")
                )
                """,
            ),
            variant(
                "With a counter",
                """
                (
                    Textarea().name("summary")
                    .label("Description")
                    .max_length(280)
                    .value("Internal tooling for the logistics team.")
                )
                """,
            ),
            variant(
                "Over the limit",
                """
                (
                    Textarea().name("blurb")
                    .label("Description")
                    .max_length(40)
                    .value(
                        "Internal tooling for the logistics team. Handles "
                        "route planning and fuel reporting."
                    )
                    .error("54 characters over the limit")
                )
                """,
            ),
            variant(
                "Autosizing",
                """
                (
                    Textarea().name("notes")
                    .label("Notes")
                    .autosize()
                    .value("One line.\\nTwo lines.\\nThree lines.")
                )
                """,
            ),
        ],
    ),
]
