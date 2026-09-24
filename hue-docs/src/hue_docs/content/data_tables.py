from __future__ import annotations

from typing import Any

from hue.context import HueContext
from hue.datatable import BulkAction, Filter, TableState, datatable
from hue.types.core import ComponentType
from hue.ui import Alert, Column, DataTable

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage

# The example, for real. The same declaration the page talks about, over a
# list of dictionaries rather than a queryset - so the filtering, the
# ordering and the paging below are the Python here and nothing needs a
# database to be true.
_INVOICES: list[dict[str, Any]] = [
    {
        "pk": "41",
        "invoice": "INV-2050",
        "customer": "Contoso Ltd",
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
        "customer": "Fabrikam Inc",
        "amount": 840,
        "status": "declined",
    },
    {
        "pk": "58",
        "invoice": "INV-2051",
        "customer": "Adventure Works",
        "amount": 415,
        "status": "draft",
    },
    {
        "pk": "62",
        "invoice": "INV-2052",
        "customer": "Tailspin Toys",
        "amount": 3120,
        "status": "paid",
    },
]

_STATUS = [
    ("paid", "Paid"),
    ("pending", "Pending"),
    ("declined", "Declined"),
    ("draft", "Draft"),
]


class _Request:
    """
    Just enough of a request to carry a query string.
    """

    def __init__(self, **params: str) -> None:
        self.params = params


class _Router:
    """
    A stand-in, because a docs page has no view to hang routes on. A real
    declaration is handed the view's own Router and registers two routes
    on it; here they are registered on nothing and never called.
    """

    def fragment_get(self, path: str) -> Any:
        return lambda view_func: view_func

    def fragment_post(self, path: str) -> Any:
        return lambda view_func: view_func

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {name: [value] for name, value in request.params.items()}

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        # Django reverses these against the URLconf. Here they are spelled
        # out, since there is nothing to reverse against.
        action = params.get("action")
        return f"/invoices/{action}/" if action else "/invoices/"

    async def _run_sync(self, func: Any, /, *args: Any) -> Any:
        # A list of dictionaries has no event loop to keep off.
        return func(*args)


def _archive(request: Any, ids: list[str]) -> None:
    """A service function, which is all an action ever is."""


def _matching(request: Any, asked: TableState) -> Any:
    """
    The one part of a table that is not fixed: which rows answer it.
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


def _table(key: str) -> Any:
    """
    The declaration, once per specimen: two tables on one page need two
    keys, because the key is the id every part of a table is named from.
    """
    return datatable(
        _Router(),  # type: ignore[arg-type]
        key=key,
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
            Filter("min", "Minimum amount", kind="number", prefix="USD"),
        ],
        hideable=["customer", "amount"],
        actions={"archive": BulkAction("Archive", _archive)},
        page_size=3,
    )


def _specimen(key: str, **params: str) -> ComponentType:
    """
    The table drawn the way a view draws it. Each specimen is a request of
    its own, so each is wrapped in a context carrying it - the nearest one
    wins, which is the same rule that lets the page's own sit outside.
    """
    return pr.section(
        HueContext(
            DataTable.from_state(_table(key)),
            request=_Request(**params),
            csrf_token="",
        )
    )


_DECLARATION = """def invoices_for(request, asked):
    \"\"\"The one part of a table that is not fixed: which rows answer it.\"\"\"
    found = Invoice.objects.filter(customer__name__icontains=asked.query)
    if statuses := asked.chosen("status"):
        found = found.filter(status__in=statuses)
    if least := asked.value("min"):
        found = found.filter(amount__gte=least)
    return found.order_by(asked.sort or "reference")


class InvoicesView(HueView):
    router = Router[HttpRequest]()

    invoices = datatable(
        router,
        key="invoices",
        columns=[
            Column("invoice", "Invoice"),
            Column("customer", "Customer", sort="customer__name"),
            Column("amount", "Amount", align="end", sort="amount"),
        ],
        rows=invoices_for,
        identifier="pk",
        search="Search customers",
        filters=[
            Filter("status", "Status", options=STATUS),
            Filter("min", "Minimum amount", kind="number", prefix="USD"),
        ],
        hideable=["customer", "amount"],
        actions={"archive": BulkAction("Archive", archive_invoices)},
    )

    async def index(self, request, context):
        return Page(title="Invoices", body=DataTable.from_state(self.invoices))"""


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Data tables"),
        pr.lead(
            "A table that knows where its own state lives. One declaration says what "
            "the columns are, where the rows come from and which actions can run on "
            "picked rows. It registers the routes that serve all three, so nothing "
            "between a click and a handler is wired by hand."
        ),
        pr.h2("The declaration"),
        pr.code(_DECLARATION),
        pr.p(
            "The rest of this page takes that declaration apart. The examples here "
            "build the same one against a list of dictionaries instead of a queryset. "
            "Filtering and ordering are plain Python, so nothing on the page needs a "
            "database."
        ),
        pr.h2("State comes from the request"),
        pr.p(
            "There is no on_sort and no on_search. An order and a search both decide "
            "which rows to show, and rows() already answers that: it receives the "
            "state that was asked for and returns the matching rows. A handler in "
            "between would have nothing to do."
        ),
        pr.p(
            "This matters because a page of a lazy queryset is sliced after it is "
            "ordered. Re-sorting the rows you already hold gives page two of the old "
            "order, sorted within itself, so only another query returns the right "
            "rows. That is why a sortable header is a link and not a click handler."
        ),
        pr.code(
            "def invoices_for(request, asked):\n"
            "    found = Invoice.objects.filter(\n"
            "        customer__name__icontains=asked.query\n"
            "    )\n"
            '    return found.order_by(asked.sort or "reference")'
        ),
        pr.p(
            "asked.sort uses the spelling Django and query strings already use: "
            '"amount", or "-amount" for descending. A view can pass its own sort '
            "parameter straight to order_by without parsing it."
        ),
        pr.h2("Acting on rows is a write"),
        pr.p(
            "The server does not need to hear about rows being picked, only about "
            "something being done with them. Actions are named, they post, and they "
            "receive the ids of the ticked rows. The two routes a declaration "
            "registers follow the usual HTTP split between reads and writes. Both go "
            "through the same rows(), so after an action the table comes back in the "
            "state it was in instead of as the first page of an unsorted list."
        ),
        pr.code(
            "GET   /invoices/?sort=-amount&q=contoso   -> the table\n"
            "POST  /invoices/archive/                  -> the table, after archiving",
            language="bash",
        ),
        pr.p(
            "Both routes answer with the whole table. Sorting and archiving produce "
            "the same kind of response, so the page has one way to update."
        ),
        pr.h2("Identifying rows"),
        pr.p(
            "identifier names the property a row is known by, and actions receive "
            "those values. It belongs to the rows instead of the columns because what "
            "identifies a row is usually not something anyone wants to see: a primary "
            "key, say, instead of the reference printed on the invoice."
        ),
        pr.p(
            "Every row has to carry it, whether or not a column shows it. If the rows "
            "lack it, the declaration raises an error. Otherwise the checkboxes would "
            "carry no value and an action would receive an empty selection."
        ),
        pr.h2("How it is wired"),
        pr.p(
            "The key does all of the wiring. It names the fragment path, the element "
            "each response replaces, and so the URL every link and form on the table "
            "points at. It has to be unique on the page, and there is nothing else to "
            "keep in sync."
        ),
        pr.code(
            '<div id="invoices" class="…">           <!-- the shell -->\n'
            '  <form id="invoices-act" method="post" hidden></form>\n'
            "  <div>   [search]  [Filter 2]  [Columns]  [reset] </div>\n"
            '  <template x-teleport="body">          <!-- floats over the page -->\n'
            '    <div role="group">  2 selected [x] | [Archive]  </div>\n'
            "  </template>\n"
            '  <div id="invoices-rows">              <!-- replaced -->\n'
            "    <table>\n"
            '      <th aria-sort="descending">\n'
            '        <a href="?sort=amount" x-target="invoices-rows">Amount</a>\n'
            "      </th>\n"
            '      <td><input type="checkbox" name="selected"\n'
            '                 value="41" form="invoices-act"></td>\n'
            "    </table>\n"
            "    [pages]\n"
            "  </div>\n"
            "</div>",
            language="html",
        ),
        pr.p(
            "The table is one shell with bands inside it. The toolbar, the rows and "
            "the pages share a border and a radius. Only the band holding the table "
            "scrolls, because overflow on the shell would clip the Filter and Columns "
            "panels."
        ),
        pr.p(
            "None of these URLs is written by hand. The key names the two routes, and "
            "binding the table reverses them through the namespace the request came in "
            "on. A view included under a prefix, included with its own namespace, or "
            "mounted twice therefore links back into the mount the reader is using. A "
            "hard-coded path would break as soon as include() moved the view."
        ),
        pr.code(
            'urlpatterns = [path("billing/", include(InvoicesView.urls))]\n'
            "\n"
            "# /billing/invoices/?sort=-amount\n"
            "# /billing/invoices/archive/?sort=-amount",
            language="python",
        ),
        pr.p(
            "In return, a table can only build its URLs while the view that declared "
            "it is serving the request. Rendering it from another view's page raises "
            "an error instead of linking into the wrong namespace."
        ),
        pr.p(
            "Sorting, paging, searching and filtering all replace the rows, not the "
            "whole shell. No response ever replaces the toolbar, so the caret stays in "
            "the search box and an open panel stays open while the rows change."
        ),
        pr.p(
            "The selection is submitted through real checkboxes, so the browser sends "
            "what is ticked and nothing reads it off the page. The checkboxes do not "
            "sit inside the form, though. The form is an empty element that each "
            "checkbox names with its form attribute. A form around the whole shell "
            "would contain the search box, which is a form of its own, and browsers "
            "discard a nested form."
        ),
        pr.p(
            "Ticking a row brings up a bar that floats at the bottom of the "
            "window, with the count, a button that clears the selection, and the "
            "actions. Escape clears the selection too. The bar is moved to the end "
            "of the page body so it stays in reach wherever the page is scrolled, "
            "and it never pushes the rows down. When a sort, a page or a search "
            "replaces the rows, any ticked row that is no longer on the page is "
            "dropped from the selection, so an action only reaches rows the reader "
            "can see."
        ),
        pr.p(
            "x-target is the only part that needs Alpine: it turns a navigation into a "
            "swap. With JavaScript off, the same links and forms do the same things "
            "with full page loads. The Columns panel is the exception. Its checkboxes "
            "are the inverse of what the URL carries, so Alpine wires them up instead "
            "of the browser submitting them."
        ),
        pr.h2("Filters and columns"),
        pr.p(
            "Each filter gets its own parameter in the URL, a group in the panel "
            "behind the Filter button and a chip in the band under it. There is no "
            "Apply button. A change takes effect as soon as a box is ticked, since the "
            "chips already show what is on and can undo it."
        ),
        pr.code(
            'Filter("status", "Status", options=STATUS)     # ?status=paid,draft\n'
            'Filter("min", "Minimum amount", kind="number") # ?min=500'
        ),
        pr.p(
            "The chips and the count on the trigger are read from the panel's own "
            "controls. Stating the same fact in two places is deliberate, because a "
            "filter that is only visible in a closed popover gets mistaken for missing "
            "data. Reading them from the controls also means a chip appears in the "
            "same frame as the tick, with no round trip."
        ),
        pr.p(
            "A filter drops any answer it does not offer instead of passing it on. "
            "Anyone can type into a query string, and rows() should not have to guard "
            "against it. Filters named sort, q, page or hide are refused, "
            "because the table already uses those names."
        ),
        pr.p(
            "hideable names the columns a reader may hide. In the panel, a ticked box "
            "means the column is showing, which is how people read a list of columns. "
            "The URL carries the hidden columns instead, so a column added later shows "
            "up for someone following an old link. Locked columns appear in the list "
            "too, ticked, disabled and labelled as locked. A table of amounts without "
            "invoice numbers is unreadable, and a click that silently did nothing "
            "would look broken."
        ),
        pr.p(
            "While a filter is on or a column is hidden, a reset button appears at "
            "the end of the toolbar. It takes the filters off and shows every column "
            "again, and keeps the search and the order. It redraws the whole table, "
            "since the filter and column panels are in the toolbar and have to come "
            "back cleared as well."
        ),
        pr.h2("Drawing the table"),
        pr.p(
            "DataTable.from_state() draws the table a declaration describes: "
            "the search box, the rows and the pages. It binds to the request "
            "the page is being rendered for, which is already in the "
            "context, so the view names the table it shows and passes "
            "nothing else. Anything chained after it, such as a caption or "
            "an empty state of your own, stays on the table."
        ),
        pr.code(
            "async def index(self, request, context):\n"
            "    return Page(\n"
            '        title="Invoices",\n'
            '        body=DataTable.from_state(self.invoices).caption("Invoices"),\n'
            "    )"
        ),
        pr.p(
            "layout() draws parts of the table instead. Each part finds the binding in "
            "the context, so it can sit anywhere inside the layout, and a pagination "
            "bar in a page footer still knows which page it is on. layout() returns a "
            "new component each time instead of adding children to the declaration, "
            "because the declaration is a class attribute shared by every request."
        ),
        pr.code(
            "self.invoices.layout(\n"
            "    TableSearch(),\n"
            "    Card().content(DataTable()),\n"
            "    TablePagination(),\n"
            ")"
        ),
        pr.p(
            "bind(request) is for code that wants the values instead of the "
            "table, such as the total for a heading. It returns the state, "
            "the page of rows and the total. It is a coroutine because it is "
            "what asks for the rows."
        ),
        pr.p(
            "The parts are TableSearch, TableFilters, TableColumns, TableReset, "
            "DataTable and TablePagination. Rendered with no bound table above it, "
            "each one raises an error saying what is missing. That is the one mistake "
            "this design makes easy."
        ),
        pr.p(
            "The search box is a GET form that submits itself 300 milliseconds after "
            "the last keystroke, so a word typed quickly costs one request instead of "
            "five. It is a form because Enter already submits a form. The order and "
            "the filters go along as hidden fields, so a search keeps everything else "
            "the table was narrowed by."
        ),
        pr.p(
            "Slash focuses the box from anywhere on the page and Escape clears it. "
            "Slash is ignored while focus is in any field, and Escape is ignored while "
            "the box is empty, which leaves that key for whatever the table sits "
            "inside."
        ),
        pr.h2("Why it is declared on the class"),
        pr.p(
            "It would read more naturally to build the table inside index, "
            "where the request already is. The routes are what stop it. A "
            "declaration registers two routes on the view's router, and they "
            "have to exist before the framework builds its URL table, which "
            "Django does once, when the URLconf is imported and before the "
            "first request arrives. A declaration built inside index would "
            "register them on the first request, after the table was built, "
            "so every sort, search and action would come back 404 and the "
            "URLs could not be reversed."
        ),
        pr.p(
            "FastAPI has the same constraint. Its include_router copies a "
            "router's routes into the app when it is called, so a route added "
            "to the router afterwards never reaches the app. The same goes "
            "for any framework that builds its route table at startup."
        ),
        pr.p(
            "So the declaration is made once, at class scope, and bound once "
            "per request, when DataTable.from_state() renders it. The view "
            "names the declaration and never builds it."
        ),
        pr.h2("Two examples"),
        pr.p(
            "Both tables below are the declaration from the top of this page, bound to "
            "different requests. The Python above really filters and orders their "
            "rows."
        ),
        _specimen("invoices", sort="-amount"),
        pr.p(
            "The first is sorted by amount, descending, three to a page. The second is "
            "searched and filtered. It keeps the order and goes back to the first "
            "page, because page two of a different set of rows is not a page anyone "
            "asked for. The chips show what is on without opening the panel:"
        ),
        _specimen("payments", q="n", status="paid", sort="customer"),
        pr.h2("Assumptions"),
        pr.bullets(
            [
                pr.p(
                    "The declaration lives at class scope because that is the only "
                    "time a route can be registered. Everything about a table is fixed "
                    "except which rows answer it, so everything else is stated once "
                    "and rows is a function. It is called for the page and again by "
                    "the routes the declaration registered."
                ),
                pr.p(
                    "Every state that matters is in the URL. That is what lets you "
                    "send someone a sorted, searched table, and what makes the back "
                    "button work."
                ),
                pr.p(
                    "One column is sorted at a time. Clicking another column replaces "
                    "the order instead of adding to it: aria-sort marks one header, "
                    "and ARIA has no way to say which of two sorted columns came "
                    "first."
                ),
                pr.p(
                    "The rows carry the identifier, whether or not a column shows it."
                ),
                pr.p(
                    "The view that declares a table is the one that draws "
                    "it. Its URLs are reversed through the namespace of the "
                    "request being served, which is what makes them follow "
                    "the mount point instead of assuming the site root."
                ),
                pr.p(
                    "Narrowing a table is a query to the server. A page of a lazy "
                    "queryset is sliced after it is filtered and ordered, so the rows "
                    "on screen are the wrong ones to narrow. That is why every control "
                    "here is a link or a form and none is a JavaScript handler."
                ),
                pr.p(
                    "One table per key, per page. The key is the id every "
                    "part of a table is named from, so two tables sharing "
                    "one would share their controls' ids as well."
                ),
                pr.p(
                    "rows() and an action's handler are plain functions, "
                    "and they run in a thread rather than on the event "
                    "loop. Counting and slicing a queryset are both "
                    "queries and archiving is a write, and Django raises "
                    "SynchronousOnlyOperation for any query made on the "
                    "loop. An async function in either place is not "
                    "supported yet."
                ),
            ]
        ),
        Alert()
        .variant("warning")
        .title("What is not done yet")
        .content(
            "The no-JavaScript fallback for an action will be refused by Django's CSRF "
            "middleware, because the form carries no hidden token. The AJAX path "
            "works, since the bundle sends the header the middleware reads. The panel "
            "also does not show how many rows each filter answer would leave. That "
            "count would have to be recomputed on the server and swapped into the one "
            "band that is never swapped."
        ),
    )


PAGE = ProsePage(
    slug="data-tables",
    title="Data tables",
    nav_label="Data tables",
    group="Guides",
    order=4,
    build=_build,
)
