"""
One page with one declared table on it, backed by a real queryset.

Everything the table does is on the declaration: the routes that serve
it are registered here, at class scope, and the view draws it with
DataTable.from_state().
"""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest
from htmy import html
from hue import toast
from hue.context import HueContext
from hue.datatable import BulkAction, Filter, TableState, build_datatable_state
from hue.types.core import ComponentType
from hue.ui import Badge, Column, DataTable, Dialog, Stack, Text, ToastRegion
from hue.ui.atoms.icon import HueIcon
from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueView

from example.invoices.models import Invoice

_TONES = {
    Invoice.Status.PAID: "success",
    Invoice.Status.PENDING: "warning",
    Invoice.Status.DECLINED: "danger",
    Invoice.Status.DRAFT: "neutral",
}


def invoices_for(request: HttpRequest, asked: TableState) -> QuerySet[Any]:
    """
    Every invoice the state asks for, as the dictionaries the table reads.
    """
    found = Invoice.objects.filter(archived=False)
    if asked.query:
        found = found.filter(customer__name__icontains=asked.query)
    if statuses := asked.chosen("status"):
        found = found.filter(status__in=statuses)
    if least := asked.value("min"):
        # Typed into a field, so it can be anything. Something that is not
        # a number narrows nothing.
        try:
            found = found.filter(amount__gte=Decimal(least))
        except InvalidOperation:
            pass
    return found.order_by(asked.sort or "-issued_on", "pk").values(
        "pk", "reference", "customer__name", "amount", "status", "issued_on"
    )


def _invoices(count: int) -> str:
    return f"{count} invoice" if count == 1 else f"{count} invoices"


def archive(request: HttpRequest, ids: list[str]) -> None:
    archived = Invoice.objects.filter(pk__in=ids).update(archived=True)
    toast.success(f"Archived {_invoices(archived)}")


def mark_paid(request: HttpRequest, ids: list[str]) -> None:
    paid = Invoice.objects.filter(pk__in=ids).update(status=Invoice.Status.PAID)
    toast.success(f"Marked {_invoices(paid)} as paid")


def _amount(row: Mapping[str, Any]) -> ComponentType:
    return f"${row['amount']:,.2f}"


def _status(row: Mapping[str, Any]) -> ComponentType:
    status = Invoice.Status(row["status"])
    return Badge().variant(_TONES[status]).dot().content(status.label)  # type: ignore[arg-type]


class InvoicesView(HueView):
    router = Router[HttpRequest]()

    invoices = build_datatable_state(
        router,
        key="invoices",
        columns=[
            Column("reference", "Invoice"),
            Column("customer__name", "Customer", sort="customer__name"),
            Column("issued_on", "Issued", sort="issued_on"),
            Column("status", "Status", render=_status),
            Column("amount", "Amount", align="end", sort="amount", render=_amount),
        ],
        rows=invoices_for,
        identifier="pk",
        search="Search customers",
        filters=[
            Filter(
                "status",
                "Status",
                # The labels are lazy strings, translated when read.
                options=[
                    (value, str(label)) for value, label in Invoice.Status.choices
                ],
            ),
            Filter("min", "Minimum amount", numeric=True, prefix="USD"),
        ],
        hideable=["customer__name", "issued_on", "status"],
        actions={
            "paid": BulkAction("Mark as paid", mark_paid, icon=HueIcon("check")),
            "archive": BulkAction(
                "Archive",
                archive,
                confirm=Dialog()
                .title("Archive these invoices?")
                .description("They leave the table until the database is reseeded."),
            ),
        },
        page_size=10,
    )

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ) -> Page:
        return Page(
            title="Invoices",
            body=html.main(
                Stack()
                .spacing("lg")
                .align_items("items-stretch")
                .content(
                    Text("Invoices").variant("title-2").tag(html.h1),
                    DataTable.from_state(self.invoices),
                ),
                # Once per page, and there before the first toast: a live
                # region made together with its content is not read out.
                ToastRegion(),
                class_="example-page",
            ),
        )
