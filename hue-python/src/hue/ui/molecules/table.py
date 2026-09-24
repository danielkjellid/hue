from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Literal,
    Mapping,
    Sequence,
)

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.checkbox import Checkbox
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.skeleton import Skeleton
from hue.ui.base import ChainableComponent
from hue.ui.molecules.empty import Empty
from hue.utils import classes_if_else, classnames, render_if

type CellAlign = Literal["start", "center", "end"]
type HeadScope = Literal["col", "row", "colgroup", "rowgroup"]
type SortDirection = Literal["ascending", "descending"]

# Ending a column and lining its digits up are one decision, not two: the
# only thing that wants to sit against the right edge is a number, and
# without tabular figures the decimal points drift and the column stops
# being scannable. Tabular figures do nothing to text with no digits in it,
# so anything else ending a column pays nothing for them.
_ALIGN_CLASSES: dict[CellAlign, str] = {
    "start": "text-start",
    "center": "text-center",
    "end": "text-end tabular-nums",
}

# The cells carry no padding of their own: it lives here, on the table, so
# one class sets the rhythm of every row and a cell cannot disagree with its
# neighbour. The gutters are the same either way - narrowing those is what
# makes a dense table unreadable - so compact is the row height and nothing
# else.
_GUTTERS = "[&_th]:px-4 [&_td]:px-4"
_ROW_HEIGHT = ["[&_th]:py-[9px]", "[&_td]:py-[11px]"]
_ROW_HEIGHT_COMPACT = ["[&_th]:py-[7px]", "[&_td]:py-[7px]"]

# The shell owns the border and the radius; the toolbar, the table and the
# footer are bands inside it, separated by hairlines. Only the band the
# table is in scrolls: overflow on the shell would clip a popover opened
# from the toolbar, and a filter panel that cannot leave the frame is no
# panel at all. The bands square off the shell's corners unless the first
# and the last are told to round with it - 11px, the 12px radius less the
# border it sits inside.
_FRAME = (
    "w-full rounded-lg border border-border bg-surface "
    "[&>*:first-child]:rounded-t-[11px] [&>*:last-child]:rounded-b-[11px]"
)

# The one band that scrolls, and the only place a table is ever too wide.
_BODY_BAND = "overflow-x-auto"

# A band of controls welded into the shell, above the rows or below them.
_BAND = "flex flex-wrap items-center gap-2 border-b border-border px-3 py-2"
# Rounded here, not by the frame: it sits inside the rows region, which is
# the frame's last child but has no background of its own to round.
#
# The end padding is the cells' 16px less the inset of a pagination step,
# which is a control-height square with a 14px glyph centred in it. That puts
# the last chevron on the same edge as the column above it, and it tracks
# the control height when a coarse pointer makes the steps larger.
_BAND_BOTTOM = (
    "flex flex-wrap items-center justify-between gap-2 gap-x-5 rounded-b-[11px] "
    "border-t border-border bg-canvas-subtle py-2.5 ps-4 "
    "pe-[calc(1rem_-_(var(--spacing-control-sm)_-_0.875rem)_/_2)]"
)

# The bar over a table with rows picked in it. accent-subtle so the whole
# frame says something is selected, not just the rows.
# The picked-rows bar floats at the foot of the viewport, over the page, so
# it is in reach wherever the reader has scrolled and never pushes a row.
_BULK_BAR = (
    "fixed inset-x-0 bottom-6 z-50 mx-auto flex w-fit max-w-[calc(100vw-2rem)] "
    "flex-wrap items-center gap-1 rounded-lg border border-border "
    "bg-surface-raised p-1 shadow-overlay"
)
_BULK_DIVIDER = "mx-1 w-px self-stretch bg-border"
_BULK_COUNT = "ps-2.5 pe-1 font-ui text-sm font-medium tabular-nums text-fg"

# Slides up from below and fades in. The stylesheet's reduced-motion rule
# already shortens every transition, so this needs nothing of its own.
_BULK_MOTION = {
    "x-transition:enter": "transition duration-200 ease-out",
    "x-transition:enter-start": "translate-y-5 opacity-0",
    "x-transition:enter-end": "translate-y-0 opacity-100",
    "x-transition:leave": "transition duration-150 ease-in",
    "x-transition:leave-start": "translate-y-0 opacity-100",
    "x-transition:leave-end": "translate-y-5 opacity-0",
}

# The header's own text, made pressable. It inherits everything from the th,
# so a sortable column reads exactly like one that is not until it is sorted.
_SORT_TRIGGER = (
    "inline-flex items-center gap-1 rounded-xs text-inherit no-underline "
    "hover:text-fg [&_svg]:size-3.5 [&_svg]:flex-none"
)

# The column the rows are in the order of says so in the header's own
# colour; the rest keep a faint hint that they could be.
_SORT_ICON = "text-accent-text"
_SORT_HINT = "text-fg-disabled"

# A checkbox column is as wide as a checkbox and no wider. Only the margin
# centres it: the box is a grid, which is what puts the tick in the middle
# of it, and telling it to be a block instead takes the tick away.
_SELECT_COLUMN = "w-0 [&>*]:mx-auto"


class Table(ChainableComponent):
    """
    A table, built from the parts a table is made of.

    TableCaption, TableHeader, TableBody, TableFooter, TableRow, TableHead
    and TableCell mirror the HTML elements one for one. compact() sets the
    padding for every cell at once, and footer() is where an empty or error
    state goes - inside the frame, under the header. A table whose rows are
    on their way says so with aria_busy("true"), and stands in for them
    with whatever placeholder rows it likes.

    For a list of records, reach for DataTable, which builds all of this from
    a column definition and your rows.
    """

    category = "Data"

    @classmethod
    def example(cls) -> Self:
        return cls().content(
            TableHeader().content(
                TableRow().content(
                    TableHead().content("Name"),
                    TableHead().content("Email"),
                ),
            ),
            TableBody().content(
                TableRow().content(
                    TableCell().content("Ada Lovelace"),
                    TableCell().content("ada@example.com"),
                ),
                TableRow().content(
                    TableCell().content("Alan Turing"),
                    TableCell().content("alan@example.com"),
                ),
            ),
        )

    def compact(self, value: bool = True) -> Self:
        """
        Tighten the rows, for a table someone scans rather than reads. About
        a third more of it fits on screen.
        """
        self._props["compact"] = value
        return self

    def form(self, action: str) -> Self:
        """
        Post what is ticked in the table to this URL.

        The form is an empty element in the frame, and the checkboxes and
        buttons name it with their own form attribute. A form wrapped around
        the frame would contain the search box in the band above the rows,
        which is a form of its own, and browsers discard a nested form.
        """
        self._props["form"] = action
        return self

    def toolbar(self, *values: ComponentType) -> Self:
        """
        What sits above the table inside the same frame, such as a bar of
        actions for the rows. It is not a row of the table, because it is not
        part of the grid and nothing in it lines up with a column.
        """
        self._props["toolbar"] = values
        return self

    def footer(self, *values: ComponentType) -> Self:
        """
        What stands in for the rows when there are none, such as an empty
        state or an error. It sits under the table inside the same id, so a
        response that finds no rows replaces both at once. This is different
        from TableFooter, which is a row of the table itself.
        """
        self._props["footer"] = values
        return self

    def under(self, *values: ComponentType) -> Self:
        """
        The band along the bottom of the frame, such as the pages or a total.
        It sits inside the region a response replaces, because what it says
        is about the rows and changes when they do.
        """
        self._props["under"] = values
        return self

    def _render(self, context: Context) -> Component:
        attrs = self._get_base_html_attrs()
        # The id names the frame rather than the table inside it, because
        # the frame is the whole of what a table is: swap only the table and
        # an empty state left under it would still be there. The Alpine
        # scope moves with it for the same reason - a toolbar above the
        # rows is as much part of the table as the rows are, and a scope on
        # the table element would leave it outside.
        frame_id = attrs.pop("id", None)
        scope = attrs.pop("x-data", None)

        inside: list[ComponentType] = [
            *self._get_prop("toolbar", ()),
            # Everything a response replaces, under one id: the rows, and
            # whatever stands in for them when there are none.
            html.div(
                html.div(
                    html.table(
                        *self._children,
                        class_=classnames(
                            "w-full border-collapse text-base",
                            _GUTTERS,
                            classes_if_else(
                                self._get_prop("compact", False),
                                _ROW_HEIGHT_COMPACT,
                                _ROW_HEIGHT,
                            ),
                            self._get_prop("class_"),
                        ),
                        **attrs,
                    ),
                    class_=_BODY_BAND,
                ),
                *self._get_prop("footer", ()),
                # Replaced with the rows. The pages and the total describe
                # them, so a response that changes the rows changes these.
                *self._get_prop("under", ()),
                id=rows_id(frame_id),
            ),
        ]
        action: str | None = self._get_prop("form")
        if action is not None:
            # The whole frame, unlike a sort or a page: an action changes
            # what is there rather than which of it is shown, and the
            # selection it was done with is gone afterwards.
            inside.insert(
                0,
                html.form(
                    id=form_id(frame_id),
                    method="post",
                    action=action,
                    hidden=True,
                    **({"x-target": frame_id} if frame_id else {}),
                ),
            )

        return html.div(
            *inside,
            id=frame_id,
            class_=_FRAME,
            **({"x-data": scope} if scope is not None else {}),
        )


class TableHeader(ChainableComponent):
    """
    The thead group of a Table.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        return html.thead(
            *self._children,
            class_=classnames(self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


class TableBody(ChainableComponent):
    """
    The tbody group of a Table.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        return html.tbody(
            *self._children,
            # The frame already draws the line under the last row.
            class_=classnames(
                "[&_tr:last-child_td]:border-b-0", self._get_prop("class_")
            ),
            **self._get_base_html_attrs(),
        )


class TableFooter(ChainableComponent):
    """
    The tfoot group of a Table, for a total or a summary of the rows above.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        return html.tfoot(
            *self._children,
            class_=classnames(
                "border-t border-border bg-surface-sunken font-ui text-sm "
                "font-medium [&_td]:border-b-0",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class TableRow(ChainableComponent):
    """
    A tr row.

    Selected rows are marked with aria-selected, which is both what a screen
    reader reads and what tints the row.
    """

    category: ClassVar[str | None] = None

    def selected(self, value: bool = True) -> Self:
        self._props["selected"] = value
        return self

    def _render(self, context: Context) -> Component:
        selected: bool = self._get_prop("selected", False)

        return html.tr(
            *self._children,
            class_=classnames(
                "transition-colors hover:bg-surface-hover",
                "aria-[selected=true]:bg-accent-subtle",
                self._get_prop("class_"),
            ),
            **{
                "aria_selected": "true" if selected else None,
                **self._get_base_html_attrs(),
            },
        )


class TableHead(ChainableComponent):
    """
    A th header cell, scoped to its column unless scope() says otherwise.

    align("end") is what a column of numbers wants: it puts the header over
    the figures and lines the digits up under it.
    """

    category: ClassVar[str | None] = None

    def scope(self, value: HeadScope) -> Self:
        self._props["scope"] = value
        return self

    def align(self, value: CellAlign) -> Self:
        self._props["align"] = value
        return self

    def sorted(self, value: SortDirection | None) -> Self:
        """
        Which way this column is sorted, if it is the one the rows are in
        the order of. One header at a time: aria-sort on two of them says
        the rows are in two orders at once, and ARIA has no way to say which
        of the two came first.
        """
        self._props["sorted"] = value
        return self

    def colspan(self, value: int) -> Self:
        self._props["colspan"] = value
        return self

    def _render(self, context: Context) -> Component:
        return html.th(
            *self._children,
            class_=classnames(
                "border-b border-border bg-surface-sunken font-ui text-xs "
                "font-bold tracking-[0.02em] whitespace-nowrap text-fg-muted",
                _ALIGN_CLASSES[self._get_prop("align", "start")],
                self._get_prop("class_"),
            ),
            scope=self._get_prop("scope", "col"),
            colspan=self._get_prop("colspan"),
            **{
                "aria_sort": self._get_prop("sorted"),
                **self._get_base_html_attrs(),
            },
        )


class TableCell(ChainableComponent):
    """
    A td data cell.

    align("end") switches the digits to tabular figures along with the
    alignment, so the decimal points line up down the column. Cells wrap
    rather than truncate: a reference cut off without saying so is worse
    than a tall row.
    """

    category: ClassVar[str | None] = None

    def align(self, value: CellAlign) -> Self:
        self._props["align"] = value
        return self

    def colspan(self, value: int) -> Self:
        self._props["colspan"] = value
        return self

    def _render(self, context: Context) -> Component:
        return html.td(
            *self._children,
            class_=classnames(
                "border-b border-border align-middle text-fg",
                _ALIGN_CLASSES[self._get_prop("align", "start")],
                self._get_prop("class_"),
            ),
            colspan=self._get_prop("colspan"),
            **self._get_base_html_attrs(),
        )


class TableCaption(ChainableComponent):
    """
    What the table is, read before it and shown above it.

    Above rather than below, because a caption is the thing that tells you
    what you are about to read - "Invoices, September 2026, 4 of 148".
    """

    category: ClassVar[str | None] = None

    def _render(self, context: Context) -> Component:
        return html.caption(
            *self._children,
            class_=classnames(
                "border-b border-border px-4 py-3 text-start text-sm text-fg-muted",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class TableSource(ABC):
    """
    Something that knows what a table is showing.

    A bound table offers one of these to everything rendered inside it,
    so a DataTable in there can draw itself without being handed anything
    and without being a direct child of anything.

    The abstract class lives here instead of with the code that makes one,
    so the components can name it without importing that code:
    hue.datatable imports the components, and the reverse import would be
    circular.
    """

    @abstractmethod
    def build_into(self, into: DataTable) -> DataTable:
        """
        The table this describes: its columns, its rows, the order they
        are in and where the next one lives.
        """

    @classmethod
    def from_context(cls, context: Context) -> TableSource:
        found = context.get(cls)
        if isinstance(found, cls):
            return found
        raise ValueError(
            "A DataTable with no columns of its own is drawn by the table "
            "declaration it sits in, and there is none here. Give it columns "
            "and rows, or draw it from one: "
            "DataTable.from_state(self.invoices)."
        )


class TableDeclaration(ABC):
    """
    A table declared once and drawn once per request.

    DataTable.from_state() takes one. It lives here for the same reason
    TableSource does: the component has to name it without importing the
    code that makes one.
    """

    @abstractmethod
    async def draw(self, table: DataTable, context: Context) -> Component:
        """
        This table, bound to the request the page is rendered for and drawn
        into table, so that anything chained onto table is kept.
        """


class _Drawn:
    """
    A DataTable waiting for its declaration, which has to fetch the rows
    before there is anything to draw. Fetching is a coroutine, and _render
    is not.
    """

    def __init__(self, state: TableDeclaration, table: DataTable) -> None:
        self._state = state
        self._table = table

    async def htmy(self, context: Context) -> Component:
        return await self._state.draw(self._table, context)


@dataclass(frozen=True)
class Column:
    """
    One column of a DataTable: where its value comes from, and how it reads.

    key resolves a row's value. It can be a key, a dotted path into a
    nested record, or a callable given the row. render takes the row and
    returns whatever the cell should hold, for columns that show a badge
    or a button instead of a value. align is where the value sits in the
    cell; align="end" also lines up the digits, which a column of numbers
    needs. sort is what the server orders by, often not the field the
    value is read from. On a table drawn from a declaration it turns the
    header into a link to the rows in that order.
    """

    key: str | Callable[[Mapping[str, Any]], Any]
    label: str
    align: CellAlign = "start"
    sort: str | None = None
    render: Callable[[Mapping[str, Any]], ComponentType] | None = None


def rows_id(frame_id: str | None) -> str | None:
    """
    The id of the region a response replaces: the rows, and whatever
    stands in for them. It is derived from the frame's id, so naming a
    table names every part of it.
    """
    return None if frame_id is None else f"{frame_id}-rows"


def form_id(frame_id: str | None) -> str | None:
    """
    The id of the form a table posts through, derived from the frame's id
    like the rows region.
    """
    return None if frame_id is None else f"{frame_id}-act"


def resolve_value(
    row: Mapping[str, Any],
    key: str | Callable[[Mapping[str, Any]], Any],
) -> Any:
    """
    A row's value for one column, by callable or by (dotted) key path.
    """
    if callable(key):
        return key(row)

    value: Any = row
    for part in key.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise ValueError(
                f"Cannot resolve key {key!r}: {part!r} is not a key of {value!r}."
            )
        value = value[part]
    return value


def _stringify(value: Any) -> str:
    """
    A resolved scalar as text. A value that is not a scalar needs a
    render() on its column, so this raises instead of guessing.
    """
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    raise ValueError(
        f"Column value {value!r} is not a scalar - give the column a render()."
    )


# Enough rows to read as a table that is filling in, and few enough that the
# wait does not look longer than it is.
_PLACEHOLDER_ROWS = 3


class DataTable(ChainableComponent):
    """
    A Table built from a column definition and a list of records.

    columns() and rows() give it its shape, and everything else is a state
    it can be in. loading() shows placeholder rows under the header,
    empty() and error() replace the rows with a message, and compact()
    tightens the rows. Sorting, searching and acting on picked rows need
    the server, so they come with a table drawn from a declaration:
    DataTable.from_state().
    """

    category = "Data"

    def __init__(self) -> None:
        super().__init__()
        self._columns: list[Column] = []
        self._rows: Sequence[Mapping[str, Any]] = []

    @classmethod
    def from_state(cls, state: TableDeclaration) -> Self:
        """
        The table a declaration describes, bound to the request of the page it
        is rendered on. Anything chained after it, such as a caption or your
        own empty state, is kept.
        """
        table = cls()
        table._props["state"] = state
        return table

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .columns(
                [
                    Column("invoice", "Invoice"),
                    Column("customer", "Customer"),
                    Column("amount", "Amount", align="end"),
                ]
            )
            .rows(
                [
                    {"invoice": "INV-2050", "customer": "Contoso", "amount": "2190"},
                    {"invoice": "INV-2048", "customer": "Northwind", "amount": "1200"},
                ]
            )
        )

    def columns(self, value: list[Column]) -> Self:
        self._columns = value
        return self

    def rows(self, value: Sequence[Mapping[str, Any]]) -> Self:
        self._rows = value
        return self

    def caption(self, value: str) -> Self:
        """
        What the table is, read before it and shown above it.
        """
        self._props["caption"] = value
        return self

    def compact(self, value: bool = True) -> Self:
        """
        Tighten the rows, for a table someone scans rather than reads.
        """
        self._props["compact"] = value
        return self

    def _form(self, action: str) -> Self:
        """
        Post the ticked rows to this URL. See Table.form().
        """
        self._props["form"] = action
        return self

    def loading(self, value: bool = True) -> Self:
        """
        Placeholder rows under the header while the real ones load. The
        columns stay where they are, so the page does not jump when the rows
        arrive.
        """
        self._props["loading"] = value
        return self

    def empty(self, value: ComponentType) -> Self:
        """
        What to show in place of the rows when there are none. An Empty that
        says why and what to do next is better than the default, which can
        only say there is nothing here.
        """
        self._props["empty"] = value
        return self

    def error(self, value: ComponentType) -> Self:
        """
        What to show when the rows could not be fetched. When set, it replaces
        the rows whatever else is going on, since there is nothing to say
        about rows that never arrived.
        """
        self._props["error"] = value
        return self

    def _selectable(self, key: str | Callable[[Mapping[str, Any]], Any]) -> Self:
        """
        Put a checkbox at the start of every row, named after what key
        resolves to for that row. "Select INV-2050" gives a screen reader
        something to pick by, where four checkboxes all announcing "Select"
        would not.
        """
        self._props["selectable"] = key
        return self

    def _bulk_actions(self, *values: ComponentType) -> Self:
        """
        What to do with the picked rows, in a bar that floats at the foot of
        the page once at least one is picked.

        The actions render inside the table's Alpine scope, so an expression in
        one can read selected, the list of values the checkboxes carry:

            Button().content("Delete").on_click(call("remove", unsafe("selected")))
        """
        self._props["bulk_actions"] = values
        return self

    def _sorted(self, value: str | None) -> Self:
        """
        The order the rows are already in, as the server spells it: "amount",
        or "-amount" for descending. It is the same string Django's order_by
        takes and a sort query parameter carries, so a view passes its own
        straight through.

        The table never sorts anything itself. A page of a lazy queryset
        cannot be re-sorted anyway, because the rows in hand are already the
        wrong ones and only another query returns the right ones.
        """
        self._props["sorted"] = value
        return self

    def _sort_href(self, value: Callable[[str], str]) -> Self:
        """
        Where an order lives, given the order a click would ask for.

        One column is sorted at a time. Clicking a column the rows are not
        sorted by replaces the order, and clicking the one they are sorted by
        reverses it.
        """
        self._props["sort_href"] = value
        return self

    def _name(self, value: str) -> Self:
        """
        What the row checkboxes are called when the table's form is
        submitted, "selected" unless set.
        """
        self._props["name"] = value
        return self

    def _toolbar(self, *values: ComponentType) -> Self:
        """
        The band above the rows, inside the same frame: the ways of narrowing
        the table.
        """
        self._props["toolbar"] = values
        return self

    def _under(self, *values: ComponentType) -> Self:
        """
        The band along the bottom of the frame, such as the pages or a total.
        """
        self._props["under"] = values
        return self

    def _render(self, context: Context) -> Component:
        state: TableDeclaration | None = self._get_prop("state")
        if state is not None:
            # A copy without the declaration goes in, or drawing it would
            # hand it straight back to the declaration again.
            return _Drawn(state, self._without_state())

        if not self._columns:
            # Nothing to draw and nobody said what: the bound table above
            # it knows, and says so through the context rather than by
            # being passed down through whatever laid this out.
            TableSource.from_context(context).build_into(self)

        error: ComponentType | None = self._get_prop("error")
        loading: bool = self._get_prop("loading", False)

        table = (
            Table()
            .compact(self._get_prop("compact", False))
            .content(
                render_if(
                    self._get_prop("caption"), lambda c: TableCaption().content(c)
                ),
                self._head(),
                *self._body(loading=loading, failed=error is not None),
            )
        )

        # Stated either way rather than only while it is true: a swap that
        # leaves the table element in place and rewrites what is around it
        # would otherwise leave a finished table busy for good.
        table.aria_busy("true" if loading else "false")

        if (action := self._get_prop("form")) is not None:
            table.form(action)

        self._frame(table)

        if error is not None:
            table.footer(error)
        elif not loading and not self._rows:
            table.footer(self._get_prop("empty") or _default_empty())

        if class_ := self._get_prop("class_"):
            table.class_(class_)
        table._attrs.update(self._attrs)
        return table

    def _frame(self, table: Table) -> None:
        """
        The bands around the rows: a toolbar above, the bar for picked rows
        that floats over the page, and a band along the bottom.
        """
        bands: list[ComponentType] = []
        if self._selection_values() is not None:
            table.x_data("hueTableSelection")
            bands = self._bands(self._bulk_bar())
        elif toolbar := self._get_prop("toolbar", ()):
            bands = [html.div(*toolbar, class_=_BAND)]
        if bands:
            table.toolbar(*bands)

        if under := self._get_prop("under", ()):
            table.under(html.div(*under, class_=_BAND_BOTTOM))

    def _without_state(self) -> DataTable:
        table = DataTable()
        table._props = {k: v for k, v in self._props.items() if k != "state"}
        table._attrs = dict(self._attrs)
        table._children = self._children
        table._columns = list(self._columns)
        table._rows = self._rows
        return table

    def _head(self) -> ComponentType:
        return TableHeader().content(
            TableRow().content(
                self._select_all(),
                *[self._header_cell(column) for column in self._columns],
            )
        )

    def _header_cell(self, column: Column) -> ComponentType:
        head = TableHead().align(column.align)
        if column.sort is None:
            return head.content(column.label)

        href: Callable[[str], str] | None = self._get_prop("sort_href")
        if href is None:
            raise ValueError(
                f"Column {column.label!r} is sortable, so its header is a "
                f"link to the rows in that order, and only a declaration "
                f"knows where that order lives. Draw the table from one - "
                f"DataTable.from_state() - or leave sort off the column."
            )

        current = _direction(self._get_prop("sorted"), column.sort)
        # Ascending first; the column the rows are already in the order of
        # turns around.
        following = f"-{column.sort}" if current == "ascending" else column.sort

        # Given an id to aim at, the browser fetches the new order and
        # swaps the rows in place; without one it follows the link. The
        # rows and not the frame, so the toolbar above them - and the
        # caret in the search box in it - is left where it was.
        target = rows_id(self._attrs.get("id"))

        return head.sorted(current).content(
            html.a(
                column.label,
                _sort_icon(current),
                href=href(following),
                class_=classnames(_SORT_TRIGGER, FOCUS_RING),
                **({"x-target": target} if target is not None else {}),
            )
        )

    def _bands(self, picked: tuple[ComponentType, ...] | None) -> list[ComponentType]:
        """
        The band above the rows, and the bar for picked rows when there are
        actions to put in it.

        The bar floats over the page instead of taking a band in the frame,
        so picking rows never moves them.
        """
        toolbar: tuple[ComponentType, ...] = self._get_prop("toolbar", ())
        bands: list[ComponentType] = (
            [html.div(*toolbar, class_=_BAND)] if toolbar else []
        )
        if picked is not None:
            bands.extend(picked)
        return bands

    def _bulk_bar(self) -> tuple[ComponentType, ...] | None:
        """
        The bar for picked rows: how many there are, a way to clear them,
        and what can be done with them.

        It is moved to the end of the body so it floats over the page, and
        it keeps the table's Alpine scope when it moves. Escape clears the
        selection too. The count is also announced from a live region that
        stays displayed, because a region shown at the moment it has
        something to say is not read out, and the bar itself is hidden until
        a row is picked.
        """
        actions: tuple[ComponentType, ...] = self._get_prop("bulk_actions", ())
        if not actions:
            return None
        clear = (
            Button()
            .variant("ghost")
            .size("xs")
            .icon_only("Clear selection")
            .content(HueIcon("x"))
            .attr("aria-keyshortcuts", "Escape")
            .x_on("click", unsafe("clear()"))
        )
        bar = html.div(
            # The count and the button that clears it read as one thing, so
            # they sit together with no gap of their own.
            html.span(
                html.span(
                    class_=_BULK_COUNT,
                    **{"x-text": "selected.length + ' selected'"},
                ),
                clear,
                class_="flex items-center",
            ),
            html.span(aria_hidden="true", class_=_BULK_DIVIDER),
            *actions,
            # A group rather than a toolbar: a toolbar promises arrow keys
            # and one tab stop, and these are ordinary buttons Tab walks.
            role="group",
            aria_label="Selected rows",
            class_=_BULK_BAR,
            **{
                "x-show": "selected.length > 0",
                "x-cloak": True,
                "x-on:keydown.escape.window": "if (selected.length) clear()",
                # A sort, a page or a search replaces the rows without
                # replacing this scope; a row that left the page leaves the
                # selection with it, so an action can only reach what is
                # on screen.
                "x-on:ajax:merged.window": "prune()",
                **_BULK_MOTION,
            },
        )
        return (
            html.template(bar, **{"x-teleport": "body"}),
            html.span(
                role="status",
                class_="sr-only",
                **{"x-text": "selected.length ? selected.length + ' selected' : ''"},
            ),
        )

    def _select_all(self) -> ComponentType:
        """
        The checkbox above the column of checkboxes.

        Both of its states are set as DOM properties instead of bound as
        attributes. indeterminate has no attribute at all, and the checked
        attribute stops reflecting the state once someone has clicked the box.
        """
        if self._selection_values() is None:
            return UNDEFINED
        return (
            TableHead()
            .class_(_SELECT_COLUMN)
            .content(
                Checkbox()
                .name("hue-select-all")
                .label("Select all rows")
                .hidden_label()
                .x_effect(unsafe("$el.checked = all; $el.indeterminate = some"))
                .x_on("change", unsafe("toggleAll($event.target.checked)"))
            )
        )

    def _select_cell(self, row: Mapping[str, Any]) -> ComponentType:
        value = str(resolve_value(row, self._get_prop("selectable")))
        box = (
            Checkbox()
            .name(self._get_prop("name", "selected"))
            .value(value)
            .label(f"Select {value}")
            .hidden_label()
            .x_model("selected")
            .attr("data-hue-row-select", "")
        )
        # Named rather than wrapped: the form is an empty element in the
        # frame, because a form around the band above the rows would
        # swallow the search box, which is a form of its own.
        if (posts_to := form_id(self._attrs.get("id"))) is not None:
            box.attr("form", posts_to)
        return TableCell().class_(_SELECT_COLUMN).content(box)

    def _selection_values(self) -> list[str] | None:
        """
        The value each row would be selected as, or None when the table has
        no checkboxes. The header needs the whole list to know when all of
        them are ticked.
        """
        key = self._get_prop("selectable")
        if key is None:
            return None
        return [str(resolve_value(row, key)) for row in self._rows]

    def _body(self, *, loading: bool, failed: bool) -> tuple[ComponentType, ...]:
        """
        The rows, the placeholders standing in for them, or nothing at all,
        which leaves a header with a message under it for the empty and error
        states.
        """
        if failed or (not loading and not self._rows):
            return ()
        if loading:
            return (self._placeholders(),)
        return (TableBody().content(*[self._row(row) for row in self._rows]),)

    def _row(self, row: Mapping[str, Any]) -> ComponentType:
        line = TableRow().content(
            self._select_cell(row)
            if self._get_prop("selectable") is not None
            else UNDEFINED,
            *[self._cell(column, row) for column in self._columns],
        )
        if (key := self._get_prop("selectable")) is not None:
            value = json.dumps(str(resolve_value(row, key)))
            line.x_bind("aria-selected", unsafe(f"isSelected({value})"))
        return line

    def _placeholders(self) -> ComponentType:
        """
        Bars where the values will be. There are as many rows as are already
        there, so the table keeps its height, and they are hidden from screen
        readers, which are already told the table is busy.
        """
        count = len(self._rows) or _PLACEHOLDER_ROWS
        return (
            TableBody()
            .aria_hidden("true")
            .content(
                *[
                    TableRow().content(
                        *[
                            self._placeholder(column, index)
                            for index, column in enumerate(self._columns)
                        ]
                    )
                    for _ in range(count)
                ]
            )
        )

    def _placeholder(self, column: Column, index: int) -> ComponentType:
        """
        One bar, where the value will be.

        It is pushed to the column's side with a margin, because a skeleton is
        a block with its own width and text-align does not move it. Without
        the margin an end-aligned column would fill in from the wrong side and
        jump when the rows arrived.
        """
        bar = Skeleton().width(_placeholder_width(index))
        if column.align != "start":
            bar.class_("mx-auto" if column.align == "center" else "ms-auto")
        return TableCell().align(column.align).content(bar)

    def _cell(self, column: Column, row: Mapping[str, Any]) -> ComponentType:
        content = (
            column.render(row)
            if column.render is not None
            else _stringify(resolve_value(row, column.key))
        )
        return TableCell().align(column.align).content(content)


def _direction(order: str | None, key: str) -> SortDirection | None:
    """
    Which way this column is sorted, if the rows are in its order at all.

    One column: anything the server put in front of a different key leaves
    every other header saying nothing.
    """
    if order is None:
        return None
    if order.lstrip("-") != key:
        return None
    return "descending" if order.startswith("-") else "ascending"


def _sort_icon(direction: SortDirection | None) -> ComponentType:
    """
    Which way the rows go, or that they could go some way at all.

    One arrow turned over rather than two icons, so the change between the
    two orders is a rotation the eye can follow; the columns the rows are
    not in the order of get a quieter glyph that claims no direction.
    """
    if direction is None:
        return HueIcon("arrow-up-down").class_(_SORT_HINT)
    return HueIcon("arrow-down").class_(
        classnames(_SORT_ICON, "rotate-180" if direction == "ascending" else None)
    )


def _placeholder_width(index: int) -> str:
    """
    Uneven widths down the row, so a loading table reads as content on its
    way rather than as a grid of identical grey boxes.
    """
    return ("w-24", "w-32", "w-20", "w-28")[index % 4]


def _default_empty() -> ComponentType:
    """
    All an empty table can say without being told anything: that it is empty.
    Built fresh each time, because a component carries state a shared one
    would carry between tables.
    """
    return (
        Empty()
        .compact()
        .title("Nothing here yet")
        .description("There are no records to show.")
    )
