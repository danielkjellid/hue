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
            return Page(title="Invoices", body=self.invoices.bind(request))

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

bind() answers with the table itself - a component, and the whole of it:
the search box, the rows and the pages. Give it children instead and it
renders those, each of them finding the same binding in the context, so
a pagination bar can sit in a page footer far from the rows it pages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from json import dumps
from math import ceil
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Literal,
    Mapping,
    Sequence,
)
from urllib.parse import urlencode

from htmy import Context, html

from hue.js import unsafe
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui.atoms.button import Button, ButtonVariant
from hue.ui.atoms.checkbox import Checkbox
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import NumberInput, TextInput
from hue.ui.base import ChainableComponent
from hue.ui.molecules.menu import (
    DropdownMenu,
    MenuItem,
    MenuLabel,
    MenuSeparator,
)
from hue.ui.molecules.pagination import Pagination
from hue.ui.molecules.popover import Popover
from hue.ui.molecules.table import (
    Column,
    DataTable,
    TableSource,
    form_id,
    resolve_value,
    rows_id,
)
from hue.utils import classnames, render_when

if TYPE_CHECKING:
    from hue.router import Router

# The name every row checkbox is submitted under.
SELECTED = "selected"

# What each part of the state is called in the query string.
SORT = "sort"
QUERY = "q"
PAGE = "page"
HIDE = "hide"
DENSITY = "density"

# What a filter cannot be called, because the table is already using it.
RESERVED = (SORT, QUERY, PAGE, HIDE, DENSITY)

# Long enough that a word typed at speed is one request rather than five,
# short enough that the table has moved by the time you look at it.
SEARCH_DELAY = "300ms"

DEFAULT_PAGE_SIZE = 25

# The count on the Filter button: how many answers are on, beside the
# word rather than instead of it, so the button still says what it opens.
_FILTER_COUNT = (
    "ms-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full "
    "bg-accent px-1 font-ui text-2xs font-bold tabular-nums text-accent-fg"
)

# A group of answers to one question, ruled off from the next.
_GROUP = "border-0 p-0 [&+&]:mt-4 [&+&]:border-t [&+&]:border-border [&+&]:pt-4"
_LEGEND = (
    "mb-2 block w-full p-0 font-ui text-2xs font-bold uppercase "
    "tracking-[0.05em] text-fg-muted"
)

# The applied row: a whole line of the band, which basis-full takes.
_APPLIED_ROW = "flex basis-full flex-wrap items-center gap-2"
_APPLIED_LABEL = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-muted"
_LOCKED = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-subtle"
_CHIP = (
    "inline-flex items-center gap-1.5 rounded-sm border border-border "
    "bg-canvas-subtle py-0.5 ps-2 pe-1.5 text-sm text-fg "
    "hover:border-border-hover hover:bg-surface-hover"
)

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

    chosen() and value() are how rows() reads the filters: one of them
    for a filter that can hold several answers and one for a filter that
    holds one, so neither call has to know how the query string spells
    them.
    """

    sort: str | None = None
    query: str = ""
    page: int = 1
    filters: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    hidden: tuple[str, ...] = ()
    compact: bool = False

    def chosen(self, name: str) -> tuple[str, ...]:
        """
        Everything picked in one filter, empty when nothing was.
        """
        return self.filters.get(name, ())

    def value(self, name: str) -> str | None:
        """
        The one answer a single-value filter holds, or None.
        """
        picked = self.chosen(name)
        return picked[0] if picked else None

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
            filters=changes.get("filters", self.filters),
            hidden=changes.get("hidden", self.hidden),
            compact=changes.get("compact", self.compact),
        )

    def without(self, name: str, value: str | None = None) -> TableState:
        """
        The same state with one filter off, or one answer taken out of
        one - which is what a chip in the applied band undoes.
        """
        left = {
            key: tuple(v for v in values if key != name or v != value)
            for key, values in self.filters.items()
        }
        if value is None:
            left.pop(name, None)
        return self.replace(filters={k: v for k, v in left.items() if v})

    def params(self) -> dict[str, str]:
        asked = {SORT: self.sort or "", QUERY: self.query}
        # One parameter per filter, answers comma-joined, which is how a
        # query string already spells a list somebody might hand-edit.
        for name, values in self.filters.items():
            if values:
                asked[name] = ",".join(values)
        if self.hidden:
            asked[HIDE] = ",".join(self.hidden)
        if self.compact:
            asked[DENSITY] = "compact"
        if self.page > 1:
            asked[PAGE] = str(self.page)
        return {name: value for name, value in asked.items() if value}


type FilterKind = Literal["choice", "text", "number"]


@dataclass(frozen=True, slots=True)
class Filter:
    """
    One way of narrowing a table, and what it is called in the URL.

    Given options it is a list to tick through, and multiple says whether
    more than one can be on at a time; given none it is a field to type
    a value into. Either way the answers land in the state rows() is
    handed, and the table draws the panel, the count on the trigger and
    the chips that undo it.

        Filter("status", "Status", options=[("paid", "Paid")])
        Filter("min", "Minimum amount", kind="number", prefix="USD")
    """

    name: str
    label: str
    options: Sequence[tuple[str, str]] = ()
    multiple: bool = True
    kind: FilterKind = "choice"
    prefix: str | None = None
    placeholder: str | None = None

    def labelled(self, value: str) -> str:
        """
        What one answer is called, for the chip that undoes it. Its own
        label when it came from a list, the value itself when it was
        typed.
        """
        for option, label in self.options:
            if option == value:
                return label
        return value


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


def _one(asked: Mapping[str, list[str]], name: str) -> str | None:
    """
    The one value a parameter holds, or the last of several.
    """
    values = asked.get(name)
    return values[-1] if values else None


def _many(asked: Mapping[str, list[str]], name: str) -> tuple[str, ...]:
    """
    Every value a parameter holds, however it was spelled.

    A browser repeats the name once per box; a link the table built
    joins them with commas, because that is what somebody hand-editing a
    query string would write. Both read the same.
    """
    return tuple(
        part for value in asked.get(name, ()) for part in value.split(",") if part
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


def bound_from(context: Context, component: str) -> BoundTable:
    """
    The bound table a component is being rendered inside, or an
    explanation of what is missing.

    Every part of a table reads the same one, which is what lets a
    pagination bar sit in a page footer far from the rows it pages.
    """
    found = context.get(TableSource)
    if isinstance(found, BoundTable):
        return found
    raise ValueError(
        f"{component} draws part of a table bound to a request, and there "
        f"is none here. Render it inside one: table.bind(request), which "
        f"is a component and offers itself to everything in it."
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
class BoundTable(TableSource):
    """
    One table, for one request: what was asked, what answers it, and the
    page that came back.

    Offered to everything inside the view that binds it. Every link a
    component draws is on here already, so none of them reaches for the
    request or works out a URL of its own.
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
        hidden = set(self.state.hidden)
        into.id(self.key).columns(
            [column for column in declared.columns if column.key not in hidden]
        ).rows(self.page).compact(self.state.compact).sorted(self.state.sort).sort_href(
            lambda order: self.href(sort=order)
        )

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
                .attr("form", form_id(self.key))
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

    def __init__(  # noqa: PLR0913 - the declaration, and see datatable() below
        self,
        router: Router[Any],
        *,
        key: str,
        columns: list[Column],
        rows: RowsFor,
        identifier: str | None = None,
        search: str | None = None,
        filters: Sequence[Filter] = (),
        hideable: Sequence[str] = (),
        density: bool = False,
        actions: Mapping[str, BulkAction] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        self.key = key
        self.columns = columns
        self.rows = rows
        self.identifier = identifier
        self.search = search
        self.filters = list(filters)
        self.hideable = list(hideable)
        self.density = density
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
        declared = {column.key for column in columns if isinstance(column.key, str)}
        for stranger in [key for key in self.hideable if key not in declared]:
            raise ValueError(
                f"{key} says {stranger!r} can be hidden, and it has no such "
                f"column. It has {sorted(declared)}."
            )
        for taken in [f.name for f in self.filters if f.name in RESERVED]:
            raise ValueError(
                f"{key} has a filter called {taken!r}, which is what the "
                f"table already calls the order, the search or the page in "
                f"its own URLs. Name it something else."
            )
        self._register()

    def bind(self, request: Any) -> TableView:
        """
        The table, for this request: a component, and the whole of it.

        Rendered on its own it is the search box, the rows and the pages.
        Given children it renders those instead, and each of them finds
        this same binding in the context - which is what lets a
        pagination bar sit in a page footer far from the rows it pages.
        """
        asked = self.state_of(request)
        matching = self.rows(request, asked)
        total = _total(matching)
        start = (asked.page - 1) * self.page_size
        page = list(matching[start : start + self.page_size])
        self._check_identifier(page)
        return TableView(BoundTable(self, asked, page, total, self._urls_for(request)))

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
        # Every value, not just the last: a set of checkboxes sharing a
        # name is how a browser submits a list, and a flat dict keeps one
        # of them.
        asked = self._router._get_query_values(request)
        try:
            page = max(1, int(_one(asked, PAGE) or "1"))
        except ValueError:
            page = 1
        hideable = set(self.hideable)
        return TableState(
            sort=_one(asked, SORT) or None,
            query=_one(asked, QUERY) or "",
            page=page,
            filters=self._filters_in(asked),
            # Only columns that could have been hidden, so a key typed
            # into the URL cannot take away a column nobody may hide.
            hidden=tuple(key for key in _many(asked, HIDE) if key in hideable),
            compact=_one(asked, DENSITY) == "compact",
        )

    def _filters_in(self, asked: Mapping[str, list[str]]) -> dict[str, tuple[str, ...]]:
        """
        What each filter was told.

        An answer a list-shaped filter does not offer is dropped rather
        than passed on: the query string is somewhere anybody can type,
        and rows() should not have to defend itself against it.
        """
        found: dict[str, tuple[str, ...]] = {}
        for declared in self.filters:
            values = _many(asked, declared.name)
            if declared.options:
                offered = {option for option, _ in declared.options}
                values = tuple(value for value in values if value in offered)
            if values:
                found[declared.name] = values if declared.multiple else values[:1]
        return found

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
            return self.bind(request)

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
            return self.bind(request)

        # Named before they are registered, not after: the router takes
        # a route's name off __name__ as it decorates.
        read.__name__ = self._read_route
        act.__name__ = self._act_route
        self._router.fragment_get(f"{self.key}/")(read)
        self._router.fragment_post(f"{self.key}/<str:action>/")(act)


def datatable(  # noqa: PLR0913 - see "One argument each" below
    router: Router[Any],
    *,
    key: str,
    columns: list[Column],
    rows: RowsFor,
    identifier: str | None = None,
    search: str | None = None,
    filters: Sequence[Filter] = (),
    hideable: Sequence[str] = (),
    density: bool = False,
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

    filters are the other ways of narrowing it. Each one becomes a
    parameter of its own in the URL, a group in the panel behind the
    Filter button, and a chip in the band under it - and its answers
    arrive in the same state rows() is already reading the search off.

    hideable names the columns a reader may put away. Everything else is
    locked, and the panel says so on the row rather than refusing the
    click silently. density adds the choice between comfortable rows and
    compact ones.

    One argument each: search, filters, hideable and density are all the
    same thing said four times - the ways of narrowing the table - and
    there is a case for them being one toolbar argument instead. Left
    apart for now, while there is still something being learned about
    what each of them needs.
    """
    return Datatable(
        router,
        key=key,
        columns=columns,
        rows=rows,
        identifier=identifier,
        search=search,
        filters=filters,
        hideable=hideable,
        density=density,
        actions=actions,
        page_size=page_size,
    )


# ----------------------------------------------------------------------
# The components a bound table draws itself with
# ----------------------------------------------------------------------


class TableView(ChainableComponent):
    """
    One table, bound to one request, and everything that narrows it.

    What bind() returns, and a component like any other. Rendered on its
    own it is the whole package - the search box, the rows and the pages.
    Given children it renders those instead, and every part of a table
    finds this binding in the context rather than being handed it, so a
    pagination bar can sit in a page footer far from the rows it pages.

        self.invoices.bind(request)

        self.invoices.bind(request).content(TableSearch(), DataTable())
    """

    category: ClassVar[str | None] = None

    def __init__(self, bound: BoundTable) -> None:
        super().__init__()
        self._bound = bound

    @property
    def state(self) -> TableState:
        """What was asked for."""
        return self._bound.state

    @property
    def page(self) -> Rows:
        """The rows that answer it, for the page being looked at."""
        return self._bound.page

    @property
    def total(self) -> int:
        """How many rows match in all, not just on this page."""
        return self._bound.total

    @property
    def urls(self) -> TableUrls:
        """Where this table's own routes live."""
        return self._bound.urls

    def href(self, **changes: Any) -> str:
        """
        This table with one thing changed, which is every link on it -
        and what a view links to when it wants to send somebody to a
        state of it.
        """
        return self._bound.href(**changes)

    def htmy_context(self) -> Context:
        return {TableSource: self._bound}

    def _render(self, context: Context) -> Component:
        return html.div(
            *(self._children or self._package()),
            class_=classnames("flex flex-col gap-3", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )

    def _package(self) -> tuple[ComponentType, ...]:
        """
        The whole table when nobody said how to lay it out, welded into
        one frame: a band of ways to narrow it, the rows, and a band with
        the pages. One border and one radius, because they are one thing.
        """
        declared = self._bound.declaration
        table = DataTable().under(TablePagination())
        band: list[ComponentType] = []
        if declared.search:
            band.append(TableSearch())
        # After the spacer, at the end of the band: a panel anchored to a
        # trigger near the middle opens across the rows.
        controls: list[ComponentType] = []
        if declared.filters:
            controls.append(TableFilters())
        if declared.hideable:
            controls.append(TableColumns())
        if declared.density:
            controls.append(TableOptions())
        if controls:
            band.extend((html.span(class_="flex-1"), *controls))
        if band:
            table.toolbar(*band)
        return (table,)


class TableSearch(ChainableComponent):
    """
    The box above a table, and the one part of it that is not swapped.

    Its own component because of where it has to be: the frame is what a
    response replaces, and a box swapped out from under the person typing
    in it loses the caret along with the focus.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = bound_from(context, "TableSearch")
        return html.div(
            *(self._children or (_search_form(bound),)),
            # Takes the free space in the band up to a readable cap: a
            # field as wide as the table reads as a search of the page,
            # and this one only ever searches these rows.
            class_=classnames(
                "min-w-0 flex-1 basis-64 sm:max-w-[340px]",
                self._get_prop("class_"),
            ),
            **{
                "x-data": "hueTableSearch",
                "x-on:keydown.window.slash": "focusField($event)",
                **self._get_base_html_attrs(),
            },
        )


class TablePagination(ChainableComponent):
    """
    The pages of a table, under the frame rather than inside it - so it is
    drawn from the same state as the rows and does not vanish with them
    when they are swapped.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = bound_from(context, "TablePagination")
        size = bound.declaration.page_size
        bar = (
            Pagination()
            .page(bound.state.page)
            .page_size(size)
            .total_records(bound.total)
            # Pagination takes all three and derives none of them, so the
            # one the other two decide is worked out here rather than left
            # at its default of one page.
            .total_pages(max(1, ceil(bound.total / size)))
            .href(lambda page: bound.href(page=page))
            .target(rows_id(bound.key) or "")
        )
        if class_ := self._get_prop("class_"):
            bar.class_(class_)
        bar._attrs.update(self._attrs)
        return bar


class TableFilters(ChainableComponent):
    """
    The other ways of narrowing a table: a panel of them behind one
    button, and a chip for every one that is on.

    The panel is a GET form that submits itself the moment something in
    it changes - there is no Apply, because the chips already say what is
    on and already undo it.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = bound_from(context, "TableFilters")
        declared = bound.declaration.filters
        if not declared:
            return UNDEFINED

        return html.div(
            html.form(
                _filter_panel(bound, declared),
                # The search and the order ride along, so narrowing keeps
                # both. The page does not: a filter is a different set of
                # rows, and page four of it is nowhere anybody was.
                *(
                    html.input_(type="hidden", name=name, value=value)
                    for name, value in bound.state.params().items()
                    if name not in {PAGE, *(f.name for f in declared)}
                ),
                method="get",
                action=bound.urls.read,
                # No box of its own: the controls belong to the band
                # around them, and this is only here to be submitted.
                class_="contents",
                **{
                    "x-ref": "form",
                    "x-target.push": rows_id(bound.key) or bound.key,
                    "@change": "apply()",
                },
            ),
            _applied_chips(),
            class_="contents",
            **{"x-data": "hueTableFilters"},
        )


def _filter_panel(bound: BoundTable, declared: Sequence[Filter]) -> ComponentType:
    """
    One popover holding every filter, grouped and legended.
    """
    return (
        Popover()
        .title("Filter")
        .placement("bottom-end")
        .trigger(
            Button()
            .variant("outline")
            .size("sm")
            .content(
                HueIcon("list-filter"),
                "Filter",
                html.span(
                    class_=_FILTER_COUNT,
                    **{
                        "x-show": "applied.length",
                        "x-text": "applied.length",
                        "x-cloak": True,
                    },
                ),
            )
        )
        .content(*(_filter_group(bound, one) for one in declared))
    )


def _filter_group(bound: BoundTable, declared: Filter) -> ComponentType:
    """
    One filter, as a legended group - which is what a set of boxes that
    answer the same question is, and the only way a screen reader hears
    the question before the answers.
    """
    picked = bound.state.chosen(declared.name)
    if not declared.options:
        return html.fieldset(
            html.legend(declared.label, class_=_LEGEND),
            _filter_field(bound.key, declared, picked),
            class_=_GROUP,
        )
    return html.fieldset(
        html.legend(declared.label, class_=_LEGEND),
        *(
            Checkbox()
            .name(declared.name)
            .value(option)
            .label(label)
            .checked(option in picked)
            # Every box in the group submits the same name, so the id
            # cannot come from it: the label beside each one has to point
            # at that one and not at the first of them.
            .id(f"{bound.key}-{declared.name}-{option}")
            .attr("data-filter", declared.name)
            .attr("data-group", declared.label)
            .attr("data-option", label)
            for option, label in declared.options
        ),
        class_=_GROUP,
    )


def _filter_field(key: str, declared: Filter, picked: tuple[str, ...]) -> ComponentType:
    """
    A filter with nothing to tick is one to type into.

    The id carries the table's key and the name does not: the name is the
    query parameter, which is the same on every table, and the id has to
    be the one thing on the page it names.
    """
    field = NumberInput() if declared.kind == "number" else TextInput()
    field.name(declared.name).label(declared.label).hidden_label().size("sm")
    field.id(f"{key}-{declared.name}")
    field.value(picked[0] if picked else "")
    field.attr("data-filter", declared.name).attr("data-group", declared.label)
    if declared.prefix is not None:
        field.prefix(declared.prefix)
    if declared.placeholder is not None:
        field.placeholder(declared.placeholder)
    return field


def _applied_chips() -> ComponentType:
    """
    Everything that is on, and one press to take any of it off.

    A whole line of the band to itself, so a narrowed table says so above
    the rows rather than only behind a closed popover.
    """
    return html.div(
        html.span("Applied", class_=_APPLIED_LABEL),
        html.template(
            html.button(
                html.span(**{"x-text": "chip.name + ': ' + chip.label"}),
                HueIcon("x").class_("size-3"),
                type="button",
                class_=_CHIP,
                **{
                    "@click": "remove(chip)",
                    ":aria-label": "'Remove filter ' + chip.name + ': ' + chip.label",
                },
            ),
            **{"x-for": "chip in applied", ":key": "chip.group + chip.value"},
        ),
        Button()
        .variant("link")
        .size("xs")
        .content("Clear all")
        .x_on("click", unsafe("clear()")),
        class_=_APPLIED_ROW,
        **{"x-show": "applied.length", "x-cloak": True},
    )


class TableColumns(ChainableComponent):
    """
    Which columns are showing, and the ones that cannot be put away.

    A checkbox list behind one button, with the count in its header. A
    ticked box is a column that is showing, which is the way round
    anybody reads a list of columns - but the URL carries the ones that
    are hidden, so a column added later shows itself to somebody
    following an old link rather than hiding from them.

    The columns nobody may hide are in the list too, ticked and disabled
    and said to be locked: the affordance states the rule rather than
    refusing the click without a word.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = bound_from(context, "TableColumns")
        declared = bound.declaration
        if not declared.hideable:
            return UNDEFINED

        hideable = set(declared.hideable)
        hidden = set(bound.state.hidden)
        showing = sum(1 for column in declared.columns if str(column.key) not in hidden)
        return html.div(
            Popover()
            .fit()
            .placement("bottom-end")
            .trigger(
                Button()
                .variant("outline")
                .size("sm")
                .content(HueIcon("columns-3"), "Columns")
            )
            .content(
                html.div(
                    html.span("Columns", class_=_APPLIED_LABEL),
                    html.span(
                        f"{showing} of {len(declared.columns)}",
                        class_="text-2xs tabular-nums text-fg-muted",
                    ),
                    class_="flex items-baseline justify-between gap-3 px-2 pb-1.5 pt-1",
                ),
                *(
                    _column_row(bound, column, hideable, hidden)
                    for column in declared.columns
                ),
            ),
            html.form(
                # One field carries the answer, because a box can only
                # submit itself while it is ticked and what the URL wants
                # is the ones that are not.
                html.input_(type="hidden", name=HIDE, **{":value": "hidden.join(',')"}),
                *_carried(bound, without={PAGE, HIDE}),
                method="get",
                action=bound.urls.read,
                hidden=True,
                **{
                    "x-ref": "form",
                    "x-target.push": rows_id(bound.key) or bound.key,
                },
            ),
            class_="contents",
            **{"x-data": f"hueTableColumns({dumps(sorted(hidden))})"},
        )


def _column_row(
    bound: BoundTable,
    column: Column,
    hideable: set[str],
    hidden: set[str],
) -> ComponentType:
    """
    One column in the panel. The box carries the key when the column is
    off, so the form submits exactly the list of what is hidden.
    """
    key = str(column.key)
    locked = key not in hideable
    box = (
        Checkbox()
        .name(f"{bound.key}-shows-{key}")
        .value(key)
        .label(column.label)
        .checked(locked or key not in hidden)
        .disabled(locked)
        .id(f"{bound.key}-{HIDE}-{key}")
    )
    if not locked:
        # Read from the scope rather than left to the attribute, which
        # stops meaning anything the moment somebody clicks the box.
        box.x_effect(unsafe(f"$el.checked = showing({key!r})")).x_on(
            "change", unsafe(f"toggle({key!r}, $event.target.checked)")
        )
    return html.div(
        box,
        render_when(locked, html.span("Locked", class_=_LOCKED)),
        class_="flex items-center justify-between gap-3 rounded-md px-2 py-1.5 "
        "hover:bg-surface-hover",
    )


class TableOptions(ChainableComponent):
    """
    The rest of what can be done to a table, behind one button: how
    tight the rows are, and a way back to the table as it was.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = bound_from(context, "TableOptions")
        if not bound.declaration.density:
            return UNDEFINED

        target = rows_id(bound.key) or bound.key
        return (
            DropdownMenu()
            .label("More table options")
            .placement("bottom-end")
            .trigger(
                Button()
                .variant("ghost")
                .size("sm")
                .icon_only("More table options")
                .content(HueIcon("ellipsis"))
            )
            .content(
                MenuLabel().content("Density"),
                *(
                    MenuItem()
                    .href(bound.href(compact=compact))
                    .selected(bound.state.compact == compact)
                    .content(label)
                    .attr("x-target.push", target)
                    for compact, label in ((False, "Comfortable"), (True, "Compact"))
                ),
                MenuSeparator(),
                MenuItem()
                .href(bound.urls.read)
                .content("Reset view")
                .attr("x-target.push", target),
            )
        )


def _carried(bound: BoundTable, *, without: set[str]) -> tuple[ComponentType, ...]:
    """
    The rest of the state, as hidden fields.

    A form narrows one thing and has to leave the others alone, so
    everything it is not itself about rides along inside it.
    """
    return tuple(
        html.input_(type="hidden", name=name, value=value)
        for name, value in bound.state.params().items()
        if name not in without
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
        .id(f"{bound.key}-{QUERY}")
        .attr("type", "search")
        .attr("x-ref", "field")
        # Stopped, so an escape that empties the box is not also an escape
        # that closes whatever the table is inside.
        .attr("x-on:keydown.escape", "clearField($event)")
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
            # The rows and not the frame, so the box this was typed into
            # is not swapped out from under the caret. replace rather than
            # push: a word typed at speed would otherwise be a history
            # entry per pause in it.
            "x-target.replace": rows_id(bound.key) or bound.key,
            f"@input.debounce.{SEARCH_DELAY}": "$el.requestSubmit()",
        },
    )
