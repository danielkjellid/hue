"""Curated showcases for ``DataTable`` (modelled on shadcn's data table)."""

from __future__ import annotations

from hue_docs.showcase import Showcase, variant

SHOWCASES: list[Showcase] = [
    Showcase(
        title="Examples",
        layout="stack",
        description=(
            "Pass columns and a list of records; DataTable emits the primitives "
            "for you. A column's value comes from its accessor (a key, a dotted "
            "path, or a callable) or a custom cell render function."
        ),
        variants=[
            variant(
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
            variant(
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
            variant(
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
            variant(
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
