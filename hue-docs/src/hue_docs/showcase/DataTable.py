"""
Curated showcases for the DataTable molecule.

The auto-grid can toggle compact and loading, but the states worth seeing -
nothing to show, and nothing fetched - need rows to be absent, which no axis
can arrange.
"""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

_COLUMNS = """
                    Column("invoice", "Invoice"),
                    Column("customer", "Customer"),
                    Column("amount", "Amount", align="end"),
                    Column(
                        "status",
                        "Status",
                        render=lambda row: Badge()
                        .variant(row["tone"])
                        .dot()
                        .content(row["status"]),
                    ),
"""

_ROWS = """
                    {
                        "invoice": "INV-2050",
                        "customer": "Contoso Ltd",
                        "amount": "$2,190.00",
                        "status": "Pending",
                        "tone": "warning",
                    },
                    {
                        "invoice": "INV-2048",
                        "customer": "Northwind Traders",
                        "amount": "$1,200.00",
                        "status": "Paid",
                        "tone": "success",
                    },
                    {
                        "invoice": "INV-2049",
                        "customer": "Fabrikam Inc",
                        "amount": "$840.00",
                        "status": "Declined",
                        "tone": "danger",
                    },
"""

_PLAIN = """
                    Column("invoice", "Invoice"),
                    Column("amount", "Amount", align="end"),
"""

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Columns and rows, and everything else is a state the table can "
            "be in instead. A column's value comes from a key, a dotted path "
            "or a callable; render() takes the row and returns whatever the "
            "cell should hold. Numeric columns end themselves and switch to "
            "tabular figures, because without them the decimal points drift "
            "and the column stops being scannable. Cells wrap rather than "
            "truncate: an invoice reference cut off without saying so is "
            "worse than an uneven row."
        ),
        variants=[
            variant(
                "Populated",
                f"""
                DataTable().caption(
                    "Invoices, September 2026 - 3 of 148 shown"
                ).columns(
                    [{_COLUMNS}                ]
                ).rows(
                    [{_ROWS}                ]
                )
                """,
            ),
            variant(
                "Compact",
                f"""
                DataTable().compact().columns(
                    [{_COLUMNS}                ]
                ).rows(
                    [{_ROWS}                ]
                )
                """,
            ),
        ],
    ),
    Showcase(
        title="While there is nothing to show",
        layout="grid",
        description=(
            "Three different sentences, and the header stays put for all of "
            "them - the columns are what the table is, whether or not there "
            "are rows. Loading stands bars where the values will be and says "
            "aria-busy once, rather than reading out rows of nothing."
        ),
        variants=[
            variant(
                "Loading",
                f"DataTable().loading().columns([{_PLAIN}                ])",
            ),
            variant(
                "Empty",
                f"""
                DataTable().columns(
                    [{_PLAIN}                ]
                ).rows([]).empty(
                    Empty()
                    .compact()
                    .title("No invoices match")
                    .description("Try clearing the Declined filter.")
                    .actions(Button().variant("outline").size("xs").content(
                        "Clear filters"
                    ))
                )
                """,
            ),
            variant(
                "Error",
                f"""
                DataTable().columns(
                    [{_PLAIN}                ]
                ).error(
                    Empty()
                    .variant("danger")
                    .compact()
                    .title("Couldn't load invoices")
                    .description("The billing service didn't respond.")
                    .actions(Button().variant("outline").size("xs").content("Retry"))
                )
                """,
            ),
        ],
    ),
]
