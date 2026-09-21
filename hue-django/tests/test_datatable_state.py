"""
The @datatable declaration, end to end against a Django view.

What this is here to show is that every way into the table goes through
the one described method, so a sort, a search, a page and an action all
come back with the table in the state it was in.
"""

import asyncio
import re
from typing import Any
from unittest.mock import MagicMock

from django.http import HttpRequest
from hue.context import HueContextArgs
from hue.datatable import BulkAction, TablePagination, TableSearch, datatable
from hue.renderer import render_tree
from hue.ui.molecules.table import Column, DataTable

from hue_django.router import Router

# A pk nobody displays, which is the point of naming the identifier apart
# from the columns.
_INVOICES: list[dict[str, Any]] = [
    {"pk": "41", "invoice": "INV-2050", "customer": "Contoso", "amount": 2190},
    {"pk": "17", "invoice": "INV-2048", "customer": "Northwind", "amount": 1200},
    {"pk": "23", "invoice": "INV-2049", "customer": "Fabrikam", "amount": 840},
    {"pk": "58", "invoice": "INV-2051", "customer": "Adventure", "amount": 415},
]

_ARCHIVED: list[str] = []


def _matching(request: Any, asked: Any) -> Any:
    """
    The only part of a table that is not fixed: which rows answer it.
    """
    found = [
        row for row in _INVOICES if asked.query.lower() in str(row["customer"]).lower()
    ]
    if asked.sort:
        field = asked.sort.lstrip("-")
        found.sort(key=lambda row: row[field], reverse=asked.sort.startswith("-"))
    return found


def _view(page_size: int = 25) -> Any:
    _ARCHIVED.clear()

    class InvoicesView:
        router = Router[HttpRequest]()

        invoices = datatable(
            router,
            key="invoices",
            columns=[
                Column("invoice", "Invoice"),
                Column("customer", "Customer", sort="customer"),
                Column("amount", "Amount", align="end", sort="amount"),
            ],
            rows=_matching,
            identifier="pk",
            search="Search customers",
            actions={
                "archive": BulkAction(
                    "Archive", lambda request, ids: _ARCHIVED.extend(ids)
                )
            },
            page_size=page_size,
        )

    return InvoicesView()


def _request(**params: str) -> Any:
    request = MagicMock()
    request.GET.dict.return_value = params
    return request


def _render(component: Any) -> str:
    return asyncio.run(
        render_tree(
            component,
            context_args=HueContextArgs(request=HttpRequest(), csrf_token="t"),
        )
    )


def test_the_declaration_registers_a_route_to_read_and_one_to_act():
    view = _view()
    assert [(route.method, route.path) for route in type(view).router.routes] == [
        ("GET", "invoices/"),
        ("POST", "invoices/<str:action>/"),
    ]


def test_the_routes_are_named_after_the_table():
    # The router takes a route's name off __name__ as it decorates, so two
    # tables on one view would otherwise both be called "read" and "act".
    view = _view()
    assert [route.name for route in type(view).router.routes] == [
        "invoices_read",
        "invoices_act",
    ]


def test_rows_is_handed_what_was_asked_for():
    bound = _view().invoices.bind(_request(sort="-amount", q="n"))
    assert bound.state.sort == "-amount"
    assert bound.state.query == "n"
    # Contoso has an n in it too; descending by amount is the order asked.
    assert [row["customer"] for row in bound.page] == [
        "Contoso",
        "Northwind",
        "Adventure",
    ]


def test_a_sort_link_keeps_the_search():
    bound = _view().invoices.bind(_request(sort="amount", q="contoso"))
    html = _render(DataTable.from_state(bound))
    hrefs = re.findall(r'<th[^>]*><a href="([^"]*)"', html)
    assert "/invoices/?sort=-amount&amp;q=contoso" in hrefs


def test_a_search_keeps_the_order_and_drops_the_page():
    # Page four of a different search is not a page anybody asked for.
    bound = _view(page_size=2).invoices.bind(_request(sort="-amount", page="2"))
    html = _render(TableSearch.from_state(bound))
    hidden = re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)"', html)
    assert hidden == [("sort", "-amount")]


def test_the_page_is_a_slice_and_the_count_is_everything():
    bound = _view(page_size=2).invoices.bind(_request(page="2"))
    assert bound.total == 4
    assert [row["pk"] for row in bound.page] == ["23", "58"]


def test_pagination_links_keep_the_rest_of_the_state():
    bound = _view(page_size=2).invoices.bind(_request(sort="-amount", q="n"))
    html = _render(TablePagination.from_state(bound))
    hrefs = re.findall(r'href="([^"]*)"', html)
    assert "/invoices/?sort=-amount&amp;q=n&amp;page=2" in hrefs


def test_an_action_posts_to_a_url_that_remembers_the_state():
    # Otherwise archiving on page two of a sorted table answers with the
    # first page of an unsorted one.
    bound = _view(page_size=2).invoices.bind(_request(sort="-amount", q="n", page="2"))
    html = _render(DataTable.from_state(bound))
    assert re.search(
        r'formaction="/invoices/archive/\?sort=-amount&amp;q=n&amp;page=2"', html
    )


def test_the_checkboxes_carry_the_identifier_not_the_columns():
    bound = _view().invoices.bind(_request())
    html = _render(DataTable.from_state(bound))
    picked = re.findall(r'name="selected" value="(\d+)"', html)
    assert picked == ["41", "17", "23", "58"]


def test_the_search_box_submits_itself_after_a_pause():
    bound = _view().invoices.bind(_request())
    html = _render(TableSearch.from_state(bound))
    assert re.search(r'@input\.debounce\.300ms="\$el\.requestSubmit\(\)"', html)
    assert re.search(r'x-target="invoices"', html)


def test_actions_with_nothing_to_hand_them_are_refused():
    try:
        datatable(
            Router[HttpRequest](),
            key="nothing",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            actions={"archive": BulkAction("Archive", lambda request, ids: None)},
        )
    except ValueError as error:
        assert "identifier" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")


def test_rows_that_do_not_carry_the_identifier_are_refused():
    bare = datatable(
        Router[HttpRequest](),
        key="bare",
        columns=[Column("invoice", "Invoice")],
        rows=lambda request, asked: [{"invoice": "INV-2050"}],
        identifier="pk",
    )

    try:
        bare.bind(_request())
    except ValueError as error:
        assert "identified by 'pk'" in str(error)
        assert "['invoice']" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")


def test_forgetting_to_bind_says_so():
    # The one slip this shape invites. Left alone it surfaces as a missing
    # attribute on a class nobody was thinking about.
    declaration = type(_view()).invoices

    for component, from_state in (
        ("DataTable", DataTable.from_state),
        ("TableSearch", TableSearch.from_state),
        ("TablePagination", TablePagination.from_state),
    ):
        try:
            from_state(declaration)
        except TypeError as error:
            assert "bound to a request" in str(error)
            assert "bind(request)" in str(error)
            assert component in str(error)
        else:  # pragma: no cover - the raise is the behaviour under test
            raise AssertionError(f"{component} accepted an unbound table")


def test_something_else_entirely_is_refused_too():
    try:
        DataTable.from_state("not a table")  # type: ignore[arg-type]
    except TypeError as error:
        assert "not str" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a TypeError")
