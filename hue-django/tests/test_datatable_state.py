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
from htmy import html
from hue.context import HueContextArgs
from hue.datatable import (
    BoundTable,
    BulkAction,
    DataTableState,
    TableSearch,
    TableState,
    datatable,
)
from hue.renderer import render_tree
from hue.ui.molecules.table import Column, DataTable

from hue_django.router import Router

# A pk nobody displays, which is the point of naming the identifier
# separately from the columns.
_INVOICES = [
    {"pk": "41", "invoice": "INV-2050", "amount": "2190"},
    {"pk": "17", "invoice": "INV-2048", "amount": "1200"},
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
        identifier="pk",
        actions={
            "archive": BulkAction("Archive", lambda request, ids: archived.extend(ids))
        },
    )
    return router, state


def _bound(state: DataTableState, asked: TableState) -> Any:
    """
    The two components a bound state gives you, as one tree.
    """

    bound = BoundTable(state, asked)
    parts: list[Any] = []
    if state.search is not None:
        parts.append(TableSearch.from_state(bound))
    parts.append(DataTable.from_state(bound))
    return html.div(*parts)


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
    html = _render(_bound(state, TableState()))
    link = re.search(r'<th[^>]*>\s*<a href="([^"]*)"[^>]*x-target="([^"]*)"', html)
    assert link is not None
    assert link.group(1) == "/invoices/?sort=amount"
    assert link.group(2) == "invoices"


def test_the_order_asked_for_is_the_order_the_rows_come_back_in():
    _, state = _build([])
    descending = _render(_bound(state, TableState(sort="-amount")))
    first = re.search(r"<tbody.*?INV-(\d+)", descending, re.S)
    assert first is not None
    assert first.group(1) == "2050"


def test_the_selection_posts_through_a_real_form():
    _, state = _build([])
    html = _render(_bound(state, TableState()))
    assert re.search(
        r'<form method="post" action="/invoices/" x-target="invoices"', html
    )
    assert re.search(r'formaction="/invoices/archive/"', html)
    # The pk, not the invoice reference: what a row is known by is not
    # what a row shows.
    assert re.findall(r'name="selected" value="(\d+)"', html) == ["17", "41"]


def test_an_action_is_handed_the_ids_as_python():
    archived: list[str] = []
    router, state = _build(archived)
    request = MagicMock()
    request.POST.getlist.return_value = ["41", "17"]

    state.actions["archive"].handler(
        request, router._get_form_list(request, "selected")
    )

    assert archived == ["41", "17"]


def test_a_flat_form_dict_would_have_kept_only_the_last_one():
    # Which is why there is a _get_form_list at all.
    router = Router[HttpRequest]()
    request = MagicMock()
    request.POST.dict.return_value = {"selected": "INV-2048"}
    request.POST.getlist.return_value = ["INV-2050", "INV-2048"]

    assert router._get_form_data(request)["selected"] == "INV-2048"
    assert router._get_form_list(request, "selected") == ["INV-2050", "INV-2048"]


def _searchable(rows_seen: list[str]) -> tuple[Router[HttpRequest], DataTableState]:
    router = Router[HttpRequest]()
    state = datatable(
        router,
        key="invoices",
        columns=[Column("invoice", "Invoice")],
        rows=lambda asked: (
            rows_seen.append(asked.query)
            or [row for row in _INVOICES if asked.query in row["invoice"]]
        ),
        search="Search invoices",
    )
    return router, state


def test_the_search_box_submits_itself_after_a_pause():
    # Debounced so a word typed at speed is one request rather than five,
    # and a form so Enter already works without any of this.
    _, state = _searchable([])
    html = _render(_bound(state, TableState()))
    assert re.search(r'@input\.debounce\.300ms="\$el\.requestSubmit\(\)"', html)
    assert re.search(
        r'<form method="get" action="/invoices/"[^>]*x-target="invoices"', html
    )


def test_the_box_sits_outside_what_gets_replaced():
    # A box swapped out from under the person typing in it loses the caret.
    _, state = _searchable([])
    html = _render(_bound(state, TableState()))
    form_at = html.index("<form")
    frame_at = html.index('id="invoices"')
    assert form_at < frame_at
    assert html.index("</form>") < frame_at


def test_what_was_searched_for_reaches_rows_and_comes_back_in_the_box():
    seen: list[str] = []
    _, state = _searchable(seen)
    html = _render(_bound(state, TableState(query="2050")))
    assert seen == ["2050"]
    assert "INV-2050" in html
    assert "INV-2048" not in html
    assert re.search(r'value="2050"', html)


def test_a_search_keeps_the_order_it_was_already_in():
    _, state = _build([])
    assert state.href(TableState(sort="-amount", query="acme")) == (
        "/invoices/?sort=-amount&q=acme"
    )


def test_actions_with_nothing_to_hand_them_are_refused():
    router = Router[HttpRequest]()
    try:
        datatable(
            router,
            key="invoices",
            columns=[Column("invoice", "Invoice")],
            rows=lambda asked: _INVOICES,
            actions={"archive": BulkAction("Archive", lambda request, ids: None)},
        )
    except ValueError as error:
        assert "identifier" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")


def test_rows_that_do_not_carry_the_identifier_are_refused():
    # Otherwise the first checkbox raises about a missing dict key, and a
    # table whose ids are quietly absent posts an empty selection.
    router = Router[HttpRequest]()
    state = datatable(
        router,
        key="invoices",
        columns=[Column("invoice", "Invoice")],
        rows=lambda asked: [{"invoice": "INV-2050"}],
        identifier="pk",
    )
    try:
        _render(_bound(state, TableState()))
    except ValueError as error:
        assert "identified by 'pk'" in str(error)
        assert "['invoice']" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")
