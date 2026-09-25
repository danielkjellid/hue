"""
A table that knows where its own state lives.

DataTable on its own only renders. Something else has to tell it what
order the rows are in, where the next order lives, what the checkboxes
are called and what to do with them, and each of those is a separate
contract that nothing checks. A table that sorts but forgets the search
is what you get when one of them is wrong.

A declaration puts all of it in one place. Everything about the table
is fixed except which rows answer it, and that one part is a function:

    def invoices_for(
        request: HttpRequest, asked: TableState
    ) -> QuerySet[Invoice]:
        return Invoice.objects.filter(
            customer__name__icontains=asked.query
        ).order_by(asked.sort or "reference")


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
            actions={"archive": BulkAction("Archive", archive_invoices)},
        )

        async def index(
            self, request: HttpRequest, context: HueContext[HttpRequest]
        ) -> Page:
            return Page(title="Invoices", body=DataTable.from_state(self.invoices))

It is declared at class scope because that is the only time a route can
be registered, and the route its actions post to calls rows() the same
way the page does. A sort, a search or a page number is a URL of the page
itself, so the page and an action both go through that one function and
every response shows the table in the state it was in. An action posts
the state with the selection, so archiving on page two of a sorted table
comes back to page two of a sorted table.

rows returns everything that matches, and the page is sliced from it
afterwards. A paginated queryset is then counted and sliced in the
database without being walked.

DataTable.from_state() draws the table a declaration describes, bound
to the request the page is rendered for. The request is already in the
context, so the view passes nothing. The search, the filters, the
column picker and the pages come with it, and none of them is exported.

rows() and an action's handler run off the event loop, through the
router, because both usually use the ORM and the ORM refuses to run on
the loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from http import HTTPStatus
from math import ceil
from typing import (
    Any,
    Callable,
    ClassVar,
    Mapping,
    Protocol,
    Sequence,
)
from urllib.parse import urlencode

from htmy import Context, html

from hue.context import HueContext
from hue.js import call, unsafe
from hue.router import HueResponse
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui.atoms.button import Button, ButtonVariant
from hue.ui.atoms.checkbox import Checkbox
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import NumberInput, TextInput
from hue.ui.base import ChainableComponent
from hue.ui.molecules.datatable import Column, DataTable, resolve_value
from hue.ui.molecules.pagination import Pagination
from hue.ui.molecules.popover import Popover
from hue.ui.molecules.table import form_id, rows_id
from hue.utils import classnames, render_when

# The name every row checkbox is submitted under.
_SELECTED = "selected"

# What each part of the state is called in the query string.
_SORT = "sort"
_QUERY = "q"
_PAGE = "page"
_HIDE = "hide"

# What a filter cannot be called, because the table is already using it.
_RESERVED = (_SORT, _QUERY, _PAGE, _HIDE, _SELECTED)

# The route a view serves its page on, which HueView registers as index.
# Every link on a declared table points at the page, so the declaring view
# has to have one.
_PAGE_ROUTE = "index"

# Long enough that a word typed at speed is one request rather than five,
# short enough that the table has moved by the time you look at it.
_SEARCH_DELAY = "300ms"


# The count on the Filter button: how many answers are on, beside the
# word rather than instead of it, so the button still says what it opens.
_FILTER_COUNT = (
    "ms-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full "
    "bg-accent px-1 font-ui text-2xs font-bold tabular-nums text-accent-fg"
)

# The groups are ruled off from each other by a wrapper around each
# fieldset rather than by the fieldset itself: a fieldset draws its top
# border through the middle of its legend and puts its padding under it.
_GROUPS = "flex flex-col divide-y divide-border"
_GROUP = "py-4 first:pt-0 last:pb-0"
_OPTIONS = "flex flex-col gap-3"

# The applied row: a whole line of the band, which basis-full takes, and
# the last of them whatever order the controls were written in -
# otherwise a full-width row in the middle of them splits the group.
_APPLIED_ROW = (
    "order-last flex basis-full flex-wrap items-center gap-2 "
    "border-t border-border pt-2"
)
# The small uppercase heading at the top of a panel, which a filter's
# legend is too.
_PANEL_LABEL = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-muted"
_LEGEND = classnames("mb-2 block w-full p-0", _PANEL_LABEL)
# A row of the columns panel: a whole control's height, so it reads as a
# list of things to press and not as a form.
_COLUMN_ROW = (
    "flex min-h-control-sm items-center gap-3 rounded-md px-2 "
    "hover:bg-surface-hover has-disabled:hover:bg-transparent"
)
_CHIP = (
    "inline-flex items-center gap-1.5 rounded-sm border border-border "
    "bg-canvas-subtle py-0.5 ps-2 pe-1.5 text-sm text-fg "
    "hover:border-border-hover hover:bg-surface-hover"
)


class _Routes(Protocol):
    """
    What a declaration needs from the router it is handed: somewhere to
    register its action route, and the framework's answers to the questions
    only the framework can answer.
    """

    def fragment_post(self, path: str) -> Callable[[Any], Any]: ...
    def _get_query_values(self, request: Any) -> dict[str, list[str]]: ...
    def _get_form_values(self, request: Any) -> dict[str, list[str]]: ...
    def _url_for(self, request: Any, name: str, **params: Any) -> str: ...
    def _narrow_to(self, rows: Any, key: str, values: list[str]) -> Any: ...
    async def _run_sync[R](self, func: Callable[..., R], /, *args: Any) -> R: ...


type Rows = Sequence[Mapping[str, Any]]
type ActionHandler = Callable[[Any, list[str]], Any]
# Given the request and what it asked for, everything that matches.
type RowsFor = Callable[[Any, "TableState"], Any]


@dataclass(frozen=True, slots=True)
class TableState:
    """
    What was asked for, read off the request and written back into every
    link and form the table builds. A sort keeps the search, a search
    keeps the order, and an action comes back to where it was done.

    rows() reads the filters with chosen() for a filter that can hold
    several answers and value() for one that holds a single answer, so it
    never has to know how the query string spells them.
    """

    sort: str | None = None
    query: str = ""
    page: int = 1
    filters: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    hidden: tuple[str, ...] = ()

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
        The same state with one thing changed. Every link on the table is one
        of these.

        Changing anything other than the page resets it to the first one,
        because page four of a different search is not a page anyone asked
        for.
        """
        return TableState(
            sort=changes.get("sort", self.sort),
            query=changes.get("query", self.query),
            page=changes["page"] if "page" in changes else 1,
            filters=changes.get("filters", self.filters),
            hidden=changes.get("hidden", self.hidden),
        )

    def without(self, name: str, value: str | None = None) -> TableState:
        """
        The same state with one filter off, or one answer removed from it,
        which is what a chip in the applied band undoes.
        """
        left = {
            key: tuple(v for v in values if key != name or v != value)
            for key, values in self.filters.items()
        }
        if value is None:
            left.pop(name, None)
        return self.replace(filters={k: v for k, v in left.items() if v})

    def params(self) -> dict[str, str]:
        asked = {_SORT: self.sort or "", _QUERY: self.query}
        # One parameter per filter, answers comma-joined, which is how a
        # query string already spells a list somebody might hand-edit.
        for name, values in self.filters.items():
            if values:
                asked[name] = ",".join(values)
        if self.hidden:
            asked[_HIDE] = ",".join(self.hidden)
        if self.page > 1:
            asked[_PAGE] = str(self.page)
        return {name: value for name, value in asked.items() if value}


@dataclass(frozen=True, slots=True)
class Filter:
    """
    One way of narrowing a table, and the name it goes by in the URL.

    With options it is a list to tick, and multiple says whether more than
    one can be on at once. Without options it is a field to type a value
    into, and numeric makes that a number field. Either way the answers
    arrive in the state rows() is handed, and the table draws the panel,
    the count on the trigger and the chips that undo it.

        Filter("status", "Status", options=[("paid", "Paid")])
        Filter("min", "Minimum amount", numeric=True, prefix="USD")
    """

    name: str
    label: str
    options: Sequence[tuple[str, str]] = ()
    multiple: bool = True
    numeric: bool = False
    prefix: str | None = None
    placeholder: str | None = None

    def labelled(self, value: str) -> str:
        """
        What one answer is called on the chip that undoes it: the option's
        label when it came from a list, or the value itself when it was typed.
        """
        for option, label in self.options:
            if option == value:
                return label
        return value


@dataclass(frozen=True, slots=True)
class BulkAction:
    """
    Something to do with the ticked rows, and what it is called.

    The handler receives the request and the ids of the picked rows. It is
    whatever you would have written anyway, such as the service function
    that archives them. The ids are only ever ones rows() returns for the
    table as the reader saw it, so a posted id for a row they could not see
    never reaches the handler. The icon goes before the label in the bar
    for picked rows.

        BulkAction("Delete", delete_invoices, icon=HueIcon("trash-2"))
    """

    label: str
    handler: ActionHandler
    variant: ButtonVariant = "ghost"
    icon: ComponentType | None = None


def _one(asked: Mapping[str, list[str]], name: str) -> str | None:
    """
    The one value a parameter holds, or the last of several.
    """
    values = asked.get(name)
    return values[-1] if values else None


def _many(asked: Mapping[str, list[str]], name: str) -> tuple[str, ...]:
    """
    Every value a parameter holds, however it was spelled.

    A browser repeats the name once per checkbox, while links the table
    builds join the values with commas, since that is what someone editing
    a query string by hand would write. Both read the same.
    """
    return tuple(
        part for value in asked.get(name, ()) for part in value.split(",") if part
    )


def _total(rows: Any) -> int:
    """
    How many rows match, without walking them.

    A queryset counts in the database. A list also has count(), but it
    takes an argument and raises without one, so the TypeError is what
    tells the two apart.
    """
    try:
        return int(rows.count())
    except (AttributeError, TypeError):
        return len(rows)


def _bound_from(context: Context, component: object) -> BoundTable:
    """
    The bound table a component is rendered inside, or an error saying
    what is missing.

    Every part of a table reads the same binding, so none of them is
    handed the request or the rows.
    """
    found = context.get(BoundTable)
    if isinstance(found, BoundTable):
        return found
    raise ValueError(
        f"{type(component).__name__} draws part of a table bound to a request, "
        "and there is none here. It is drawn by DataTable.from_state()."
    )


@dataclass(frozen=True, slots=True)
class _TableUrls:
    """
    Where this table lives, for one request: the page it is drawn on, which
    every link and toolbar form points at, and the route of each action.

    Reading is the page itself. Alpine AJAX fetches it and swaps in the part
    that changed, so the address bar holds a URL that reloads, can be sent
    to someone, and works with JavaScript off. The URLs are reversed when
    the table is bound, because a path written into a link would break as
    soon as include() moved the view under a prefix.
    """

    read: str
    act: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class BoundTable:
    """
    One table for one request: what was asked, how many rows match, and
    the page that came back.

    Every part of the table reads this from the context. The links a part
    draws are all built from it, so no part reaches for the request or
    works out a URL of its own.
    """

    declaration: _Declaration
    state: TableState
    page: Rows
    total: int
    urls: _TableUrls

    @property
    def key(self) -> str:
        return self.declaration.key

    def href(self, **changes: Any) -> str:
        """
        This table with one thing changed. Every link on the table is one of
        these.
        """
        asked = self.state.replace(**changes).params()
        return self.urls.read + (f"?{urlencode(asked)}" if asked else "")


class _Declaration:
    """
    A table declared once, at class scope, and the route its actions post to.

    key names the fragment path and the element every response is swapped
    into, so it has to be unique on the page. Every URL the table builds
    comes from it.

    rows is the only part of a table that is not fixed, so it is the only
    part that is a function. It receives the request and the state that
    was asked for, and returns everything that matches: the whole filtered,
    ordered set. The page is sliced afterwards, so a queryset stays lazy
    and is counted instead of walked.

    actions are what can be done with picked rows, and identifier names
    the property a row is known by, which is what an action receives. The
    two come together: actions put a checkbox in every row, and a
    checkbox with nothing to do is not drawn. The identifier is separate
    from the columns because a row is usually known by something nobody
    wants to see.

    filters are the other ways of narrowing the table. Each one gets its
    own parameter in the URL, a group in the panel behind the Filter
    button and a chip in the band under it, and its answers arrive in the
    same state rows() reads the search from.

    hideable names the columns a reader may hide. The others are locked,
    and the panel marks them as locked instead of ignoring the click.
    """

    def __init__(
        self,
        router: _Routes,
        *,
        key: str,
        columns: list[Column],
        rows: RowsFor,
        identifier: str | None = None,
        search: str | None = None,
        filters: Sequence[Filter] = (),
        hideable: Sequence[str] = (),
        actions: Mapping[str, BulkAction] | None = None,
        page_size: int = 25,
    ) -> None:
        self.key = key
        self.columns = columns
        self.rows = rows
        self.identifier = identifier
        self.search = search
        self.filters = list(filters)
        self.hideable = list(hideable)
        self.actions = dict(actions or {})
        self.page_size = page_size
        self._router = router
        # One spelling of the action route's name, used to register it and
        # to find it again. Two tables on one view would otherwise both call
        # theirs "act", since the router takes a route's name off the
        # handler's __name__ as it decorates.
        self._act_route = f"{key}_act"
        # The toolbar's forms, in the order they sit in the band. Decided
        # once, here, and read by the toolbar and by what the forms carry.
        self.forms: tuple[type[_ToolbarForm], ...] = tuple(
            form
            for form, wanted in (
                (_TableSearch, bool(search)),
                (_TableFilters, bool(filters)),
                (_TableColumns, bool(hideable)),
                (_TableReset, bool(filters or hideable)),
            )
            if wanted
        )
        self._check()
        self._register()

    def _check(self) -> None:
        """
        The mistakes a declaration can be refused for before it serves
        anything.
        """
        if self.page_size < 1:
            raise ValueError(
                f"{self.key} has a page size of {self.page_size}. A page "
                f"holds at least one row."
            )
        if self.actions and self.identifier is None:
            raise ValueError(
                f"{self.key} has actions but no identifier, so there is "
                f"nothing to hand them. Name the property a row is known by."
            )
        if self.identifier is not None and not self.actions:
            raise ValueError(
                f"{self.key} has an identifier but no actions. The identifier "
                f"is what an action is handed, so without one it does nothing. "
                f"Give the table an action, or leave the identifier out."
            )
        declared = {c.key for c in self.columns if isinstance(c.key, str)}
        for stranger in [key for key in self.hideable if key not in declared]:
            raise ValueError(
                f"{self.key} says {stranger!r} can be hidden, and it has no "
                f"such column. It has {sorted(declared)}."
            )
        for taken in [f.name for f in self.filters if f.name in _RESERVED]:
            raise ValueError(
                f"{self.key} has a filter called {taken!r}, which is what "
                f"the table already calls the order, the search, the page, "
                f"the hidden columns or the selection. Name it something else."
            )

    async def draw(self, table: DataTable, context: Context) -> Component:
        """
        The table bound to the request this page is rendered for, with the
        ways to narrow it in a band above the rows and the pages below.

        DataTable.from_state() hands over to this. The request is already in
        the context, so the view has nothing to pass.
        """
        request = HueContext.from_context(context).request
        return self._drawn(table, await self.bind(request))

    async def bind(self, request: Any) -> BoundTable:
        """
        The state, the page of rows and the total for one request, for code
        that wants the values instead of the table.
        """
        return await self._bind(
            request, self._state_from(self._router._get_query_values(request))
        )

    async def _bind(self, request: Any, asked: TableState) -> BoundTable:
        page, total, number = await self._router._run_sync(self._fetch, request, asked)
        self._check_identifier(page)
        return BoundTable(
            self, replace(asked, page=number), page, total, self._urls_for(request)
        )

    def _drawn(self, table: DataTable, bound: BoundTable) -> Component:
        """
        The whole table for one binding: the rows in the order asked, the
        toolbar above them and the pages below, all in one frame, inside
        the component that offers the binding to every part of it.
        """
        hidden = set(bound.state.hidden)
        # The wiring modifiers are private: they only work as a set, and
        # this is the one place that sets all of them together.
        table.id(self.key).columns(
            [column for column in self.columns if column.key not in hidden]
        ).rows(bound.page)._sorted(bound.state.sort)._sort_href(
            lambda order: bound.href(sort=order)
        )
        if self.actions and self.identifier is not None:
            table._bulk_actions(
                self.identifier,
                *(
                    Button()
                    .variant(action.variant)
                    .size("sm")
                    .type("submit")
                    .content(*((action.icon,) if action.icon else ()), action.label)
                    .form(form_id(self.key) or "")
                    .formaction(bound.urls.act[name])
                    for name, action in self.actions.items()
                ),
            )
            # A real form around real checkboxes, inside the frame so the
            # table is still the outermost thing and still what a response
            # is swapped into. Every button names its own action, so the
            # form's own is only a fallback for a browser that ignores
            # formaction.
            table._form(bound.urls.act[next(iter(self.actions))])

        forms = [form() for form in self.forms]
        if forms:
            # The search first, then a spacer, then the panels at the end of
            # the band: a panel anchored to a trigger near the middle opens
            # across the rows.
            search = [form for form in forms if isinstance(form, _TableSearch)]
            panels = [form for form in forms if not isinstance(form, _TableSearch)]
            spacer = [html.span(class_="flex-1")] if panels else []
            table._toolbar(*search, *spacer, *panels)
        # The carried state goes under the rows, in the region every
        # response replaces, so the forms up in the toolbar always send
        # the state the table is in now and not the one it was drawn in.
        table._under(_TablePagination(), _TableCarried())
        return _TableView(bound).content(table)

    def _fetch(self, request: Any, asked: TableState) -> tuple[Rows, int, int]:
        """
        The page of rows, the total and the page number they are. These are
        all the queries a table makes, in one blocking call the router can
        run off the event loop.

        A page past the last is the last page: after an action removes rows,
        or when a link is followed later, the reader still sees rows.
        """
        matching = self.rows(request, asked)
        total = _total(matching)
        number = min(asked.page, max(1, ceil(total / self.page_size)))
        start = (number - 1) * self.page_size
        return list(matching[start : start + self.page_size]), total, number

    def _picked(self, request: Any, asked: TableState, posted: list[str]) -> list[str]:
        """
        The posted ids that belong to rows the table shows for this state,
        in the order they were posted, each once.

        The browser only posts the boxes it drew, but anyone can post
        anything, and rows() is where a table says which rows are the
        reader's to see.
        """
        key = self.identifier
        if key is None:  # refused by _check, since there are actions
            return []
        kept = self._router._narrow_to(self.rows(request, asked), key, posted)
        allowed = {str(resolve_value(row, key)) for row in kept}
        return [value for value in dict.fromkeys(posted) if value in allowed]

    def _urls_for(self, request: Any) -> _TableUrls:
        """
        The page and the actions, reversed for this request.

        This happens once per binding instead of once per link, because every
        href on the table is one of these URLs with a different query string.
        """
        return _TableUrls(
            read=self._router._url_for(request, _PAGE_ROUTE),
            act={
                name: self._router._url_for(request, self._act_route, action=name)
                for name in self.actions
            },
        )

    def _state_from(self, asked: Mapping[str, list[str]]) -> TableState:
        # Every value, not just the last: a set of checkboxes sharing a
        # name is how a browser submits a list, and a flat dict keeps one
        # of them.
        try:
            page = max(1, int(_one(asked, _PAGE) or "1"))
        except ValueError:
            page = 1
        hideable = set(self.hideable)
        return TableState(
            sort=self._sort_in(asked),
            query=_one(asked, _QUERY) or "",
            page=page,
            filters=self._filters_in(asked),
            # Only columns that could have been hidden, so a key typed
            # into the URL cannot take away a column nobody may hide.
            hidden=tuple(key for key in _many(asked, _HIDE) if key in hideable),
        )

    def _sort_in(self, asked: Mapping[str, list[str]]) -> str | None:
        """
        The order asked for, if it is one a column offers.

        rows() hands this to the database, so an order nobody declared is
        dropped here: sorting on any field someone types into a URL would
        tell them things about fields the table never shows.
        """
        order = _one(asked, _SORT)
        offered = {column.sort for column in self.columns if column.sort}
        return order if order and order.removeprefix("-") in offered else None

    def _filters_in(self, asked: Mapping[str, list[str]]) -> dict[str, tuple[str, ...]]:
        """
        What each filter was told.

        A list-shaped filter drops any answer it does not offer. Anyone can
        type into a query string, and rows() should not have to guard against
        it. A typed answer is taken whole, commas and all, because 1,000 is
        one number and not two.
        """
        found: dict[str, tuple[str, ...]] = {}
        for declared in self.filters:
            if declared.options:
                offered = {option for option, _ in declared.options}
                values = tuple(v for v in _many(asked, declared.name) if v in offered)
            else:
                typed = _one(asked, declared.name)
                values = (typed,) if typed else ()
            if values:
                found[declared.name] = values if declared.multiple else values[:1]
        return found

    def _check_identifier(self, page: Rows) -> None:
        """
        Every row has to carry the property it is known by.

        This is checked up front because the error from the first checkbox
        would name a key and a dict without saying why either matters. A table
        whose ids were silently missing would also post an empty selection to
        its action.
        """
        if self.identifier is None or not page:
            return
        try:
            resolve_value(page[0], self.identifier)
        except ValueError:
            first = page[0]
            carried = (
                f"they have {sorted(first)}"
                if isinstance(first, Mapping)
                else f"they are {type(first).__name__} and not mappings"
            )
            raise ValueError(
                f"{self.key} is identified by {self.identifier!r}, and its "
                f"rows do not carry it - {carried}. Every row needs the "
                f"property it is known by, whether or not a column shows it: "
                f"it is what a checkbox submits and what an action is handed."
            ) from None

    def _register(self) -> None:
        """
        The route an action posts to. Reading needs no route of its own,
        because the page the table is drawn on reads its state from the same
        query string.
        """

        async def act(view: Any, request: Any, context: Any, action: str) -> Any:
            chosen = self.actions.get(action)
            if chosen is None:
                return HueResponse(
                    component=html.p(f"{self.key} has no action called {action!r}."),
                    status_code=HTTPStatus.NOT_FOUND,
                )
            # The state comes with the selection, in the body, from fields
            # that are redrawn with every response, so the table comes back
            # the way the reader was looking at it.
            posted = self._router._get_form_values(request)
            asked = self._state_from(posted)
            picked = await self._router._run_sync(
                self._picked, request, asked, posted.get(_SELECTED, [])
            )
            await self._router._run_sync(chosen.handler, request, picked)
            # Drawn after, because the rows have just changed under it.
            return self._drawn(DataTable(), await self._bind(request, asked))

        # Named before it is registered, not after: the router takes a
        # route's name off __name__ as it decorates.
        act.__name__ = self._act_route
        self._router.fragment_post(f"{self.key}/<str:action>/")(act)


# What a view calls, at class scope, to declare a table.
build_datatable_state = _Declaration


# ----------------------------------------------------------------------
# The components a bound table draws itself with
# ----------------------------------------------------------------------


class _TableView(ChainableComponent):
    """
    Offers one binding to every part of a table rendered inside it.

    The binding is a frozen value, because every part reads it and none of
    them owns it, so a separate component has to provide it.
    """

    category: ClassVar[str | None] = None

    def __init__(self, bound: BoundTable) -> None:
        super().__init__()
        self._bound = bound

    def htmy_context(self) -> Context:
        return {BoundTable: self._bound}

    def _render(self, context: Context) -> Component:
        return html.div(*self._children, class_="flex flex-col gap-3")


class _ToolbarForm(ChainableComponent):
    """
    A part of the toolbar that is a form: it changes some of the state and
    sends the rest along unchanged.

    The rest is not drawn inside it. The toolbar is left alone by a sort, a
    page or a search, so fields in here would go on sending the state the
    table was first drawn in. _TableCarried draws them under the rows
    instead, tied to this form by its id.
    """

    category: ClassVar[str | None] = None
    # The end of the form's id, after the table's key.
    part: ClassVar[str]

    @classmethod
    def form_of(cls, bound: BoundTable) -> str:
        return f"{bound.key}-{cls.part}"

    @classmethod
    def sets(cls, bound: BoundTable) -> set[str]:
        """
        The parameters this form sends itself, which it does not carry.
        """
        raise NotImplementedError


class _TableSearch(_ToolbarForm):
    """
    The search box for a table.

    It sits in the toolbar, which no response replaces, so the box keeps
    its caret and focus while the rows change.
    """

    part = "search"

    @classmethod
    def sets(cls, bound: BoundTable) -> set[str]:
        return {_QUERY}

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        return html.div(
            _search_form(bound, self.form_of(bound)),
            # Takes the free space in the band up to a readable cap: a
            # field as wide as the table reads as a search of the page,
            # and this one only ever searches these rows.
            class_="min-w-0 flex-1 basis-64 sm:max-w-[340px]",
            **{
                "data-hue-table-search": "",
                "x-data": "hueTableSearch",
                "x-on:keydown.window.slash": "focusField($event)",
            },
        )


class _TablePagination(ChainableComponent):
    """
    The pages of a table, drawn from the same binding as the rows.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        size = bound.declaration.page_size
        return (
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


class _TableCarried(ChainableComponent):
    """
    The state each toolbar form sends besides its own part of it, as
    hidden fields tied to the form by id, and the state an action posts.

    Drawn under the rows, in the region every response replaces, so every
    form sends the state the table is in now. A browser submits a field
    tied to a form by id wherever the field is, with or without Alpine.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        fields = [
            # Never the page: anything a toolbar form changes is a
            # different set of rows, and page four of it is nowhere
            # anybody was.
            *(
                one
                for form in bound.declaration.forms
                for one in _carried(
                    bound, form=form.form_of(bound), without={_PAGE, *form.sets(bound)}
                )
            ),
            # All of it, page included: an action comes back to the page
            # it was done on.
            *(
                _carried(bound, form=form_id(bound.key) or "", without=set())
                if bound.declaration.actions
                else ()
            ),
        ]
        return html.div(*fields, hidden=True) if fields else UNDEFINED


class _TableFilters(_ToolbarForm):
    """
    The other ways of narrowing a table: a panel of filters behind one
    button, and a chip for each one that is on.

    The panel is a GET form that submits itself as soon as anything in it
    changes. There is no Apply button, since the chips already show what is
    on and can undo it.
    """

    part = "filters"

    @classmethod
    def sets(cls, bound: BoundTable) -> set[str]:
        return {f.name for f in bound.declaration.filters}

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        declared = bound.declaration.filters

        return html.div(
            html.form(
                _filter_panel(bound, declared),
                id=self.form_of(bound),
                method="get",
                action=bound.urls.read,
                # No box of its own: the controls belong to the band
                # around them, and this is only here to be submitted.
                class_="contents",
                **{
                    "x-ref": "form",
                    "x-target.push": rows_id(bound.key) or bound.key,
                    "@change": "apply()",
                    # An empty field is not an answer, and a URL people
                    # are meant to send each other should not carry one.
                    "@submit": "dropEmpty()",
                },
            ),
            _applied_chips(),
            class_="contents",
            **{"x-data": call("hueTableFilters", bound.key)},
        )


def _filter_panel(bound: BoundTable, declared: Sequence[Filter]) -> ComponentType:
    """
    One popover holding every filter, each in a legended group.
    """
    return (
        Popover()
        .label("Filter")
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
        .content(
            html.div(
                html.div(
                    html.span("Filter", class_=_PANEL_LABEL),
                    Button()
                    .variant("link")
                    .size("xs")
                    .content("Clear")
                    .x_on("click", unsafe("clear()")),
                    class_="mb-3 flex items-center justify-between gap-3",
                ),
                html.div(
                    *(_filter_group(bound, one) for one in declared),
                    class_=_GROUPS,
                ),
            )
        )
    )


def _filter_group(bound: BoundTable, declared: Filter) -> ComponentType:
    """
    One filter as a fieldset with a legend. A set of checkboxes that
    answer one question is a group, and the legend is how a screen reader
    hears the question before the answers.
    """
    picked = bound.state.chosen(declared.name)
    if not declared.options:
        answers: ComponentType = _filter_field(bound.key, declared, picked)
    else:
        answers = html.div(*_filter_options(bound, declared, picked), class_=_OPTIONS)
    return html.div(
        html.fieldset(html.legend(declared.label, class_=_LEGEND), answers),
        class_=_GROUP,
    )


def _filter_options(
    bound: BoundTable, declared: Filter, picked: tuple[str, ...]
) -> list[ComponentType]:
    """
    A box to tick for every option a filter offers.
    """
    return [
        Checkbox()
        .name(declared.name)
        .value(option)
        .label(label)
        .checked(option in picked)
        # Every box in the group submits the same name, so the id
        # cannot come from it: the label beside each one has to point
        # at that one and not at the first of them.
        .id(f"{bound.key}-filter-{declared.name}-{option}")
        .data("filter", declared.name)
        .data("filter-label", declared.label)
        .data("option", label)
        for option, label in declared.options
    ]


def _filter_field(key: str, declared: Filter, picked: tuple[str, ...]) -> ComponentType:
    """
    A text or number field, for a filter with no options to tick.

    The id carries the table's key and the name does not. The name is the
    query parameter, which is the same on every table, while the id has to
    be unique on the page.
    """
    field = NumberInput() if declared.numeric else TextInput()
    field.name(declared.name).label(declared.label).hidden_label().size("sm")
    field.id(f"{key}-filter-{declared.name}")
    field.value(picked[0] if picked else "")
    field.data("filter", declared.name).data("filter-label", declared.label)
    if declared.prefix is not None:
        field.prefix(declared.prefix)
    if declared.placeholder is not None:
        field.placeholder(declared.placeholder)
    return field


def _applied_chips() -> ComponentType:
    """
    Everything that is on, and one press to remove any of it.

    The chips take a full line of the band, so a narrowed table says so
    above the rows as well as inside the closed popover.
    """
    return html.div(
        html.template(
            html.button(
                html.span(**{"x-text": "chip.filterLabel + ': ' + chip.label"}),
                HueIcon("x").class_("size-3"),
                type="button",
                class_=_CHIP,
                **{
                    "@click": "remove(chip)",
                    ":aria-label": "'Remove filter ' + chip.filterLabel + ': ' "
                    "+ chip.label",
                },
            ),
            **{"x-for": "chip in applied", ":key": "chip.filter + chip.value"},
        ),
        Button()
        .variant("link")
        .size("xs")
        .content("Clear all")
        .x_on("click", unsafe("clear()")),
        class_=_APPLIED_ROW,
        **{"x-show": "applied.length", "x-cloak": True},
    )


class _TableColumns(_ToolbarForm):
    """
    Which columns are showing, including the ones that cannot be hidden.

    A checkbox list behind one button, with a count in its header. A
    ticked box means the column is showing, which is how people read a
    list of columns. The URL carries the hidden ones instead, so a column
    added later shows up for someone following an old link.

    Locked columns are in the list too, ticked, disabled and labelled as
    locked, so the rule is visible instead of a click that does nothing.
    """

    part = "columns"

    @classmethod
    def sets(cls, bound: BoundTable) -> set[str]:
        return {_HIDE}

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        declared = bound.declaration

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
            .label("Columns")
            .content(
                html.div(
                    html.div(
                        html.span("Columns", class_=_PANEL_LABEL),
                        html.span(
                            f"{showing} of {len(declared.columns)}",
                            class_="text-2xs tabular-nums text-fg-muted",
                        ),
                        class_="flex items-baseline justify-between gap-3 "
                        "px-2 pb-2 pt-1.5",
                    ),
                    *(
                        _column_row(bound, column, hideable, hidden)
                        for column in declared.columns
                    ),
                    class_="w-60 p-1",
                )
            ),
            html.form(
                # One field carries the answer, because a box can only
                # submit itself while it is ticked and what the URL wants
                # is the ones that are not.
                html.input_(
                    type="hidden", name=_HIDE, **{":value": "hidden.join(',')"}
                ),
                id=self.form_of(bound),
                method="get",
                action=bound.urls.read,
                hidden=True,
                **{
                    "x-ref": "form",
                    "x-target.push": rows_id(bound.key) or bound.key,
                },
            ),
            class_="contents",
            **{"x-data": call("hueTableColumns", sorted(hidden), bound.key)},
        )


def _column_row(
    bound: BoundTable,
    column: Column,
    hideable: set[str],
    hidden: set[str],
) -> ComponentType:
    """
    One column in the panel, its box ticked while the column shows. The
    boxes are not submitted: a hidden field built from them carries the
    list of hidden columns.
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
        .id(f"{bound.key}-{_HIDE}-{key}")
        # The whole row is the label, so the box is not a small target
        # in a wide one.
        .class_("flex-1")
    )
    locked_id = f"{bound.key}-{_HIDE}-{key}-locked"
    if locked:
        # The padlock is drawn, not read; the word is what a screen reader
        # hears after the column's name.
        box.aria_describedby(locked_id)
    else:
        # Read from the scope rather than left to the attribute, which
        # stops meaning anything the moment somebody clicks the box.
        box.x_effect(unsafe(f"$el.checked = {call('showing', key)}")).x_on(
            "change", call("toggle", key, unsafe("$event.target.checked"))
        )
    return html.div(
        box,
        render_when(
            locked,
            html.span(
                HueIcon("lock").class_("size-3.5"),
                html.span("Locked", id=locked_id, class_="sr-only"),
                class_="text-fg-muted",
            ),
        ),
        class_=_COLUMN_ROW,
    )


class _TableReset(_ToolbarForm):
    """
    One button that takes the filters off and shows every column again,
    there only while something is filtered or hidden.

    The search and the order are kept. The whole frame is redrawn, because
    the filter and column panels live in the toolbar, which a response
    otherwise leaves alone, and they have to show the reset state too.
    """

    part = "reset"

    @classmethod
    def sets(cls, bound: BoundTable) -> set[str]:
        # It sends none of what the panels send, which is how it takes
        # them off.
        return _TableFilters.sets(bound) | _TableColumns.sets(bound)

    def _render(self, context: Context) -> Component:
        bound = _bound_from(context, self)
        filtered = sum(len(values) for values in bound.state.filters.values())
        hidden = len(bound.state.hidden)
        return html.form(
            Button()
            .variant("ghost")
            .size("sm")
            .type("submit")
            .icon_only("Reset filters and columns")
            .content(HueIcon("rotate-ccw")),
            id=self.form_of(bound),
            method="get",
            action=bound.urls.read,
            # Pulled out by the inset of its own glyph, so the icon, which is
            # all that shows of a ghost button, sits on the edge of the column
            # under it. A button draws its icon at 1rem; the pagination band
            # does the same for its chevron, which is drawn at 0.875rem.
            class_="-me-[calc((var(--spacing-control-sm)_-_1rem)_/_2)] inline-flex",
            **{
                # Told when a filter or a column changes, since the toolbar
                # is not redrawn for either and this has to show and hide
                # with them.
                "x-data": call("hueTableReset", bound.key, filtered, hidden),
                "x-show": "narrowed",
                "x-on:hue-table-narrowed.window": "hear($event.detail)",
                "x-target.push": bound.key,
                **({} if filtered or hidden else {"x-cloak": True}),
            },
        )


def _carried(
    bound: BoundTable, *, form: str, without: set[str]
) -> tuple[ComponentType, ...]:
    """
    The state apart from without, as hidden fields tied to one form.
    """
    return tuple(
        html.input_(type="hidden", name=name, value=value, form=form)
        for name, value in bound.state.params().items()
        if name not in without
    )


class _SearchField(TextInput):
    """
    A text input with the search type, which gives it the search role and
    a search key on a phone's keyboard. The type is the control's own, so
    it has to be the class that says so.
    """

    _input_type = "search"


def _search_form(bound: BoundTable, form: str) -> ComponentType:
    """
    The search box's own GET form. It is a form because Enter already
    submits one, and x-target only turns the navigation into a swap, so
    search still works with Alpine switched off.
    """
    return html.form(
        _SearchField()
        .name(_QUERY)
        .id(f"{bound.key}-{_QUERY}")
        .size("sm")
        .x_ref("field")
        # Stopped, so an escape that empties the box is not also an escape
        # that closes whatever the table is inside.
        .x_on("keydown.escape", unsafe("clearField($event)"))
        .label(bound.declaration.search or "")
        .hidden_label()
        .placeholder(bound.declaration.search or "")
        .value(bound.state.query)
        .leading_icon(HueIcon("search")),
        id=form,
        method="get",
        action=bound.urls.read,
        **{
            # The rows and not the frame, so the box this was typed into
            # is not swapped out from under the caret. replace rather than
            # push: a word typed at speed would otherwise be a history
            # entry per pause in it.
            "x-target.replace": rows_id(bound.key) or bound.key,
            f"@input.debounce.{_SEARCH_DELAY}": "$el.requestSubmit()",
        },
    )
