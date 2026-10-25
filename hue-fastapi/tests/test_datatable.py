"""
A declared table end to end on FastAPI: the one consumer of every request
hook at once, mounted under a prefix because that is where a table that
spells its own URLs goes wrong.
"""

from typing import Any

from hue.datatable import BulkAction, Filter, build_datatable_state
from hue.ui.molecules.datatable import Column, DataTable
from starlette.requests import Request

from hue_fastapi import HueView, Page, Router
from tests.conftest import ALPINE_AJAX_HEADERS, make_app

_INVOICES = [
    {"pk": "41", "customer": "Contoso", "amount": 2190, "status": "paid"},
    {"pk": "17", "customer": "Northwind", "amount": 1200, "status": "draft"},
    {"pk": "23", "customer": "Fabrikam", "amount": 840, "status": "paid"},
]
_ARCHIVED: list[str] = []


def _matching(request: Any, asked: Any) -> list[dict[str, Any]]:
    found = list(_INVOICES)
    if statuses := asked.chosen("status"):
        found = [row for row in found if row["status"] in statuses]
    if asked.sort:
        field = asked.sort.lstrip("-")
        found.sort(key=lambda row: row[field], reverse=asked.sort.startswith("-"))
    return found


class Invoices(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: Any) -> Page:
        return Page(title="Invoices", body=DataTable.from_state(self.invoices))

    invoices = build_datatable_state(
        router,
        key="invoices",
        columns=[
            Column("customer", "Customer"),
            Column("amount", "Amount", sort="amount"),
        ],
        rows=_matching,
        identifier="pk",
        filters=[Filter("status", "Status", options=[("paid", "Paid")])],
        actions={
            "archive": BulkAction("Archive", lambda request, ids: _ARCHIVED.extend(ids))
        },
    )


async def test_the_page_links_its_actions_under_the_mount(client_for):
    async with client_for(make_app(("/billing", Invoices))) as client:
        html = (await client.get("/billing/?invoices-status=paid")).text

    assert 'formaction="/billing/invoices/archive/"' in html
    assert "Northwind" not in html


async def test_an_action_gets_only_rows_the_reader_could_see(client_for):
    _ARCHIVED.clear()
    async with client_for(make_app(("/billing", Invoices))) as client:
        response = await client.post(
            "/billing/invoices/archive/",
            data={
                "selected": ["41", "17", "nonesuch"],
                "invoices-status": "paid",
                "invoices-sort": "amount",
            },
            headers=ALPINE_AJAX_HEADERS,
        )

    assert response.status_code == 200
    assert _ARCHIVED == ["41"]
    assert 'aria-sort="ascending"' in response.text


async def test_an_unknown_action_is_not_found(client_for):
    async with client_for(make_app(("/billing", Invoices))) as client:
        response = await client.post(
            "/billing/invoices/nonesuch/", headers=ALPINE_AJAX_HEADERS
        )

    assert response.status_code == 404


async def _matching_async(request: Any, asked: Any) -> list[dict[str, Any]]:
    return _matching(request, asked)


async def _archive_async(request: Any, ids: list[str]) -> None:
    _ARCHIVED.extend(ids)


class AsyncInvoices(HueView):
    router = Router[Request]()

    async def index(self, request: Request, context: Any) -> Page:
        return Page(title="Invoices", body=DataTable.from_state(self.invoices))

    invoices = build_datatable_state(
        router,
        key="invoices",
        columns=[Column("customer", "Customer")],
        rows=_matching_async,
        identifier="pk",
        actions={"archive": BulkAction("Archive", _archive_async)},
    )


async def test_async_rows_and_an_async_action_both_run(client_for):
    """
    An async def is awaited on the loop. Handed to the thread pool like a
    plain function, it would return a coroutine nobody awaits.
    """
    _ARCHIVED.clear()
    async with client_for(make_app(("/billing", AsyncInvoices))) as client:
        page = await client.get("/billing/")
        response = await client.post(
            "/billing/invoices/archive/",
            data={"selected": ["41", "nonesuch"]},
            headers=ALPINE_AJAX_HEADERS,
        )

    assert "Northwind" in page.text
    assert response.status_code == 200
    assert _ARCHIVED == ["41"]
