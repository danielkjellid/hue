"""
A review of the layout fixes: the pager folding by screen width, a Card and
a Panel shrinking in a row, the bar rising while its confirmation is open,
the last column that cannot be hidden, and the empty search left unnamed.
"""

from typing import Any

import pytest
from htmy import html
from playwright.sync_api import Page, Route, expect

from hue.datatable import BulkAction, build_datatable_state
from hue.ui import (
    Card,
    CardBody,
    CardHeader,
    CardMedia,
    Column,
    DataTable,
    Dialog,
    LineChart,
    Pagination,
    Panel,
    ScrollArea,
    Stack,
)
from tests.browser.conftest import Show
from tests.browser.test_data_navigation_promises import _coarse
from tests.browser.test_datatable import _Router, _table
from tests.browser.test_sticky_bar_promises import _tick_first

_BAR = '[aria-label="Selected rows"]'

# Pagination.


def _pager(**extra: Any) -> Pagination:
    pager = (
        Pagination()
        .id("pages")
        .page(4)
        .total_pages(9)
        .total_records(90)
        .href(lambda n: f"/?page={n}")
    )
    if extra.get("sizes"):
        pager.page_sizes([10, 25, 50])
    return pager


# The steps still showing, each as its box.
_STEPS = """() => [...document.querySelectorAll('nav > *')]
    .filter((step) => step.checkVisibility())
    .map((step) => { const b = step.getBoundingClientRect();
        return [b.left, b.top, b.right, b.bottom] })"""


def _overlapping(boxes: list[list[float]]) -> list[tuple[int, int]]:
    return [
        (i, j)
        for i, a in enumerate(boxes)
        for j, b in enumerate(boxes)
        if i < j and a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5
        if a[1] < b[3] - 0.5 and b[1] < a[3] - 0.5
    ]


@pytest.mark.parametrize("width", [320, 360, 390, 639, 640, 768, 1024, 1440])
@pytest.mark.parametrize("pointer", ["fine", "coarse"])
def test_the_pager_holds_one_row_without_overlap_at_every_width(
    show: Show, width: int, pointer: str
) -> None:
    # A phone's 16px gutters rather than the harness's 32px.
    page = show(html.div(_pager(), class_="-mx-4"), width=width)
    if pointer == "coarse":
        _coarse(page)
    boxes = page.evaluate(_STEPS)
    assert not _overlapping(boxes)
    assert len({round(box[1]) for box in boxes}) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width


@pytest.mark.parametrize("pointer", ["fine", "coarse"])
@pytest.mark.parametrize("sizes", [False, True])
def test_a_pager_wrapped_in_a_narrow_column_stays_usable(
    show: Show, pointer: str, sizes: bool
) -> None:
    page = show(
        html.div(
            html.aside(_pager(sizes=sizes), id="side", class_="w-56 shrink-0"),
            html.div("Main", class_="flex-1"),
            class_="flex gap-4",
        ),
        width=1440,
    )
    if pointer == "coarse":
        _coarse(page)
    boxes = page.evaluate(_STEPS)
    assert not _overlapping(boxes)
    side = page.evaluate(
        "(() => { const b = document.getElementById('side')"
        ".getBoundingClientRect(); return [b.left, b.right] })()"
    )
    assert all(side[0] - 0.5 <= box[0] and box[2] <= side[1] + 0.5 for box in boxes)
    # Next is on top where it is drawn, and Tab gets to it.
    nxt = page.get_by_role("link", name="Next page")
    assert page.evaluate(
        "(() => { const n = document.querySelector('[aria-label=\"Next page\"]');"
        " const b = n.getBoundingClientRect();"
        " return n.contains(document.elementFromPoint("
        "b.left + b.width / 2, b.top + b.height / 2)) })()"
    )
    page.get_by_role("link", name="Previous page").focus()
    for _ in range(12):
        if page.evaluate("document.activeElement.ariaLabel") == "Next page":
            break
        page.keyboard.press("Tab")
    expect(nxt).to_be_focused()


@pytest.mark.parametrize("width", [390, 1440])
def test_a_tables_pager_in_a_card_stays_on_one_row(show: Show, width: int) -> None:
    table = DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=[Column("invoice", "Invoice"), Column("amount", "Amount")],
            rows=lambda request, asked: [
                {"invoice": f"INV-{n:03}", "amount": str(n)} for n in range(90)
            ][30:40],
            page_size=10,
        )
    )
    page = show(Card().content(CardBody().content(table)), width=width)
    if width == 390:
        _coarse(page)
    boxes = page.evaluate(_STEPS)
    assert not _overlapping(boxes)
    assert len({round(box[1]) for box in boxes}) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width


@pytest.mark.parametrize("width", [390, 1280])
def test_every_focused_step_draws_its_ring_on_top(show: Show, width: int) -> None:
    page = show(_pager(), width=width)
    if width == 390:
        _coarse(page)
    page.get_by_role("link", name="Previous page").focus()
    for _ in range(8):
        # Raised over the neighbours, whose backgrounds would cover the
        # ring in a 1px gap.
        assert page.evaluate("getComputedStyle(document.activeElement).zIndex") == "10"
        if page.evaluate("document.activeElement.ariaLabel") == "Next page":
            break
        page.keyboard.press("Tab")


# Card and Panel.


_IMAGE = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='600' height='300'%3E%3Crect width='600' height='300' "
    "fill='red'/%3E%3C/svg%3E"
)


def test_a_card_with_media_still_clips_its_rounded_corner(show: Show) -> None:
    page = show(
        Stack()
        .horizontal()
        .content(
            Card()
            .id("card")
            .class_("flex-1")
            .content(
                CardMedia().content(html.img(src=_IMAGE, alt="", id="img")),
                CardBody().content("Body"),
            ),
            Card().class_("flex-1").content(CardBody().content("Two")),
        ),
        width=390,
    )
    page.wait_for_function("document.getElementById('img').complete")
    corner = page.evaluate(
        "(() => { const b = document.getElementById('card').getBoundingClientRect();"
        " const hit = document.elementFromPoint(b.left + 1.5, b.top + 1.5);"
        " const mid = document.elementFromPoint(b.left + b.width / 2, b.top + 20);"
        " return [hit.id, mid.id, b.right] })()"
    )
    assert corner[0] != "img"
    assert corner[1] == "img"
    assert corner[2] <= 390
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


def test_a_shrunk_linked_card_is_still_clickable_all_over(show: Show) -> None:
    page = show(
        Stack()
        .horizontal()
        .content(
            Card()
            .id("card")
            .href("/elsewhere")
            .class_("flex-1")
            .content(
                CardHeader().title("A title long enough to want more room"),
                CardBody().content(html.div(style="width: 500px", class_="h-10")),
            ),
            Card().class_("flex-1").content(CardBody().content("Two")),
        ),
        width=390,
    )
    hits = page.evaluate(
        "(() => { const b = document.getElementById('card').getBoundingClientRect();"
        " return [[b.left + 10, b.bottom - 10], [b.right - 10, b.top + 10],"
        " [b.right - 10, b.bottom - 10]].map(([x, y]) =>"
        " !!document.elementFromPoint(x, y).closest('[data-card-link]')) })()"
    )
    assert hits == [True, True, True]


def test_a_chart_in_a_shrinking_card_fits_the_card(show: Show) -> None:
    chart = (
        LineChart()
        .labels(["Mon", "Tue", "Wed"])
        .series([1, 2, 3], label="Sign-ups")
        .description("Sign-ups rose.")
    )
    page = show(
        Stack()
        .horizontal()
        .content(
            Card().id("card").class_("flex-1").content(CardBody().content(chart)),
            Card().class_("flex-1").content(CardBody().content("Two")),
        ),
        width=390,
    )
    page.wait_for_function("document.querySelector('#card canvas')")
    inside = page.evaluate(
        "(() => { const card = document.getElementById('card').getBoundingClientRect();"
        " const c = document.querySelector('#card canvas').getBoundingClientRect();"
        " return c.right <= card.right + 0.5 && c.width > 50 })()"
    )
    assert inside
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


def test_a_scroll_area_in_a_shrinking_card_still_scrolls(show: Show) -> None:
    area = (
        ScrollArea()
        .id("area")
        .label("Notes")
        .max_height("max-h-32")
        .content(*[html.p(f"Note {n} " * 10) for n in range(30)])
    )
    page = show(
        Stack()
        .horizontal()
        .content(
            Card().id("card").class_("flex-1").content(CardBody().content(area)),
            Card().class_("flex-1").content(CardBody().content("Two")),
        ),
        width=390,
    )
    box = page.evaluate(
        "(() => { const a = document.getElementById('area');"
        " const c = document.getElementById('card').getBoundingClientRect();"
        " return [a.scrollHeight > a.clientHeight,"
        " a.getBoundingClientRect().right <= c.right] })()"
    )
    assert box == [True, True]


@pytest.mark.parametrize("padding", ["none", "sm", "md"])
def test_a_panel_in_a_sidebar_keeps_its_header_and_padding(
    show: Show, padding: str
) -> None:
    page = show(
        html.div(
            html.aside(
                Panel()
                .id("panel")
                .label("Filters")
                .hint("3 on")
                .padding(padding)  # type: ignore[arg-type]
                .content(html.div("Body", id="body")),
                class_="w-64 shrink-0",
            ),
            html.div(html.div(style="width: 2000px"), class_="flex-1"),
            class_="flex gap-4",
        ),
        width=1280,
    )
    sizes = page.evaluate(
        "(() => { const p = document.getElementById('panel').getBoundingClientRect();"
        " const head = document.querySelector('#panel > div').getBoundingClientRect();"
        " const body = document.getElementById('body').getBoundingClientRect();"
        " return [p.width, head.height, body.left - p.left] })()"
    )
    assert sizes[0] == 256
    assert sizes[1] > 20
    inset = {"none": 1, "sm": 17, "md": 25}[padding]
    assert abs(sizes[2] - inset) <= 1


# The bar while its confirmation is open.


def _two_actions() -> DataTable:
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=[Column("invoice", "Invoice"), Column("amount", "Amount")],
            rows=lambda request, asked: [
                {"invoice": f"INV-{n:03}", "amount": str(n)} for n in range(40)
            ],
            identifier="invoice",
            actions={
                "export": BulkAction("Export", lambda request, ids: None),
                "delete": BulkAction(
                    "Delete",
                    lambda request, ids: None,
                    variant="danger",
                    confirm=Dialog().destructive().title("Delete these invoices?"),
                ),
            },
            page_size=40,
        )
    )


def _bar_z(page: Page) -> str:
    return page.evaluate(
        f"getComputedStyle(document.querySelector('#invoices {_BAR}')).zIndex"
    )


def test_the_scrim_covers_the_bars_other_buttons(show: Show) -> None:
    page = show(_two_actions(), width=1280, height=700)
    _tick_first(page)
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    expect(page.get_by_role("alertdialog")).to_be_visible()
    covered = page.evaluate(
        "(() => { const bar = document.querySelector('#invoices "
        '[aria-label="Selected rows"]\');'
        " const exp = [...bar.querySelectorAll('button')]"
        ".find((b) => b.textContent.trim() === 'Export');"
        " const r = exp.getBoundingClientRect();"
        " return !exp.contains(document.elementFromPoint("
        "r.left + r.width / 2, r.top + r.height / 2)) })()"
    )
    assert covered


def test_the_bar_drops_back_once_the_confirmation_has_left(show: Show) -> None:
    page = show(_two_actions(), width=1280, height=700)
    _tick_first(page)
    assert _bar_z(page) == "20"
    page.locator(_BAR).get_by_role("button", name="Delete").click()
    expect(page.get_by_role("alertdialog")).to_be_visible()
    assert _bar_z(page) == "80"
    page.get_by_role("alertdialog").get_by_role("button", name="Cancel").click()
    # Still up while the dialog fades, then back under the page's overlays.
    page.wait_for_function(
        f"getComputedStyle(document.querySelector('#invoices {_BAR}')).zIndex === '20'"
    )
    expect(page.locator(_BAR).get_by_role("button", name="Delete")).to_be_focused()


# The last column.


def _three() -> DataTable:
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=[
                Column("invoice", "Invoice"),
                Column("amount", "Amount"),
                Column("status", "Status"),
            ],
            rows=lambda request, asked: [
                {"invoice": "INV-1", "amount": "1", "status": "paid"}
            ],
            hideable=["invoice", "amount", "status"],
            group_by="status",
        )
    )


def test_the_keyboard_cannot_hide_the_last_column(show: Show) -> None:
    page = show(_three())
    page.get_by_role("button", name="Columns", exact=True).click()
    boxes = [page.get_by_role("checkbox", name=n) for n in ("Invoice", "Amount")]
    for box in boxes:
        box.focus()
        page.keyboard.press("Space")
        expect(box).not_to_be_checked()
    status = page.get_by_role("checkbox", name="Status")
    expect(status).to_be_disabled()
    expect(status).to_be_checked()
    # Focus stays on the box just unticked, not lost to the page.
    expect(boxes[1]).to_be_focused()
    page.keyboard.press("Tab")
    expect(status).not_to_be_focused()
    boxes[0].focus()
    page.keyboard.press("Space")
    expect(status).to_be_enabled()


def test_reset_gives_the_last_box_back(show: Show) -> None:
    page = show(_three())
    page.get_by_role("button", name="Columns", exact=True).click()
    page.get_by_role("checkbox", name="Invoice").uncheck()
    page.get_by_role("checkbox", name="Amount").uncheck()
    expect(page.get_by_role("checkbox", name="Status")).to_be_disabled()
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Reset filters and columns").click()
    page.get_by_role("button", name="Columns", exact=True).click()
    for name in ("Invoice", "Amount", "Status"):
        expect(page.get_by_role("checkbox", name=name)).to_be_enabled()
        expect(page.get_by_role("checkbox", name=name)).to_be_checked()


# The empty search.


def test_rapid_typing_then_enter_sends_what_was_typed(show: Show) -> None:
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.press_sequentially("2050")
    with page.expect_request(lambda r: "invoices-q=2050" in r.url):
        field.press("Enter")


def test_paste_then_clear_then_enter_sends_no_query(show: Show) -> None:
    page = show(_table("invoices"))
    field = page.get_by_role("searchbox")
    field.focus()
    field.fill("2050")  # A paste is one input event, as fill() is.
    field.press("ControlOrMeta+a")
    field.press("Backspace")
    with page.expect_request(lambda r: r.method == "GET") as req:
        field.press("Enter")
    assert "invoices-q" not in req.value.url
    expect(field).to_have_attribute("name", "invoices-q")


def test_two_tables_searches_keep_their_own_names(show: Show) -> None:
    page = show(_table("first"), _table("second"))
    one = page.locator("#first").get_by_role("searchbox")
    two = page.locator("#second").get_by_role("searchbox")
    one.focus()
    with page.expect_request(lambda r: r.method == "GET") as req:
        page.keyboard.press("Enter")
    assert "first-q" not in req.value.url
    two.fill("2050")
    page.wait_for_url("**second-q=2050**")
    expect(one).to_have_attribute("name", "first-q")
    expect(two).to_have_attribute("name", "second-q")


def test_a_search_typed_while_an_empty_one_is_in_flight_is_sent(show: Show) -> None:
    page = show(_table("invoices"))
    held: list[Route] = []
    page.route(lambda url: "?" in url, lambda route: held.append(route))
    field = page.get_by_role("searchbox")
    field.focus()
    page.keyboard.press("Enter")
    page.wait_for_function("() => true")
    with page.expect_request(lambda r: "invoices-q=7" in r.url):
        page.keyboard.type("7")
        page.keyboard.press("Enter")
    for route in held:
        route.abort()
