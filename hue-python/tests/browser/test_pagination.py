import re
from itertools import pairwise

import pytest
from htmy import html
from playwright.sync_api import Page, Route, expect

from hue.ui import Pagination
from tests.browser.conftest import ORIGIN, Show, render_page


def _pagination(number: int, total: int = 3) -> Pagination:
    return (
        Pagination()
        .id("pages")
        .target("rows")
        .page(number)
        .total_pages(total)
        .href(lambda n: f"/?page={n}")
    )


def _page(number: int) -> tuple[object, ...]:
    return (html.div(f"Rows of page {number}", id="rows"), _pagination(number))


def _serve(page: Page, title: str | None = "Page {}") -> None:
    """
    Answer each page link with that page, titled title (None leaves it out).
    """

    def fulfil(route: Route) -> None:
        number = int(route.request.url.split("page=")[1])
        document = render_page(*_page(number))  # type: ignore[arg-type]
        new = "" if title is None else f"<title>{title.format(number)}</title>"
        document = re.sub(r"<title[^>]*>Test</title>", new, document, count=1)
        route.fulfill(body=document, content_type="text/html")

    page.route(f"{ORIGIN}/?page=*", fulfil)


def coarse(page: Page) -> None:
    """
    Turn the page into a touch screen, whose controls are bigger.
    """
    session = page.context.new_cdp_session(page)
    session.send("Emulation.setTouchEmulationEnabled", {"enabled": True})
    page.wait_for_function("matchMedia('(pointer: coarse)').matches")


# How many lines the visible children of the first nav take.
ROWS = (
    "new Set([...document.querySelector('nav').children]"
    ".filter((child) => child.checkVisibility())"
    ".map((child) => Math.round(child.getBoundingClientRect().top))).size"
)


def test_the_current_page_replaces_rather_than_pushes(show: Show) -> None:
    page = show(*_page(2))
    _serve(page)
    before = page.evaluate("history.length")
    page.evaluate("document.getElementById('rows').textContent = 'Stale'")
    page.locator("#pages-page-2").click()
    expect(page.locator("#rows")).to_have_text("Rows of page 2")
    assert page.evaluate("history.length") == before


def test_focus_goes_to_the_page_a_spent_step_led_to(show: Show) -> None:
    page = show(*_page(2))
    _serve(page)
    page.get_by_role("link", name="Next").focus()
    page.keyboard.press("Enter")
    expect(page.locator("#rows")).to_have_text("Rows of page 3")
    # Next is spent on the last page, so focus lands on page 3 instead.
    expect(page.locator("#pages-page-3")).to_be_focused()


@pytest.mark.parametrize(
    ("width", "total", "number", "sizes"),
    [
        # 3 and 13 fill a one-page gap, the widest a narrow row gets.
        (320, 15, 3, False),
        (320, 15, 13, False),
        (320, 100, 50, False),
        (320, 100, 98, False),
        (320, 15, 8, True),
        (1280, 100, 50, True),
    ],
)
def test_the_row_fits_one_line_with_whole_targets(
    show: Show, width: int, total: int, number: int, sizes: bool
) -> None:
    pager = _pagination(number, total)
    if sizes:
        pager.total_records(total * 10).page_size(10).page_sizes([10, 25])
    # A phone page's usual 16px gutter, rather than the harness's 32px.
    page = show(html.div(pager, class_="-mx-4"), width=width)
    if width == 320:
        coarse(page)
    for edge in (1, number, total):
        expect(page.locator(f"#pages-page-{edge}")).to_be_visible()
    assert page.evaluate(ROWS) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= width
    steps = page.evaluate(
        "[...document.querySelectorAll('nav > *')]"
        ".filter((c) => c.checkVisibility() && c.textContent.trim() !== '…')"
        ".map((c) => { const b = c.getBoundingClientRect();"
        " return [b.left, b.right, b.width, b.height] })"
    )
    target = 40 if width == 320 else 32
    for _, _, w, h in steps:
        assert w >= target - 0.5 and h >= target - 0.5
    for (_, right, _, _), (left, _, _, _) in pairwise(steps):
        assert left >= right


@pytest.mark.parametrize(
    ("number", "width", "seen"),
    [
        (8, 1280, ["1", "…", "7", "8", "9", "…", "15"]),
        (8, 320, ["1", "…", "8", "…", "15"]),
        # The wide row shows 2 and 3 where the narrow one folds them.
        (4, 1280, ["1", "2", "3", "4", "5", "…", "15"]),
        (4, 320, ["1", "…", "4", "…", "15"]),
    ],
)
def test_a_narrow_row_folds_the_siblings(
    show: Show, number: int, width: int, seen: list[str]
) -> None:
    page = show(_pagination(number, total=15), width=width)
    shown = page.evaluate(
        "[...document.querySelectorAll('nav > *')]"
        ".filter(child => child.checkVisibility())"
        ".map(child => child.textContent.trim()).filter(Boolean)"
    )
    assert shown == seen


def test_tab_walks_the_visible_steps_with_each_ring_on_top(show: Show) -> None:
    page = show(html.div(_pagination(8, total=15), class_="-mx-4"), width=320)
    coarse(page)
    visible = page.evaluate(
        "[...document.querySelectorAll('nav a')]"
        ".filter((a) => a.checkVisibility()).map((a) => a.id || a.textContent)"
    )
    page.locator("body").focus()
    reached = []
    for _ in visible:
        page.keyboard.press("Tab")
        reached.append(
            page.evaluate(
                "document.activeElement.id || document.activeElement.textContent"
            )
        )
        # Raised over the neighbours, whose backgrounds would cover the ring
        # in a 1px gap.
        assert page.evaluate("getComputedStyle(document.activeElement).zIndex") == "10"
    assert reached == visible


def _wide_pager() -> Pagination:
    return (
        Pagination()
        .id("pages")
        .page(4)
        .total_pages(9)
        .total_records(90)
        .href(lambda n: f"/?page={n}")
    )


def test_the_pager_fills_its_row_with_the_count_at_the_start(show: Show) -> None:
    page = show(html.div(_wide_pager(), id="row"), width=1280)
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


# A parent sized to its content, which gives the pager the width of its
# own content rather than none.
_SHRINKING = {
    "fit": lambda pager: html.div(pager, class_="w-fit"),
    "pushed": lambda pager: html.div(html.div(pager, class_="ml-auto"), class_="flex"),
}


@pytest.mark.parametrize("parent", list(_SHRINKING))
def test_a_pager_keeps_its_width_in_a_parent_sized_to_it(
    show: Show, parent: str
) -> None:
    page = show(_SHRINKING[parent](_wide_pager()), width=390)
    coarse(page)
    assert page.evaluate("document.querySelector('nav').offsetWidth") > 200
    assert page.evaluate(ROWS) == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


def test_a_pager_in_a_narrow_column_stays_usable(show: Show) -> None:
    page = show(
        html.div(
            html.aside(
                _wide_pager().page_sizes([10, 25, 50]),
                id="side",
                class_="w-56 shrink-0",
            ),
            html.div("Main", class_="flex-1"),
            class_="flex gap-4",
        ),
        width=1440,
    )
    coarse(page)
    boxes = page.evaluate(
        "[...document.querySelectorAll('nav > *')]"
        ".filter((step) => step.checkVisibility())"
        ".map((step) => { const b = step.getBoundingClientRect();"
        " return [b.left, b.top, b.right, b.bottom] })"
    )
    overlapping = [
        (a, b)
        for a, b in pairwise(boxes)
        if a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5 and a[1] < b[3] - 0.5
        if b[1] < a[3] - 0.5
    ]
    assert not overlapping
    side = page.evaluate(
        "(() => { const b = document.getElementById('side')"
        ".getBoundingClientRect(); return [b.left, b.right] })()"
    )
    assert all(side[0] - 0.5 <= box[0] and box[2] <= side[1] + 0.5 for box in boxes)
    # Next is on top where it is drawn, and Tab gets to it.
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
    expect(page.get_by_role("link", name="Next page")).to_be_focused()


def test_a_push_swap_takes_the_title_of_the_page_it_lands_on(show: Show) -> None:
    page = show(*_page(1))
    _serve(page)
    assert page.title() == "Test"
    page.locator("#pages-page-2").click()
    expect(page).to_have_title("Page 2")
    page.locator("#pages-page-3").click()
    expect(page).to_have_title("Page 3")
    # Back reloads the entry, so the title it shows is the one it was saved
    # with as well as the one the page carries.
    page.go_back()
    expect(page).to_have_url(f"{ORIGIN}/?page=2")
    expect(page).to_have_title("Page 2")
    page.go_back()
    expect(page).to_have_title("Test")
    page.go_forward()
    expect(page).to_have_title("Page 2")


def test_a_response_with_no_title_leaves_the_title(show: Show) -> None:
    page = show(*_page(1))
    _serve(page, None)
    page.locator("#pages-page-2").click()
    expect(page.locator("#rows")).to_have_text("Rows of page 2")
    expect(page).to_have_url(f"{ORIGIN}/?page=2")
    assert page.title() == "Test"


def test_a_swap_that_does_not_move_the_address_keeps_the_title(show: Show) -> None:
    page = show(
        html.form(
            html.input_(type="hidden", name="page", value="2"),
            html.button("Refresh", type="submit"),
            action="/",
            method="get",
            **{"x-target": "rows"},
        ),
        *_page(1),
    )
    _serve(page, "Elsewhere")
    page.get_by_role("button", name="Refresh").click()
    expect(page.locator("#rows")).to_have_text("Rows of page 2")
    expect(page).to_have_url(f"{ORIGIN}/")
    assert page.title() == "Test"


def test_a_title_with_markup_characters_is_taken_as_text(show: Show) -> None:
    page = show(*_page(1))
    _serve(page, "Q&amp;A &lt;2&gt;")
    page.locator("#pages-page-2").click()
    expect(page).to_have_title("Q&A <2>")
