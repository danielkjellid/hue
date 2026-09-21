from __future__ import annotations

from typing import Any

from hue.datatable import (
    BoundTable,
    BulkAction,
    TableSearch,
    TableState,
    datatable,
)
from hue.types.core import ComponentType
from hue.ui import Alert, Column, DataTable

from hue_docs.content import _prose as pr
from hue_docs.models import ProsePage

# The example, for real: the same declaration the page talks about, built
# against a list of dicts so nothing here needs a database. The specimens
# below are this table bound to states it might be asked for.
_INVOICES: list[dict[str, Any]] = [
    {"pk": "41", "invoice": "INV-2050", "customer": "Contoso Ltd", "amount": 2190},
    {"pk": "17", "invoice": "INV-2048", "customer": "Northwind", "amount": 1200},
    {"pk": "23", "invoice": "INV-2049", "customer": "Fabrikam Inc", "amount": 840},
    {"pk": "58", "invoice": "INV-2051", "customer": "Adventure Works", "amount": 415},
]

_ARCHIVED: set[str] = set()


def _invoices(asked: TableState) -> list[dict[str, Any]]:
    """
    One function, both questions: what was searched for and what order.
    """
    found = [
        row
        for row in _INVOICES
        if row["pk"] not in _ARCHIVED
        and asked.query.lower() in str(row["customer"]).lower()
    ]
    if asked.sort:
        key = asked.sort.lstrip("-")
        found.sort(key=lambda row: row[key], reverse=asked.sort.startswith("-"))
    return found


class _Router:
    """
    A stand-in, because a docs page has no view to hang routes on. A real
    declaration is handed the view's own Router and registers two routes on
    it; here they are registered on nothing and never called.
    """

    def fragment_get(self, path: str):  # type: ignore[no-untyped-def]
        return lambda view_func: view_func

    def fragment_post(self, path: str):  # type: ignore[no-untyped-def]
        return lambda view_func: view_func


_TABLE = datatable(
    _Router(),  # type: ignore[arg-type]
    key="invoices",
    columns=[
        Column("invoice", "Invoice"),
        Column("customer", "Customer", sort="customer"),
        Column("amount", "Amount", align="end", sort="amount"),
    ],
    rows=_invoices,
    identifier="pk",
    search="Search customers",
    actions={"archive": BulkAction("Archive", lambda request, ids: None)},
)


def _specimen(asked: TableState) -> ComponentType:
    bound = BoundTable(_TABLE, asked)
    return pr.section(
        TableSearch.from_state(bound),
        DataTable.from_state(bound),
    )


_DECLARATION = '''from hue.datatable import BulkAction, datatable
from hue.ui import Column, DataTable, TableSearch


def invoices_for(asked):
    """Both questions, one answer: what was searched for, and in what order."""
    found = Invoice.objects.filter(customer__name__icontains=asked.query)
    return found.order_by(asked.sort or "reference")


def archive(request, ids):
    Invoice.objects.filter(pk__in=ids).update(archived=True)


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
        actions={"archive": BulkAction("Archive", archive)},
    )

    async def index(self, request, context):
        invoices = self.invoices.bind(request)
        return Page(
            title="Invoices",
            body=Stack().content(
                TableSearch.from_state(invoices),
                DataTable.from_state(invoices),
            ),
        )'''


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
            "routes a declaration registers are exactly that pair."
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
        pr.h2("Why the search box is a separate component"),
        pr.p(
            "TableSearch is placed by you rather than rendered by the table, "
            "and that is structural rather than cosmetic. The frame is what "
            "a response replaces; a box inside it would be swapped out from "
            "under the person typing in it, losing the caret and the focus "
            "every time a request came back."
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
        _specimen(TableState(sort="-amount")),
        pr.p("Sorted by amount, descending. And the same table searched:"),
        _specimen(TableState(query="n", sort="customer")),
        pr.h2("What it assumes"),
        pr.bullets(
            [
                pr.p(
                    "The declaration lives at class scope. Routes register as "
                    "the class body runs, and rows are per request - which is "
                    "why rows is a function and not a list, and why a table "
                    "cannot be declared inside index()."
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
            ]
        ),
        Alert()
        .variant("warning")
        .title("What is not done yet")
        .content(
            "The URLs a declaration builds are rooted at /, so a view mounted "
            "under a prefix by include() will build the wrong ones - they "
            "need to go through reverse(). And the no-JavaScript fallback "
            "for an action will be refused by Django's CSRF middleware, "
            "because the form carries no hidden token; the AJAX path is fine, "
            "since the bundle sends the header. Both are integration work "
            "rather than anything about the shape above."
        ),
    )


PAGE = ProsePage(
    slug="data-tables",
    title="Data tables",
    nav_label="Data tables",
    group="Guides",
    order=3,
    build=_build,
)
