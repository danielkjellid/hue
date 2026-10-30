"""
Promises of the frames a table or a pager sits in: Pagination filling its
row, a Card and a Panel clipping what runs past their edges, and a bulk
action's confirmation.
"""

from htmy import html
from playwright.sync_api import expect

from hue.datatable import BulkAction, build_datatable_state
from hue.ui import (
    Card,
    CardBody,
    Column,
    DataTable,
    Dialog,
    Pagination,
    Panel,
)
from tests.browser.conftest import Show
from tests.browser.test_datatable import _Router
from tests.browser.test_sticky_bar_promises import _tick_first

_BAR = '[aria-label="Selected rows"]'


def _pager() -> Pagination:
    return (
        Pagination()
        .id("pages")
        .page(4)
        .total_pages(9)
        .total_records(90)
        .href(lambda n: f"/?page={n}")
    )


# Pagination.


def test_the_pager_fills_its_row_with_the_count_at_the_start(show: Show) -> None:
    page = show(html.div(_pager(), id="row"), width=1280)
    box = page.evaluate(
        "(() => { const row = document.getElementById('row').getBoundingClientRect();"
        " const bar = document.getElementById('pages').getBoundingClientRect();"
        " const nav = document.querySelector('nav').getBoundingClientRect();"
        " return [row.left, row.right, bar.left, bar.right, nav.right] })()"
    )
    row_left, row_right, bar_left, bar_right, nav_right = box
    assert (bar_left, bar_right) == (row_left, row_right)
    # The steps sit against the far edge, across from the count.
    assert abs(nav_right - row_right) < 1


# Card.


def test_a_card_clips_what_runs_past_its_edge(show: Show) -> None:
    page = show(
        Card().id("card").content(CardBody().content(html.div(style="width: 2000px"))),
        width=390,
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert page.evaluate(
        "document.getElementById('card').getBoundingClientRect().right <= 390"
    )


def test_cards_in_a_grid_share_the_row_equally(show: Show) -> None:
    page = show(
        html.div(
            Card().id("one").content(CardBody().content("One")),
            Card().id("two").content(CardBody().content("Two")),
            class_="grid gap-4 md:grid-cols-2",
        ),
        width=1280,
    )
    widths = page.evaluate(
        "['one', 'two'].map((id) =>"
        " document.getElementById(id).getBoundingClientRect().width)"
    )
    assert abs(widths[0] - widths[1]) < 1


# Panel.


def test_a_panel_without_padding_clips_a_table_to_its_frame(show: Show) -> None:
    page = show(
        Panel()
        .id("panel")
        .label("Wide")
        .padding("none")
        .content(html.div(style="width: 2000px; height: 40px")),
        width=390,
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert page.evaluate(
        "document.getElementById('panel').getBoundingClientRect().right <= 390"
    )


# A bulk action's confirmation.


def _confirmed() -> DataTable:
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=[Column("invoice", "Invoice"), Column("amount", "Amount")],
            rows=lambda request, asked: [
                {"invoice": f"INV-{n:03}", "amount": str(n)} for n in range(3)
            ],
            identifier="invoice",
            actions={
                "delete": BulkAction(
                    "Delete",
                    lambda request, ids: None,
                    variant="danger",
                    confirm=Dialog().destructive().title("Delete these invoices?"),
                )
            },
            page_size=3,
        )
    )


def test_escape_closes_the_confirmation_then_clears_the_selection(
    show: Show,
) -> None:
    page = show(_confirmed(), width=1280)
    _tick_first(page)
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    dialog = page.get_by_role("alertdialog")
    expect(dialog).to_be_visible()
    # Once the dialog holds focus, as it does by the time anyone can press a
    # key.
    page.wait_for_function(
        "() => document.activeElement?.closest('[role=alertdialog]') !== null"
    )
    page.keyboard.press("Escape")
    expect(dialog).to_be_hidden()
    # The selection outlives the first Escape, and focus is back on Delete.
    expect(page.locator(_BAR)).to_be_visible()
    expect(page.locator(_BAR).get_by_role("button", name="Delete")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.locator(_BAR)).to_be_hidden()


def test_cancel_closes_the_confirmation_and_keeps_the_selection(show: Show) -> None:
    page = show(_confirmed(), width=1280)
    _tick_first(page)
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    page.get_by_role("alertdialog").get_by_role("button", name="Cancel").click()
    expect(page.get_by_role("alertdialog")).to_be_hidden()
    expect(page.locator(_BAR)).to_contain_text("1 selected")


def test_the_confirmation_posts_the_picked_rows(show: Show) -> None:
    page = show(_confirmed(), width=1280)
    _tick_first(page)
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    with page.expect_request(lambda request: request.method == "POST") as sent:
        page.get_by_role("alertdialog").get_by_role("button", name="Delete").click()
    assert "INV-000" in (sent.value.post_data or "")
    expect(page.get_by_role("alertdialog")).to_be_hidden()
