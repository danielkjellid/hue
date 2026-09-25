"""
The @datatable declaration, end to end against a Django view.

What this is here to show is that every way into the table goes through
the one described method, so a sort, a search, a page and an action all
come back with the table in the state it was in.
"""

import asyncio
import re
from html.parser import HTMLParser
from importlib.resources import files
from typing import Any, ClassVar
from unittest.mock import MagicMock
from urllib.parse import urlencode

import pytest
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest, QueryDict
from django.test import Client
from django.urls import NoReverseMatch, clear_url_caches, include, path, resolve
from hue.context import HueContextArgs
from hue.datatable import (
    BulkAction,
    Filter,
    build_datatable_state,
)
from hue.renderer import render_tree
from hue.ui import Dialog, Empty
from hue.ui.molecules.datatable import Column, DataTable

from hue_django.pages import Page
from hue_django.router import Router
from hue_django.views import HueFragmentsView, HueView

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

        async def index(self, request: Any, context: Any) -> Any:
            return Page(title="Invoices", body=DataTable.from_state(self.invoices))

        invoices = build_datatable_state(
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
                Filter("min", "Minimum amount", numeric=True),
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


def _ours(params: dict[str, Any]) -> dict[str, Any]:
    """
    The fixture table's state, under its key, as the URL spells it. A name
    that already has a key, or is nobody's state, is left as it is.
    """
    return {
        name if "-" in name or name == "selected" else f"invoices-{name}": value
        for name, value in params.items()
    }


def _request(at: str | None = MOUNT, **params: str) -> Any:
    request = MagicMock()
    # A real QueryDict: what the table reads off it is every value under
    # a name, which is the part a flat mapping gets wrong.
    request.GET = QueryDict(urlencode(_ours(params), doseq=True))
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
    The ids of every element open around the first one whose attr starts
    with a given value, its aria-label unless told otherwise.
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

    def __init__(self, label: str, attr: str = "aria-label") -> None:
        super().__init__()
        self.label = label
        self.attr = attr
        self.open: list[str | None] = []
        self.found: list[str | None] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        named = dict(attrs)
        if self.found is None and (named.get(self.attr) or "").startswith(self.label):
            self.found = list(self.open)
        if tag not in self.VOID:
            self.open.append(named.get("id"))

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.VOID and self.open:
            self.open.pop()


def _ids_around(html: str, label: str, attr: str = "aria-label") -> list[str | None]:
    nesting = _Nesting(label, attr)
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


def _form(html: str, marker: str) -> str:
    """
    The one form in a drawn table that carries marker. Every panel is a
    form of its own, so a flag read off the whole table could belong to
    any of them.
    """
    found = [f for f in re.findall(r"<form.*?</form>", html, re.S) if marker in f]
    assert len(found) == 1, f"{len(found)} forms carry {marker!r}"
    return found[0]


def _carried(html: str, form: str) -> dict[str, str]:
    """
    The hidden fields a form submits besides its own controls: the ones
    tied to it by id, which are drawn under the rows.
    """
    return dict(
        re.findall(
            rf'<input type="hidden" name="([\w-]+)" value="([^"]*)" form="{form}"', html
        )
    )


def test_the_declaration_registers_one_route_to_act_named_for_the_table():
    # Reading is the page: every link and form points at it, so a URL in
    # the address bar reloads. The name comes off the table, since the router
    # takes a route's name off __name__ and two tables would both be "act".
    routes = type(_view()).router.routes
    assert [(route.method, route.path, route.name) for route in routes] == [
        ("POST", "invoices/<str:action>/", "invoices_act"),
    ]


def test_reading_the_table_is_loading_the_page(mounted):
    # What the address bar holds after a sort, reloaded: the whole page,
    # in that order, with no AJAX header to ask for it.
    mounted()
    response = Client().get(f"/{MOUNT}", {"invoices-sort": "-amount"})
    assert response.status_code == 200
    html = response.content.decode()
    assert 'aria-sort="descending"' in html
    assert html.index("INV-2050") < html.index("INV-2048")


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
    html = _table(mounted().invoices, _request(sort="amount", q="contoso"))
    hrefs = re.findall(r'<th[^>]*><a href="([^"]*)"', html)
    assert "/billing/?invoices-sort=-amount&amp;invoices-q=contoso" in hrefs


def test_a_search_keeps_the_order_and_drops_the_page(mounted):
    # Page four of a different search is not a page anybody asked for.
    html = _table(mounted(page_size=2).invoices, _request(sort="-amount", page="2"))
    assert _carried(html, "invoices-search") == {"invoices-sort": "-amount"}


def test_what_the_forms_carry_is_redrawn_with_the_rows(mounted):
    # The toolbar is left alone by a sort, a page or a search, so a field
    # in there would go on sending the state the table was first drawn in:
    # sort, then search, and the order would come undone.
    html = _table(mounted().invoices, _request(sort="-amount"))
    ids = _ids_around(html, "invoices-search", attr="form")
    assert "invoices-rows" in ids


def test_each_form_carries_everything_but_its_own_part(mounted):
    html = _table(
        mounted(page_size=2).invoices,
        _request(q="n", sort="-amount", status="paid", hide="customer", page="2"),
    )
    assert _carried(html, "invoices-filters") == {
        "invoices-sort": "-amount",
        "invoices-q": "n",
        "invoices-hide": "customer",
    }
    assert _carried(html, "invoices-columns") == {
        "invoices-sort": "-amount",
        "invoices-q": "n",
        "invoices-status": "paid",
    }
    # Reset takes off what the panels put on, and only that.
    assert _carried(html, "invoices-reset") == {
        "invoices-sort": "-amount",
        "invoices-q": "n",
    }


def test_the_page_is_a_slice_and_the_count_is_everything(mounted):
    bound = _bind(mounted(page_size=2).invoices, _request(page="2"))
    assert bound.total == 4
    assert [row["pk"] for row in bound.page] == ["23", "58"]


def test_pagination_links_keep_the_rest_of_the_state(mounted):
    html = _table(mounted(page_size=2).invoices, _request(sort="-amount", q="n"))
    hrefs = re.findall(r'href="([^"]*)"', html)
    assert (
        "/billing/?invoices-sort=-amount&amp;invoices-q=n&amp;invoices-page=2" in hrefs
    )


def test_an_action_posts_the_state_it_was_done_in(mounted):
    # Otherwise archiving on page two of a sorted table answers with the
    # first page of an unsorted one. Page included, unlike the toolbar's
    # forms: an action comes back to where it was done.
    html = _table(
        mounted(page_size=2).invoices, _request(sort="-amount", q="n", page="2")
    )
    assert 'formaction="/billing/invoices/archive/"' in html
    assert _carried(html, "invoices-act") == {
        "invoices-sort": "-amount",
        "invoices-q": "n",
        "invoices-page": "2",
    }


def _act(action: str, **posted: Any) -> Any:
    return Client().post(
        f"/{MOUNT}invoices/{action}/", _ours(posted), HTTP_X_ALPINE_REQUEST="true"
    )


def test_an_action_is_handed_only_rows_the_reader_could_see(mounted):
    # 17 is a draft, and the table was filtered to paid: whoever posted it
    # did not get it from a checkbox on this table.
    mounted()
    response = _act("archive", selected=["41", "17", "nonesuch", "41"], status="paid")
    assert response.status_code == 200
    assert _ARCHIVED == ["41"]


def test_an_action_answers_with_the_table_in_the_posted_state(mounted):
    mounted()
    response = _act("archive", selected=["41"], sort="amount", status="paid")
    html = response.content.decode()
    assert 'aria-sort="ascending"' in html
    assert "INV-2048" not in html


def test_an_action_the_table_does_not_have_is_not_found(mounted):
    mounted()
    assert _act("nonesuch", selected=["41"]).status_code == 404


def test_every_url_follows_the_mount_point(mounted):
    # The same declaration, included somewhere else. Nothing about the
    # table changed; where it lives did.
    bound = _bind(mounted(at="admin/reports/").invoices, _request(at="admin/reports/"))
    assert bound.urls.read == "/admin/reports/"
    assert bound.urls.act == {"archive": "/admin/reports/invoices/archive/"}


def test_the_search_form_posts_back_to_the_mounted_table(mounted):
    html = _table(mounted().invoices, _request())
    assert 'action="/billing/"' in html


def test_a_table_whose_view_is_not_serving_the_request_says_so(mounted):
    # Reversed through the namespace the request came in on, so a table
    # drawn from somewhere else has no URL to build - which is worth
    # saying rather than leaving as a bare NoReverseMatch.
    view = mounted()
    elsewhere = _request()
    elsewhere.resolver_match.namespace = "somebodyelse"

    with pytest.raises(NoReverseMatch, match="somebodyelse:index") as error:
        _bind(view.invoices, elsewhere)
    assert "declared on a HueView" in str(error.value)


def test_the_checkboxes_carry_the_identifier_not_the_columns(mounted):
    html = _table(mounted().invoices, _request())
    picked = re.findall(r'name="selected" value="(\d+)"', html)
    assert picked == ["41", "17", "23", "58"]


def test_the_search_box_submits_itself_after_a_pause(mounted):
    html = _table(mounted().invoices, _request())
    assert re.search(r'@input\.debounce\.300ms="\$el\.requestSubmit\(\)"', html)
    # The rows and not the frame, or the box would be swapped out from
    # under the caret that typed into it. replace, so a word typed at
    # speed is not a history entry per pause in it.
    assert re.search(r'x-target\.replace="invoices-rows"', html)


def test_actions_with_nothing_to_hand_them_are_refused():
    with pytest.raises(ValueError, match="identifier"):
        build_datatable_state(
            Router[HttpRequest](),
            key="nothing",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            actions={"archive": BulkAction("Archive", lambda request, ids: None)},
        )


_NOTHING_TO_DO = {"archive": BulkAction("Archive", lambda request, ids: None)}


def test_an_identifier_with_no_actions_is_refused():
    # It is what an action is handed, and a checkbox with nothing to do is
    # not drawn, so on its own it would be a knob that does nothing.
    with pytest.raises(ValueError, match="identifier but no actions"):
        build_datatable_state(
            Router[HttpRequest](),
            key="idle",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            identifier="pk",
        )


def test_rows_that_do_not_carry_the_identifier_are_refused():
    bare = build_datatable_state(
        Router[HttpRequest](),
        key="bare",
        columns=[Column("invoice", "Invoice")],
        rows=lambda request, asked: [{"invoice": "INV-2050"}],
        identifier="pk",
        actions=_NOTHING_TO_DO,
    )

    with pytest.raises(ValueError, match="identified by 'pk'") as error:
        _bind(bare, _request(at=None))
    assert "['invoice']" in str(error.value)


def test_rows_that_are_not_mappings_are_refused_with_the_same_reason():
    # A model instance has no keys to list, which is itself the answer.
    class Invoice:
        pk = "41"

    models = build_datatable_state(
        Router[HttpRequest](),
        key="models",
        columns=[Column("invoice", "Invoice")],
        rows=lambda request, asked: [Invoice()],
        identifier="pk",
        actions=_NOTHING_TO_DO,
    )
    with pytest.raises(ValueError, match="they are Invoice and not mappings"):
        _bind(models, _request(at=None))


def test_the_search_box_answers_to_slash_and_escape(mounted):
    html = _table(mounted().invoices, _request())
    assert 'x-data="hueTableSearch"' in html
    assert 'x-on:keydown.window.slash="focusField($event)"' in html
    assert '@keydown.escape="clearField($event)"' in html
    # What the shortcut counts to decide whether it means anything: a
    # page-wide key with two candidates belongs to neither.
    assert "data-hue-table-search" in html


def test_the_pages_are_redrawn_with_the_rows_and_remembered(mounted):
    # A page, a sort or a search replaces the rows region; the bar saying
    # which page of how many has to be inside it, or it goes stale. push,
    # so a page is somewhere to come back to.
    html = _table(mounted(page_size=2).invoices, _request())
    assert "invoices-rows" in _ids_around(html, "Pagination")
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


def test_the_panel_says_what_is_on_and_the_chips_undo_it(mounted):
    html = _table(mounted().invoices, _request(status="paid"))
    assert """x-data='hueTableFilters("invoices")'""" in html
    # The count on the trigger and the chips in the band are the same
    # fact twice, both read off the controls rather than sent down.
    assert 'x-text="applied.length"' in html
    assert 'x-for="chip in applied"' in html
    assert 'data-filter="status"' in html
    assert 'data-option="Paid"' in html
    assert re.search(
        r'id="invoices-filter-status-paid"[^>]*checked', html
    ) or re.search(r'checked[^>]*id="invoices-filter-status-paid"', html)


def test_a_filter_cannot_be_called_what_the_table_already_calls_something():
    for taken in ("sort", "q", "page", "hide", "selected"):
        with pytest.raises(ValueError, match=repr(taken)):
            build_datatable_state(
                Router[HttpRequest](),
                key=f"clash_{taken}",
                columns=[Column("invoice", "Invoice")],
                rows=lambda request, asked: _INVOICES,
                filters=[Filter(taken, "Clash")],
            )


def test_a_page_holds_at_least_one_row():
    with pytest.raises(ValueError, match="page size of 0"):
        build_datatable_state(
            Router[HttpRequest](),
            key="empty_pages",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            page_size=0,
        )


def test_an_order_no_column_offers_is_dropped(mounted):
    # rows() hands the sort to the database, and ordering by a field the
    # table never shows would tell a reader things about it.
    view = mounted()
    assert _bind(view.invoices, _request(sort="-customer")).state.sort == "-customer"
    assert _bind(view.invoices, _request(sort="invoice")).state.sort is None
    assert _bind(view.invoices, _request(sort="secret")).state.sort is None


def test_a_page_past_the_last_is_the_last(mounted):
    bound = _bind(mounted(page_size=2).invoices, _request(page="99"))
    assert bound.state.page == 2
    assert [row["pk"] for row in bound.page] == ["23", "58"]


def test_a_typed_answer_is_taken_whole(mounted):
    # 1,000 is one number, and only a list-shaped filter is spelled with
    # commas between its answers.
    state, _ = mounted().invoices._read({"invoices-min": ["1,000"]})
    assert state.value("min") == "1,000"


def test_a_browser_repeating_a_name_is_read_the_same_as_a_comma(mounted):
    # A set of checkboxes sharing a name is how a browser submits a
    # list; the links the table builds join them with commas. Both are
    # the same question.
    view = mounted()
    request = MagicMock()
    request.GET = QueryDict("invoices-status=paid&invoices-status=draft")
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
    html = _table(mounted().invoices, _request(hide="customer"))
    assert """x-data='hueTableColumns(["customer"], "invoices")'""" in html
    assert """x-effect='$el.checked = showing("customer")'""" in html
    # Locked is a padlock to look at and a description to hear.
    assert re.search(
        r'id="invoices-hide-invoice"[^>]*aria-describedby="invoices-hide-invoice-locked"',
        html,
    ) or re.search(
        r'aria-describedby="invoices-hide-invoice-locked"[^>]*id="invoices-hide-invoice"',
        html,
    )
    assert 'id="invoices-hide-invoice-locked" class="sr-only">Locked<' in html
    assert "invoices-hide-customer-locked" not in html


def test_reset_is_out_of_the_way_until_something_is_narrowed(mounted):
    html = _form(_table(mounted().invoices, _request(sort="amount")), "hueTableReset")
    assert 'x-show="narrowed"' in html
    assert "x-cloak" in html
    assert """x-data='hueTableReset("invoices", 0, 0)'""" in html


def test_reset_shows_once_a_filter_or_a_column_is_off(mounted):
    html = _form(
        _table(mounted().invoices, _request(status="paid,draft", hide="customer")),
        "hueTableReset",
    )
    assert """x-data='hueTableReset("invoices", 2, 1)'""" in html
    assert "x-cloak" not in html
    assert 'aria-label="Reset filters and columns"' in html


def test_reset_redraws_the_whole_frame(mounted):
    # The panels live in the toolbar, which a sort or a page leaves alone,
    # and they have to come back unticked.
    html = _table(mounted().invoices, _request(status="paid"))
    html = _form(html, "hueTableReset")
    assert 'x-target.push="invoices"' in html


def test_the_panels_tell_the_reset_which_table_they_belong_to(mounted):
    html = _table(mounted().invoices, _request())
    assert """x-data='hueTableFilters("invoices")'""" in html
    assert """x-data='hueTableColumns([], "invoices")'""" in html


def test_every_name_the_markup_hands_the_script_is_one_it_reads(mounted):
    # Spelled once in Python and once in table.js. A rename on one side
    # would otherwise leave the chips or the reset button dead without a
    # test noticing.
    script = (files("hue") / "static" / "js" / "table.js").read_text()
    html = _table(mounted().invoices, _request(status="paid"))
    names = {
        *re.findall(r"""x-data=["'](hueTable\w+)""", html),
        *re.findall(r"x-on:(hue-table-[\w-]+)", html),
    }
    attributes = set(re.findall(r"data-(hue-[\w-]+|filter[\w-]*|option)=", html))
    assert len(names) >= 5 and len(attributes) >= 5, (names, attributes)
    missing = [name for name in sorted(names) if name not in script]
    missing += [
        name
        for name in sorted(attributes)
        # Read either as a selector or off dataset, where data-filter-label
        # is spelled filterLabel.
        if f"[data-{name}]" not in script
        and "dataset." + re.sub(r"-(\w)", lambda m: m.group(1).upper(), name)
        not in script
    ]
    assert not missing, f"table.js never reads {missing}"


def test_hiding_a_column_nobody_declared_is_refused():
    with pytest.raises(ValueError, match="nonesuch"):
        build_datatable_state(
            Router[HttpRequest](),
            key="strangers",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            hideable=["nonesuch"],
        )


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
        invoices = build_datatable_state(
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
        invoices = build_datatable_state(
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
    assert re.search(r'type="search"[^>]*name="invoices-q"', html)
    assert re.search(r"<table", html)
    assert re.search(r'aria-label="Pagination', html)
    # Welded: one frame, with the search in a band above the rows and the
    # pages in a band below them.
    assert html.count("w-full rounded-lg border border-border bg-surface") == 1


def test_a_queryset_is_narrowed_in_the_database():
    # One query for the few ids that were posted, rather than every row
    # that matches walked in Python to find them.
    rows = MagicMock(spec=QuerySet)
    Router[HttpRequest]()._narrow_to(rows, "customer.pk", ["41", "17"])
    rows.filter.assert_called_once_with(customer__pk__in=["41", "17"])


def test_anything_else_is_narrowed_by_walking_it():
    kept = Router[HttpRequest]()._narrow_to(_INVOICES, "pk", ["41", "17"])
    assert [row["pk"] for row in kept] == ["41", "17"]


def _plain(urlpatterns_: list[Any], **declared: Any) -> Any:
    """
    A table with only what a test names, mounted like the others.
    """

    class PlainView(HueView):
        router = Router[HttpRequest]()
        invoices = build_datatable_state(
            router,
            key="invoices",
            columns=[Column("invoice", "Invoice"), Column("amount", "Amount")],
            rows=declared.pop("rows", lambda request, asked: _INVOICES),
            **declared,
        )

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

    urlpatterns_.append(path(MOUNT, include(PlainView.urls)))
    clear_url_caches()
    return PlainView.invoices


def test_a_table_with_no_actions_posts_no_state(urlpatterns_):
    html = _table(_plain(urlpatterns_, search="Search"), _request(q="n"))
    assert _carried(html, "invoices-search") == {}
    assert 'form="invoices-act"' not in html


def test_a_table_with_nothing_to_narrow_carries_nothing(urlpatterns_):
    html = _table(_plain(urlpatterns_), _request())
    assert 'type="hidden"' not in html


def test_an_id_the_key_cannot_hold_picks_nothing():
    # Posted by nothing the table drew, and not worth a server error.
    rows = MagicMock(spec=QuerySet)
    rows.filter.side_effect = ValueError("Field 'id' expected a number but got 'abc'")
    kept = Router[HttpRequest]()._narrow_to(rows, "pk", ["abc"])
    assert kept is rows.none.return_value


def test_a_filter_cannot_take_the_id_of_a_form_in_the_toolbar(mounted):
    # A text filter called columns would otherwise be the element the
    # columns form's carried fields point at.
    html = _table(mounted().invoices, _request())
    ids = re.findall(r' id="([^"]+)"', html)
    assert "invoices-filter-min" in ids
    assert len(ids) == len(set(ids)), sorted(i for i in ids if ids.count(i) > 1)


def _breaks(request: Any, ids: list[str]) -> None:
    raise RuntimeError("the billing service is down")


def test_an_action_that_fails_says_so_and_keeps_the_table(urlpatterns_, caplog):
    # Silence is the worst answer: the reader cannot tell a failure from a
    # slow success, and nothing in the logs says what went wrong.
    _plain(
        urlpatterns_,
        identifier="pk",
        actions={"send": BulkAction("Send reminders", _breaks)},
    )
    response = _act("send", selected=["41"])
    html = response.content.decode()
    assert response.status_code == 500
    assert "Send reminders failed" in html
    assert 'id="invoices"' in html
    assert "the billing service is down" in caplog.text
    assert "Traceback" in caplog.text


def test_an_action_that_works_raises_no_alarm(mounted):
    mounted()
    assert "failed" not in _act("archive", selected=["41"]).content.decode()


def _confirmed(urlpatterns_: list[Any]) -> Any:
    return _plain(
        urlpatterns_,
        identifier="pk",
        actions={
            "delete": BulkAction(
                "Delete",
                lambda request, ids: None,
                variant="danger",
                confirm=Dialog().destructive().title("Delete these invoices?"),
            )
        },
    )


def test_an_action_to_confirm_opens_a_dialog_first(urlpatterns_):
    html = _table(_confirmed(urlpatterns_), _request())
    assert "Delete these invoices?" in html
    # The bar's button only opens it; the one that posts is in the dialog.
    assert re.search(r'<button[^>]*aria-haspopup="dialog"[^>]*>', _bar(html))
    submits = [
        _attrs(tag) for tag in re.findall(r"<button[^>]*formaction=[^>]*>", html)
    ]
    assert [(b["formaction"], b["form"], b["type"]) for b in submits] == [
        ("/billing/invoices/delete/", "invoices-act", "submit")
    ]


def _bar(html: str) -> str:
    found = re.search(r'<template x-teleport="body">(.*?)</template>', html, re.S)
    assert found, "no bar for picked rows"
    return found.group(1)


def test_an_action_with_nothing_to_confirm_posts_straight_away(mounted):
    bar = _bar(_table(mounted().invoices, _request()))
    assert 'aria-haspopup="dialog"' not in bar
    assert 'formaction="/billing/invoices/archive/"' in bar


def test_the_dialog_on_the_declaration_is_left_as_it_was(urlpatterns_):
    # Shared by every request, so drawing one must not change the next.
    declared = _confirmed(urlpatterns_)
    _table(declared, _request())
    assert "trigger" not in declared.actions["delete"].confirm._props


def test_a_table_narrowed_to_nothing_says_so_and_the_way_out(mounted):
    html = _table(mounted().invoices, _request(q="nobody", sort="amount"))
    assert "Nothing matches" in html
    way_out = _form(html, "Clear search and filters")
    # The order survives; the search does not.
    assert 'name="invoices-sort" value="amount"' in way_out
    assert 'name="invoices-q"' not in way_out


def test_an_empty_table_that_is_not_narrowed_is_just_empty(urlpatterns_):
    html = _table(_plain(urlpatterns_, rows=lambda request, asked: []), _request())
    assert "Nothing matches" not in html


def test_your_own_empty_state_wins(mounted):
    html = _render(
        DataTable.from_state(mounted().invoices).empty(Empty().title("No invoices")),
        _request(q="nobody"),
    )
    assert "No invoices" in html
    assert "Nothing matches" not in html


def _summary(html: str) -> str:
    found = re.search(r'<p id="invoices-summary"[^>]*>([^<]*)</p>', html)
    assert found, "no summary"
    return found.group(1)


def test_the_rows_are_counted_out_loud(mounted):
    html = _table(mounted(page_size=2).invoices, _request())
    # Outside the rows, which a response replaces, and synced by id, so
    # the region stays and only its words change.
    assert "invoices-rows" not in _ids_around(html, "invoices-summary", attr="id")
    assert re.search(r'<p id="invoices-summary"[^>]*x-sync', html)
    assert _summary(html) == "4 records, showing 1 to 2."


def test_a_count_that_fits_one_page_is_just_the_count(mounted):
    assert _summary(_table(mounted().invoices, _request(q="contoso"))) == "1 record."


def test_a_count_of_nothing_says_why(mounted):
    assert (
        _summary(_table(mounted().invoices, _request(q="nobody")))
        == "No records match."
    )


def _attrs(tag: str) -> dict[str, str]:
    return dict(re.findall(r'([\w:.@-]+)="([^"]*)"', tag))


def test_a_count_of_an_empty_table_says_only_that(urlpatterns_):
    html = _table(_plain(urlpatterns_, rows=lambda request, asked: []), _request())
    assert _summary(html) == "No records."


def test_a_filter_alone_is_narrowing_too(mounted):
    # Not only a search: a filter that leaves nothing gets the way out.
    view = mounted()
    html = _table(view.invoices, _request(status="paid", min="999999"))
    assert "Nothing matches" in html


def test_the_rows_are_refreshed_by_any_response_that_carries_them(mounted):
    # A sort on one table swaps only its rows; another table's links would
    # otherwise carry the first one's old state.
    html = _table(mounted().invoices, _request())
    assert re.search(r'<div id="invoices-rows"[^>]*x-sync', html)


def test_two_tables_on_a_page_keep_their_own_state(urlpatterns_):
    class TwoTables(HueView):
        router = Router[HttpRequest]()
        first = build_datatable_state(
            router,
            key="first",
            columns=[
                Column("invoice", "Invoice"),
                Column("amount", "Amount", sort="amount"),
            ],
            rows=lambda request, asked: sorted(
                _INVOICES,
                key=lambda row: row["amount"],
                reverse=(asked.sort or "").startswith("-"),
            ),
        )
        second = build_datatable_state(
            router,
            key="second",
            columns=[
                Column("invoice", "Invoice"),
                Column("amount", "Amount", sort="amount"),
            ],
            rows=lambda request, asked: _INVOICES,
            page_size=2,
        )

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

    urlpatterns_.append(path(MOUNT, include(TwoTables.urls)))
    clear_url_caches()
    request = _request(**{"first-sort": "-amount", "second-page": "2"})

    first = _bind(TwoTables.first, request)
    second = _bind(TwoTables.second, request)
    assert (first.state.sort, first.state.page) == ("-amount", 1)
    assert (second.state.sort, second.state.page) == (None, 2)
    # Paging the second table leaves the first one sorted, and the other way
    # round.
    assert second.href(page=1) == "/billing/?first-sort=-amount"
    assert first.href(sort="amount") == "/billing/?second-page=2&first-sort=amount"


def test_a_refused_permission_is_the_frameworks_answer(urlpatterns_):
    # A 403 is an answer, not a failure: no toast, no error in the log.
    def forbidden(request: Any, ids: list[str]) -> None:
        raise PermissionDenied

    _plain(
        urlpatterns_, identifier="pk", actions={"send": BulkAction("Send", forbidden)}
    )
    assert _act("send", selected=["41"]).status_code == 403


def test_a_table_with_no_page_fails_before_anything_is_written(urlpatterns_):
    ran: list[bool] = []

    class NoPage(HueFragmentsView):
        router = Router[HttpRequest]()
        invoices = build_datatable_state(
            router,
            key="invoices",
            columns=[Column("invoice", "Invoice")],
            rows=lambda request, asked: _INVOICES,
            identifier="pk",
            actions={"archive": BulkAction("Archive", lambda r, ids: ran.append(True))},
        )

    urlpatterns_.append(path(MOUNT, include(NoPage.urls)))
    clear_url_caches()
    with pytest.raises(NoReverseMatch, match="declared on a HueView"):
        _act("archive", selected=["41"])
    assert ran == []


def test_the_page_is_registered_under_the_name_a_table_reverses():
    view = _view()
    assert "index" in [pattern.name for pattern in type(view).urls[0]]


_SORTABLE = [Column("invoice", "Invoice"), Column("amount", "Amount", sort="amount")]


def test_a_key_that_starts_another_keeps_to_its_own(urlpatterns_):
    # a-b-sort starts with a-, and is still b's.
    class Prefixed(HueView):
        router = Router[HttpRequest]()
        a = build_datatable_state(
            router, key="a", columns=_SORTABLE, rows=lambda r, asked: _INVOICES
        )
        a_b = build_datatable_state(
            router, key="a-b", columns=_SORTABLE, rows=lambda r, asked: _INVOICES
        )

        async def index(self, request: Any, context: Any) -> Any:  # pragma: no cover
            raise NotImplementedError

    urlpatterns_.append(path(MOUNT, include(Prefixed.urls)))
    clear_url_caches()
    first = _bind(Prefixed.a, _request(**{"a-b-sort": "-amount"}))
    assert first.state.sort is None
    assert first.href(sort="amount") == "/billing/?a-b-sort=-amount&a-sort=amount"
