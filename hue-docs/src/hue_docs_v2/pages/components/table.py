from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import (
    DataTable,
    Empty,
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableFooter,
    TableHead,
    TableHeader,
    TableRow,
)

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def team() -> Table:
    return Table().content(
        TableHeader().content(
            TableRow().content(
                TableHead().content("Name"),
                TableHead().content("Email"),
                TableHead().content("Role"),
            )
        ),
        TableBody().content(
            TableRow().content(
                TableCell().content("Ada Lovelace"),
                TableCell().content("ada@example.com"),
                TableCell().content("Admin"),
            ),
            TableRow().content(
                TableCell().content("Alan Turing"),
                TableCell().content("alan@example.com"),
                TableCell().content("Member"),
            ),
        ),
    )


# Anatomy


def caption_and_footer() -> Table:
    return Table().content(
        TableCaption().content("Invoices, September 2026"),
        TableHeader().content(
            TableRow().content(
                TableHead().content("Invoice"),
                TableHead().content("Method"),
                TableHead().align("end").content("Amount"),
            )
        ),
        TableBody().content(
            TableRow().content(
                TableCell().content("INV-2048"),
                TableCell().content("Card"),
                TableCell().align("end").content("250.00"),
            ),
            TableRow().content(
                TableCell().content("INV-2049"),
                TableCell().content("Bank transfer"),
                TableCell().align("end").content("1,350.00"),
            ),
        ),
        TableFooter().content(
            TableRow().content(
                TableCell().colspan(2).content("Total"),
                TableCell().align("end").content("1,600.00"),
            )
        ),
    )


def sections() -> Table:
    return Table().content(
        TableHeader().content(
            TableRow().content(
                TableHead().content("Guest"),
                TableHead().align("end").content("Nights"),
            )
        ),
        TableBody()
        .title("October 2026", colspan=2)
        .content(
            TableRow().content(
                TableCell().content("Ingrid Haugen"),
                TableCell().align("end").content("2"),
            )
        ),
        TableBody()
        .title("November 2026", colspan=2)
        .content(
            TableRow().content(
                TableCell().content("Ada Lovelace"),
                TableCell().align("end").content("3"),
            ),
            TableRow().content(
                TableCell().content("Alan Turing"),
                TableCell().align("end").content("2"),
            ),
        ),
    )


def row_headers() -> Table:
    return Table().content(
        TableHeader().content(
            TableRow().content(
                TableHead().content("Plan"),
                TableHead().align("end").content("Seats"),
                TableHead().align("end").content("Price"),
            )
        ),
        TableBody().content(
            TableRow().content(
                TableHead().scope("row").content("Pro"),
                TableCell().align("end").content("10"),
                TableCell().align("end").content("49.00"),
            ),
            TableRow().content(
                TableHead().scope("row").content("Scale"),
                TableCell().align("end").content("50"),
                TableCell().align("end").content("199.00"),
            ),
        ),
    )


def column_groups() -> Table:
    return Table().content(
        TableHeader().content(
            TableRow().content(
                TableCell(),
                TableHead()
                .scope("colgroup")
                .colspan(2)
                .align("center")
                .content("2025"),
                TableHead()
                .scope("colgroup")
                .colspan(2)
                .align("center")
                .content("2026"),
            ),
            TableRow().content(
                TableHead().content("Region"),
                TableHead().align("end").content("H1"),
                TableHead().align("end").content("H2"),
                TableHead().align("end").content("H1"),
                TableHead().align("end").content("H2"),
            ),
        ),
        TableBody().content(
            TableRow().content(
                TableHead().scope("row").content("Nordics"),
                TableCell().align("end").content("1.2M"),
                TableCell().align("end").content("1.4M"),
                TableCell().align("end").content("1.6M"),
                TableCell().align("end").content("1.9M"),
            ),
        ),
    )


# Alignment


def start_center_end() -> Table:
    return Table().content(
        TableHeader().content(
            TableRow().content(
                TableHead().align("start").content("Start"),
                TableHead().align("center").content("Center"),
                TableHead().align("end").content("End"),
            )
        ),
        TableBody().content(
            TableRow().content(
                TableCell().align("start").content("INV-2048"),
                TableCell().align("center").content("Paid"),
                TableCell().align("end").content("1,200.00"),
            ),
            TableRow().content(
                TableCell().align("start").content("INV-2049"),
                TableCell().align("center").content("Due"),
                TableCell().align("end").content("84.50"),
            ),
        ),
    )


# States


def selected_row() -> Table:
    return Table().content(
        TableHeader().content(
            TableRow().content(
                TableHead().content("Invoice"),
                TableHead().sorted("descending").align("end").content("Amount"),
            )
        ),
        TableBody().content(
            TableRow().content(
                TableCell().content("INV-2050"),
                TableCell().align("end").content("2,190.00"),
            ),
            TableRow()
            .selected()
            .content(
                TableCell().content("INV-2048"),
                TableCell().align("end").content("1,200.00"),
            ),
            TableRow().content(
                TableCell().content("INV-2049"),
                TableCell().align("end").content("840.00"),
            ),
        ),
    )


def compact() -> Table:
    return (
        Table()
        .compact()
        .content(
            TableHeader().content(
                TableRow().content(
                    TableHead().content("Invoice"),
                    TableHead().sorted("ascending").align("end").content("Amount"),
                )
            ),
            TableBody().content(
                TableRow().content(
                    TableCell().content("INV-2049"),
                    TableCell().align("end").content("840.00"),
                ),
                TableRow().content(
                    TableCell().content("INV-2048"),
                    TableCell().align("end").content("1,200.00"),
                ),
                TableRow().content(
                    TableCell().content("INV-2050"),
                    TableCell().align("end").content("2,190.00"),
                ),
            ),
        )
    )


# Empty


def empty_footer() -> Table:
    return (
        Table()
        .content(
            TableHeader().content(
                TableRow().content(
                    TableHead().content("Invoice"),
                    TableHead().align("end").content("Amount"),
                )
            )
        )
        .footer(
            Empty()
            .compact()
            .title("No invoices yet")
            .description("Invoices you send appear here.")
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Building a Table"),
        pr.p(
            "`Table` is the frame, and its parts mirror the HTML elements one for "
            "one: `TableCaption`, `TableHeader`, `TableBody`, `TableFooter`, "
            "`TableRow`, `TableHead` and `TableCell`. Put the parts in `content()` in "
            "the order the elements go."
        ),
        pr.code(
            "Table().content(\n"
            "    TableHeader().content(\n"
            '        TableRow().content(TableHead().content("Name"), '
            'TableHead().content("Email")),\n'
            "    ),\n"
            "    TableBody().content(\n"
            "        *[\n"
            "            TableRow().content(TableCell().content(user.name), "
            "TableCell().content(user.email))\n"
            "            for user in users\n"
            "        ]\n"
            "    ),\n"
            ")"
        ),
        pr.p(
            "For a list of records, `DataTable` builds all of this from a column "
            "definition and the rows, and adds loading, empty and error states. "
            "Reach for `Table` when the layout is your own: row headers, column "
            "groups, a totals row."
        ),
        pr.h2("Table frame and bands"),
        pr.p(
            "The frame owns the border and the radius. `toolbar()` adds a band "
            "above the table inside the frame, `under()` a band along the bottom, "
            "and `footer()` is where an empty or error state goes, under the "
            "header. Only the band holding the table scrolls sideways, so a "
            "popover opened from the toolbar is not clipped. An id set on the "
            "`Table` goes on the frame, and the region holding the rows and "
            "whatever stands in for them gets the same id with `-rows` on the end, "
            "so a response can replace the rows alone."
        ),
        pr.p(
            "`footer()` is not `TableFooter`. `TableFooter` is a `tfoot` row group "
            "inside the table, for a total or a summary of the rows above it."
        ),
        pr.h2("Table columns, sections and density"),
        pr.p(
            '`align()` on `TableHead` and `TableCell` takes `"start"`, `"center"` or '
            '`"end"`. `"end"` also switches the cell to tabular figures, so the '
            "digits line up down a column of numbers. Set it on the header and "
            "on every cell of the column. Cells wrap rather than truncate."
        ),
        pr.p(
            '`TableHead` is scoped to its column. `scope("row")` makes it the header '
            'of its row, and `scope("colgroup")` with `colspan()` heads a group of '
            "columns."
        ),
        pr.p(
            "A table can hold several `TableBody` groups. `title()` on each turns it "
            "into a section that opens with a row naming it, as a `rowgroup` "
            "header, so a screen reader announces the section with each cell in "
            "it. `colspan` is the number of columns, so the title runs the width "
            "of the table, and a blank title raises."
        ),
        pr.p(
            "`compact()` on the `Table` sets the row height of every cell at once, so "
            "no two cells can disagree. The side padding stays the same."
        ),
        pr.h2("Table row and header states"),
        pr.p(
            "`selected()` on a `TableRow` sets `aria-selected`, which is what a screen "
            'reader reads and what tints the row. `sorted("ascending")` or '
            '`sorted("descending")` on a `TableHead` sets `aria-sort`. It draws no '
            "arrow, so put an icon in the header if the order should show."
        ),
    )


PAGE = ComponentPage(
    Table,
    lede=(
        "A `Table` is a styled HTML table built from parts that mirror the "
        "elements one for one. Use it when the layout is your own; for a list "
        "of records, `DataTable` builds the table from columns and rows."
    ),
    usage=_usage,
    panels=[
        panel("Live", team, layout="stack"),
        panel(
            "Anatomy",
            caption_and_footer,
            sections,
            row_headers,
            column_groups,
            layout="stack",
        ),
        panel(
            "Alignment",
            start_center_end,
            layout="stack",
            hint='`"end"` also lines up the digits',
        ),
        panel("States", selected_row, compact, layout="stack"),
        panel("Empty", empty_footer, layout="stack", hint="`footer()` holds it"),
    ],
    notes=[
        Note(
            "a11y",
            "Every part renders its own element (`table`, `caption`, `thead`, "
            "`tbody`, `tfoot`, `tr`, `th`, `td`), so a screen reader gets real table "
            "navigation.",
        ),
        Note(
            "a11y",
            '`TableHead` renders `scope="col"` unless `scope()` says otherwise. A '
            "section title from `TableBody.title()` is a `th` with "
            '`scope="rowgroup"`.',
        ),
        Note(
            "a11y",
            "`TableCaption` names the table and is read before it. It renders "
            "above the table.",
        ),
        Note(
            "note",
            "`sorted()` sets `aria-sort` on one header. Set it on one header "
            "only, because ARIA cannot say which of two sorted columns came first.",
        ),
        Note(
            "warn",
            "`TableRow().selected()` only tints the row and sets `aria-selected`. "
            "It does not pick or submit the row.",
        ),
    ],
    parts=[
        TableCaption,
        TableHeader,
        TableBody,
        TableFooter,
        TableRow,
        TableHead,
        TableCell,
    ],
    related=[DataTable],
)
