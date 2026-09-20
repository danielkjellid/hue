from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Literal, Mapping, Sequence

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.atoms.skeleton import Skeleton
from hue.ui.base import ChainableComponent
from hue.ui.molecules.empty import Empty
from hue.utils import classes_if_else, classnames, render_if

type CellAlign = Literal["start", "center", "end"]
type HeadScope = Literal["col", "row", "colgroup", "rowgroup"]

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

_FRAME = "w-full overflow-x-auto rounded-lg border border-border bg-surface"


class Table(ChainableComponent):
    """
    A table, built from the parts a table is made of.

    TableCaption, TableHeader, TableBody, TableFooter, TableRow, TableHead
    and TableCell mirror the HTML elements one for one. compact() sets the
    padding for every cell at once, and footer() is where an empty or error
    state goes - inside the frame, under the header.

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

    def footer(self, *values: ComponentType) -> Self:
        """
        What sits under the table inside the same frame, which is where an
        empty or an error state goes: a full-width message is not a cell, and
        a table with a header and no rows is still a table. Not the same
        thing as TableFooter, which is a row of the table itself.
        """
        self._props["footer"] = values
        return self

    def busy(self, value: bool = True) -> Self:
        """
        Say the contents are being replaced, so a screen reader is told the
        table is mid-update rather than reading out placeholder rows.
        """
        self._props["busy"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        busy: bool = self._get_prop("busy", False)

        return html.div(
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
                **{
                    "aria_busy": "true" if busy else None,
                    **self._get_base_html_attrs(),
                },
            ),
            *self._get_prop("footer", ()),
            class_=_FRAME,
        )


class TableHeader(ChainableComponent):
    """
    The thead group of a Table.
    """

    category: ClassVar[str | None] = None

    def _render(self, context: HueContext) -> Component:
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

    def _render(self, context: HueContext) -> Component:
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

    def _render(self, context: HueContext) -> Component:
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

    def _render(self, context: HueContext) -> Component:
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

    def colspan(self, value: int) -> Self:
        self._props["colspan"] = value
        return self

    def _render(self, context: HueContext) -> Component:
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
            **self._get_base_html_attrs(),
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

    def _render(self, context: HueContext) -> Component:
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

    def _render(self, context: HueContext) -> Component:
        return html.caption(
            *self._children,
            class_=classnames(
                "border-b border-border px-4 py-3 text-start text-sm text-fg-muted",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


@dataclass(frozen=True)
class Column:
    """
    One column of a DataTable: where its value comes from, and how it reads.

    key resolves a row's value - a key, a dotted path into a nested record,
    or a callable given the row. render takes the row instead and returns
    whatever the cell should hold, for the columns that are a badge or a
    button rather than a value. align is where the value sits in the cell,
    and align="end" is what a column of numbers wants: it lines the digits
    up as well as the edge.
    """

    key: str | Callable[[Mapping[str, Any]], Any]
    label: str
    align: CellAlign = "start"
    render: Callable[[Mapping[str, Any]], ComponentType] | None = None


def _resolve(
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
    A resolved scalar as text. Anything else is a render() the column is
    missing, rather than something to guess at.
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

    columns() and rows() are the shape of it; everything else is a state it
    can be in instead. loading() puts placeholder rows under the header,
    empty() and error() replace the rows with a message under it, and
    compact() tightens the rows.
    """

    category = "Data"

    def __init__(self) -> None:
        super().__init__()
        self._columns: list[Column] = []
        self._rows: Sequence[Mapping[str, Any]] = []

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

    def loading(self, value: bool = True) -> Self:
        """
        Placeholder rows under the header while the real ones are on their
        way, keeping the columns where they are so the page does not jump
        when they land.
        """
        self._props["loading"] = value
        return self

    def empty(self, value: ComponentType) -> Self:
        """
        What to show in place of the rows when there are none. An Empty that
        says why there is nothing here and what to do about it beats the
        default, which can only say that there is nothing.
        """
        self._props["empty"] = value
        return self

    def error(self, value: ComponentType) -> Self:
        """
        What to show when the rows could not be fetched at all. Set, it
        replaces them whatever else is going on - there is nothing to say
        about rows nobody has.
        """
        self._props["error"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        error: ComponentType | None = self._get_prop("error")
        loading: bool = self._get_prop("loading", False)

        table = (
            Table()
            .compact(self._get_prop("compact", False))
            .busy(loading)
            .content(
                render_if(
                    self._get_prop("caption"), lambda c: TableCaption().content(c)
                ),
                self._head(),
                *self._body(loading=loading, failed=error is not None),
            )
        )

        if error is not None:
            table.footer(error)
        elif not loading and not self._rows:
            table.footer(self._get_prop("empty") or _default_empty())

        if class_ := self._get_prop("class_"):
            table.class_(class_)
        table._attrs.update(self._attrs)
        return table

    def _head(self) -> ComponentType:
        return TableHeader().content(
            TableRow().content(*[self._header_cell(column) for column in self._columns])
        )

    def _header_cell(self, column: Column) -> ComponentType:
        return TableHead().align(column.align).content(column.label)

    def _body(self, *, loading: bool, failed: bool) -> tuple[ComponentType, ...]:
        """
        The rows, the placeholders that stand in for them, or nothing at all -
        a header with a message under it, which is what empty and error are.
        """
        if failed or (not loading and not self._rows):
            return ()
        if loading:
            return (self._placeholders(),)
        return (
            TableBody().content(
                *[
                    TableRow().content(
                        *[self._cell(column, row) for column in self._columns]
                    )
                    for row in self._rows
                ]
            ),
        )

    def _placeholders(self) -> ComponentType:
        """
        Bars where the values will be, as many rows as are already there so
        the table keeps its height, and hidden from the screen reader that is
        already being told the table is busy.
        """
        count = len(self._rows) or _PLACEHOLDER_ROWS
        return (
            TableBody()
            .aria_hidden("true")
            .content(
                *[
                    TableRow().content(
                        *[
                            TableCell()
                            .align(column.align)
                            .content(Skeleton().width(_placeholder_width(index)))
                            for index, column in enumerate(self._columns)
                        ]
                    )
                    for _ in range(count)
                ]
            )
        )

    def _cell(self, column: Column, row: Mapping[str, Any]) -> ComponentType:
        content = (
            column.render(row)
            if column.render is not None
            else _stringify(_resolve(row, column.key))
        )
        return TableCell().align(column.align).content(content)


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
