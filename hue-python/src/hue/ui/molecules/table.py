from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Literal, Mapping, Sequence

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.atoms.text import Text
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type CellAlign = Literal["left", "center", "right"]
type HeadScope = Literal["col", "row", "colgroup", "rowgroup"]

_ALIGN_CLASSES: dict[CellAlign, str] = {
    "left": "text-left",
    "center": "text-center",
    "right": "text-right",
}


class Table(ChainableComponent):
    """
    An accessible data table styled with the design system.

    Composed from subcomponents — ``TableHeader``, ``TableBody``,
    ``TableFooter``, ``TableRow``, ``TableHead``, ``TableCell``, and
    ``TableCaption`` — that mirror the native HTML table elements. The
    ``<table>`` is wrapped in a horizontally scrollable container, and ``.id()``
    / ``.class_()`` / the ARIA and Alpine modifiers target the table itself.

    For the common case of rendering a list of records, reach for ``DataTable``,
    which builds these primitives from a column definition and your data.

    Example::

        Table().content(
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
            ),
        )
    """

    category = "Data"

    @classmethod
    def example(cls) -> Self:
        """A representative instance, used by the docs site for previews."""
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

    def _render(self, context: HueContext) -> Component:
        classes = classnames(
            "w-full caption-bottom text-sm",
            self._get_prop("class_"),
        )
        return html.div(
            html.table(
                *self._children,
                class_=classes,
                **self._get_base_html_attrs(),
            ),
            class_="relative w-full overflow-x-auto",
        )


class TableHeader(ChainableComponent):
    """The ``<thead>`` group of a ``Table``."""

    category = "Data"

    def _render(self, context: HueContext) -> Component:
        classes = classnames(
            "[&_tr]:border-b [&_tr]:border-surface-200",
            self._get_prop("class_"),
        )
        return html.thead(
            *self._children,
            class_=classes,
            **self._get_base_html_attrs(),
        )


class TableBody(ChainableComponent):
    """The ``<tbody>`` group of a ``Table``."""

    category = "Data"

    def _render(self, context: HueContext) -> Component:
        classes = classnames(
            "[&_tr:last-child]:border-0",
            self._get_prop("class_"),
        )
        return html.tbody(
            *self._children,
            class_=classes,
            **self._get_base_html_attrs(),
        )


class TableFooter(ChainableComponent):
    """The ``<tfoot>`` group of a ``Table``."""

    category = "Data"

    def _render(self, context: HueContext) -> Component:
        classes = classnames(
            "border-t border-surface-200 bg-surface-50 font-medium",
            self._get_prop("class_"),
        )
        return html.tfoot(
            *self._children,
            class_=classes,
            **self._get_base_html_attrs(),
        )


class TableRow(ChainableComponent):
    """
    A ``<tr>`` row.

    Carries the hover style and a ``data-[state=selected]`` hook: a future
    selection feature can bind ``data-state`` (via Alpine) to highlight selected
    rows without changing this markup.
    """

    category = "Data"

    def _render(self, context: HueContext) -> Component:
        classes = classnames(
            "border-b border-surface-200 transition-colors",
            "hover:bg-surface-50 data-[state=selected]:bg-surface-100",
            self._get_prop("class_"),
        )
        return html.tr(
            *self._children,
            class_=classes,
            **self._get_base_html_attrs(),
        )


class TableHead(ChainableComponent):
    """
    A ``<th>`` header cell.

    Defaults to ``scope="col"`` for accessibility; use ``.scope()`` to mark a
    row header instead. ``.align()`` sets text alignment and ``.colspan()`` the
    column span.
    """

    category = "Data"

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
        align: CellAlign = self._get_prop("align", "left")
        classes = classnames(
            "h-10 px-2 align-middle font-medium whitespace-nowrap",
            "text-surface-900 [&:has([role=checkbox])]:pr-0",
            _ALIGN_CLASSES[align],
            self._get_prop("class_"),
        )
        return html.th(
            *self._children,
            class_=classes,
            scope=self._get_prop("scope", "col"),
            colspan=self._get_prop("colspan"),
            **self._get_base_html_attrs(),
        )


class TableCell(ChainableComponent):
    """
    A ``<td>`` data cell.

    ``.align()`` sets text alignment and ``.colspan()`` the column span.
    """

    category = "Data"

    def align(self, value: CellAlign) -> Self:
        self._props["align"] = value
        return self

    def colspan(self, value: int) -> Self:
        self._props["colspan"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        align: CellAlign = self._get_prop("align", "left")
        classes = classnames(
            "p-2 align-middle whitespace-nowrap",
            "text-surface-900 [&:has([role=checkbox])]:pr-0",
            _ALIGN_CLASSES[align],
            self._get_prop("class_"),
        )
        return html.td(
            *self._children,
            class_=classes,
            colspan=self._get_prop("colspan"),
            **self._get_base_html_attrs(),
        )


class TableCaption(ChainableComponent):
    """A ``<caption>`` rendered below the table."""

    category = "Data"

    def _render(self, context: HueContext) -> Component:
        classes = classnames(
            "mt-4 text-sm text-surface-500",
            self._get_prop("class_"),
        )
        return html.caption(
            *self._children,
            class_=classes,
            **self._get_base_html_attrs(),
        )


@dataclass(frozen=True)
class Column:
    """
    A column definition for ``DataTable``.

    ``accessor`` resolves a row's value: either a key / dotted path into the
    (possibly nested) record (e.g. ``"address.city"``), or a callable taking the
    row and returning a value. ``cell`` optionally renders custom cell content
    from the row instead of the resolved value. ``align`` sets the text
    alignment of both the header and body cells.
    """

    header: str
    accessor: str | Callable[[Mapping[str, Any]], Any]
    cell: Callable[[Mapping[str, Any]], ComponentType] | None = None
    align: CellAlign = "left"


def _resolve(
    row: Mapping[str, Any],
    accessor: str | Callable[[Mapping[str, Any]], Any],
) -> Any:
    """Resolve a column's value from a row via a callable or (dotted) key path."""
    if callable(accessor):
        return accessor(row)

    value: Any = row
    for part in accessor.split("."):
        if not isinstance(value, Mapping):
            raise ValueError(
                f"Cannot resolve accessor {accessor!r}: "
                f"{part!r} is not a key of a mapping."
            )
        value = value[part]
    return value


def _stringify(value: Any) -> str:
    """Render a resolved scalar value as text, erroring on complex values."""
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    raise ValueError(
        f"Column value {value!r} is not a scalar — provide a `cell` render function."
    )


class DataTable(ChainableComponent):
    """
    A ``Table`` built from a column definition and a list of records.

    Pass ``.columns()`` (a list of ``Column``) and ``.data()`` (a sequence of
    mappings); ``DataTable`` emits the ``Table`` primitives, one body row per
    record. A column's value comes from its ``cell`` render function when set,
    otherwise from its ``accessor``. When ``data`` is empty an accessible
    empty-state row is shown. ``.caption()`` adds a caption below the table.

    Note: row selection and pagination are intentionally not implemented yet.
    The primitives already carry the hooks for them — the ``data-[state=selected]``
    style and ``[role=checkbox]`` cell padding on ``TableRow`` / ``TableCell``
    support a future Alpine-tracked selection column, and pagination is intended
    to fetch pages server-side via Alpine AJAX (``x-merge`` swapping the
    ``<tbody>``).

    Example::

        DataTable().columns(
            [
                Column("Name", accessor="name"),
                Column("Email", accessor="email"),
            ]
        ).data(
            [
                {"name": "Ada Lovelace", "email": "ada@example.com"},
                {"name": "Alan Turing", "email": "alan@example.com"},
            ]
        )
    """

    category = "Data"

    def __init__(self) -> None:
        super().__init__()
        self._columns: list[Column] = []
        self._data: Sequence[Mapping[str, Any]] = []

    @classmethod
    def example(cls) -> Self:
        """A representative instance, used by the docs site for previews."""
        return (
            cls()
            .columns(
                [
                    Column("Name", accessor="name"),
                    Column("Email", accessor="email"),
                ]
            )
            .data(
                [
                    {"name": "Ada Lovelace", "email": "ada@example.com"},
                    {"name": "Alan Turing", "email": "alan@example.com"},
                ]
            )
        )

    def columns(self, value: list[Column]) -> Self:
        self._columns = value
        return self

    def data(self, value: Sequence[Mapping[str, Any]]) -> Self:
        self._data = value
        return self

    def caption(self, value: str) -> Self:
        self._props["caption"] = value
        return self

    def _render_head(self) -> ComponentType:
        return TableHeader().content(
            TableRow().content(
                *[
                    TableHead().align(column.align).content(column.header)
                    for column in self._columns
                ]
            )
        )

    def _render_cell(self, column: Column, row: Mapping[str, Any]) -> ComponentType:
        if column.cell is not None:
            content: ComponentType = column.cell(row)
        else:
            content = _stringify(_resolve(row, column.accessor))
        return TableCell().align(column.align).content(content)

    def _render_body(self) -> ComponentType:
        if not self._data:
            return TableBody().content(
                TableRow().content(
                    TableCell()
                    .colspan(len(self._columns))
                    .align("center")
                    .role("status")
                    .content(Text("No results.").muted())
                )
            )

        return TableBody().content(
            *[
                TableRow().content(
                    *[self._render_cell(column, row) for column in self._columns]
                )
                for row in self._data
            ]
        )

    def _render(self, context: HueContext) -> Component:
        caption = self._get_prop("caption")
        table = Table().content(
            self._render_head(),
            self._render_body(),
            render_if(caption, lambda c: TableCaption().content(c)),
        )

        class_ = self._get_prop("class_")
        if class_:
            table = table.class_(class_)
        for key, value in self._attrs.items():
            table._attrs.setdefault(key, value)

        return table._render(context)
