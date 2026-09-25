from __future__ import annotations

from collections.abc import Callable
from typing import Any

from hue.context import HueContext
from hue.datatable import BulkAction, Filter, TableState, build_datatable_state
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
    declaration is handed the view's own Router and registers its action
    route on it; here it is registered on nothing and never called.
    """

    def fragment_post(self, path: str) -> Any:
        return lambda view_func: view_func

    def _get_query_values(self, request: Any) -> dict[str, list[str]]:
        return {name: [value] for name, value in request.params.items()}

    def _get_form_values(self, request: Any) -> dict[str, list[str]]:
        # Nothing is ever posted to a docs page.
        return {}

    def _passes_through(self, error: Exception) -> bool:
        return False

    def _form_fields(self) -> frozenset[str]:
        return frozenset()

    def _narrow_to(self, rows: Any, key: str, values: list[str]) -> Any:
        return [row for row in rows if str(row[key]) in values]

    def _url_for(self, request: Any, name: str, **params: Any) -> str:
        # Django reverses these against the URLconf. Here they are spelled
        # out, since there is nothing to reverse against.
        action = params.get("action")
        return f"/invoices/{action}/" if action else "/invoices/"

    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R:
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
    return build_datatable_state(
        _Router(),
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
            Filter("min", "Minimum amount", numeric=True, prefix="USD"),
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
            # Under the table's key, as a URL carries it.
            request=_Request(
                **{f"{key}-{name}": value for name, value in params.items()}
            ),
            csrf_token="",
        )
    )


_DECLARATION = """def invoices_for(
    request: HttpRequest, asked: TableState
) -> QuerySet[Invoice]:
    \"\"\"The one part of a table that is not fixed: which rows answer it.\"\"\"
    found = Invoice.objects.filter(customer__name__icontains=asked.query)
    if statuses := asked.chosen("status"):
        found = found.filter(status__in=statuses)
    if least := asked.value("min"):
        found = found.filter(amount__gte=least)
    return found.order_by(asked.sort or "reference")


def archive_invoices(request: HttpRequest, ids: list[str]) -> None:
    Invoice.objects.filter(pk__in=ids).update(archived=True)


class InvoicesView(HueView):
    router = Router[HttpRequest]()

    invoices = build_datatable_state(
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
            Filter("min", "Minimum amount", numeric=True, prefix="USD"),
        ],
        hideable=["customer", "amount"],
        actions={"archive": BulkAction("Archive", archive_invoices)},
    )

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ) -> Page:
        return Page(title="Invoices", body=DataTable.from_state(self.invoices))"""


def _build() -> ComponentType:
    return pr.page(
        pr.h1("Data tables"),
        pr.lead(
            "A table whose state lives in the URL. You declare it once on a view: "
            "its columns, the function that finds its rows, and what can be done "
            "with the rows a reader picks. The table draws its own search, filters, "
            "column picker, sort links, pages and a bar of actions, and every one of "
            "them is a link or a form."
        ),
        pr.h2("The declaration"),
        pr.code(_DECLARATION),
        pr.p(
            "The view draws the table with DataTable.from_state(self.invoices). The "
            "rest of this page covers what the declaration does."
        ),
        pr.p(
            "The examples further down use the same declaration over a list of "
            "dictionaries, so the filtering and ordering they show are plain Python "
            "and the page needs no database."
        ),
        pr.h2("Rows come from one function"),
        pr.p(
            "rows is the only part of a table that changes with each request, so it "
            "is the only part that is a function. It receives the request and a "
            "TableState holding what was asked for, and returns every row that "
            "matches: the whole filtered, ordered set, not just the page. The table "
            "counts it and slices out the page itself. A queryset stays lazy, so a "
            "paginated table costs one count and one slice in the database."
        ),
        pr.code(
            "def invoices_for(\n"
            "    request: HttpRequest, asked: TableState\n"
            ") -> QuerySet[Invoice]:\n"
            "    found = Invoice.objects.filter(\n"
            "        customer__name__icontains=asked.query\n"
            "    )\n"
            '    if statuses := asked.chosen("status"):\n'
            "        found = found.filter(status__in=statuses)\n"
            '    if least := asked.value("min"):\n'
            "        found = found.filter(amount__gte=least)\n"
            '    return found.order_by(asked.sort or "reference")'
        ),
        pr.p(
            "TableState carries the search in query, the order in sort, the page "
            "number in page, and the hidden columns in hidden. chosen() reads a "
            "filter that can hold several answers and value() reads one that holds a "
            "single answer."
        ),
        pr.p(
            "asked.sort is spelled the way Django and query strings already spell "
            'it: "amount", or "-amount" for descending. You can pass it straight to '
            "order_by, because the table only accepts an order that one of its "
            "columns declares with sort=. An order typed into the URL by hand "
            "arrives as None, so nobody can sort by a field the table never shows. "
            "Filters are checked the same way: an answer a filter does not offer is "
            "dropped before rows sees it."
        ),
        pr.p(
            "There is no on_sort and no on_search. Both decide which rows to show, "
            "and rows already answers that. Sorting the rows already on screen would "
            "give the wrong answer anyway. A page of a queryset is sliced after it "
            "is ordered, so only another query returns the right rows."
        ),
        pr.h2("The URL is the state"),
        pr.p(
            "Everything a reader does to the table is in the address bar: the order, "
            "the search, the page, the filters and the hidden columns. Each one is "
            "named under the table's key."
        ),
        pr.code(
            "/billing/?invoices-sort=-amount&invoices-q=contoso&invoices-status=paid",
            language="bash",
        ),
        pr.p(
            "Every link and toolbar form on the table points at the page the table "
            "is drawn on. Alpine AJAX fetches that page and swaps in the part that "
            "changed, and the address bar ends up holding a URL that reloads to the "
            "same table, can be sent to someone, and works with the back button. "
            "With JavaScript off, sorting, paging and searching still work, as full "
            "page loads."
        ),
        pr.p(
            "Because each table keeps to names under its own key, two tables on one "
            "page keep separate state in one URL. Each table carries the other's "
            "parameters through its links and forms unchanged, and a response "
            "refreshes both tables' links, so sorting one never resets the other."
        ),
        pr.p(
            "None of these URLs is written by hand. Binding the table reverses the "
            "page and the action route through the namespace the request came in on, "
            "so a view included under a prefix, under a namespace of its own, or "
            "twice, links back into the mount the reader is using."
        ),
        pr.code(
            'urlpatterns = [path("billing/", include(InvoicesView.urls))]\n'
            "\n"
            "# the page:    /billing/?invoices-sort=-amount\n"
            "# an action:   /billing/invoices/archive/"
        ),
        pr.p(
            "The page is the view's index, so a table has to be declared on a "
            "HueView. A table can only build its URLs while the view that declared "
            "it is serving the request, and rendering it from another view raises an "
            "error instead of linking into the wrong place."
        ),
        pr.h2("Search, filters and columns"),
        pr.p(
            "search gives the table a search box, with the text as its placeholder. "
            "It is a GET form that submits itself 300 milliseconds after the last "
            "keystroke, so a word typed quickly costs one request, and Enter submits "
            "it straight away. Slash focuses it from anywhere on the page and Escape "
            "empties it. Slash is ignored while you are typing in another field, and "
            "Escape is left alone while the box is empty, so the key still reaches "
            "whatever the table sits inside."
        ),
        pr.p(
            "Each Filter gets a parameter in the URL, a group in the panel behind "
            "the Filter button, and a chip under the toolbar for every answer that "
            "is on."
        ),
        pr.code(
            "# ?invoices-status=paid,draft\n"
            'Filter("status", "Status", options=STATUS)\n'
            "# ?invoices-min=500\n"
            'Filter("min", "Minimum amount", numeric=True, prefix="USD")'
        ),
        pr.p(
            "A filter with options is a list of boxes to tick, several at a time "
            "unless multiple=False. Without options it is a field to type into, and "
            "numeric=True makes that a number field. prefix and placeholder decorate "
            "the field. There is no Apply button: a change takes effect as soon as "
            "it is made, and the chips show what is on and take it off again. The "
            "chips and the count on the Filter button are read from the panel's own "
            "controls, so a chip appears in the same moment as the tick. A filter "
            "cannot be called sort, q, page, hide or selected, which the table "
            "already uses."
        ),
        pr.p(
            "hideable lists the columns a reader may hide. In the Columns panel a "
            "ticked box is a column that shows, while the URL carries the hidden "
            "ones, so a column added later shows up for someone following an old "
            "link. The other columns are in the list too, ticked, disabled and "
            "marked with a padlock, so the rule is visible and a click never "
            "silently does nothing."
        ),
        pr.p(
            "While a filter is on or a column is hidden, a reset button appears at "
            "the end of the toolbar. It takes the filters off and shows every "
            "column, and keeps the search and the order."
        ),
        pr.h2("Actions"),
        pr.p(
            "Actions are what can be done with the rows a reader picks, and "
            "identifier names the property a row is known by. The two come as a "
            "pair. Giving a table actions puts a checkbox in every row, and a table "
            "without actions has none. An identifier without actions is refused, "
            "because it would do nothing."
        ),
        pr.p(
            "The identifier is kept apart from the columns because a row is usually "
            "known by something nobody needs to see, such as a primary key. Every "
            "row has to carry it whether or not a column shows it. Rows that lack it "
            "are refused with an error instead of drawing checkboxes with no value."
        ),
        pr.code(
            'BulkAction("Archive", archive_invoices)\n'
            'BulkAction("Mark as paid", mark_paid, icon=HueIcon("check"))\n'
            "BulkAction(\n"
            '    "Delete",\n'
            "    delete_invoices,\n"
            '    variant="danger",\n'
            '    confirm=Dialog().destructive().title("Delete these invoices?"),\n'
            ")"
        ),
        pr.p(
            "A handler receives the request and the ids of the picked rows, and is "
            "whatever you would have written anyway, such as a service function. It "
            "never receives an id the reader could not see. The table posts its "
            "state along with the selection, runs rows for that state, and keeps "
            "only the posted ids it finds there. For a queryset that check is one "
            "filter on the identifier."
        ),
        pr.p(
            "An action that cannot be taken back can ask first. Give its BulkAction "
            "a Dialog with the question on it. The table makes the button in the bar "
            "open the dialog and fills its footer with Cancel and the button that "
            "does the action."
        ),
        pr.p(
            "After an action the table redraws in the state it was in: on the same "
            "page, in the same order, with the same filters. If the handler raises, "
            "the reader gets a danger toast naming the action, the table redraws as "
            "it now is, and the ticked rows stay ticked for another try. The error "
            "is logged with its traceback, which is how an error tracker hears about "
            "it, since nothing is raised past the route. A permission denied, a not "
            "found or a bad request is Django's own answer, and Django gives it."
        ),
        pr.p(
            "Ticking a row brings up a bar that floats at the bottom of the window "
            "with the count, a button that clears the selection, and the actions. "
            "Escape clears the selection too. There is one selection per page: "
            "starting one in a table clears any other. When a sort, a page or a "
            "search takes a ticked row off the page, it is dropped from the "
            "selection, so an action only reaches rows the reader can see."
        ),
        pr.h2("What the reader sees and hears"),
        pr.p(
            "While a request is running, the part of the table about to be replaced "
            "dims. Alpine AJAX marks it aria-busy, which also tells a screen reader "
            "the rows are about to change."
        ),
        pr.p(
            "After every change, a screen reader hears how many records there are, "
            "such as 61 records, showing 1 to 10. It comes from a live region "
            "outside the rows, which stays on the page and changes only its words. A "
            "region swapped in with the rows would be new, and a new region is not "
            "read out."
        ),
        pr.p(
            "A search or filter that leaves nothing says Nothing matches, with a "
            "button that clears the search and filters but keeps the order and the "
            "hidden columns. An empty state of your own, chained after from_state(), "
            "is shown instead."
        ),
        pr.p(
            "Dates and decimals need no render(). A date is written as 2026-03-01 "
            "and a date with a time as 2026-03-01 14:05, unless the HUE_DATE_FORMAT "
            "and HUE_DATETIME_FORMAT settings give other strftime formats. With "
            "USE_TZ on, an aware datetime is converted to the current timezone "
            "first, as a template would convert it. A decimal is written in full as "
            "stored, so 2190.00 keeps its places. Anything else that is not a string "
            "or a number needs a render() on its column."
        ),
        pr.h2("Drawing the table"),
        pr.p(
            "DataTable.from_state() draws everything the declaration describes. None "
            "of the parts is exported on its own, so there is one way to put a "
            "declared table on a page. It binds to the request the page is rendered "
            "for, which is already in the context, so the view passes nothing else. "
            "Anything chained after it, such as a caption or an empty state of your "
            "own, stays on the table."
        ),
        pr.code(
            "async def index(\n"
            "    self, request: HttpRequest, context: HueContext[HttpRequest]\n"
            ") -> Page:\n"
            "    return Page(\n"
            '        title="Invoices",\n'
            '        body=DataTable.from_state(self.invoices).caption("Invoices"),\n'
            "    )"
        ),
        pr.p(
            "bind(request) is for code that wants the values instead of the table, "
            "such as a total for a heading. It returns the state, the page of rows "
            "and the total, and it is a coroutine because it is what asks for the "
            "rows."
        ),
        pr.h2("Why it is declared on the class"),
        pr.p(
            "It would read more naturally to build the table inside index, where the "
            "request already is. The action route is what stops it. A declaration "
            "registers that route on the view's router, and the route has to exist "
            "before Django builds its URL table, which happens once, when the "
            "URLconf is imported. A table built inside index would register it on "
            "the first request, too late: every action would come back 404, and its "
            "URL could not be reversed. FastAPI has the same constraint, since its "
            "include_router copies a router's routes when it is called."
        ),
        pr.p(
            "So the declaration is made once, at class scope, and bound once per "
            "request, when DataTable.from_state() renders it."
        ),
        pr.h2("How it fits together"),
        pr.p(
            "This section is for anyone changing the table. The key names every part "
            "of it: the element each response replaces, the action route, and the "
            "parameters in the URL. It has to be unique on the page."
        ),
        pr.code(
            '<div id="invoices" class="…">       <!-- the frame -->\n'
            '  <form id="invoices-act" method="post" hidden></form>\n'
            "  <div>  [search]   [Filter 2] [Columns] [reset]  </div>\n"
            '  <template x-teleport="body">     <!-- floats over the page -->\n'
            '    <div role="group">  2 selected [x] | [Archive]  </div>\n'
            "  </template>\n"
            '  <div id="invoices-rows" x-sync>  <!-- replaced -->\n'
            "    <table>\n"
            '      <th aria-sort="descending">\n'
            '        <a href="?invoices-sort=amount" x-target.push="invoices-rows">\n'
            "          Amount</a>\n"
            "      </th>\n"
            '      <td><input type="checkbox" name="selected"\n'
            '                 value="41" form="invoices-act"></td>\n'
            "    </table>\n"
            "    [pages]\n"
            "    <div hidden>                  <!-- what the forms carry -->\n"
            '      <input type="hidden" name="invoices-sort" value="-amount"\n'
            '             form="invoices-search">\n'
            "    </div>\n"
            "  </div>\n"
            "</div>\n"
            '<p id="invoices-summary" role="status" x-sync>61 records.</p>',
            language="html",
        ),
        pr.p(
            "The table is one frame with bands inside it. The toolbar, the rows and "
            "the pages share one border and radius. Only the band holding the table "
            "scrolls, because overflow on the frame would clip the Filter and "
            "Columns panels."
        ),
        pr.p(
            "Sorting, paging, searching and filtering replace the rows region and "
            "leave the toolbar alone, so the caret stays in the search box and an "
            "open panel stays open. Resetting and acting replace the whole frame, so "
            "the panels come back cleared."
        ),
        pr.p(
            "Since the toolbar is never replaced by a read, its forms cannot hold "
            "the rest of the state themselves: a hidden field in the search form "
            "would go on sending the order the table was first drawn in. Those "
            "fields are drawn in the rows region instead, each tied to its form by "
            "the form's id, and a browser submits a field tied to a form wherever it "
            "sits. The rows region is also synced, so any response that carries it "
            "refreshes it, which is what keeps a second table's links current when "
            "the first one changes."
        ),
        pr.p(
            "The selection goes through real checkboxes tied to an empty form in the "
            "same way. A form wrapped around the frame would contain the search "
            "form, and browsers discard a form nested inside another."
        ),
        pr.p(
            "Without Alpine, the sort links, the pages and the search box still work "
            "as full page loads. Everything else needs it: turning those loads into "
            "swaps, opening the Filter and Columns panels, the chips, the reset "
            "button and the selection bar. The Columns panel also needs it for a "
            "reason of its own, since its boxes mean the opposite of what the URL "
            "carries."
        ),
        pr.h2("Two examples"),
        pr.p(
            "Both tables below are the declaration from the top of the page, bound "
            "to different requests. The Python in this page filters and orders their "
            "rows."
        ),
        _specimen("invoices", sort="-amount"),
        pr.p(
            "The first is sorted by amount, descending, three to a page. The second "
            "is searched and filtered. It kept the order and went back to the first "
            "page, since page two of a different set of rows is not a page anyone "
            "asked for. The chips show what is on without opening the panel."
        ),
        _specimen("payments", q="n", status="paid", sort="customer"),
        pr.h2("Assumptions"),
        pr.bullets(
            [
                pr.p(
                    "One column is sorted at a time. Clicking another column "
                    "replaces the order: aria-sort marks one header, and ARIA has no "
                    "way to say which of two sorted columns came first."
                ),
                pr.p(
                    "Narrowing a table is a query to the server, so every control is "
                    "a link or a form and none is a JavaScript handler."
                ),
                pr.p(
                    "rows and an action's handler are plain functions, and run in a "
                    "thread rather than on the event loop, because Django raises "
                    "SynchronousOnlyOperation for a query made on the loop. Async "
                    "functions are not supported in either place yet."
                ),
                pr.p(
                    "Each read loads the page, so whatever else index computes runs "
                    "on every sort, search and page as well. Keep index cheap on a "
                    "page with a table."
                ),
            ]
        ),
        Alert()
        .variant("warning")
        .title("What is not done yet")
        .content(
            pr.bullets(
                [
                    pr.p(
                        "Actions need JavaScript. Alpine draws the bar they sit in, "
                        "so with it off there is nothing to press. The action form "
                        "carries no CSRF token of its own either, since the bundle "
                        "sends the header Django reads."
                    ),
                    pr.p(
                        "An action redraws the table from its declaration alone, so "
                        "a caption or an empty state chained after from_state() is "
                        "gone after the first action. A sort, a search or a page "
                        "keeps it, because each of those loads the page again."
                    ),
                    pr.p(
                        "A hyphen in a filter's name or an option's value can give "
                        "two controls the same id: a filter a with an option b-c and "
                        "a filter a-b with an option c both get "
                        "invoices-filter-a-b-c."
                    ),
                    pr.p(
                        "The filter panel does not show how many rows each answer "
                        "would leave. That count would have to be computed on the "
                        "server and swapped into the toolbar, which a read never "
                        "replaces."
                    ),
                ]
            )
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
