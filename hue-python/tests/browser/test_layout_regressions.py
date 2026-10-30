"""
Regressions in the frames a table or a pager sits in: a pager in a parent
sized to it, and a Card or a Panel in a row or holding a long table.
"""

import pytest
from htmy import html

from hue.datatable import BulkAction, build_datatable_state
from hue.ui import Card, CardBody, Column, DataTable, Stack
from tests.browser.conftest import Show
from tests.browser.test_data_navigation_promises import _coarse
from tests.browser.test_datatable import _Router
from tests.browser.test_layout_promises import _pager

# Pagination.


# A parent sized to its content, which gives the pager the width of its
# own content rather than none.
_SHRINKING = {
    "fit": lambda pager: html.div(pager, class_="w-fit"),
    "centred": lambda pager: html.div(pager, class_="mx-auto w-fit"),
    "pushed": lambda pager: html.div(html.div(pager, class_="ml-auto"), class_="flex"),
    "card": lambda pager: html.div(
        Card().content(CardBody().content(pager)), class_="flex"
    ),
}


@pytest.mark.parametrize("parent", list(_SHRINKING))
@pytest.mark.parametrize("width", [390, 1440])
def test_a_pager_keeps_its_width_in_a_parent_sized_to_it(
    show: Show, parent: str, width: int
) -> None:
    page = show(_SHRINKING[parent](_pager()), width=width)
    if width == 390:
        _coarse(page)
    assert page.evaluate("document.querySelector('nav').offsetWidth") > 200
    tops = page.evaluate(
        "new Set([...document.querySelectorAll('nav > *')]"
        ".filter((child) => child.checkVisibility())"
        ".map((child) => Math.round(child.getBoundingClientRect().top))).size"
    )
    assert tops == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width


# Card.


def _wide(key: str = "invoices", rows: int = 3) -> DataTable:
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key=key,
            columns=[
                Column("invoice", "Invoice"),
                *[Column(f"c{n}", f"Column {n}") for n in range(8)],
            ],
            rows=lambda request, asked: [
                {"invoice": f"INV-{n:03}", **{f"c{c}": "wide value" for c in range(8)}}
                for n in range(rows)
            ],
            identifier="invoice",
            actions={"archive": BulkAction("Archive", lambda request, ids: None)},
            page_size=rows,
        )
    )


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("layout", ["flex", "grid"])
def test_cards_beside_each_other_shrink_around_a_wide_table(
    show: Show, width: int, layout: str
) -> None:
    cards = (
        Card().id("one").class_("flex-1").content(CardBody().content(_wide())),
        Card().id("two").class_("flex-1").content(CardBody().content("Two")),
    )
    row = (
        Stack().horizontal().content(*cards)
        if layout == "flex"
        else html.div(*cards, class_="grid grid-cols-2 gap-4")
    )
    page = show(row, width=width)
    if width == 390:
        _coarse(page)
    assert page.evaluate("document.documentElement.scrollWidth") <= width
    widths = page.evaluate(
        "['one', 'two'].map((id) =>"
        " document.getElementById(id).getBoundingClientRect().width)"
    )
    assert abs(widths[0] - widths[1]) < 1
    # The table scrolls sideways in its own band instead.
    assert page.evaluate(
        "(() => { const band = document.querySelector('#invoices table')"
        ".parentElement; return band.scrollWidth > band.clientWidth })()"
    )
