from __future__ import annotations

from typing import (
    ClassVar,
    Literal,
)

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classes_if_else, classnames

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

# Alpine AJAX marks what it is about to replace aria-busy for as long as the
# request runs. Dimmed, so a slow query reads as working rather than as a
# click that did nothing; the attribute itself tells a screen reader.
_LOADING = (
    "transition-opacity duration-150 aria-busy:opacity-60 aria-busy:cursor-progress"
)

# The one band that scrolls, and the only place a table is ever too wide.
_BODY_BAND = "overflow-x-auto"


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
                class_=_LOADING,
                # Refreshed by every response that carries it, not only the
                # ones aimed at it. Each read loads the whole page, so another
                # table's links and carried state keep up with this one's.
                **({"x-sync": ""} if frame_id else {}),
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
            class_=classnames(_FRAME, _LOADING),
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
