"""
Curated showcases for the Toast molecule.

The auto-grid renders the variants as specimens, which is what they look
like. What it cannot do is raise one, which is what they are.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Raise one",
        layout="row",
        description=(
            "These call $toast in the browser, which is the trigger for "
            "things the server never hears about. Hover a toast to pause its "
            "timer, which WCAG 2.2.1 asks for: a message that leaves on its "
            "own has to be stoppable by whoever is still reading it. From "
            "Python it is toast.success(...) in any handler, and the toast "
            "rides along with whatever that handler returns."
        ),
        variants=[
            variant(
                "Success",
                """
                (
                    Button()
                    .variant("outline")
                    .content("Invoice sent")
                    .x_on(
                        "click",
                        "$toast.success('Invoice sent', "
                        "{ description: 'INV-2048 sent to ada@example.com' })",
                    )
                )
                """,
            ),
            variant(
                "Failure",
                """
                (
                    Button()
                    .variant("outline")
                    .content("Could not send")
                    .x_on(
                        "click",
                        "$toast.danger('Could not send invoice', "
                        "{ description: 'The mail server rejected the address.' })",
                    )
                )
                """,
            ),
            variant(
                "Title only",
                """
                (
                    Button()
                    .variant("outline")
                    .content("Copied")
                    .x_on("click", "$toast.success('Copied to clipboard')")
                )
                """,
            ),
            variant(
                "One that stays",
                """
                (
                    Button()
                    .variant("outline")
                    .content("Exporting")
                    .x_on(
                        "click",
                        "$toast.loading('Exporting 2,481 rows', "
                        "{ description: 'This usually takes about a minute.', "
                        "duration: null })",
                    )
                )
                """,
            ),
        ],
    ),
    Showcase(
        title="Anatomy",
        layout="stack",
        description=(
            "The same markup, standing still. A toast is a card until it is "
            "in a region: the region is what announces it and what times it."
        ),
        variants=[
            variant(
                "With a description",
                """
                (
                    Toast()
                    .variant("success")
                    .title("Invoice sent")
                    .description("INV-2048 sent to ada@example.com")
                )
                """,
            ),
            variant(
                "With a way to retry",
                """
                (
                    Toast()
                    .variant("danger")
                    .title("Could not send invoice")
                    .description("The mail server rejected ada@exampl.com")
                    .action(Button().variant("outline").size("xs").content("Retry"))
                )
                """,
            ),
            variant(
                "Pending",
                """
                (
                    Toast()
                    .variant("loading")
                    .title("Exporting 2,481 rows")
                    .description("This usually takes about a minute.")
                    .duration(None)
                    .dismissible(False)
                )
                """,
            ),
        ],
    ),
]
