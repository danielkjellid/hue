"""
A table that knows where its own state lives.

DataTable on its own is a renderer: you tell it what order the rows are in,
where the next order lives, what the checkboxes are called and what to do
with them, and you wire the four of those together yourself. Every one of
them is a separate contract, and none of them is checkable - a missing id
means the header quietly navigates instead of swapping, and a bulk action
only works if its expression happens to name the right variable.

datatable() collapses that into one declaration. It registers the routes,
so the header link and the action button already point at something; it
reads the state back off the request, so the order the rows are in is the
order that was asked for; and it hands the ids to a Python function rather
than to an expression.

    class InvoicesView(HueView):
        router = Router[HttpRequest]()

        invoices = datatable(
            router,
            key="invoices",
            columns=[
                Column("invoice", "Invoice", identifies=True),
                Column("amount", "Amount", align="end", sort="amount"),
            ],
            rows=lambda asked: Invoice.objects.filter(
                reference__icontains=asked.query
            ).order_by(asked.sort or "reference"),
            search="Search invoices",
            actions={"archive": BulkAction("Archive", archive_invoices)},
        )

        async def index(self, request, context):
            invoices = self.invoices.bind(request)
            return Page(
                title="Invoices",
                body=Stack().content(
                    Heading().content("Invoices"),
                    Card().content(
                        TableSearch.from_state(invoices),
                        DataTable.from_state(invoices),
                    ),
                ),
            )

    identifies marks the column a row is known by, so archive_invoices is
    handed the references of the ticked rows and the columns say as much
    without anything else having to be read.

Reads and writes are split the way HTTP already splits them. An order is
state, so it rides in the URL and rows() answers it - there is no on_sort,
because there is nothing for a handler to do that the next call to rows()
does not. Acting on the rows that are ticked is a write, so it is a POST to
a named action that is given the ids.
"""

from __future__ import annotations

from dataclasses import dataclass
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
from hue.ui.molecules.table import Column, DataTable
from hue.utils import classnames

if TYPE_CHECKING:
    from hue.router import Router

# The name every row checkbox is submitted under.
SELECTED = "selected"

# What the search box is called in the query string.
QUERY = "q"

# Long enough that a word typed at speed is one request rather than five,
# short enough that the table has moved by the time you stop to look at it.
SEARCH_DELAY = "300ms"

type Rows = Sequence[Mapping[str, Any]]
type RowsFor = Callable[["TableState"], Rows]
type ActionHandler = Callable[[Any, list[str]], Any]


@dataclass(frozen=True, slots=True)
class TableState:
    """
    What was asked for, read off the request.

    Only the order so far. A page number and a filter belong here too, and
    belong in the query string with it, which is the reason this is a value
    rather than a pile of arguments.
    """

    sort: str | None = None
    query: str = ""


@dataclass(frozen=True, slots=True)
class BulkAction:
    """
    Something to do with the rows that are ticked, and what it is called.
    """

    label: str
    handler: ActionHandler
    variant: ButtonVariant = "outline"


def _key_of(column: Column) -> str:
    """
    The column's key as a string, which a checkbox value has to be.
    """
    if not isinstance(column.key, str):
        raise ValueError(
            f"The column marked identifies is read by a function, and a row "
            f"has to be known by something that survives a round trip. Give "
            f"{column.label!r} a key."
        )
    return column.key


@dataclass(frozen=True, slots=True)
class BoundTable:
    """
    A declaration and what one request asked of it.

    The components take this rather than the request, so a view binds once
    and then places them wherever the tree wants them.
    """

    declaration: DataTableState
    state: TableState

    def table(self, into: DataTable) -> DataTable:
        return self.declaration.apply(into, self.state)

    def search(self) -> ComponentType:
        return self.declaration.search_input(self.state)


class DataTableState:
    """
    One table's declaration, and the routes that serve it.

    Built by datatable() at class scope, because that is when routes can
    still be registered - the rows are per request, and arrive by calling
    rows() with whatever the request asked for.
    """

    def __init__(
        self,
        router: Router[Any],
        *,
        key: str,
        columns: list[Column],
        rows: RowsFor,
        actions: Mapping[str, BulkAction] | None = None,
        search: str | None = None,
    ) -> None:
        self.key = key
        self.columns = columns
        self.rows = rows
        self.search = search
        # Which column a row is known by, read off the columns rather than
        # named again beside them: an action is handed these values, and
        # the only honest place to say so is the column itself.
        identifying = [column for column in columns if column.identifies]
        if len(identifying) > 1:
            raise ValueError(
                f"{key} has {len(identifying)} columns marked identifies. A "
                f"row is known by one of them, and an action is handed that "
                f"one's values."
            )
        self.identity = _key_of(identifying[0]) if identifying else None
        if actions and self.identity is None:
            raise ValueError(
                f"{key} has actions but no column marked identifies, so "
                f"there is nothing to hand them. Mark the column a row is "
                f"known by."
            )
        self.actions = dict(actions or {})
        self._router = router
        self._register()

    # ------------------------------------------------------------------
    # Where the state lives
    # ------------------------------------------------------------------

    def path(self) -> str:
        return f"{self.key}/"

    def href(self, state: TableState) -> str:
        """
        The URL for a state, which is the same URL whichever side asks for
        it: the header link, and the action that re-renders afterwards.
        """
        asked = {
            name: value
            for name, value in (("sort", state.sort), (QUERY, state.query))
            if value
        }
        return f"/{self.path()}" + (f"?{urlencode(asked)}" if asked else "")

    def state_of(self, request: Any) -> TableState:
        asked = self._router._get_query_params(request)
        return TableState(sort=asked.get("sort"), query=asked.get(QUERY, ""))

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def bind(self, request: Any) -> BoundTable:
        """
        This declaration and what the request asked of it, together.

        The one value the components take: bind once in the view and then
        place them, rather than each of them reaching for the request.
        """
        return BoundTable(self, self.state_of(request))

    def render(self, request: Any) -> ComponentType:
        """
        Both components, one above the other, for a view that wants the
        whole thing and not a say in how it is arranged.
        """
        bound = self.bind(request)
        return html.div(
            *((TableSearch.from_state(bound),) if self.search is not None else ()),
            DataTable.from_state(bound),
            class_="flex flex-col gap-3",
        )

    def search_input(self, state: TableState) -> ComponentType:
        """
        A GET form of its own, above the frame and outside it.

        Outside because the frame is what gets replaced: a box swapped out
        from under the person typing in it loses the caret and the focus
        along with it. A form because that is what Enter already does, and
        x-target only changes it from a navigation into a swap.
        """
        return html.form(
            TextInput()
            .name(QUERY)
            .attr("type", "search")
            .label(self.search or "")
            .hidden_label()
            .placeholder(self.search or "")
            .value(state.query)
            .leading_icon(HueIcon("search")),
            # The sort survives a search because it is still in the form.
            *(
                (html.input_(type="hidden", name="sort", value=state.sort),)
                if state.sort
                else ()
            ),
            method="get",
            action=f"/{self.path()}",
            **{
                "x-target": self.key,
                f"@input.debounce.{SEARCH_DELAY}": "$el.requestSubmit()",
            },
        )

    def apply(self, table: DataTable, state: TableState) -> DataTable:
        table = (
            DataTable()
            .id(self.key)
            .columns(self.columns)
            .rows(self.rows(state))
            .sorted(state.sort)
            .sort_href(lambda order: self.href(TableState(sort=order)))
        )
        if self.identity is None:
            return table

        table.selectable(self.identity).name(SELECTED)
        if not self.actions:
            return table

        table.bulk_actions(
            *(
                Button()
                .variant(action.variant)
                .size("xs")
                .type("submit")
                .content(action.label)
                .attr("formaction", f"/{self.path()}{name}/")
                for name, action in self.actions.items()
            )
        )
        # A real form around real checkboxes, inside the frame so the
        # table is still the outermost thing and still what gets swapped.
        return table.form(f"/{self.path()}")

    # ------------------------------------------------------------------
    # The routes
    # ------------------------------------------------------------------

    def _register(self) -> None:
        """
        One route to read a state and one to act on a selection.

        Both answer with the whole table, so the response to sorting and the
        response to deleting are the same thing and there is only one way for
        the page to be brought up to date.
        """

        async def read(view: Any, request: Any, context: Any) -> ComponentType:
            return self.render(request)

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
            return self.render(request)

        # Named before they are registered, not after: the router takes the
        # route's name off __name__ as it decorates, so renaming them
        # afterwards would leave two tables on one view both calling their
        # routes "read" and "act".
        read.__name__ = f"{self.key}_read"
        act.__name__ = f"{self.key}_act"
        self._router.fragment_get(self.path())(read)
        self._router.fragment_post(f"{self.path()}<str:action>/")(act)


class TableSearch(ChainableComponent):
    """
    The box above a table, and the only part of it that is not swapped.

    Its own component because of where it has to be: the frame is what a
    response replaces, and a box swapped out from under the person typing
    in it loses the caret along with the focus. Placing it yourself is also
    the honest version - it is a separate thing in the tree, and it looks
    like one.
    """

    category: ClassVar[str | None] = None

    @classmethod
    def from_state(cls, state: BoundTable) -> Self:
        return cls().content(state.search())

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames("max-w-xs", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


def datatable(
    router: Router[Any],
    *,
    key: str,
    columns: list[Column],
    rows: RowsFor,
    actions: Mapping[str, BulkAction] | None = None,
    search: str | None = None,
) -> DataTableState:
    """
    Declare a table and the routes that serve it.

    key names the fragment path and the element the response is swapped
    into, so it has to be unique on the page. rows is given the state that
    was asked for and returns the rows for it - not a callback that fires
    when something is sorted, because a sort is a question and rows() is
    already the answer to it, and so is a search.

    search is the placeholder for a box above the table, and having one is
    what puts a box there at all.
    """
    return DataTableState(
        router,
        key=key,
        columns=columns,
        rows=rows,
        actions=actions,
        search=search,
    )
