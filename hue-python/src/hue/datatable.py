"""
A table that knows where its own state lives.

DataTable on its own is a renderer: you tell it what order the rows are in,
where the next order lives, what the checkboxes are called and what to do
with them, and you wire the four of those together yourself. Every one of
them is a separate contract, none of them is checkable, and a table that
sorts but forgets what was searched for is what you get when one is wrong.

This is the other way round. One method describes the table, and is given
the request and what the request asked for:

    class InvoicesView(HueView):
        router = Router[HttpRequest]()

        @datatable(router, "invoices")
        def invoices(self, request, asked):
            return table(
                columns=[
                    Column("invoice", "Invoice"),
                    Column("customer", "Customer", sort="customer__name"),
                    Column("amount", "Amount", align="end", sort="amount"),
                ],
                rows=Invoice.objects.filter(
                    customer__name__icontains=asked.query
                ).order_by(asked.sort or "reference"),
                identifier="pk",
                search="Search customers",
                actions={"archive": BulkAction("Archive", archive_invoices)},
            )

        async def index(self, request, context):
            invoices = self.invoices(request)
            return Page(
                title="Invoices",
                body=Stack().content(
                    TableSearch.from_state(invoices),
                    DataTable.from_state(invoices),
                    TablePagination.from_state(invoices),
                ),
            )

The decorator is what holds the rest together. Routes can only be
registered while the class body runs, and the rows can only be known once
there is a request - so the method is declared at class scope and called
at request time, and the routes it registers call it too. Every way in
goes through the same method, which is why a sort, a search, a page and an
action all come back with the table in the state it was in.

rows is everything that matches, not the page of it. The page is taken
here, so a paginated table is a count and a slice rather than a queryset
walked to find out how long it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Mapping, Sequence
from urllib.parse import urlencode

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
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
type Describe = Callable[[Any, Any, "TableState"], "TableSpec"]


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


@dataclass(frozen=True, slots=True)
class TableSpec:
    """
    What one table is, for one request. What the described method returns.
    """

    columns: list[Column]
    rows: Any
    identifier: str | None = None
    search: str | None = None
    actions: Mapping[str, BulkAction] = field(default_factory=dict)
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        if self.actions and self.identifier is None:
            raise ValueError(
                "This table has actions but no identifier, so there is "
                "nothing to hand them. Name the property a row is known by."
            )


def table(
    *,
    columns: list[Column],
    rows: Any,
    identifier: str | None = None,
    search: str | None = None,
    actions: Mapping[str, BulkAction] | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> TableSpec:
    """
    Describe a table for the request being answered.

    rows is everything that matches - the whole filtered, ordered set. The
    page is taken from it afterwards, so a queryset stays lazy and gets
    counted rather than walked.

    identifier names the property a row is known by. Giving one is what
    puts a checkbox in every row, and it is those values an action is
    handed. It is not one of the columns, because a row is usually known
    by something nobody wants to see.
    """
    return TableSpec(
        columns=columns,
        rows=rows,
        identifier=identifier,
        search=search,
        actions=dict(actions or {}),
        page_size=page_size,
    )


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


@dataclass(frozen=True, slots=True)
class BoundTable:
    """
    One table, for one request: what was asked, what answers it, and the
    page that came back.

    The components take this. Every link they draw is on it already, so
    none of them reaches for the request or works out a URL of its own.
    """

    key: str
    root: str
    state: TableState
    spec: TableSpec
    page: Rows
    total: int

    def href(self, **changes: Any) -> str:
        """
        This table with one thing changed, which is every link on it.
        """
        asked = self.state.replace(**changes).params()
        return self.root + (f"?{urlencode(asked)}" if asked else "")

    def build_into(self, into: DataTable) -> DataTable:
        """
        The DataTable this describes.

        A method on the value rather than a function the component
        imports: table.py knowing about this module would be a circle, and
        what is being asked here is what the bound state is for.
        """
        spec = self.spec
        into.id(self.key).columns(spec.columns).rows(self.page).sorted(
            self.state.sort
        ).sort_href(lambda order: self.href(sort=order))

        if spec.identifier is None:
            return into

        into.selectable(spec.identifier).name(SELECTED)
        if not spec.actions:
            return into

        into.bulk_actions(
            *(
                Button()
                .variant(action.variant)
                .size("xs")
                .type("submit")
                .content(action.label)
                .attr("formaction", self.action_url(name))
                for name, action in spec.actions.items()
            )
        )
        # A real form around real checkboxes, inside the frame so the
        # table is still the outermost thing and still what a response is
        # swapped into. Every button names its own action, so the form's
        # own is only a fallback for a browser that ignores formaction.
        return into.form(self.action_url(next(iter(spec.actions))))

    def action_url(self, name: str) -> str:
        """
        Where an action posts - carrying the state, so what comes back is
        the table as it was and not the first page of an unsorted one.
        """
        asked = self.state.params()
        return f"{self.root}{name}/" + (f"?{urlencode(asked)}" if asked else "")


class Datatable:
    """
    A described table and the two routes that serve it.

    Built by the decorator while the class body runs, which is the only
    time a route can be registered - and it calls the method it decorates
    at request time, which is the only time the rows can be known.
    """

    def __init__(self, router: Router[Any], key: str, describe: Describe) -> None:
        self.key = key
        self.describe = describe
        self._router = router
        self._register()

    @property
    def root(self) -> str:
        return f"/{self.key}/"

    def __get__(self, view: Any, owner: type | None = None) -> Any:
        """
        self.invoices(request) on the view, and the Datatable itself off
        the class - so the routes can reach it without an instance.
        """
        if view is None:
            return self
        return lambda request: self.bind(view, request)

    def bind(self, view: Any, request: Any) -> BoundTable:
        """
        Everything one request needs, in one value.
        """
        asked = self.state_of(request)
        spec = self.describe(view, request, asked)
        total = _total(spec.rows)
        start = (asked.page - 1) * spec.page_size
        page = list(spec.rows[start : start + spec.page_size])
        self._check_identifier(spec, page)
        return BoundTable(self.key, self.root, asked, spec, page, total)

    def state_of(self, request: Any) -> TableState:
        asked = self._router._get_query_params(request)
        try:
            page = max(1, int(asked.get(PAGE, "1")))
        except ValueError:
            page = 1
        return TableState(
            sort=asked.get(SORT) or None, query=asked.get(QUERY, ""), page=page
        )

    def render(self, view: Any, request: Any) -> ComponentType:
        """
        All of it, for a view that wants the table and no say in how it is
        arranged.
        """
        bound = self.bind(view, request)
        return html.div(
            *((TableSearch.from_state(bound),) if bound.spec.search else ()),
            DataTable.from_state(bound),
            TablePagination.from_state(bound),
            class_="flex flex-col gap-3",
        )

    def _check_identifier(self, spec: TableSpec, page: Rows) -> None:
        """
        Every row has to carry what it is known by.

        Checked here rather than left to the first checkbox, because the
        error out of that names a key and a dict and not the reason either
        of them matters - and because a table whose ids are quietly
        missing posts an empty selection to an action that then does
        nothing to nothing.
        """
        if spec.identifier is None or not page:
            return
        try:
            resolve_value(page[0], spec.identifier)
        except ValueError:
            raise ValueError(
                f"{self.key} is identified by {spec.identifier!r}, and its "
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
            return DataTable.from_state(self.bind(view, request))

        async def act(
            view: Any, request: Any, context: Any, action: str
        ) -> ComponentType:
            chosen = self.bind(view, request).spec.actions.get(action)
            if chosen is None:
                known = sorted(self.bind(view, request).spec.actions)
                raise ValueError(
                    f"{self.key} has no action called {action!r}. It has "
                    f"{known or 'none at all'}."
                )
            chosen.handler(request, self._router._get_form_list(request, SELECTED))
            # Bound again, because the rows have just changed under it.
            return DataTable.from_state(self.bind(view, request))

        # Named before they are registered, not after: the router takes a
        # route's name off __name__ as it decorates, so two tables on one
        # view would otherwise both call their routes "read" and "act".
        read.__name__ = f"{self.key}_read"
        act.__name__ = f"{self.key}_act"
        self._router.fragment_get(f"{self.key}/")(read)
        self._router.fragment_post(f"{self.key}/<str:action>/")(act)


def datatable(router: Router[Any], key: str) -> Callable[[Describe], Datatable]:
    """
    Declare a table, and the routes that serve it, from the method that
    describes it.

    key names the fragment path and the element every response is swapped
    into, so it has to be unique on the page - and it is the whole of the
    wiring, since every URL the table builds comes off it.

    The method is given the view, the request and the state that was asked
    for, and returns table(). It runs for the page, for a sort, for a
    search, for a page and for an action, which is what keeps all five
    answering with the table in the state it was in.
    """

    def decorate(describe: Describe) -> Datatable:
        return Datatable(router, key, describe)

    return decorate


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
        return cls().content(_search_form(state))

    def _render(self, context: HueContext) -> Component:
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
        size = state.spec.page_size
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

    def _render(self, context: HueContext) -> Component:
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
        .label(bound.spec.search or "")
        .hidden_label()
        .placeholder(bound.spec.search or "")
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
        action=bound.root,
        **{
            "x-target": bound.key,
            f"@input.debounce.{SEARCH_DELAY}": "$el.requestSubmit()",
        },
    )
