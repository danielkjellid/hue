"""Curated showcases for the ``Table`` primitives (modelled on shadcn's table)."""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Compose a table from its primitives. Use .align() for numeric "
            "columns, .colspan() to span cells, and TableCaption / TableFooter "
            "for a caption and a totals row."
        ),
        variants=[
            variant(
                "Basic",
                """
                Table().content(
                    TableHeader().content(
                        TableRow().content(
                            TableHead().content("Name"),
                            TableHead().content("Email"),
                            TableHead().align("right").content("Role"),
                        ),
                    ),
                    TableBody().content(
                        TableRow().content(
                            TableCell().content("Ada Lovelace"),
                            TableCell().content("ada@example.com"),
                            TableCell().align("right").content("Admin"),
                        ),
                        TableRow().content(
                            TableCell().content("Alan Turing"),
                            TableCell().content("alan@example.com"),
                            TableCell().align("right").content("Member"),
                        ),
                    ),
                )
                """,
            ),
            variant(
                "With caption",
                """
                Table().content(
                    TableHeader().content(
                        TableRow().content(
                            TableHead().content("Name"),
                            TableHead().content("Email"),
                        ),
                    ),
                    TableBody().content(
                        TableRow().content(
                            TableCell().content("Ada Lovelace"),
                            TableCell().content("ada@example.com"),
                        ),
                    ),
                    TableCaption().content("A list of your users."),
                )
                """,
            ),
            variant(
                "With footer",
                """
                Table().content(
                    TableHeader().content(
                        TableRow().content(
                            TableHead().content("Invoice"),
                            TableHead().content("Status"),
                            TableHead().content("Method"),
                            TableHead().align("right").content("Amount"),
                        ),
                    ),
                    TableBody().content(
                        TableRow().content(
                            TableCell().content("INV001"),
                            TableCell().content("Paid"),
                            TableCell().content("Credit Card"),
                            TableCell().align("right").content("$250.00"),
                        ),
                        TableRow().content(
                            TableCell().content("INV002"),
                            TableCell().content("Pending"),
                            TableCell().content("PayPal"),
                            TableCell().align("right").content("$150.00"),
                        ),
                        TableRow().content(
                            TableCell().content("INV003"),
                            TableCell().content("Unpaid"),
                            TableCell().content("Bank Transfer"),
                            TableCell().align("right").content("$350.00"),
                        ),
                    ),
                    TableFooter().content(
                        TableRow().content(
                            TableCell().colspan(3).content("Total"),
                            TableCell().align("right").content("$750.00"),
                        ),
                    ),
                )
                """,
            ),
        ],
    ),
]
