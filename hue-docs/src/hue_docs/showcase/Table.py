"""Curated showcases for the Table primitives (modelled on shadcn's table)."""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            'Compose a table from its primitives. align("end") ends a column '
            "and lines its digits up, colspan() spans cells, and "
            "TableCaption / TableFooter add a caption and a totals row. "
            "A table can hold several bodies, and title() on each turns "
            "them into sections. "
            "compact() sets the padding for every cell at once, from the "
            "table, so no two cells can disagree about it."
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
                            TableHead().align("end").content("Role"),
                        ),
                    ),
                    TableBody().content(
                        TableRow().content(
                            TableCell().content("Ada Lovelace"),
                            TableCell().content("ada@example.com"),
                            TableCell().align("end").content("Admin"),
                        ),
                        TableRow().content(
                            TableCell().content("Alan Turing"),
                            TableCell().content("alan@example.com"),
                            TableCell().align("end").content("Member"),
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
                            TableHead().align("end").content("Amount"),
                        ),
                    ),
                    TableBody().content(
                        TableRow().content(
                            TableCell().content("INV001"),
                            TableCell().content("Paid"),
                            TableCell().content("Credit Card"),
                            TableCell().align("end").content("$250.00"),
                        ),
                        TableRow().content(
                            TableCell().content("INV002"),
                            TableCell().content("Pending"),
                            TableCell().content("PayPal"),
                            TableCell().align("end").content("$150.00"),
                        ),
                        TableRow().content(
                            TableCell().content("INV003"),
                            TableCell().content("Unpaid"),
                            TableCell().content("Bank Transfer"),
                            TableCell().align("end").content("$350.00"),
                        ),
                    ),
                    TableFooter().content(
                        TableRow().content(
                            TableCell().colspan(3).content("Total"),
                            TableCell().align("end").content("$750.00"),
                        ),
                    ),
                )
                """,
            ),
            variant(
                "With sections",
                """
                Table().content(
                    TableHeader().content(
                        TableRow().content(
                            TableHead().content("Dates"),
                            TableHead().content("Guest"),
                            TableHead().align("end").content("Nights"),
                        ),
                    ),
                    TableBody().title("October 2026", colspan=3).content(
                        TableRow().content(
                            TableCell().content("Sat 24 - Mon 26 Oct"),
                            TableCell().content("Ingrid Haugen"),
                            TableCell().align("end").content("2"),
                        ),
                    ),
                    TableBody().title("November 2026", colspan=3).content(
                        TableRow().content(
                            TableCell().content("Sat 7 - Tue 10 Nov"),
                            TableCell().content("Ada Lovelace"),
                            TableCell().align("end").content("3"),
                        ),
                        TableRow().content(
                            TableCell().content("Sat 14 - Mon 16 Nov"),
                            TableCell().content("Alan Turing"),
                            TableCell().align("end").content("2"),
                        ),
                    ),
                )
                """,
            ),
        ],
    ),
]
