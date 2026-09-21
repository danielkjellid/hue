"""
A table that knows where its own state lives.

DataTable on its own is a renderer: you tell it what order the rows are in,
where the next order lives, what the checkboxes are called and what to do
with them, and you wire the four of those together yourself. Every one of
them is a separate contract, none of them is checkable, and a table that
sorts but forgets what was searched for is what you get when one is wrong.

This is the other way round. One declaration says everything a table is,
and the one part of it that is not fixed - which rows answer it - is the
one part that is a function:

    def invoices_for(request, asked):
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
            invoices = self.invoices.bind(request)
            return Page(
                title="Invoices",
                body=Stack().content(
                    TableSearch.from_state(invoices),
                    DataTable.from_state(invoices),
                    TablePagination.from_state(invoices),
                ),
            )

It is declared at class scope because that is the only time a route can
be registered, and the routes it registers call rows() the same way the
page does. Every way in - the page, a sort, a search, a page number, an
action - goes through that one function, which is what keeps all five
answering with the table in the state it was in. Action URLs carry the
state, so archiving on page two of a sorted table comes back to page two
of a sorted table.

rows is everything that matches, not the page of it. The page is sliced
afterwards, so a paginated table is a count and a slice rather than a
queryset walked to find out how long it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Mapping, Sequence
from urllib.parse import urlencode

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button, ButtonVariant
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import TextInput
from hue.ui.base import ChainableComponent
from hue.ui.molecules.pagination import Pagination
from hue.ui.molecules.table import Column, DataTable, resolve_value
from hue.utils import classnames

if TYPE_CHECKING:
    from hue.router import Router

# The name every row checkbox is submitted under.
SELECTED = "selected"

# What each part of the state is called in the query string.
SORT = "sort"
QUERY = "q"
PAGE = "page"

# Long enough that a word typed at speed is one request rather than five,
# short enough that the table has moved by the time you look at it.
SEARCH_DELAY = "300ms"

DEFAULT_PAGE_SIZE = 25

type Rows = Sequence[Mapping[str, Any]]
type ActionHandler = Callable[[Any, list[str]], Any]
# Given the request and what it asked for, everything that matches.
type RowsFor = Callable[[Any, "TableState"], Any]


@dataclass(frozen=True, slots=True)
class TableState:
    """
    What was asked for, read off the request and put back into every URL
    the table builds - so a sort keeps the search, a search keeps the
    order, and an action comes back to where it was done.
    """

    sort: str | None = None
    query: str = ""
    page: int = 1

    def replace(self, **changes: Any) -> TableState:
        """
        The same state with one thing different, which is what every link
        on the table is.

        Anything but the page sends you back to the first one: page four
        of a different search is not a page anybody asked for.
        """
        return TableState(
            sort=changes.get("sort", self.sort),
            query=changes.get("query", self.query),
            page=changes["page"] if "page" in changes else 1,
        )

    def params(self) -> dict[str, str]:
        asked = {SORT: self.sort or "", QUERY: self.query}
        if self.page > 1:
            asked[PAGE] = str(self.page)
        return {name: value for name, value in asked.items() if value}


@dataclass(frozen=True, slots=True)
class BulkAction:
    """
    Something to do with the rows that are ticked, and what it is called.

    The handler is given the request and the ids, and is whatever you would
    have written anyway - the service function that archives them.
    """

    label: str
    handler: ActionHandler
    variant: ButtonVariant = "outline"


def _total(rows: Any) -> int:
    """
    How many rows match, without walking them.

    A queryset counts in the database. A list has a count() too, but it
    wants an argument and raises without one, which is the difference
    worth catching.
    """
    try:
        return int(rows.count())
    except (AttributeError, TypeError):
        return len(rows)


def bound_or_raise(state: Any, component: str) -> BoundTable:
    """
    The bound table a component was given, or an explanation.

    Forgetting bind() is the one slip this shape invites, and left alone
    it surfaces as a missing attribute on a class nobody was thinking
    about. The declaration is a perfectly good object; it just does not
    know which rows to draw yet.
    """
    if isinstance(state, BoundTable):
        return state
    if isinstance(state, Datatable):
        raise TypeError(
            f"{component}.from_state() takes a table bound to a request, and "
            f"{state.key!r} is the declaration. Which rows answer a table "
            f"depends on what was asked for, so bind it to the request "
            f"first: table.bind(request)."
        )
    raise TypeError(
        f"{component}.from_state() takes a table bound to a request, not "
        f"{type(state).__name__}."
    )


@dataclass(frozen=True, slots=True)
class TableUrls:
    """
    Where this table's two routes live, for one request.

    Resolved when the table is bound rather than spelled by hand, because
    a path written into a link is right until the first include() moves
    the view under a prefix. The routes are registered by name and looked
    up by the same name, so there is one spelling of each and the
    framework fills in the rest.
    """

    read: str
    act: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class BoundTable:
    """
    One table, for one request: what was asked, what answers it, and the
    page that came back.

    The components take this. Every link they draw is on it already, so
    none of them reaches for the request or works out a URL of its own.
    """

    declaration: Datatable
    state: TableState
    page: Rows
    total: int
    urls: TableUrls

    @property
    def key(self) -> str:
        return self.declaration.key

    def href(self, **changes: Any) -> str:
        """
        This table with one thing changed, which is every link on it.
        """
        asked = self.state.replace(**changes).params()
        return self.urls.read + (f"?{urlencode(asked)}" if asked else "")

    def build_into(self, into: DataTable) -> DataTable:
        """
        The DataTable this describes.

        A method on the value rather than a function the component
        imports: table.py knowing about this module would be a circle, and
        what is being asked here is what the bound state is for.
        """
        declared = self.declaration
        into.id(self.key).columns(declared.columns).rows(self.page).sorted(
            self.state.sort
        ).sort_href(lambda order: self.href(sort=order))

        if declared.identifier is None:
            return into

        into.selectable(declared.identifier).name(SELECTED)
        if not declared.actions:
            return into

        into.bulk_actions(
            *(
                Button()
                .variant(action.variant)
                .size("xs")
                .type("submit")
                .content(action.label)
                .attr("formaction", self.action_url(name))
                for name, action in declared.actions.items()
            )
        )
        # A real form around real checkboxes, inside the frame so the
        # table is still the outermost thing and still what a response is
        # swapped into. Every button names its own action, so the form's
        # own is only a fallback for a browser that ignores formaction.
        return into.form(self.action_url(next(iter(declared.actions))))

    def action_url(self, name: str) -> str:
        """
        Where an action posts - carrying the state, so what comes back is
        the table as it was and not the first page of an unsorted one.
        """
        asked = self.state.params()
        return self.urls.act[name] + (f"?{urlencode(asked)}" if asked else "")


class Datatable:
    """
    One table's declaration, and the two routes that serve it.

    Everything about a table is fixed except which rows answer it, so
    everything but rows is stated here once and rows is a function called
    per request. Declared at class scope, because that is the only time a
    route can be registered.
    """

    def __init__(
        self,
        router: Router[Any],
        *,
        key: str,
        columns: list[Column],
        rows: RowsFor,
        identifier: str | None = None,
        search: str | None = None,
        actions: Mapping[str, BulkAction] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        self.key = key
        self.columns = columns
        self.rows = rows
        self.identifier = identifier
        self.search = search
        self.actions = dict(actions or {})
        self.page_size = page_size
        self._router = router
        # One spelling of each route name, used to register them and to
        # find them again. Two tables on one view would otherwise both
        # call their routes "read" and "act", since the router takes a
        # route's name off the handler's __name__ as it decorates.
        self._read_route = f"{key}_read"
        self._act_route = f"{key}_act"
        if self.actions and identifier is None:
            raise ValueError(
                f"{key} has actions but no identifier, so there is nothing "
                f"to hand them. Name the property a row is known by."
            )
        self._register()

    def build_into(self, into: DataTable) -> DataTable:
        """
        Never: a declaration cannot draw itself, because it does not know
        what was asked for. Here so that handing one to
        DataTable.from_state() says that rather than failing on a missing
        attribute.
        """
        bound_or_raise(self, "DataTable")
        raise AssertionError("unreachable")  # pragma: no cover

    def bind(self, request: Any) -> BoundTable:
        """
        Everything one request needs, in one value.
        """
        asked = self.state_of(request)
        matching = self.rows(request, asked)
        total = _total(matching)
        start = (asked.page - 1) * self.page_size
        page = list(matching[start : start + self.page_size])
        self._check_identifier(page)
        return BoundTable(self, asked, page, total, self._urls_for(request))

    def _urls_for(self, request: Any) -> TableUrls:
        """
        Both routes, reversed for this request.

        Once per binding rather than once per link: every href on the
        table is one of these two with a different query string on it.
        """
        return TableUrls(
            read=self._router._url_for(request, self._read_route),
            act={
                name: self._router._url_for(request, self._act_route, action=name)
                for name in self.actions
            },
        )

    def state_of(self, request: Any) -> TableState:
        asked = self._router._get_query_params(request)
        try:
            page = max(1, int(asked.get(PAGE, "1")))
        except ValueError:
            page = 1
        return TableState(
            sort=asked.get(SORT) or None, query=asked.get(QUERY, ""), page=page
        )

    def render(self, request: Any) -> ComponentType:
        """
        All of it, for a view that wants the table and no say in how it is
        arranged.
        """
        bound = self.bind(request)
        return html.div(
            *((TableSearch.from_state(bound),) if self.search else ()),
            DataTable.from_state(bound),
            TablePagination.from_state(bound),
            class_="flex flex-col gap-3",
        )

    def _check_identifier(self, page: Rows) -> None:
        """
        Every row has to carry what it is known by.

        Checked here rather than left to the first checkbox, because the
        error out of that names a key and a dict and not the reason either
        of them matters - and because a table whose ids are quietly
        missing posts an empty selection to an action that then does
        nothing to nothing.
        """
        if self.identifier is None or not page:
            return
        try:
            resolve_value(page[0], self.identifier)
        except ValueError:
            raise ValueError(
                f"{self.key} is identified by {self.identifier!r}, and its "
                f"rows do not carry it - they have {sorted(page[0])}. Every "
                f"row needs the property it is known by, whether or not a "
                f"column shows it: it is what a checkbox submits and what "
                f"an action is handed."
            ) from None

    def _register(self) -> None:
        """
        One route to read a state and one to act on a selection.

        Both go through the described method and both answer with the
        table, so the response to sorting and the response to archiving
        are the same thing and there is one way for the page to come up to
        date.
        """

        async def read(view: Any, request: Any, context: Any) -> ComponentType:
            return DataTable.from_state(self.bind(request))

        async def act(
            view: Any, request: Any, context: Any, action: str
        ) -> ComponentType:
            chosen = self.actions.get(action)
            if chosen is None:
                raise ValueError(
                    f"{self.key} has no action called {action!r}. It has "
                    f"{sorted(self.actions) or 'none at all'}."
                )
            chosen.handler(request, self._router._get_form_list(request, SELECTED))
            # Bound after, because the rows have just changed under it.
            return DataTable.from_state(self.bind(request))

        # Named before they are registered, not after: the router takes
        # a route's name off __name__ as it decorates.
        read.__name__ = self._read_route
        act.__name__ = self._act_route
        self._router.fragment_get(f"{self.key}/")(read)
        self._router.fragment_post(f"{self.key}/<str:action>/")(act)


def datatable(
    router: Router[Any],
    *,
    key: str,
    columns: list[Column],
    rows: RowsFor,
    identifier: str | None = None,
    search: str | None = None,
    actions: Mapping[str, BulkAction] | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> Datatable:
    """
    Declare a table and the two routes that serve it.

    key names the fragment path and the element every response is swapped
    into, so it has to be unique on the page - and it is the whole of the
    wiring, since every URL the table builds comes off it.

    rows is the only part of a table that is not fixed, so it is the only
    part that is a function. It is handed the request and the state that
    was asked for, and returns everything that matches - the whole
    filtered, ordered set, not the page of it. The page is sliced
    afterwards, so a queryset stays lazy and gets counted rather than
    walked.

    identifier names the property a row is known by. Giving one is what
    puts a checkbox in every row, and it is those values an action is
    handed. It is not one of the columns, because a row is usually known
    by something nobody wants to see.
    """
    return Datatable(
        router,
        key=key,
        columns=columns,
        rows=rows,
        identifier=identifier,
        search=search,
        actions=actions,
        page_size=page_size,
    )


# ----------------------------------------------------------------------
# The components a bound table draws itself with
# ----------------------------------------------------------------------


class TableSearch(ChainableComponent):
    """
    The box above a table, and the one part of it that is not swapped.

    Its own component because of where it has to be: the frame is what a
    response replaces, and a box swapped out from under the person typing
    in it loses the caret along with the focus.
    """

    category: ClassVar[str | None] = None

    @classmethod
    def from_state(cls, state: BoundTable) -> Self:
        return cls().content(_search_form(bound_or_raise(state, "TableSearch")))

    def _render(self, context: Context) -> Component:
        return html.div(
            *self._children,
            class_=classnames("max-w-xs", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


class TablePagination(ChainableComponent):
    """
    The pages of a table, under the frame rather than inside it - so it is
    drawn from the same state as the rows and does not vanish with them
    when they are swapped.
    """

    category: ClassVar[str | None] = None

    @classmethod
    def from_state(cls, state: BoundTable) -> Self:
        state = bound_or_raise(state, "TablePagination")
        size = state.declaration.page_size
        return cls().content(
            Pagination()
            .page(state.state.page)
            .page_size(size)
            .total_records(state.total)
            # Pagination takes all three and derives none of them, so the
            # one the other two decide is worked out here rather than left
            # at its default of one page.
            .total_pages(max(1, ceil(state.total / size)))
            .href(lambda page: state.href(page=page))
        )

    def _render(self, context: Context) -> Component:
        return html.div(
            *self._children,
            class_=classnames(self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


def _search_form(bound: BoundTable) -> ComponentType:
    """
    A GET form of its own. A form because Enter already does this, and
    x-target only turns the navigation into a swap - so it still works
    with Alpine switched off.
    """
    return html.form(
        TextInput()
        .name(QUERY)
        .attr("type", "search")
        .label(bound.declaration.search or "")
        .hidden_label()
        .placeholder(bound.declaration.search or "")
        .value(bound.state.query)
        .leading_icon(HueIcon("search")),
        # The order rides along, so searching keeps the order it was in.
        # The page does not: a search is a different set of rows, and page
        # four of it is not a page anybody asked for.
        *(
            html.input_(type="hidden", name=name, value=value)
            for name, value in bound.state.params().items()
            if name not in (QUERY, PAGE)
        ),
        method="get",
        action=bound.urls.read,
        **{
            "x-target": bound.key,
            f"@input.debounce.{SEARCH_DELAY}": "$el.requestSubmit()",
        },
    )
