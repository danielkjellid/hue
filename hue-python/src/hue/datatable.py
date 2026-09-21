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
                Column("invoice", "Invoice"),
                Column("amount", "Amount", align="end", sort="amount"),
            ],
            rows=lambda state: query(order=state.sort),
            select="invoice",
            actions={"delete": lambda request, ids: archive(ids)},
        )

        async def index(self, request, context):
            return Page(title="Invoices", body=self.invoices.render(request))

Reads and writes are split the way HTTP already splits them. An order is
state, so it rides in the URL and rows() answers it - there is no on_sort,
because there is nothing for a handler to do that the next call to rows()
does not. Acting on the rows that are ticked is a write, so it is a POST to
a named action that is given the ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence
from urllib.parse import urlencode

from htmy import html

from hue.types.core import ComponentType
from hue.ui.atoms.button import Button, ButtonVariant
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.input import TextInput
from hue.ui.molecules.table import Column, DataTable

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
        select: str | None = None,
        actions: Mapping[str, BulkAction] | None = None,
        search: str | None = None,
    ) -> None:
        self.key = key
        self.columns = columns
        self.rows = rows
        self.select = select
        self.search = search
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

    def render(self, request: Any) -> ComponentType:
        """
        The table as the request asked for it.
        """
        return self.build(self.state_of(request))

    def build(self, state: TableState) -> ComponentType:
        return html.div(
            *((self._search(state),) if self.search is not None else ()),
            self._table(state),
            class_="flex flex-col gap-3",
        )

    def _search(self, state: TableState) -> ComponentType:
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
            class_="max-w-xs",
            **{
                "x-target": self.key,
                f"@input.debounce.{SEARCH_DELAY}": "$el.requestSubmit()",
            },
        )

    def _table(self, state: TableState) -> ComponentType:
        table = (
            DataTable()
            .id(self.key)
            .columns(self.columns)
            .rows(self.rows(state))
            .sorted(state.sort)
            .sort_href(lambda order: self.href(TableState(sort=order)))
        )
        if self.select is None:
            return table

        table.selectable(self.select).name(SELECTED)
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
        # A real form around real checkboxes: the action posts what is
        # ticked without anything reading the page, and x-target is the
        # only part of it that needs Alpine at all.
        return html.form(
            table,
            method="post",
            action=f"/{self.path()}",
            **{"x-target": self.key},
        )

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


def datatable(
    router: Router[Any],
    *,
    key: str,
    columns: list[Column],
    rows: RowsFor,
    select: str | None = None,
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
        select=select,
        actions=actions,
        search=search,
    )
