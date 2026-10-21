from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from itertools import groupby
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Mapping,
    Sequence,
)

from htmy import Context, html
from typing_extensions import Self

from hue.formats import Formats
from hue.js import unsafe
from hue.types.core import UNDEFINED, Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.button import Button
from hue.ui.atoms.checkbox import Checkbox
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.skeleton import Skeleton
from hue.ui.base import ChainableComponent
from hue.ui.molecules.empty import Empty
from hue.ui.molecules.table import (
    CellAlign,
    SortDirection,
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
    form_id,
    rows_id,
)
from hue.ui.navigation import swap
from hue.utils import classnames, render_if

if TYPE_CHECKING:
    # For the annotation only. hue.datatable imports this module, so a
    # runtime import the other way round would be circular.
    from hue.datatable import _Declaration


# The name every row checkbox is submitted under, which the action route
# reads the picked ids from. Here rather than in hue.datatable, which
# imports this module.
SELECTED = "selected"

# A band of controls welded into the shell, above the rows or below them.
# Its sides match the cells' gutters, so a control's edge lines up with the
# column under it.
_BAND = "flex flex-wrap items-center gap-2 border-b border-border px-4 py-2"
# Rounded here: it is the last thing in the frame, and the band above it
# only rounds its own bottom when nothing is under it.
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


class _Drawn:
    """
    A DataTable waiting for its declaration, which has to fetch the rows
    before there is anything to draw. Fetching is a coroutine, and _render
    is not.
    """

    def __init__(self, declaration: _Declaration, table: DataTable) -> None:
        self._declaration = declaration
        self._table = table

    async def htmy(self, context: Context) -> Component:
        return await self._declaration.draw(self._table, context)


# Where a value comes from in a row: a key, a dotted path, or a callable
# given the row.
type RowKey = str | Callable[[Any], Any]


@dataclass(frozen=True)
class Column:
    """
    One column of a DataTable: where its value comes from, and how it reads.

    key resolves a row's value. It can be a key or attribute, a dotted path
    into a nested record or related object, or a callable given the row.
    render takes the row and returns whatever the cell should hold, for
    columns that show a badge or a button instead of a value. align is
    where the value sits in the cell; align="end" also lines up the
    digits, which a column of numbers needs. sort is what the server
    orders by, often not the field the value is read from. On a table
    drawn from a declaration it turns the header into a link to the rows
    in that order.
    """

    key: RowKey
    label: str
    align: CellAlign = "start"
    sort: str | None = None
    render: Callable[[Any], ComponentType] | None = None


# Told apart from an attribute that is there and holds None.
_MISSING = object()


def resolve_value(
    row: Any,
    key: RowKey,
) -> Any:
    """
    A row's value for one column, by callable or by (dotted) key path.

    Each part of the path is a key of a mapping or an attribute of anything
    else, so a dict, a model instance and a dataclass all read the same way,
    and customer.name can cross from one to the other. A None part way along
    is a nullable relation that is not set, so the cell is empty; only a part
    that is not there at all raises.
    """
    if callable(key):
        return key(row)

    value: Any = row
    for part in key.split("."):
        if value is None:
            return None
        if isinstance(value, Mapping):
            found = value.get(part, _MISSING)
        else:
            found = getattr(value, part, _MISSING)
        if found is _MISSING:
            raise ValueError(
                f"Cannot resolve key {key!r}: "
                f"{type(value).__name__} {value!r} has no {part!r}."
            )
        value = found
    return value


class _Value:
    """
    A resolved value as text. Dates and decimals are written in the formats
    the context holds, and anything else that is not a scalar needs a
    render() on its column, so this raises instead of guessing.
    """

    def __init__(self, value: Any) -> None:
        self._value = value

    def htmy(self, context: Context) -> Component:
        value = self._value
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return str(value)
        if isinstance(value, Decimal):
            # Fixed-point, so 2190.00 keeps the places it was stored with and
            # a small one is 0.0000001 rather than 1E-7.
            return format(value, "f")
        text = Formats.from_context(context).text(value)
        if text is not None:
            return text
        raise ValueError(
            f"{value!r} is not a scalar - return text from a callable key, or "
            f"give its column a render()."
        )


# Enough rows to read as a table that is filling in, and few enough that the
# wait does not look longer than it is.
_PLACEHOLDER_ROWS = 3


class DataTable(ChainableComponent):
    """
    A Table built from a column definition and a list of records.

    columns() and rows() give it its shape, and everything else is a state
    it can be in. loading() shows placeholder rows under the header,
    empty() and error() replace the rows with a message, compact()
    tightens the rows, and group_by() splits them into sections. Sorting,
    searching and acting on picked rows need the server, so they come with
    a table drawn from a declaration: DataTable.from_state().
    """

    category = "Data"

    def __init__(self) -> None:
        super().__init__()
        self._columns: list[Column] = []
        self._rows: Sequence[Any] = []

    @classmethod
    def from_state(cls, declaration: _Declaration) -> Self:
        """
        The table a declaration describes, bound to the request of the page it
        is rendered on. Anything chained after it, such as a caption or your
        own empty state, is kept.
        """
        table = cls()
        table._props["declaration"] = declaration
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

    def rows(self, value: Sequence[Any]) -> Self:
        self._rows = value
        return self

    def caption(self, value: str) -> Self:
        """
        What the table is, read before it and shown above it.
        """
        self._props["caption"] = value
        return self

    def group_by(self, key: RowKey) -> Self:
        """
        Split the rows into sections, each titled with the value key reads
        from its rows, as a column's key would. The rows have to arrive in
        that order: a value that comes back later opens a section of its own.
        A blank value raises, because a section needs a name; a callable can
        give those rows one.
        """
        self._props["group_by"] = key
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

    def _bulk_actions(self, key: str, *values: ComponentType) -> Self:
        """
        What to do with picked rows, and a checkbox at the start of every row
        to pick them with. The two come together, because a checkbox with
        nothing to do is not worth drawing.

        Each checkbox submits what key resolves to for its row, and is named
        after the row's first cell, so a screen reader hears "Select
        INV-2050" rather than a pk nobody can see. The actions sit in a bar
        that floats at the foot of the page once a row is picked, inside the
        table's Alpine scope, so an expression in one can read selected, the
        list of values the checkboxes carry.
        """
        self._props["selectable"] = key
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
        declaration: _Declaration | None = self._get_prop("declaration")
        if declaration is not None:
            # A copy without the declaration goes in, or drawing it would
            # hand it straight back to the declaration again.
            return _Drawn(declaration, self._undeclared())

        if self._get_prop("selectable") is not None and "id" not in self._attrs:
            # Every row's ids are built from the table's, and a fallback
            # shared by two tables on one page would make them collide.
            raise ValueError(
                "A DataTable with selectable rows needs an id to build its "
                "rows' ids from. Draw it with DataTable.from_state(), which "
                "sets one."
            )

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
        if toolbar := self._get_prop("toolbar", ()):
            table.toolbar(html.div(*toolbar, class_=_BAND))
        if self._get_prop("selectable") is not None:
            table.x_data("hueTableSelection")
            # The bar floats over the page instead of taking a band in the
            # frame, so picking rows never moves them.
            table._floating(*self._bulk_bar())

        if under := self._get_prop("under", ()):
            table.under(html.div(*under, class_=_BAND_BOTTOM))

    def _undeclared(self) -> DataTable:
        table = DataTable()
        table._props = {k: v for k, v in self._props.items() if k != "declaration"}
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
                # The order is a place, as a page or a filter is.
                **swap(target),
            )
        )

    def _bulk_bar(self) -> tuple[ComponentType, ...]:
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
        clear = (
            Button()
            .variant("ghost")
            .size("xs")
            .icon_only("Clear selection")
            .content(HueIcon("x"))
            .aria_keyshortcuts("Escape")
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
        if self._get_prop("selectable") is None:
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

    def _select_cell(self, row: Any, line: str, name_id: str | None) -> ComponentType:
        value = str(resolve_value(row, self._get_prop("selectable")))
        box_id = f"{line}-select"
        box = (
            Checkbox()
            .name(SELECTED)
            .id(box_id)
            .value(value)
            .label("Select")
            .hidden_label()
            .x_model(unsafe("selected"))
            .data("hue-row-select", "")
        )
        if name_id is not None:
            # "Select" and then whatever the row's first cell shows. The
            # identifier is usually a pk nobody can see, so naming the box
            # after it would read out a number tied to nothing on screen.
            box.aria_labelledby(f"{box_id} {name_id}")
        # Named rather than wrapped: the form is an empty element in the
        # frame, because a form around the band above the rows would
        # swallow the search box, which is a form of its own.
        if (posts_to := form_id(self._attrs.get("id"))) is not None:
            box.form(posts_to)
        return TableCell().class_(_SELECT_COLUMN).content(box)

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
        rows = [self._row(row, index) for index, row in enumerate(self._rows)]
        key: RowKey | None = self._get_prop("group_by")
        if key is None:
            return (TableBody().content(*rows),)
        # The title spans the checkboxes too, so it reads as the start of a
        # section rather than as a row of it.
        width = len(self._columns) + (self._get_prop("selectable") is not None)
        return tuple(
            TableBody()
            .title(_Value(name), colspan=width)
            .content(*[line for _, line in section])
            for name, section in groupby(
                zip(self._rows, rows, strict=True),
                key=lambda pair: _section(pair[0], key),
            )
        )

    def _row(self, row: Any, index: int) -> ComponentType:
        cells = [self._cell(column, row) for column in self._columns]
        if (key := self._get_prop("selectable")) is None:
            return TableRow().content(*cells)
        # By position rather than by the row's value, which can be anything
        # and is not safe to spell an id with. Under the table's id, which
        # _render requires, so two tables on a page keep apart.
        line = f"{self._attrs['id']}-row-{index}"
        name_id = f"{line}-name" if cells else None
        if name_id is not None:
            cells[0].id(name_id)
        value = json.dumps(str(resolve_value(row, key)))
        return (
            TableRow()
            .content(self._select_cell(row, line, name_id), *cells)
            .x_bind("aria-selected", unsafe(f"isSelected({value})"))
        )

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

    def _cell(self, column: Column, row: Any) -> TableCell:
        content = (
            column.render(row)
            if column.render is not None
            else _Value(resolve_value(row, column.key))
        )
        return TableCell().align(column.align).content(content)


def _section(row: Any, key: RowKey) -> Any:
    """
    The name of the section a row falls in. A blank one raises, since a
    screen reader would announce the section as nothing.
    """
    value = resolve_value(row, key)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(
            f"A row has no value to be grouped by ({value!r}), and a section "
            f"needs a name. Group by a callable that gives these rows one."
        )
    return value


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
