"""
Regressions in the frames a table or a pager sits in: a pager in a parent
sized to it, and a Card or a Panel in a row or holding a long table.
"""

import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.datatable import BulkAction, build_datatable_state
from hue.ui import Card, CardBody, Column, DataTable, Panel, Stack
from tests.browser.conftest import Show
from tests.browser.test_data_navigation_promises import _coarse
from tests.browser.test_datatable import _Router, _table
from tests.browser.test_layout_promises import _BAR, _confirmed, _pager
from tests.browser.test_sticky_bar_promises import _in_reach, _long, _tick_first

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


# Panel.


@pytest.mark.parametrize(
    ("width", "theme"), [(1440, "light"), (390, "dark")], ids=["desk", "phone"]
)
def test_a_long_tables_bar_is_in_reach_in_a_panel(
    show: Show, width: int, theme: str
) -> None:
    page = show(
        Panel().label("Invoices").padding("none").content(_long()),
        width=width,
        height=700,
        theme=theme,
    )
    if width == 390:
        _coarse(page)
    _tick_first(page)
    page.mouse.wheel(0, 600)
    page.wait_for_function("() => scrollY >= 600")
    assert _in_reach(page)


def test_a_panel_beside_another_shrinks_around_a_wide_table(show: Show) -> None:
    page = show(
        Stack()
        .horizontal()
        .content(
            Panel().id("one").class_("flex-1").padding("none").content(_wide()),
            Panel().id("two").class_("flex-1").content("Two"),
        ),
        width=390,
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


# A bulk action's confirmation.


@pytest.mark.parametrize("width", [390, 1440])
def test_a_confirm_from_the_bar_covers_a_sticky_header(show: Show, width: int) -> None:
    page = show(
        html.header(
            html.a("Home", href="/elsewhere"),
            id="head",
            class_="sticky top-0 z-30 h-14 bg-surface",
        ),
        _confirmed(),
        width=width,
    )
    if width == 390:
        _coarse(page)
    _tick_first(page)
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    expect(page.get_by_role("alertdialog")).to_be_visible()
    assert page.evaluate(
        "(() => { const box = document.getElementById('head').getBoundingClientRect();"
        " const hit = document.elementFromPoint(box.left + 20, box.top + 20);"
        " return document.querySelector('[role=alertdialog]').parentElement"
        ".contains(hit) })()"
    )


# Hidden columns.


def test_the_columns_panel_keeps_the_last_column_showing(show: Show) -> None:
    table = DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=[Column("invoice", "Invoice"), Column("amount", "Amount")],
            rows=lambda request, asked: [{"invoice": "INV-1", "amount": "1"}],
            hideable=["invoice", "amount"],
        )
    )
    page = show(table)
    page.get_by_role("button", name="Columns").click()
    invoice = page.get_by_role("checkbox", name="Invoice")
    amount = page.get_by_role("checkbox", name="Amount")
    invoice.uncheck()
    expect(amount).to_be_checked()
    expect(amount).to_be_disabled()
    invoice.check()
    expect(amount).to_be_enabled()


# The empty search.


def _search_sent_by_enter(page: Page) -> str:
    field = page.get_by_role("searchbox")
    field.focus()
    with page.expect_request(lambda request: request.method == "GET") as sent:
        page.keyboard.press("Enter")
    return sent.value.url


def test_enter_in_an_empty_search_sends_no_query(show: Show) -> None:
    page = show(_table("invoices"))
    assert "invoices-q" not in _search_sent_by_enter(page)
    expect(page.get_by_role("searchbox")).to_have_attribute("name", "invoices-q")


def test_enter_in_a_cleared_search_sends_no_query(show: Show) -> None:
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.fill("2050")
    page.wait_for_url("**invoices-q=2050**")
    field.fill("")
    page.wait_for_function("() => !location.search.includes('2050')")
    assert "invoices-q" not in _search_sent_by_enter(page)
    assert "invoices-q" not in page.evaluate("location.search")
    # A search typed next is still sent under its name.
    field.fill("2048")
    page.wait_for_url("**invoices-q=2048**")
