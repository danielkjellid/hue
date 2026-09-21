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
from urllib.parse import urlencode

import pytest
from django.http import HttpRequest, QueryDict
from django.urls import NoReverseMatch, clear_url_caches, include, path, resolve
from htmy.html import div as html_div
from hue.context import HueContextArgs
from hue.datatable import (
    BulkAction,
    Filter,
    TableColumns,
    TableFilters,
    TableOptions,
    TablePagination,
    TableSearch,
    datatable,
)
from hue.renderer import render_tree
from hue.ui.molecules.table import Column, DataTable

from hue_django.router import Router
from hue_django.views import HueView

# A pk nobody displays, which is the point of naming the identifier apart
# from the columns.
_INVOICES: list[dict[str, Any]] = [
    {"pk": "41", "invoice": "INV-2050", "customer": "Contoso", "amount": 2190},
    {"pk": "17", "invoice": "INV-2048", "customer": "Northwind", "amount": 1200},
    {"pk": "23", "invoice": "INV-2049", "customer": "Fabrikam", "amount": 840},
    {"pk": "58", "invoice": "INV-2051", "customer": "Adventure", "amount": 415},
]

# Paid for the two ends of the range, draft for the two in the middle,
# so a filter and a sort narrow to different rows and neither can pass
# for the other.
_STATUSES = {"41": "paid", "17": "draft", "23": "paid", "58": "draft"}
for _row in _INVOICES:
    _row["status"] = _STATUSES[_row["pk"]]

_STATUS = [("paid", "Paid"), ("draft", "Draft")]

_ARCHIVED: list[str] = []


def _matching(request: Any, asked: Any) -> Any:
    """
    The only part of a table that is not fixed: which rows answer it.
    """
    found = [
        row for row in _INVOICES if asked.query.lower() in str(row["customer"]).lower()
    ]
    if statuses := asked.chosen("status"):
        found = [row for row in found if row["status"] in statuses]
    if least := asked.value("min"):
        found = [row for row in found if row["amount"] >= int(least)]
    if asked.sort:
        field = asked.sort.lstrip("-")
        found.sort(key=lambda row: row[field], reverse=asked.sort.startswith("-"))
    return found


def _view(page_size: int = 25) -> Any:
    _ARCHIVED.clear()

    class InvoicesView(HueView):
        router = Router[HttpRequest]()

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

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
            filters=[
                Filter("status", "Status", options=_STATUS),
                Filter("min", "Minimum amount", kind="number"),
            ],
            hideable=["customer", "amount"],
            density=True,
            actions={
                "archive": BulkAction(
                    "Archive", lambda request, ids: _ARCHIVED.extend(ids)
                )
            },
            page_size=page_size,
        )

    return InvoicesView()


MOUNT = "billing/"


@pytest.fixture
def mounted(urlpatterns_: list[Any]) -> Any:
    """
    A view with a table on it, mounted under a prefix.

    Under a prefix on purpose: a table that spells its own path is right
    until the first include(), and nothing about that shows up when
    everything sits at the root.
    """

    def build(page_size: int = 25, at: str = MOUNT) -> Any:
        view = _view(page_size)
        urlpatterns_.append(path(at, include(type(view).urls)))
        clear_url_caches()
        return view

    return build


def _request(at: str | None = MOUNT, **params: str) -> Any:
    request = MagicMock()
    # A real QueryDict: what the table reads off it is every value under
    # a name, which is the part a flat mapping gets wrong.
    request.GET = QueryDict(urlencode(params, doseq=True))
    # What Django puts on the request before the view runs, and what the
    # namespace of every URL the table builds comes from. None for the
    # tests that never get as far as building one.
    request.resolver_match = resolve(f"/{at}") if at else None
    return request


def _render(component: Any) -> str:
    return asyncio.run(
        render_tree(
            component,
            context_args=HueContextArgs(request=HttpRequest(), csrf_token="t"),
        )
    )


def _part(bound: Any, part: Any) -> str:
    """
    One part of a table, rendered where it finds the binding: inside it.
    """
    return _render(bound.content(part))


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


def test_rows_is_handed_what_was_asked_for(mounted):
    bound = mounted().invoices.bind(_request(sort="-amount", q="n"))
    assert bound.state.sort == "-amount"
    assert bound.state.query == "n"
    # Contoso has an n in it too; descending by amount is the order asked.
    assert [row["customer"] for row in bound.page] == [
        "Contoso",
        "Northwind",
        "Adventure",
    ]


def test_a_sort_link_keeps_the_search(mounted):
    bound = mounted().invoices.bind(_request(sort="amount", q="contoso"))
    html = _part(bound, DataTable())
    hrefs = re.findall(r'<th[^>]*><a href="([^"]*)"', html)
    assert "/billing/invoices/?sort=-amount&amp;q=contoso" in hrefs


def test_a_search_keeps_the_order_and_drops_the_page(mounted):
    # Page four of a different search is not a page anybody asked for.
    bound = mounted(page_size=2).invoices.bind(_request(sort="-amount", page="2"))
    html = _part(bound, TableSearch())
    hidden = re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)"', html)
    assert hidden == [("sort", "-amount")]


def test_the_page_is_a_slice_and_the_count_is_everything(mounted):
    bound = mounted(page_size=2).invoices.bind(_request(page="2"))
    assert bound.total == 4
    assert [row["pk"] for row in bound.page] == ["23", "58"]


def test_pagination_links_keep_the_rest_of_the_state(mounted):
    bound = mounted(page_size=2).invoices.bind(_request(sort="-amount", q="n"))
    html = _part(bound, TablePagination())
    hrefs = re.findall(r'href="([^"]*)"', html)
    assert "/billing/invoices/?sort=-amount&amp;q=n&amp;page=2" in hrefs


def test_an_action_posts_to_a_url_that_remembers_the_state(mounted):
    # Otherwise archiving on page two of a sorted table answers with the
    # first page of an unsorted one.
    bound = mounted(page_size=2).invoices.bind(
        _request(sort="-amount", q="n", page="2")
    )
    html = _part(bound, DataTable())
    assert re.search(
        r'formaction="/billing/invoices/archive/\?sort=-amount&amp;q=n&amp;page=2"',
        html,
    )


def test_every_url_follows_the_mount_point(mounted):
    # The same declaration, included somewhere else. Nothing about the
    # table changed; where it lives did.
    bound = mounted(at="admin/reports/").invoices.bind(_request(at="admin/reports/"))
    assert bound.urls.read == "/admin/reports/invoices/"
    assert bound.urls.act == {"archive": "/admin/reports/invoices/archive/"}


def test_the_search_form_posts_back_to_the_mounted_table(mounted):
    bound = mounted().invoices.bind(_request())
    html = _part(bound, TableSearch())
    assert 'action="/billing/invoices/"' in html


def test_a_table_whose_view_is_not_serving_the_request_says_so(mounted):
    # Reversed through the namespace the request came in on, so a table
    # drawn from somewhere else has no URL to build - which is worth
    # saying rather than leaving as a bare NoReverseMatch.
    view = mounted()
    elsewhere = _request()
    elsewhere.resolver_match.namespace = "somebodyelse"

    try:
        view.invoices.bind(elsewhere)
    except NoReverseMatch as error:
        assert "somebodyelse:invoices_read" in str(error)
        assert "its own fragments" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a NoReverseMatch")


def test_the_checkboxes_carry_the_identifier_not_the_columns(mounted):
    bound = mounted().invoices.bind(_request())
    html = _part(bound, DataTable())
    picked = re.findall(r'name="selected" value="(\d+)"', html)
    assert picked == ["41", "17", "23", "58"]


def test_the_search_box_submits_itself_after_a_pause(mounted):
    bound = mounted().invoices.bind(_request())
    html = _part(bound, TableSearch())
    assert re.search(r'@input\.debounce\.300ms="\$el\.requestSubmit\(\)"', html)
    # The rows and not the frame, or the box would be swapped out from
    # under the caret that typed into it. replace, so a word typed at
    # speed is not a history entry per pause in it.
    assert re.search(r'x-target\.replace="invoices-rows"', html)


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
        bare.bind(_request(at=None))
    except ValueError as error:
        assert "identified by 'pk'" in str(error)
        assert "['invoice']" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")


def test_a_part_drawn_outside_a_bound_table_says_so():
    # The one slip this shape invites. Left alone it surfaces as an empty
    # table, or as a missing key on a context nobody was thinking about.
    for component in (TableSearch(), TablePagination()):
        try:
            _render(component)
        except ValueError as error:
            assert "bind(request)" in str(error)
            assert type(component).__name__ in str(error)
        else:  # pragma: no cover - the raise is the behaviour under test
            raise AssertionError(f"{component} drew itself out of nothing")


def test_a_datatable_with_no_columns_and_nothing_above_it_says_so():
    try:
        _render(DataTable())
    except ValueError as error:
        assert "bind(request)" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")


def test_the_search_box_answers_to_slash_and_escape(mounted):
    html = _part(mounted().invoices.bind(_request()), TableSearch())
    assert 'x-data="hueTableSearch"' in html
    assert 'x-on:keydown.window.slash="focusField($event)"' in html
    assert 'x-on:keydown.escape="clearField($event)"' in html


def test_the_pages_land_in_the_rows_and_are_a_place_to_come_back_to(mounted):
    bound = mounted(page_size=2).invoices.bind(_request())
    html = _part(bound, TablePagination())
    assert 'x-target.push="invoices-rows"' in html


def test_a_filter_narrows_the_rows_it_names(mounted):
    bound = mounted().invoices.bind(_request(status="paid"))
    assert bound.state.chosen("status") == ("paid",)
    assert [row["pk"] for row in bound.page] == ["41", "23"]


def test_several_answers_to_one_filter_ride_in_one_parameter(mounted):
    bound = mounted().invoices.bind(_request(status="paid,draft"))
    assert bound.state.chosen("status") == ("paid", "draft")
    assert len(bound.page) == 4


def test_an_answer_the_filter_never_offered_is_dropped(mounted):
    # The query string is somewhere anybody can type, and rows() should
    # not have to defend itself against what lands in it.
    bound = mounted().invoices.bind(_request(status="paid,whatever"))
    assert bound.state.chosen("status") == ("paid",)


def test_a_filter_with_nothing_to_tick_takes_what_it_is_given(mounted):
    bound = mounted().invoices.bind(_request(min="1000"))
    assert bound.state.value("min") == "1000"
    assert [row["pk"] for row in bound.page] == ["41", "17"]


def test_a_filter_rides_in_every_url_the_table_builds(mounted):
    bound = mounted().invoices.bind(_request(status="paid", sort="amount"))
    assert bound.href(sort="-amount") == "/billing/invoices/?sort=-amount&status=paid"


def test_the_panel_says_what_is_on_and_the_chips_undo_it(mounted):
    html = _part(mounted().invoices.bind(_request(status="paid")), TableFilters())
    assert 'x-data="hueTableFilters"' in html
    # The count on the trigger and the chips in the band are the same
    # fact twice, both read off the controls rather than sent down.
    assert 'x-text="applied.length"' in html
    assert 'x-for="chip in applied"' in html
    assert 'data-filter="status"' in html
    assert 'data-option="Paid"' in html
    assert re.search(r'id="invoices-status-paid"[^>]*checked', html) or re.search(
        r'checked[^>]*id="invoices-status-paid"', html
    )


def test_a_filter_cannot_be_called_what_the_table_already_calls_something():
    for taken in ("sort", "q", "page"):
        try:
            datatable(
                Router[HttpRequest](),
                key=f"clash_{taken}",
                columns=[Column("invoice", "Invoice")],
                rows=lambda request, asked: _INVOICES,
                filters=[Filter(taken, "Clash")],
            )
        except ValueError as error:
            assert taken in str(error)
        else:  # pragma: no cover - the raise is the behaviour under test
            raise AssertionError(f"a filter called {taken!r} was accepted")


def test_a_browser_repeating_a_name_is_read_the_same_as_a_comma(mounted):
    # A set of checkboxes sharing a name is how a browser submits a
    # list; the links the table builds join them with commas. Both are
    # the same question.
    view = mounted()
    request = MagicMock()
    request.GET = QueryDict("status=paid&status=draft")
    request.resolver_match = resolve(f"/{MOUNT}")
    assert view.invoices.bind(request).state.chosen("status") == ("paid", "draft")


def test_a_hidden_column_is_not_drawn(mounted):
    bound = mounted().invoices.bind(_request(hide="customer"))
    assert bound.state.hidden == ("customer",)
    html = _render(bound)
    assert "Northwind" not in html
    assert "INV-2048" in html


def test_a_column_nobody_may_hide_stays(mounted):
    # Typed into the URL rather than clicked, which is the only way to
    # ask for it - and the answer is no.
    bound = mounted().invoices.bind(_request(hide="invoice"))
    assert bound.state.hidden == ()
    assert "INV-2048" in _render(bound)


def test_the_panel_ticks_the_columns_that_are_showing(mounted):
    # The way round anybody reads a list of columns, while the URL
    # carries the ones that are hidden.
    html = _part(mounted().invoices.bind(_request(hide="customer")), TableColumns())
    assert 'hueTableColumns(["customer"])' in html
    assert "x-effect=\"$el.checked = showing('customer')\"" in html
    assert "Locked" in html


def test_density_is_a_radio_and_a_link(mounted):
    html = _part(mounted().invoices.bind(_request(density="compact")), TableOptions())
    assert 'role="menuitemradio"' in html
    assert 'aria-checked="true"' in html
    assert "/billing/invoices/?density=compact" in html
    # And a way back to the table as it came.
    assert "Reset view" in html


def test_compact_tightens_the_rows(mounted):
    loose = _render(mounted().invoices.bind(_request()))
    tight = _render(mounted().invoices.bind(_request(density="compact")))
    assert "_td]:py-[11px]" in loose
    assert "_td]:py-[7px]" in tight


def test_hiding_a_column_nobody_declared_is_refused():
    try:
        datatable(
            Router[HttpRequest](),
            key="strangers",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            hideable=["nonesuch"],
        )
    except ValueError as error:
        assert "nonesuch" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")


def test_the_whole_table_is_one_component(mounted):
    # No parts to place: bound and rendered is the search box, the rows
    # and the pages.
    html = _render(mounted().invoices.bind(_request()))
    assert re.search(r'name="q"', html)
    assert re.search(r"<table", html)
    assert re.search(r'aria-label="Pagination', html)
    # Welded: one frame, with the search in a band above the rows and the
    # pages in a band below them.
    assert html.count("w-full rounded-lg border border-border bg-surface") == 1


def test_the_parts_can_be_placed_instead(mounted):
    # And each of them finds the same binding, however deeply it is laid
    # out inside the view.
    bound = mounted().invoices.bind(_request())
    html = _render(bound.content(html_div(TablePagination()), DataTable()))
    assert re.search(r"<table", html)
    assert re.search(r'aria-label="Pagination', html)
    assert 'type="search"' not in html
