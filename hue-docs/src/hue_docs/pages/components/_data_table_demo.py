from __future__ import annotations

from typing import Any

from fastapi import Request
from hue import html, toast
from hue.context import HueContext
from hue.datatable import BulkAction, Filter, TableState, build_datatable_state
from hue.ui import Badge, Column, DataTable, ToastRegion
from hue.ui.atoms.badge import BadgeVariant
from hue_fastapi import HueView, Page, Router

# A list of dictionaries, so the filtering, ordering and paging are the
# Python below. A database query does the same in rows=.
INVOICES: list[dict[str, Any]] = [
    {
        "pk": "41",
        "invoice": "INV-2050",
        "customer": "Contoso",
        "amount": 2190,
        "status": "pending",
    },
    {
        "pk": "17",
        "invoice": "INV-2048",
        "customer": "Northwind",
        "amount": 1200,
        "status": "paid",
    },
    {
        "pk": "23",
        "invoice": "INV-2049",
        "customer": "Fabrikam",
        "amount": 840,
        "status": "overdue",
    },
    {
        "pk": "58",
        "invoice": "INV-2051",
        "customer": "Adventure Works",
        "amount": 415,
        "status": "paid",
    },
    {
        "pk": "62",
        "invoice": "INV-2052",
        "customer": "Tailspin Toys",
        "amount": 3120,
        "status": "paid",
    },
    {
        "pk": "70",
        "invoice": "INV-2053",
        "customer": "Litware",
        "amount": 960,
        "status": "pending",
    },
    {
        "pk": "74",
        "invoice": "INV-2054",
        "customer": "Proseware",
        "amount": 1875,
        "status": "overdue",
    },
    {
        "pk": "81",
        "invoice": "INV-2055",
        "customer": "Wingtip",
        "amount": 230,
        "status": "paid",
    },
]

STATUS = [("paid", "Paid"), ("pending", "Pending"), ("overdue", "Overdue")]
TONE: dict[str, BadgeVariant] = {
    "paid": "success",
    "pending": "warning",
    "overdue": "danger",
}


def invoices_for(request: Request, asked: TableState) -> list[dict[str, Any]]:
    found = [row for row in INVOICES if asked.query.lower() in row["customer"].lower()]
    if statuses := asked.chosen("status"):
        found = [row for row in found if row["status"] in statuses]
    if asked.sort:
        field = asked.sort.removeprefix("-")
        found.sort(key=lambda row: row[field], reverse=asked.sort.startswith("-"))
    return found


def archive_invoices(request: Request, ids: list[str]) -> None:
    # Every reader of the docs shares this table, so it changes nothing.
    toast.success(f"Archived {len(ids)}", description="The demo keeps the rows.")


class InvoicesView(HueView):
    router = Router[Request]()

    invoices = build_datatable_state(
        router,
        key="invoices",
        columns=[
            Column("invoice", "Invoice"),
            Column("customer", "Customer", sort="customer"),
            Column("amount", "Amount", align="end", sort="amount"),
            Column(
                "status",
                "Status",
                render=lambda row: (
                    Badge().variant(TONE[row["status"]]).content(row["status"].title())
                ),
            ),
        ],
        rows=invoices_for,
        identifier="pk",
        search="Search customers",
        filters=[Filter("status", "Status", options=STATUS)],
        hideable=["customer", "status"],
        actions={"archive": BulkAction("Archive", archive_invoices)},
        page_size=3,
    )

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(
            title="Invoices",
            body=html.div(
                html.div(DataTable.from_state(self.invoices))
                .id("invoices-demo")
                .class_("w-full"),
                ToastRegion(),
            ).class_("p-4"),
        )
