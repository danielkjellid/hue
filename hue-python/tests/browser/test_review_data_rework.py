"""
Review tests for the data rework: the bar's room on the table's scroller,
Pagination's narrow window decided by width, and the single-mode Accordion
that opens only the section of the field the browser reports.
"""

import struct
import zlib
from itertools import pairwise
from typing import Any

import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.datatable import BulkAction, build_datatable_state
from hue.ui import Accordion, AccordionItem, Column, DataTable, Disclosure, TextInput
from tests.browser.conftest import ORIGIN, Show, render_page
from tests.browser.test_datatable import _Router, _table
from tests.browser.test_review_data_navigation import _coarse, _form, _pager

# The bar's room.

_BAR_TOP = (
    "(() => { const bar = document.querySelector('[aria-label=\"Selected rows\"]');"
    " return innerHeight - parseFloat(getComputedStyle(bar).bottom)"
    " - bar.offsetHeight })()"
)


def _tick(page: Page, scope: str = "#invoices") -> None:
    page.locator(scope).get_by_role("checkbox", name="Select INV-2050").check()
    expect(
        page.get_by_role("group", name="Selected rows").locator("visible=true")
    ).to_have_count(1)


def _frames(page: Page) -> None:
    page.evaluate(
        "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )


def _shell(*parts: object, style: str = "") -> object:
    return html.div(
        html.div(style="height: 600px"),
        *parts,
        id="shell",
        style="position: fixed; inset: 0; overflow-y: auto; padding: 16px;" + style,
    )


def test_two_tables_in_one_shell_give_back_its_own_padding(show: Show) -> None:
    page = show(
        _shell(_table("first"), _table("second"), style="padding-bottom: 12px"),
        width=390,
        height=600,
    )
    _tick(page, "#first")
    page.wait_for_function(
        "() => document.getElementById('shell').style.paddingBottom !== '12px'"
    )
    first = page.evaluate("document.getElementById('shell').style.paddingBottom")
    assert float(first.removesuffix("px")) > 12
    _tick(page, "#second")
    _frames(page)
    assert (
        page.evaluate("document.getElementById('shell').style.paddingBottom") == first
    )
    page.keyboard.press("Escape")
    page.wait_for_function(
        "() => document.getElementById('shell').style.paddingBottom === '12px'"
        " && document.getElementById('shell').style.scrollPaddingBottom === ''"
    )
    # The page itself was never touched.
    assert page.evaluate("document.documentElement.style.paddingBottom") == ""


def test_a_table_swapped_out_of_its_shell_gives_back_the_room(show: Show) -> None:
    page = show(_shell(html.div(_table("invoices"), id="region")), width=390)
    _tick(page)
    page.wait_for_function("() => document.getElementById('shell').style.paddingBottom")
    page.evaluate("document.getElementById('region').replaceChildren()")
    # 16px is the shell's own, from its padding shorthand.
    page.wait_for_function(
        "() => document.getElementById('shell').style.paddingBottom === '16px'"
        " && !document.getElementById('shell').style.scrollPaddingBottom"
    )


def test_a_focused_page_link_in_a_shell_is_not_under_the_bar(show: Show) -> None:
    page = show(_shell(_table("invoices")), width=390, height=600)
    _tick(page)
    page.locator("#invoices-rows-pagination-page-2").focus()
    page.wait_for_function(
        "() => document.querySelector('#invoices-rows-pagination-page-2')"
        f".getBoundingClientRect().bottom <= {_BAR_TOP}"
    )


# Pagination.

_ROWS = (
    "new Set([...document.querySelectorAll('nav[aria-label=Pagination] > *')]"
    ".filter((child) => child.checkVisibility())"
    ".map((child) => Math.round(child.getBoundingClientRect().top))).size"
)

_STEPS = (
    "[...document.querySelectorAll('nav[aria-label=Pagination] > *')]"
    ".filter((child) => child.checkVisibility() && child.textContent.trim() !== '…')"
    ".map((child) => { const box = child.getBoundingClientRect();"
    " return [box.left, box.right, box.width, box.height] })"
)


def _swap_to(page: Page, *components: Any) -> None:
    """
    Load another page in the same tab, so a touch screen set up once stays.
    """
    document = render_page(*components)
    page.unroute(f"{ORIGIN}/next")
    page.route(
        f"{ORIGIN}/next",
        lambda route: route.fulfill(body=document, content_type="text/html"),
    )
    page.goto(f"{ORIGIN}/next")
    page.wait_for_function("() => window.Alpine && document.body._x_dataStack")


@pytest.mark.parametrize("coarse", [False, True], ids=["fine", "coarse"])
@pytest.mark.parametrize("width", [320, 360, 390])
@pytest.mark.parametrize("total", [3, 5, 15, 100])
def test_every_page_fits_one_line(
    show: Show, total: int, width: int, coarse: bool
) -> None:
    page = show(html.div(_pager(1, total), class_="-mx-4"), width=width)
    if coarse:
        _coarse(page)
    target = 40 if coarse else 32
    for number in range(1, total + 1):
        if number > 1:
            _swap_to(page, html.div(_pager(number, total), class_="-mx-4"))
        where = f"page {number} of {total}"
        assert page.evaluate(_ROWS) == 1, where
        assert page.evaluate("document.documentElement.scrollWidth") <= width, where
        for edge in (1, number, total):
            link = page.locator(f"#pages-page-{edge}")
            assert link.is_visible(), where
        assert (
            page.locator(f"#pages-page-{number}").get_attribute("aria-current")
            == "page"
        ), where
        steps = page.evaluate(_STEPS)
        for _, _, w, h in steps:
            assert w >= target - 0.5 and h >= target - 0.5, where
        for (_, right, _, _), (left, _, _, _) in pairwise(steps):
            assert left >= right, where


def test_the_select_and_a_one_line_row_at_320_on_touch(show: Show) -> None:
    page = show(
        html.div(
            _pager(8).total_records(148).page_size(10).page_sizes([10, 25]),
            class_="-mx-4",
        ),
        width=320,
    )
    _coarse(page)
    expect(page.get_by_label("Rows per page")).to_have_value("10")
    assert page.evaluate(_ROWS) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= 320


def _long_table(pages: int) -> DataTable:
    return DataTable.from_state(
        build_datatable_state(
            _Router(),
            key="invoices",
            columns=[Column("invoice", "Invoice"), Column("amount", "Amount")],
            rows=lambda request, asked: [
                {"invoice": f"INV-{n}", "amount": str(n)} for n in range(pages)
            ],
            identifier="invoice",
            search="Search invoices",
            actions={"archive": BulkAction("Archive", lambda request, ids: None)},
            page_size=1,
        )
    )


@pytest.mark.parametrize("width", [320, 360, 390])
def test_a_long_tables_pager_fits_one_line_in_its_card(show: Show, width: int) -> None:
    page = show(html.div(_long_table(100), class_="-mx-4"), width=width)
    _coarse(page)
    expect(page.locator("nav[aria-label=Pagination]")).to_be_visible()
    assert page.evaluate(_ROWS) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width


def _pixels(png: bytes) -> tuple[int, int, list[bytes]]:
    """
    Decode a screenshot into rows of RGBA, enough for a few samples.
    """
    width, height = struct.unpack(">II", png[16:24])
    depth, colour = png[24], png[25]
    assert depth == 8 and colour in (2, 6)
    channels = 4 if colour == 6 else 3
    data = b""
    at = 8
    while at < len(png):
        (length,) = struct.unpack(">I", png[at : at + 4])
        kind = png[at + 4 : at + 8]
        if kind == b"IDAT":
            data += png[at + 8 : at + 8 + length]
        at += 12 + length
    raw = zlib.decompress(data)
    stride = width * channels
    rows: list[bytes] = []
    previous = bytearray(stride)
    for y in range(height):
        kind = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1 : (y + 1) * (stride + 1)])
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b = previous[x]
            c = previous[x - channels] if x >= channels else 0
            if kind == 1:
                line[x] = (line[x] + a) & 255
            elif kind == 2:
                line[x] = (line[x] + b) & 255
            elif kind == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif kind == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else b if pb <= pc else c
                line[x] = (line[x] + pred) & 255
        rows.append(bytes(line))
        previous = line
    return width, channels, rows


# The single-mode Accordion.


def _plans(*, open_billing: bool = True, billing: object = "Billing text") -> object:
    return Accordion().content(
        AccordionItem().title("Billing").open(open_billing).content(billing),
        AccordionItem()
        .title("Plans")
        .content(TextInput().name("plan").label("Plan").required()),
        AccordionItem()
        .title("Extras")
        .content(TextInput().name("extra").label("Extra").required()),
    )


def _name() -> TextInput:
    return TextInput().name("name").label("Name").required()


def _expanded(page: Page, title: str) -> str | None:
    return page.get_by_role("button", name=title).get_attribute("aria-expanded")


def _submit(page: Page) -> None:
    page.get_by_role("button", name="Save").click()
    _frames(page)


def test_the_reported_field_after_an_open_section_opens_its_own(show: Show) -> None:
    page = show(_form(_plans(), _name()))
    _submit(page)
    expect(page.get_by_role("textbox", name="Plan")).to_be_focused()
    expect(page.get_by_role("textbox", name="Plan")).to_be_visible()
    assert _expanded(page, "Extras") == "false"


def test_a_field_reported_before_a_closed_accordion_leaves_one_open(
    show: Show,
) -> None:
    # Nothing was open, so the first invalid section may open, but only one.
    page = show(_form(_name(), _plans(open_billing=False)))
    _submit(page)
    expect(page.get_by_role("textbox", name="Name")).to_be_focused()
    assert [_expanded(page, t) for t in ("Billing", "Plans", "Extras")].count(
        "true"
    ) <= 1


def test_a_reported_field_nested_in_the_open_section_keeps_it(show: Show) -> None:
    page = show(
        _form(
            _plans(
                billing=Disclosure()
                .title("Card")
                .closed()
                .content(TextInput().name("card").label("Card").required())
            )
        )
    )
    _submit(page)
    card = page.get_by_role("textbox", name="Card")
    expect(card).to_be_focused()
    expect(card).to_be_visible()
    assert _expanded(page, "Billing") == "true"
    assert _expanded(page, "Plans") == "false"


def test_multiple_opens_every_section_with_a_field_outside_first(show: Show) -> None:
    page = show(
        _form(
            _name(),
            Accordion()
            .multiple()
            .content(
                AccordionItem().title("Billing").open().content("Billing text"),
                AccordionItem().title("Plans").content(_field_plan()),
            ),
        )
    )
    _submit(page)
    expect(page.get_by_role("textbox", name="Name")).to_be_focused()
    expect(page.get_by_text("Billing text")).to_be_visible()


def _field_plan() -> TextInput:
    return TextInput().name("plan").label("Plan").required()
