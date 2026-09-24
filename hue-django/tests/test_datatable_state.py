"""
The @datatable declaration, end to end against a Django view.

What this is here to show is that every way into the table goes through
the one described method, so a sort, a search, a page and an action all
come back with the table in the state it was in.
"""

import asyncio
import re
from html.parser import HTMLParser
from typing import Any, ClassVar
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from django.http import HttpRequest, QueryDict
from django.test import Client
from django.urls import NoReverseMatch, clear_url_caches, include, path, resolve
from htmy.html import div as html_div
from hue.context import HueContextArgs
from hue.datatable import (
    BulkAction,
    Filter,
    TableColumns,
    TableFilters,
    TablePagination,
    TableReset,
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


def _render(component: Any, request: Any = None) -> str:
    """
    A component rendered for a request, the way a page renders it: the
    request goes in the context, which is where a table looks for it.
    """
    return asyncio.run(
        render_tree(
            component,
            context_args=HueContextArgs(
                request=HttpRequest() if request is None else request,
                csrf_token="t",
            ),
        )
    )


class _Nesting(HTMLParser):
    """
    The ids of every element open around the first one whose aria-label
    starts with a given word.
    """

    VOID: ClassVar[set[str]] = {
        "input",
        "img",
        "br",
        "hr",
        "meta",
        "link",
        "source",
        "path",
        "circle",
    }

    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label
        self.open: list[str | None] = []
        self.found: list[str | None] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        named = dict(attrs)
        if self.found is None and (named.get("aria-label") or "").startswith(
            self.label
        ):
            self.found = list(self.open)
        if tag not in self.VOID:
            self.open.append(named.get("id"))

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.VOID and self.open:
            self.open.pop()


def _ids_around(html: str, label: str) -> list[str | None]:
    nesting = _Nesting(label)
    nesting.feed(html)
    assert nesting.found is not None, f"nothing labelled {label!r}"
    return nesting.found


def _bind(declaration: Any, request: Any) -> Any:
    """
    The values a table was drawn from. bind() is a coroutine - it runs
    rows() through the router - and these tests are sync.
    """
    return asyncio.run(declaration.bind(request))


def _table(declaration: Any, request: Any) -> str:
    """
    The whole table, drawn the way a view draws it.
    """
    return _render(DataTable.from_state(declaration), request)


def _part(declaration: Any, request: Any, part: Any) -> str:
    """
    One part of a table, rendered where it finds the binding: in a layout.
    """
    return _render(declaration.layout(part), request)


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
    bound = _bind(mounted().invoices, _request(sort="-amount", q="n"))
    assert bound.state.sort == "-amount"
    assert bound.state.query == "n"
    # Contoso has an n in it too; descending by amount is the order asked.
    assert [row["customer"] for row in bound.page] == [
        "Contoso",
        "Northwind",
        "Adventure",
    ]


def test_a_sort_link_keeps_the_search(mounted):
    html = _part(mounted().invoices, _request(sort="amount", q="contoso"), DataTable())
    hrefs = re.findall(r'<th[^>]*><a href="([^"]*)"', html)
    assert "/billing/invoices/?sort=-amount&amp;q=contoso" in hrefs


def test_a_search_keeps_the_order_and_drops_the_page(mounted):
    # Page four of a different search is not a page anybody asked for.
    html = _part(
        mounted(page_size=2).invoices, _request(sort="-amount", page="2"), TableSearch()
    )
    hidden = re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)"', html)
    assert hidden == [("sort", "-amount")]


def test_the_page_is_a_slice_and_the_count_is_everything(mounted):
    bound = _bind(mounted(page_size=2).invoices, _request(page="2"))
    assert bound.total == 4
    assert [row["pk"] for row in bound.page] == ["23", "58"]


def test_pagination_links_keep_the_rest_of_the_state(mounted):
    html = _part(
        mounted(page_size=2).invoices,
        _request(sort="-amount", q="n"),
        TablePagination(),
    )
    hrefs = re.findall(r'href="([^"]*)"', html)
    assert "/billing/invoices/?sort=-amount&amp;q=n&amp;page=2" in hrefs


def test_an_action_posts_to_a_url_that_remembers_the_state(mounted):
    # Otherwise archiving on page two of a sorted table answers with the
    # first page of an unsorted one.
    html = _part(
        mounted(page_size=2).invoices,
        _request(sort="-amount", q="n", page="2"),
        DataTable(),
    )
    assert re.search(
        r'formaction="/billing/invoices/archive/\?sort=-amount&amp;q=n&amp;page=2"',
        html,
    )


def test_every_url_follows_the_mount_point(mounted):
    # The same declaration, included somewhere else. Nothing about the
    # table changed; where it lives did.
    bound = _bind(mounted(at="admin/reports/").invoices, _request(at="admin/reports/"))
    assert bound.urls.read == "/admin/reports/invoices/"
    assert bound.urls.act == {"archive": "/admin/reports/invoices/archive/"}


def test_the_search_form_posts_back_to_the_mounted_table(mounted):
    html = _part(mounted().invoices, _request(), TableSearch())
    assert 'action="/billing/invoices/"' in html


def test_a_table_whose_view_is_not_serving_the_request_says_so(mounted):
    # Reversed through the namespace the request came in on, so a table
    # drawn from somewhere else has no URL to build - which is worth
    # saying rather than leaving as a bare NoReverseMatch.
    view = mounted()
    elsewhere = _request()
    elsewhere.resolver_match.namespace = "somebodyelse"

    try:
        _bind(view.invoices, elsewhere)
    except NoReverseMatch as error:
        assert "somebodyelse:invoices_read" in str(error)
        assert "its own fragments" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a NoReverseMatch")


def test_the_checkboxes_carry_the_identifier_not_the_columns(mounted):
    html = _part(mounted().invoices, _request(), DataTable())
    picked = re.findall(r'name="selected" value="(\d+)"', html)
    assert picked == ["41", "17", "23", "58"]


def test_the_search_box_submits_itself_after_a_pause(mounted):
    html = _part(mounted().invoices, _request(), TableSearch())
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
        _bind(bare, _request(at=None))
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
            assert "layout(" in str(error)
            assert type(component).__name__ in str(error)
        else:  # pragma: no cover - the raise is the behaviour under test
            raise AssertionError(f"{component} drew itself out of nothing")


def test_a_datatable_with_no_columns_and_nothing_above_it_says_so():
    try:
        _render(DataTable())
    except ValueError as error:
        assert "DataTable.from_state(" in str(error)
    else:  # pragma: no cover - the raise is the behaviour under test
        raise AssertionError("expected a ValueError")


def test_the_search_box_answers_to_slash_and_escape(mounted):
    html = _part(mounted().invoices, _request(), TableSearch())
    assert 'x-data="hueTableSearch"' in html
    assert 'x-on:keydown.window.slash="focusField($event)"' in html
    assert 'x-on:keydown.escape="clearField($event)"' in html
    # What the shortcut counts to decide whether it means anything: a
    # page-wide key with two candidates belongs to neither.
    assert "data-hue-table-search" in html


def test_the_applied_row_comes_after_the_controls(mounted):
    # basis-full puts it on a line of its own, and order-last keeps that
    # line under the controls rather than splitting them.
    html = _part(mounted().invoices, _request(status="paid"), TableFilters())
    assert "order-last" in html
    assert "basis-full" in html


def test_the_pages_are_redrawn_with_the_rows(mounted):
    # A page, a sort or a search replaces the rows region; the bar saying
    # which page of how many has to be inside it, or it goes stale.
    html = _table(mounted(page_size=2).invoices, _request())
    assert "invoices-rows" in _ids_around(html, "Pagination")


def test_the_pages_land_in_the_rows_and_are_a_place_to_come_back_to(mounted):
    html = _part(mounted(page_size=2).invoices, _request(), TablePagination())
    assert 'x-target.push="invoices-rows"' in html


def test_a_filter_narrows_the_rows_it_names(mounted):
    bound = _bind(mounted().invoices, _request(status="paid"))
    assert bound.state.chosen("status") == ("paid",)
    assert [row["pk"] for row in bound.page] == ["41", "23"]


def test_several_answers_to_one_filter_ride_in_one_parameter(mounted):
    bound = _bind(mounted().invoices, _request(status="paid,draft"))
    assert bound.state.chosen("status") == ("paid", "draft")
    assert len(bound.page) == 4


def test_an_answer_the_filter_never_offered_is_dropped(mounted):
    # The query string is somewhere anybody can type, and rows() should
    # not have to defend itself against what lands in it.
    bound = _bind(mounted().invoices, _request(status="paid,whatever"))
    assert bound.state.chosen("status") == ("paid",)


def test_a_filter_with_nothing_to_tick_takes_what_it_is_given(mounted):
    bound = _bind(mounted().invoices, _request(min="1000"))
    assert bound.state.value("min") == "1000"
    assert [row["pk"] for row in bound.page] == ["41", "17"]


def test_a_filter_rides_in_every_url_the_table_builds(mounted):
    bound = _bind(mounted().invoices, _request(status="paid", sort="amount"))
    assert bound.href(sort="-amount") == "/billing/invoices/?sort=-amount&status=paid"


def test_the_panel_says_what_is_on_and_the_chips_undo_it(mounted):
    html = _part(mounted().invoices, _request(status="paid"), TableFilters())
    assert "hueTableFilters('invoices')" in html
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
    assert _bind(view.invoices, request).state.chosen("status") == ("paid", "draft")


def test_a_hidden_column_is_not_drawn(mounted):
    view, request = mounted(), _request(hide="customer")
    assert _bind(view.invoices, request).state.hidden == ("customer",)
    html = _table(view.invoices, request)
    assert "Northwind" not in html
    assert "INV-2048" in html


def test_a_column_nobody_may_hide_stays(mounted):
    # Typed into the URL rather than clicked, which is the only way to
    # ask for it - and the answer is no.
    view, request = mounted(), _request(hide="invoice")
    assert _bind(view.invoices, request).state.hidden == ()
    assert "INV-2048" in _table(view.invoices, request)


def test_the_panel_ticks_the_columns_that_are_showing(mounted):
    # The way round anybody reads a list of columns, while the URL
    # carries the ones that are hidden.
    html = _part(mounted().invoices, _request(hide="customer"), TableColumns())
    assert "hueTableColumns([&quot;customer&quot;], 'invoices')" in html
    assert "x-effect=\"$el.checked = showing('customer')\"" in html
    assert "Locked" in html


def test_reset_is_out_of_the_way_until_something_is_narrowed(mounted):
    html = _part(mounted().invoices, _request(sort="amount"), TableReset())
    assert 'x-show="narrowed"' in html
    assert "x-cloak" in html
    assert "hueTableReset('invoices', 0, 0)" in html


def test_reset_shows_once_a_filter_or_a_column_is_off(mounted):
    html = _part(
        mounted().invoices, _request(status="paid,draft", hide="customer"), TableReset()
    )
    assert "hueTableReset('invoices', 2, 1)" in html
    assert "x-cloak" not in html
    assert 'aria-label="Reset filters and columns"' in html


def test_reset_keeps_the_search_and_the_order(mounted):
    # It takes off what the panels put on, and only that.
    html = _part(
        mounted().invoices,
        _request(q="n", sort="-amount", status="paid", hide="customer", page="2"),
        TableReset(),
    )
    hidden = dict(
        re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)"', html)
    )
    assert hidden == {"sort": "-amount", "q": "n"}


def test_reset_redraws_the_whole_frame(mounted):
    # The panels live in the toolbar, which a sort or a page leaves alone,
    # and they have to come back unticked.
    html = _part(mounted().invoices, _request(status="paid"), TableReset())
    assert 'x-target.push="invoices"' in html


def test_the_panels_tell_the_reset_which_table_they_belong_to(mounted):
    html = _table(mounted().invoices, _request())
    assert "hueTableFilters('invoices')" in html
    assert "hueTableColumns([], 'invoices')" in html


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


def test_the_declaration_draws_itself_for_the_page_it_is_on(mounted):
    # Nothing to bind: the request is already in the context the page is
    # rendered with, so a view hands over the declaration as it is.
    view = mounted()
    html = asyncio.run(
        render_tree(
            DataTable.from_state(view.invoices),
            context_args=HueContextArgs(
                request=_request(sort="-amount"), csrf_token="t"
            ),
        )
    )
    assert 'aria-sort="descending"' in html
    assert html.index("INV-2050") < html.index("INV-2048")


def test_what_is_chained_after_from_state_is_kept(mounted):
    # The reason it answers with a DataTable rather than something that
    # only renders as one: a caption or an empty state of your own still
    # goes on the table the declaration draws.
    html = _render(
        DataTable.from_state(mounted().invoices).caption("Invoices, September"),
        _request(),
    )
    assert "<caption" in html
    assert "Invoices, September" in html


def test_one_from_state_can_be_drawn_for_two_requests(mounted):
    # Drawn into a copy, so the second request is not shown the first
    # one's rows - which a DataTable filling itself in would do.
    view = mounted()
    table = DataTable.from_state(view.invoices)
    first = _render(table, _request(q="contoso"))
    second = _render(table, _request(q="northwind"))
    assert "Contoso" in first and "Northwind" not in first
    assert "Northwind" in second and "Contoso" not in second


def test_layout_draws_the_parts_it_was_given(mounted):
    view = mounted()
    html = asyncio.run(
        render_tree(
            view.invoices.layout(html_div(TablePagination()), DataTable()),
            context_args=HueContextArgs(request=_request(), csrf_token="t"),
        )
    )
    assert "<table" in html
    assert 'aria-label="Pagination' in html
    assert 'name="q"' not in html


def test_a_layout_leaves_the_declaration_whole(mounted):
    # The declaration is a class attribute every request shares, so a
    # page laying out parts of it must not change what the next page gets.
    view = mounted()
    context_args = HueContextArgs(request=_request(), csrf_token="t")
    asyncio.run(
        render_tree(view.invoices.layout(DataTable()), context_args=context_args)
    )
    html = asyncio.run(
        render_tree(DataTable.from_state(view.invoices), context_args=context_args)
    )
    assert 'name="q"' in html


def _on_the_event_loop() -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def test_the_rows_are_asked_for_off_the_event_loop(urlpatterns_):
    # Counting and slicing a queryset are both queries, and Django raises
    # SynchronousOnlyOperation for a query made on the loop.
    seen: list[bool] = []

    def rows(request: Any, asked: Any) -> Any:
        seen.append(_on_the_event_loop())
        return _INVOICES

    class ProbeView(HueView):
        router = Router[HttpRequest]()
        invoices = datatable(
            router, key="invoices", columns=[Column("invoice", "Invoice")], rows=rows
        )

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

    urlpatterns_.append(path(MOUNT, include(ProbeView.urls)))
    clear_url_caches()
    _bind(ProbeView.invoices, _request())
    assert seen == [False]


def test_an_action_runs_off_the_event_loop_too(urlpatterns_):
    # Archiving is a write, which is the same query on the same loop.
    ran: list[bool] = []

    class ArchiveView(HueView):
        router = Router[HttpRequest]()
        invoices = datatable(
            router,
            key="invoices",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            identifier="pk",
            actions={
                "archive": BulkAction(
                    "Archive", lambda request, ids: ran.append(_on_the_event_loop())
                )
            },
        )

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

    urlpatterns_.append(path(MOUNT, include(ArchiveView.urls)))
    clear_url_caches()
    response = Client().post(
        f"/{MOUNT}invoices/archive/",
        {"selected": ["41"]},
        HTTP_X_ALPINE_REQUEST="true",
    )
    assert response.status_code == 200
    assert ran == [False]


def test_the_whole_table_is_one_component(mounted):
    # No parts to place: bound and rendered is the search box, the rows
    # and the pages.
    html = _table(mounted().invoices, _request())
    assert re.search(r'name="q"', html)
    assert re.search(r"<table", html)
    assert re.search(r'aria-label="Pagination', html)
    # Welded: one frame, with the search in a band above the rows and the
    # pages in a band below them.
    assert html.count("w-full rounded-lg border border-border bg-surface") == 1


def test_the_parts_can_be_placed_instead(mounted):
    # And each of them finds the same binding, however deeply it is laid
    # out inside the view.
    html = _render(
        mounted().invoices.layout(html_div(TablePagination()), DataTable()),
        _request(),
    )
    assert re.search(r"<table", html)
    assert re.search(r'aria-label="Pagination', html)
    assert 'type="search"' not in html
