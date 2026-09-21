"""
The datatable() declaration, end to end against a Django request.

What this is here to show is that nothing between the header link and the
handler is wired by hand: the routes, the URLs and the id they are swapped
into all come off the one key.
"""

import asyncio
import re
from typing import Any
from unittest.mock import MagicMock

from django.http import HttpRequest
from hue.context import HueContextArgs
from hue.datatable import BulkAction, DataTableState, TableState, datatable
from hue.renderer import render_tree
from hue.ui.molecules.table import Column

from hue_django.router import Router

_INVOICES = [
    {"invoice": "INV-2050", "amount": "2190"},
    {"invoice": "INV-2048", "amount": "1200"},
]


def _build(archived: list[str]) -> tuple[Router[HttpRequest], DataTableState]:
    router = Router[HttpRequest]()
    state = datatable(
        router,
        key="invoices",
        columns=[
            Column("invoice", "Invoice"),
            Column("amount", "Amount", align="end", sort="amount"),
        ],
        # The whole read path: given the order that was asked for, the rows
        # in it. No handler sits between the click and this.
        rows=lambda asked: sorted(
            _INVOICES,
            key=lambda row: row["amount"],
            reverse=(asked.sort or "").startswith("-"),
        ),
        select="invoice",
        actions={
            "archive": BulkAction("Archive", lambda request, ids: archived.extend(ids))
        },
    )
    return router, state


def _render(component: Any) -> str:
    return asyncio.run(
        render_tree(
            component,
            context_args=HueContextArgs(request=HttpRequest(), csrf_token="t"),
        )
    )


def test_one_declaration_registers_a_route_to_read_and_one_to_act():
    router, _ = _build([])
    assert [(route.method, route.path) for route in router.routes] == [
        ("GET", "invoices/"),
        ("POST", "invoices/<str:action>/"),
    ]


def test_the_routes_are_named_after_the_table():
    # The router takes a route's name off __name__ as it decorates, so two
    # tables on one view would otherwise both be called "read" and "act".
    router, _ = _build([])
    assert [route.name for route in router.routes] == ["invoices_read", "invoices_act"]


def test_the_header_links_to_its_own_route_and_swaps_itself():
    _, state = _build([])
    html = _render(state.build(TableState()))
    link = re.search(r'<th[^>]*>\s*<a href="([^"]*)"[^>]*x-target="([^"]*)"', html)
    assert link is not None
    assert link.group(1) == "/invoices/?sort=amount"
    assert link.group(2) == "invoices"


def test_the_order_asked_for_is_the_order_the_rows_come_back_in():
    _, state = _build([])
    descending = _render(state.build(TableState(sort="-amount")))
    first = re.search(r"<tbody.*?INV-(\d+)", descending, re.S)
    assert first is not None
    assert first.group(1) == "2050"


def test_the_selection_posts_through_a_real_form():
    _, state = _build([])
    html = _render(state.build(TableState()))
    assert re.search(
        r'<form method="post" action="/invoices/" x-target="invoices"', html
    )
    assert re.search(r'formaction="/invoices/archive/"', html)
    # Ascending by default, which is what rows() was asked for.
    assert re.findall(r'name="selected" value="(INV-\d+)"', html) == [
        "INV-2048",
        "INV-2050",
    ]


def test_an_action_is_handed_the_ids_as_python():
    archived: list[str] = []
    router, state = _build(archived)
    request = MagicMock()
    request.POST.getlist.return_value = ["INV-2050", "INV-2048"]

    state.actions["archive"].handler(
        request, router._get_form_list(request, "selected")
    )

    assert archived == ["INV-2050", "INV-2048"]


def test_a_flat_form_dict_would_have_kept_only_the_last_one():
    # Which is why there is a _get_form_list at all.
    router = Router[HttpRequest]()
    request = MagicMock()
    request.POST.dict.return_value = {"selected": "INV-2048"}
    request.POST.getlist.return_value = ["INV-2050", "INV-2048"]

    assert router._get_form_data(request)["selected"] == "INV-2048"
    assert router._get_form_list(request, "selected") == ["INV-2050", "INV-2048"]
