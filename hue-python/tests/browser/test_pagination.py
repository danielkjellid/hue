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


def _serve(page: Page) -> None:
    def fulfil(route: Route) -> None:
        number = int(route.request.url.split("page=")[1])
        document = render_page(*_page(number))  # type: ignore[arg-type]
        route.fulfill(body=document, content_type="text/html")

    page.route(f"{ORIGIN}/?page=*", fulfil)


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


def test_many_pages_fit_a_phone(show: Show) -> None:
    page = show(_pagination(50, total=100).page_sizes([10, 25]), width=390)
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


@pytest.mark.parametrize(
    "pagination",
    [
        _pagination(8, total=15),
        _pagination(50, total=100),
        _pagination(8, total=15).total_records(148),
    ],
)
def test_the_steps_stay_on_one_line_at_320(show: Show, pagination: Pagination) -> None:
    # A wrapped row leaves Next alone on a line under the numbers.
    page = show(pagination, width=320)
    tops = page.evaluate(
        "[...document.querySelectorAll('nav > *')]"
        ".filter(child => child.checkVisibility())"
        ".map(child => child.getBoundingClientRect().top)"
    )
    assert len(set(tops)) == 1, tops
    assert page.evaluate("document.documentElement.scrollWidth") <= 320


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
    expect(page.locator(f"#pages-page-{number}")).to_have_attribute(
        "aria-current", "page"
    )
