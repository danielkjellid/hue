from __future__ import annotations

from typing import Any

from fastapi import Request
from hue import html, toast
from hue.context import HueContext
from hue.datatable import BulkAction, Filter, TableState, build_datatable_state
from hue.js import ajax
from hue.types.core import ComponentType
from hue.ui import Alert, Badge, Button, Column, DataTable, Empty, Pagination, Table
from hue.ui.atoms.badge import BadgeVariant
from hue_fastapi import HueView, Page, Router

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# The live demo: a declared table over a list of dictionaries, so the
# filtering, ordering and paging are the Python here. Eight rows and three to
# a page, because the demo route runs on a Worker with 10ms of CPU.
_INVOICES: list[dict[str, Any]] = [
    {
        "pk": "41",
        "invoice": "INV-2050",
        "customer": "Contoso",
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
        "customer": "Fabrikam",
        "amount": 840,
        "status": "overdue",
    },
    {
        "pk": "58",
        "invoice": "INV-2051",
        "customer": "Adventure Works",
        "amount": 415,
        "status": "paid",
    },
    {
        "pk": "62",
        "invoice": "INV-2052",
        "customer": "Tailspin Toys",
        "amount": 3120,
        "status": "paid",
    },
    {
        "pk": "70",
        "invoice": "INV-2053",
        "customer": "Litware",
        "amount": 960,
        "status": "pending",
    },
    {
        "pk": "74",
        "invoice": "INV-2054",
        "customer": "Proseware",
        "amount": 1875,
        "status": "overdue",
    },
    {
        "pk": "81",
        "invoice": "INV-2055",
        "customer": "Wingtip",
        "amount": 230,
        "status": "paid",
    },
]

_STATUS = [("paid", "Paid"), ("pending", "Pending"), ("overdue", "Overdue")]
_TONE: dict[str, BadgeVariant] = {
    "paid": "success",
    "pending": "warning",
    "overdue": "danger",
}


def _matching(request: Request, asked: TableState) -> list[dict[str, Any]]:
    found = [row for row in _INVOICES if asked.query.lower() in row["customer"].lower()]
    if statuses := asked.chosen("status"):
        found = [row for row in found if row["status"] in statuses]
    if asked.sort:
        field = asked.sort.removeprefix("-")
        found.sort(key=lambda row: row[field], reverse=asked.sort.startswith("-"))
    return found


def _archive(request: Request, ids: list[str]) -> None:
    # The demo is shared by every reader, so it says what it would do and
    # changes nothing.
    toast.success(f"Archived {len(ids)}", description="The demo keeps the rows.")


class DataTableDemo(HueView):
    """
    The page the live table reads from: every sort, search, filter and page
    is a GET of this index, and the archive action posts to the route the
    declaration registers on the router.
    """

    router = Router[Request]()

    invoices = build_datatable_state(
        router,
        key="invoices",
        columns=[
            Column("invoice", "Invoice"),
            Column("customer", "Customer", sort="customer"),
            Column("amount", "Amount", align="end", sort="amount"),
            Column(
                "status",
                "Status",
                render=lambda row: (
                    Badge().variant(_TONE[row["status"]]).content(row["status"].title())
                ),
            ),
        ],
        rows=_matching,
        identifier="pk",
        search="Search customers",
        filters=[Filter("status", "Status", options=_STATUS)],
        hideable=["customer", "status"],
        actions={"archive": BulkAction("Archive", _archive)},
        page_size=3,
    )

    async def index(self, request: Request, context: HueContext[Request]) -> Page:
        return Page(
            title="Invoices",
            body=html.div(DataTable.from_state(self.invoices))
            .id("invoices-demo")
            .class_("w-full"),
        )


# Live


def declared_table() -> ComponentType:
    return (
        html.div(
            DataTable()
            .loading()
            .columns(
                [
                    Column("invoice", "Invoice"),
                    Column("customer", "Customer"),
                    Column("amount", "Amount", align="end"),
                    Column("status", "Status"),
                ]
            )
        )
        .id("invoices-demo")
        .class_("w-full")
        .x_init(ajax("/demos/data-table/", target="invoices-demo"))
    )


# Anatomy


def columns_and_rows() -> DataTable:
    return (
        DataTable()
        .caption("Invoices, September 2026")
        .columns(
            [
                Column("invoice", "Invoice"),
                Column("customer.name", "Customer"),
                Column("customer.plan", "Plan"),
                Column("amount", "Amount", align="end"),
                Column(
                    "status",
                    "Status",
                    render=lambda row: (
                        Badge().variant(row["tone"]).dot().content(row["status"])
                    ),
                ),
            ]
        )
        .rows(
            [
                {
                    "invoice": "INV-2050",
                    "customer": {"name": "Contoso", "plan": "Scale"},
                    "amount": "2,190.00",
                    "status": "Pending",
                    "tone": "warning",
                },
                {
                    "invoice": "INV-2048",
                    "customer": {"name": "Northwind", "plan": "Pro"},
                    "amount": "1,200.00",
                    "status": "Paid",
                    "tone": "success",
                },
                {
                    "invoice": "INV-2049",
                    "customer": {"name": "Fabrikam", "plan": "Free"},
                    "amount": "840.00",
                    "status": "Declined",
                    "tone": "danger",
                },
            ]
        )
    )


def compact() -> DataTable:
    return (
        DataTable()
        .compact()
        .columns(
            [Column("invoice", "Invoice"), Column("amount", "Amount", align="end")]
        )
        .rows(
            [
                {"invoice": "INV-2050", "amount": "2,190.00"},
                {"invoice": "INV-2048", "amount": "1,200.00"},
                {"invoice": "INV-2049", "amount": "840.00"},
            ]
        )
    )


def grouped() -> DataTable:
    return (
        DataTable()
        .group_by("month")
        .columns(
            [Column("invoice", "Invoice"), Column("amount", "Amount", align="end")]
        )
        .rows(
            [
                {
                    "month": "September 2026",
                    "invoice": "INV-2048",
                    "amount": "1,200.00",
                },
                {"month": "September 2026", "invoice": "INV-2049", "amount": "840.00"},
                {"month": "October 2026", "invoice": "INV-2050", "amount": "2,190.00"},
            ]
        )
    )


# Loading, Empty, Error


def loading() -> DataTable:
    return (
        DataTable()
        .loading()
        .columns(
            [Column("invoice", "Invoice"), Column("amount", "Amount", align="end")]
        )
    )


def no_rows() -> DataTable:
    return DataTable().columns(
        [Column("invoice", "Invoice"), Column("amount", "Amount", align="end")]
    )


def own_empty_state() -> DataTable:
    return (
        DataTable()
        .columns(
            [Column("invoice", "Invoice"), Column("amount", "Amount", align="end")]
        )
        .empty(
            Empty()
            .compact()
            .title("No invoices yet")
            .description("Invoices you send appear here.")
            .actions(Button().variant("outline").size("xs").content("New invoice"))
        )
    )


def error() -> DataTable:
    return (
        DataTable()
        .columns(
            [Column("invoice", "Invoice"), Column("amount", "Amount", align="end")]
        )
        .error(
            Empty()
            .variant("danger")
            .compact()
            .title("Could not load invoices")
            .description("The billing service did not respond.")
            .actions(Button().variant("outline").size("xs").content("Retry"))
        )
    )


_DECLARATION = """from hue.datatable import (
    BulkAction,
    Filter,
    TableState,
    build_datatable_state,
)
from hue.ui import Column, DataTable


def invoices_for(request: HttpRequest, asked: TableState) -> QuerySet[Invoice]:
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
            Column("reference", "Invoice"),
            Column("customer.name", "Customer", sort="customer__name"),
            Column("amount", "Amount", align="end", sort="amount"),
        ],
        rows=invoices_for,
        identifier="pk",
        search="Search customers",
        filters=[
            Filter("status", "Status", options=STATUS),
            Filter("min", "Minimum amount", numeric=True, prefix="USD"),
        ],
        hideable=["customer.name", "amount"],
        actions={"archive": BulkAction("Archive", archive_invoices)},
    )

    async def index(
        self, request: HttpRequest, context: HueContext[HttpRequest]
    ) -> Page:
        return Page(title="Invoices", body=DataTable.from_state(self.invoices))"""


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("A DataTable from columns and rows"),
        pr.p(
            "columns() takes a list of Column and rows() takes the records. A "
            "Column reads its value with key, which is a dictionary key or an "
            "attribute, a dotted path such as customer.name into a nested record "
            "or a related object, or a callable given the row. render takes the "
            "row and returns whatever the cell holds, such as a Badge. "
            'align="end" ends the column and switches it to tabular figures, so '
            "the digits line up."
        ),
        pr.code(
            "DataTable().columns([\n"
            '    Column("reference", "Invoice"),\n'
            '    Column("customer.name", "Customer"),\n'
            '    Column("amount", "Amount", align="end"),\n'
            '    Column("status", "Status", render=lambda row: Badge()'
            '.content(row["status"])),\n'
            "]).rows(invoices)"
        ),
        pr.p(
            "A string, a number or a boolean is written as it is, and None as an "
            "empty cell. A date, a datetime and a time are written in the formats "
            "the context holds, which default to ISO 8601: 2026-03-01, "
            "2026-03-01 14:05 and 14:05. hue-django fills them from the "
            "HUE_DATE_FORMAT, HUE_DATETIME_FORMAT and HUE_TIME_FORMAT settings, "
            "and with USE_TZ on converts an aware datetime to the current "
            "timezone first. hue-fastapi takes them as formats= on configure_hue. "
            "A Decimal is written in full as stored, so 2190.00 keeps its places. "
            "Any other value raises, and needs a render() on its column."
        ),
        pr.p(
            "group_by() splits the rows into sections titled with the value its "
            "key reads. The rows have to arrive in that order, because a value "
            "that comes back later opens a section of its own. A blank value "
            "raises, since a section needs a name."
        ),
        pr.p(
            "loading() puts placeholder rows under the header, as many as there "
            "are rows already or three when there are none. empty() replaces the "
            "default empty state, and error() replaces the rows whatever else is "
            "set. A column with sort= raises on a DataTable built this way, "
            "because only a declaration knows where the sorted rows live."
        ),
        pr.h2("Declare a DataTable on a view"),
        pr.p(
            "Sorting, searching, filtering, paging and acting on picked rows all "
            "need the server, so they come with a table declared once on a "
            "HueView with build_datatable_state(). The declaration names the "
            "columns, the function that finds the rows, and what can be done with "
            "the rows a reader picks. DataTable.from_state() draws it."
        ),
        pr.code(_DECLARATION),
        pr.p(
            "The live example at the top of this page is this declaration over a "
            "list of dictionaries, served from a HueView under /demos/data-table/."
        ),
        pr.h3("Rows come from one function"),
        pr.p(
            "rows is the only part of a declared table that changes with each "
            "request, so it is the only part that is a function. It receives the "
            "request and a TableState holding what was asked for, and returns "
            "every row that matches: the whole filtered, ordered set, not just "
            "the page. The table counts it and slices out the page. A queryset "
            "stays lazy, so a paginated table costs one count and one slice in "
            "the database. A page number past the last page shows the last page."
        ),
        pr.p(
            "TableState carries the search in query, the order in sort, the page "
            "number in page and the hidden columns in hidden. chosen() reads a "
            "filter that can hold several answers, and value() reads one that "
            "holds a single answer."
        ),
        pr.p(
            'sort is spelled the way order_by and query strings spell it: "amount", '
            'or "-amount" for descending. The table only accepts an order that '
            "one of its columns declares with sort=. Any other order in the URL "
            "arrives as None, so nobody can sort by a field the table never "
            "shows, and sort can go straight to order_by. Filters are checked the "
            "same way: an answer a filter does not offer is dropped before rows "
            "sees it."
        ),
        pr.p(
            "There is no on_sort and no on_search. Both decide which rows to "
            "show, and rows already answers that. A page of a queryset is sliced "
            "after it is ordered, so sorting the rows already on screen would "
            "give the wrong rows."
        ),
        pr.h3("Why the declaration is on the class"),
        pr.p(
            "The declaration registers its action route on the view's router, "
            "and that route has to exist before the URLs are built. Django builds "
            "its URL table once, when the URLconf is imported, and FastAPI's "
            "include_router copies a router's routes when it is called. A table "
            "built inside index would register the route too late, and every "
            "action would come back 404. So the declaration is made once, at "
            "class scope, and bound to each request when DataTable.from_state() "
            "renders it."
        ),
        pr.h2("A declared DataTable keeps its state in the URL"),
        pr.p(
            "The order, the search, the page, the filters and the hidden columns "
            "are all in the address bar, each named under the table's key."
        ),
        pr.code(
            "/billing/?invoices-sort=-amount&invoices-q=contoso&invoices-status=paid",
            language="bash",
        ),
        pr.p(
            "Every link and toolbar form on the table points at the page the "
            "table is drawn on, which is the view's index. Alpine AJAX fetches "
            "that page and swaps in the part that changed, and pushes the URL, "
            "so it reloads to the same table, can be sent to someone, and works "
            "with the back button. With JavaScript off, sorting, paging and "
            "searching still work as full page loads."
        ),
        pr.p(
            "Each read loads the whole page, so whatever else index computes runs "
            "on every sort, search and page too."
        ),
        pr.p(
            "Two tables on one page keep separate state in one URL. Each table "
            "carries the other's parameters through its links and forms "
            "unchanged, so sorting one never resets the other. The key names "
            "every element of a table and every parameter, so it has to be "
            "unique on the page."
        ),
        pr.p(
            "No URL is written by hand. The table works out the page and the "
            "action route from the mount the request came in on, so a view "
            "included under a prefix, or included twice, links back into the "
            "mount the reader is using. A table can only build its URLs while "
            "the view that declared it is serving the request, and rendering it "
            "from another view raises an error."
        ),
        pr.code(
            'urlpatterns = [path("billing/", include(InvoicesView.urls))]\n'
            "\n"
            "# the page:    /billing/?invoices-sort=-amount\n"
            "# an action:   /billing/invoices/archive/"
        ),
        pr.h2("DataTable search, filters and columns"),
        pr.p(
            "search gives the table a search box, with the text as its label and "
            "placeholder. It is a GET form that submits 300 milliseconds after "
            "the last keystroke, and Enter submits it at once. Slash focuses it "
            "from anywhere on the page, except while focus is in another field "
            "or when the page has more than one table search. Escape empties it, "
            "and leaves the key alone while the box is already empty, so Escape "
            "still reaches a dialog the table sits in."
        ),
        pr.p(
            "Each Filter gets a parameter in the URL, a group in the panel behind "
            "the Filter button, and a chip under the toolbar for every answer "
            "that is on."
        ),
        pr.code(
            "# ?invoices-status=paid,draft\n"
            'Filter("status", "Status", options=STATUS)\n'
            "# ?invoices-min=500\n"
            'Filter("min", "Minimum amount", numeric=True, prefix="USD")'
        ),
        pr.p(
            "A Filter with options is a list of checkboxes, or radios with "
            "multiple=False. Without options it is a text field, and "
            "numeric=True makes it a number field, which drops anything that is "
            "not a finite number. prefix and placeholder decorate the field. "
            "There is no Apply button: a change submits the panel at once, and "
            "the chips show what is on and take it off again."
        ),
        pr.p(
            "A filter cannot be called sort, q, page, hide or selected, which the "
            "table already uses, and an option's value cannot hold a comma, which "
            "is what the URL puts between answers. Both raise when the table is "
            "declared."
        ),
        pr.p(
            "hideable lists the columns a reader may hide, by key. In the Columns "
            "panel a ticked box is a column that shows, while the URL carries the "
            "hidden ones, so a column added later shows up for someone following "
            "an old link. The other columns are listed too, ticked, disabled and "
            "marked locked."
        ),
        pr.p(
            "While a filter is on or a column is hidden, a reset button appears "
            "at the end of the toolbar. It takes the filters off and shows every "
            "column, and keeps the search and the order."
        ),
        pr.h2("DataTable bulk actions"),
        pr.p(
            "actions are what can be done with the rows a reader ticks, and "
            "identifier names the property a row is known by. The two come as a "
            "pair: actions put a checkbox in every row, and a declaration with "
            "one and not the other raises. The identifier is kept apart from the "
            "columns because a row is usually known by something nobody needs to "
            "see, such as a primary key. A row that lacks it raises."
        ),
        pr.code(
            'BulkAction("Archive", archive_invoices)\n'
            'BulkAction("Mark as paid", mark_paid, icon=Icon("check"))\n'
            "BulkAction(\n"
            '    "Delete",\n'
            "    delete_invoices,\n"
            '    variant="danger",\n'
            '    confirm=Dialog().destructive().title("Delete these invoices?"),\n'
            ")"
        ),
        pr.p(
            "A handler receives the request and the ids of the ticked rows. It "
            "never receives an id the reader could not see: the table posts its "
            "state along with the selection, runs rows for that state, and keeps "
            "only the posted ids it finds there. For a queryset that check is one "
            "filter on the identifier."
        ),
        pr.p(
            "confirm takes a Dialog with the question on it, for an action that "
            "cannot be taken back. The button in the bar opens the dialog, and "
            "the table fills its footer with Cancel and the button that runs the "
            "action."
        ),
        pr.p(
            "After an action the table redraws in the state it was in: the same "
            "page, order and filters. If the handler raises, the reader gets a "
            "danger toast naming the action, the table redraws as it now is, and "
            "the ticked rows stay ticked. The error is logged with its traceback, "
            "since nothing is raised past the route. A 403, 404 or other "
            "framework error raised by the handler is passed on for the framework "
            "to answer."
        ),
        pr.p(
            "Ticking a row brings up a bar that floats at the bottom of the "
            "window, with the count, a button that clears the selection, and the "
            "actions. Escape clears the selection too. There is one selection per "
            "page: starting one in a table clears any other. A ticked row that a "
            "sort, a page or a search takes off the page leaves the selection."
        ),
        pr.p(
            "rows and the handlers run in a thread rather than on the event loop, "
            "because Django refuses a query made on the loop. Async functions are "
            "not supported in either place."
        ),
        pr.h2("Drawing a declared DataTable"),
        pr.p(
            "DataTable.from_state() draws everything the declaration describes, "
            "and none of the parts is exported on its own. It binds to the "
            "request in the context, so the view passes nothing else. Anything "
            "chained after it, such as a caption or an empty state, stays on the "
            "table."
        ),
        pr.code(
            "async def index(self, request, context) -> Page:\n"
            "    return Page(\n"
            '        title="Invoices",\n'
            '        body=DataTable.from_state(self.invoices).caption("Invoices"),\n'
            "    )"
        ),
        pr.p(
            "A table searched or filtered down to nothing says Nothing matches, "
            "with a button that clears the search and the filters and keeps the "
            "order and the hidden columns. An empty() of your own is shown "
            "instead."
        ),
        pr.p(
            "bind(request) on the declaration is for code that wants the values "
            "instead of the table, such as a total for a heading. It is a "
            "coroutine that returns the state, the page of rows and the total."
        ),
        pr.h3("How a declared DataTable is put together"),
        pr.p(
            "The table is one frame with bands inside it: the toolbar, the rows "
            "and the pages share one border. Only the band holding the table "
            "scrolls sideways, because overflow on the frame would clip the "
            "Filter and Columns panels."
        ),
        pr.code(
            '<div id="invoices">                  <!-- the frame -->\n'
            '  <form id="invoices-act" method="post" hidden></form>\n'
            "  <div>  [search]   [Filter] [Columns] [reset]  </div>\n"
            '  <div id="invoices-rows" x-sync>    <!-- replaced by a read -->\n'
            "    <table>...</table>\n"
            "    [pages]\n"
            "    <div hidden>                     <!-- the state the forms send -->\n"
            '      <input type="hidden" name="invoices-sort" value="-amount"\n'
            '             form="invoices-search">\n'
            "    </div>\n"
            "  </div>\n"
            "</div>\n"
            '<p id="invoices-summary" role="status" x-sync>8 records.</p>',
            language="html",
        ),
        pr.p(
            "Sorting, paging, searching, filtering and hiding a column replace "
            "the rows region and leave the toolbar alone, so the caret stays in "
            "the search box and an open panel stays open. Resetting and running "
            "an action replace the whole frame."
        ),
        pr.p(
            "Since a read never replaces the toolbar, its forms cannot hold the "
            "rest of the state themselves. Those hidden fields are drawn in the "
            "rows region instead, each tied to its form by the form attribute. "
            "The row checkboxes are tied to the empty action form the same way, "
            "because a form wrapped around the frame would contain the search "
            "form, and browsers discard a nested form."
        ),
        Alert()
        .variant("warning")
        .title("Known gaps in a declared DataTable")
        .content(
            pr.bullets(
                [
                    pr.p(
                        "Actions need JavaScript, since Alpine draws the bar they "
                        "sit in. The action form carries no CSRF field, so the "
                        "CSRF token travels in the header hue's bundle sends."
                    ),
                    pr.p(
                        "An action redraws the table from its declaration alone, "
                        "so a caption or an empty() chained after from_state() is "
                        "gone after the first action. A sort, a search or a page "
                        "keeps it, because each of those loads the page again."
                    ),
                    pr.p(
                        "A hyphen in a filter's name can give two controls one "
                        "id: the second option of a filter called a and a text "
                        "filter called a-1 both get invoices-filter-a-1."
                    ),
                    pr.p(
                        "One column is sorted at a time. Clicking another column "
                        "replaces the order."
                    ),
                ]
            )
        ),
    )


PAGE = ComponentPage(
    DataTable,
    lede=(
        "A DataTable builds a Table from a list of columns and a list of "
        "records. Declared on a view, it also sorts, searches, filters, pages "
        "and acts on picked rows, all through links and forms whose state "
        "lives in the URL."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            declared_table,
            layout="stack",
            min_height=420,
            hint="A declared table on a demo route; Archive changes nothing",
        ),
        panel(
            "Anatomy",
            columns_and_rows,
            compact,
            grouped,
            layout="stack",
        ),
        panel("Loading", loading, layout="stack"),
        panel("Empty", no_rows, own_empty_state, layout="stack"),
        panel("Error", error, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "Each row's checkbox is labelled Select plus the text of the row's "
            "first cell, so a screen reader hears Select INV-2050 rather than a "
            "primary key.",
        ),
        Note(
            "a11y",
            "The header of the column the rows are sorted by carries aria-sort, "
            "on one header at a time. A sortable header's label is a link, so "
            "it is reached with Tab and followed with Enter.",
        ),
        Note(
            "a11y",
            "After each change a status region outside the rows says how many "
            "records there are, such as 8 records, showing 1 to 3. It stays on "
            "the page and only its words change, because a live region swapped "
            "in with the rows would not be read out.",
        ),
        Note(
            "a11y",
            "While a request runs, Alpine AJAX marks the part about to be "
            "replaced aria-busy, and the table dims it.",
        ),
        Note(
            "a11y",
            "loading() hides the placeholder rows with aria-hidden and marks "
            "the table aria-busy, so a screen reader is not read rows of nothing.",
        ),
        Note(
            "note",
            "The bar for picked rows is a group labelled Selected rows, not a "
            "toolbar, so Tab walks its buttons. Escape clears the selection.",
        ),
        Note(
            "warn",
            "The key names every id and parameter of a declared table, so two "
            "tables on one page need two keys.",
        ),
    ],
    related=[Table, Pagination],
    views=[DataTableDemo],
)
