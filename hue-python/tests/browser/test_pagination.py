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
