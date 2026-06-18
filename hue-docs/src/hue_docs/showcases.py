"""Hand-authored showcases for components the auto-grid can't represent.

Most components are documented entirely automatically: their enum/bool axes
become variant grids (see ``registry.auto_showcases``). Compositional components
like ``Table`` have no such axes — they're assembled from subcomponents — so an
auto-grid has nothing to show. For those we curate a few representative examples
here, modelled on shadcn's table docs (a basic table, a caption, a footer with a
total; for ``DataTable`` a custom cell, the empty state, and a caption).

Each example is written once as a source expression: it is both ``eval``-ed to
build the live preview and shown verbatim as the code snippet, so the two can
never drift. The strings are trusted, in-repo literals evaluated at build time
against the public ``hue.ui`` names — there is no external input.
"""

from __future__ import annotations

import textwrap
from typing import Any

from hue import ui

from hue_docs.discovery import ComponentDoc
from hue_docs.registry import Showcase, Variant

# The names a curated snippet may reference — the public component surface.
_NS: dict[str, Any] = {name: getattr(ui, name) for name in ui.__all__}


def _variant(label: str, source: str) -> Variant:
    """A variant whose preview and code come from one source expression."""
    code = textwrap.dedent(source).strip()
    return Variant(
        label=label,
        build=lambda code=code: eval(code, dict(_NS)),
        code=code,
    )


_TABLE_SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Compose a table from its primitives. Use .align() for numeric "
            "columns, .colspan() to span cells, and TableCaption / TableFooter "
            "for a caption and a totals row."
        ),
        variants=[
            _variant(
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
            _variant(
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
            _variant(
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


_DATATABLE_SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Pass columns and a list of records; DataTable emits the primitives "
            "for you. A column's value comes from its accessor (a key, a dotted "
            "path, or a callable) or a custom cell render function."
        ),
        variants=[
            _variant(
                "Basic",
                """
                DataTable().columns(
                    [
                        Column("Name", accessor="name"),
                        Column("Email", accessor="email"),
                        Column("Role", accessor="role", align="right"),
                    ]
                ).data(
                    [
                        {
                            "name": "Ada Lovelace",
                            "email": "ada@example.com",
                            "role": "Admin",
                        },
                        {
                            "name": "Alan Turing",
                            "email": "alan@example.com",
                            "role": "Member",
                        },
                    ]
                )
                """,
            ),
            _variant(
                "Custom cell",
                """
                DataTable().columns(
                    [
                        Column("Invoice", accessor="invoice"),
                        Column(
                            "Status",
                            accessor="status",
                            cell=lambda row: Text(row["status"]).muted(),
                        ),
                        Column("Amount", accessor="amount", align="right"),
                    ]
                ).data(
                    [
                        {"invoice": "INV001", "status": "Paid", "amount": "$250.00"},
                        {"invoice": "INV002", "status": "Pending", "amount": "$150.00"},
                    ]
                )
                """,
            ),
            _variant(
                "Empty state",
                """
                DataTable().columns(
                    [
                        Column("Name", accessor="name"),
                        Column("Email", accessor="email"),
                    ]
                ).data([])
                """,
            ),
            _variant(
                "With caption",
                """
                DataTable().columns(
                    [
                        Column("Name", accessor="name"),
                        Column("Email", accessor="email"),
                    ]
                ).data(
                    [
                        {"name": "Ada Lovelace", "email": "ada@example.com"},
                    ]
                ).caption("A list of your users.")
                """,
            ),
        ],
    ),
]


_CURATED: dict[str, list[Showcase]] = {
    "Table": _TABLE_SHOWCASES,
    "DataTable": _DATATABLE_SHOWCASES,
}


def curated_showcases(doc: ComponentDoc) -> list[Showcase]:
    """Hand-authored showcases for *doc*, or an empty list if none."""
    return _CURATED.get(doc.name, [])
