from __future__ import annotations

from typing import Any

from hue.datatable import BulkAction, Filter, TableState, datatable
from hue.types.core import ComponentType
from hue.ui import Alert, Column

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
        density=True,
        actions={"archive": BulkAction("Archive", _archive)},
        page_size=3,
    )


def _specimen(key: str, **params: str) -> ComponentType:
    return pr.section(_table(key).bind(_Request(**params)))


_DECLARATION = """def invoices_for(request, asked):
    \"\"\"The one part of a table that is not fixed: which rows answer it.\"\"\"
    return Invoice.objects.filter(
        customer__name__icontains=asked.query
    ).order_by(asked.sort or "reference")


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
        actions={"archive": BulkAction("Archive", archive_invoices)},
    )

    async def index(self, request, context):
        return Page(title="Invoices", body=self.invoices.bind(request))"""


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Data tables"),
        pr.lead(
            "A table that knows where its own state lives. One declaration "
            "says what the columns are, where the rows come from and what "
            "there is to do with the ones that are picked; it registers the "
            "routes that serve all three, so nothing between a click and a "
            "handler is wired by hand."
        ),
        pr.h2("The whole of it"),
        pr.code(_DECLARATION),
        pr.p(
            "Everything below is that declaration, taken apart. The examples "
            "on this page are the same one built against a list of "
            "dictionaries rather than a queryset - the filtering and the "
            "ordering are plain Python, so nothing here needs a database to "
            "be true."
        ),
        pr.h2("State is a question, not an event"),
        pr.p(
            "There is no on_sort and no on_search. An order and a search are "
            "both questions about which rows to show, and rows() is already "
            "the answer to them: it is handed the state that was asked for "
            "and returns the rows for it. A handler between the two would "
            "have nothing to do that the next call does not."
        ),
        pr.p(
            "That is not a stylistic preference. A page of a lazy queryset is "
            "sliced after it is ordered, so re-sorting the rows you are "
            "holding gives you page two of the old order sorted within "
            "itself. The rows in hand are already the wrong rows, and only "
            "another query fixes it - which is why the header is a link and "
            "not a click handler."
        ),
        pr.code(
            "def invoices_for(asked):\n"
            "    found = Invoice.objects.filter(\n"
            "        customer__name__icontains=asked.query\n"
            "    )\n"
            '    return found.order_by(asked.sort or "reference")'
        ),
        pr.p(
            "asked.sort is spelled the way Django and a query string both "
            'already spell it - "amount", or "-amount" for the other way '
            "- so a view hands its own sort parameter straight to order_by "
            "without parsing anything in between."
        ),
        pr.h2("Acting on rows is a write"),
        pr.p(
            "Picking rows is not something the server needs to hear about; "
            "doing something with them is. So actions are named, they post, "
            "and they are handed the ids of what was ticked. Reads and "
            "writes split the way HTTP already splits them, and the two "
            "routes the declaration registers are exactly that pair - and "
            "both go through the same rows(), so an action answers "
            "with the table in the state it was done in rather than the "
            "first page of an unsorted one."
        ),
        pr.code(
            "GET   /invoices/?sort=-amount&q=contoso   -> the table\n"
            "POST  /invoices/archive/                  -> the table, after archiving",
            language="bash",
        ),
        pr.p(
            "Both answer with the whole table, so the response to sorting and "
            "the response to archiving are the same thing and there is only "
            "one way for the page to be brought up to date."
        ),
        pr.h2("What the ids are"),
        pr.p(
            "identifier names the property a row is known by, and an action "
            "is handed those values. It is a property of the rows rather "
            "than one of the columns, because what identifies a row is "
            "usually not something anybody wants to look at - a primary key, "
            "not the reference that is printed on the invoice."
        ),
        pr.p(
            "Every row has to carry it whether or not a column shows it. A "
            "declaration whose rows do not raises rather than rendering "
            "checkboxes with nothing in them, which would post an empty "
            "selection to an action that then does nothing to nothing."
        ),
        pr.h2("Under the hood"),
        pr.p(
            "The key is the whole of the wiring. It names the fragment path, "
            "the element the response is swapped into, and by extension the "
            "URL every link and form on the table points at - so it has to "
            "be unique on the page, and there is nothing else to keep in "
            "step."
        ),
        pr.code(
            '<div id="invoices" class="…">          <!-- the frame: swapped -->\n'
            '  <form method="post" action="/invoices/" x-target="invoices">\n'
            "    <div>2 selected  [Archive]</div>   <!-- shown once one is -->\n"
            "    <table>\n"
            '      <th aria-sort="descending">\n'
            '        <a href="/invoices/?sort=amount" x-target="invoices">Amount</a>\n'
            "      </th>\n"
            '      <td><input type="checkbox" name="selected" value="41"></td>\n'
            "    </table>\n"
            "  </form>\n"
            "</div>",
            language="html",
        ),
        pr.p(
            "None of those URLs is spelled by hand. The key names the two "
            "routes, and binding the table reverses them through the "
            "namespace the request came in on - so a view included under a "
            "prefix, included with a namespace of its own, or mounted twice "
            "builds links back into the mount the reader is actually in. A "
            "path written into a link would be right until the first "
            "include() moved it."
        ),
        pr.code(
            'urlpatterns = [path("billing/", include(InvoicesView.urls))]\n'
            "\n"
            "# /billing/invoices/?sort=-amount\n"
            "# /billing/invoices/archive/?sort=-amount",
            language="python",
        ),
        pr.p(
            "The other side of that: a table can only build its URLs while "
            "the view that declared it is the one serving the request. "
            "Rendering one from somebody else's page raises rather than "
            "quietly linking into the wrong namespace."
        ),
        pr.p(
            "The selection posts through a real form around real checkboxes, "
            "so what is ticked is submitted by the browser and not read off "
            "the page by anything. x-target is the only part of it that "
            "needs Alpine at all: it turns a navigation into a swap. With "
            "JavaScript switched off the same link and the same form do the "
            "same thing the long way round."
        ),
        pr.p(
            "The form sits inside the frame rather than around it, so the "
            "table is still the outermost element and still what a response "
            "replaces. The id is on the frame and not on the table element "
            "for the same reason: an empty state lives under the table "
            "inside the frame, and swapping only the table would leave a "
            "stale one sitting beneath the new rows."
        ),
        pr.h2("One component, or the parts of one"),
        pr.p(
            "bind() answers with the table itself, and rendering it is the "
            "whole of it: the search box, the rows and the pages. That is "
            "what a view wants nine times in ten, and it is one line."
        ),
        pr.code(
            "async def index(self, request, context):\n"
            '    return Page(title="Invoices", body=self.invoices.bind(request))'
        ),
        pr.p(
            "Give it children and it renders those instead. Each of them "
            "finds the same binding in the context rather than being handed "
            "it, so a part can sit anywhere inside - a pagination bar in a "
            "page footer, far from the rows it pages, still knowing which "
            "page it is on."
        ),
        pr.code(
            "self.invoices.bind(request).content(\n"
            "    TableSearch(),\n"
            "    Card().content(DataTable()),\n"
            "    TablePagination(),\n"
            ")"
        ),
        pr.p(
            "The search box stays outside the frame either way, and that is "
            "structural rather than cosmetic. The frame is what a response "
            "replaces; a box inside it would be swapped out from under the "
            "person typing in it, losing the caret and the focus every time "
            "a request came back."
        ),
        pr.p(
            "It is a GET form that submits itself 300 milliseconds after the "
            "last keystroke - long enough that a word typed at speed is one "
            "request rather than five. A form rather than a handler, because "
            "Enter already does this. The order rides along as a hidden "
            "field, so searching keeps the order the table was already in."
        ),
        pr.h2("The two states, side by side"),
        pr.p(
            "Both of these are the declaration at the top of this page, "
            "bound to a state it might be asked for. The rows really are "
            "filtered and ordered by the Python above - nothing on this page "
            "is a picture of a table."
        ),
        _specimen("invoices", sort="-amount"),
        pr.p(
            "Sorted by amount, descending, three to a page. And the same "
            "table searched - which keeps the order and goes back to the "
            "first page, because page two of a different search is not a "
            "page anybody asked for:"
        ),
        _specimen("payments", q="n", sort="customer"),
        pr.h2("What it assumes"),
        pr.bullets(
            [
                pr.p(
                    "The declaration lives at class scope, because that is "
                    "the only time a route can be registered. Everything "
                    "about a table is fixed except which rows answer it, so "
                    "everything but rows is stated once and rows is the one "
                    "part that is a function - called for the page, and "
                    "called again by the routes the declaration registered."
                ),
                pr.p(
                    "Every state that matters is in the URL. That is what "
                    "makes a sorted, searched table a thing you can send to "
                    "somebody, and what lets the back button work."
                ),
                pr.p(
                    "One column is sorted at a time. Clicking another "
                    "replaces the order rather than adding to it: aria-sort "
                    "marks one header, and ARIA has no way to say which of "
                    "two sorted columns came first."
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
            ]
        ),
        Alert()
        .variant("warning")
        .title("What is not done yet")
        .content(
            "The no-JavaScript fallback for an action will be refused by "
            "Django's CSRF middleware, because the form carries no hidden "
            "token; the AJAX path is fine, since the bundle sends the header "
            "the middleware reads. Integration work rather than anything "
            "about the shape above."
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
