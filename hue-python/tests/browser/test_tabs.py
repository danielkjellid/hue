from htmy import html
from playwright.sync_api import Page, Route, expect

from hue.ui import Tab, Tabs
from tests.browser.conftest import ORIGIN, Show, render_page


def _tabs(current: str) -> Tabs:
    return (
        Tabs()
        .id("tabs")
        .label("Sections")
        .target("content")
        .current(current)
        .content(
            Tab().href("/").content("One"),
            Tab().href("/two").content("Two"),
            Tab().disabled().content("Three"),
        )
    )


def _page(current: str, text: str) -> tuple[object, ...]:
    return (_tabs(current), html.div(text, id="content"))


def _serve_two(page: Page) -> None:
    document = render_page(*_page("/two", "Two"))  # type: ignore[arg-type]

    def fulfil(route: Route) -> None:
        route.fulfill(body=document, content_type="text/html")

    page.route(f"{ORIGIN}/two", fulfil)


def _many_tabs() -> Tabs:
    return (
        Tabs()
        .label("Many")
        .current("/0")
        .content(*(Tab().href(f"/{n}").content(f"Section {n}") for n in range(12)))
    )


def test_a_push_swap_then_back_restores_the_first_page(show: Show) -> None:
    page = show(*_page("/", "One"))
    _serve_two(page)
    page.get_by_role("link", name="Two").click()
    expect(page.locator("#content")).to_have_text("Two")
    expect(page).to_have_url(f"{ORIGIN}/two")
    page.go_back()
    expect(page.locator("#content")).to_have_text("One")
    expect(page.get_by_role("link", name="One")).to_have_attribute(
        "aria-current", "page"
    )


def test_the_current_tab_replaces_rather_than_pushes(show: Show) -> None:
    page = show(*_page("/", "One"))
    before = page.evaluate("history.length")
    page.evaluate("document.getElementById('content').textContent = 'Stale'")
    page.get_by_role("link", name="One").click()
    expect(page.locator("#content")).to_have_text("One")
    assert page.evaluate("history.length") == before


def test_focus_returns_to_the_tab_a_swap_replaced(show: Show) -> None:
    page = show(*_page("/", "One"))
    _serve_two(page)
    page.get_by_role("link", name="Two").focus()
    page.keyboard.press("Enter")
    expect(page.locator("#content")).to_have_text("Two")
    expect(page.locator("#tabs-tab-1")).to_be_focused()


def test_a_disabled_tab_is_an_unavailable_link(show: Show) -> None:
    page = show(*_page("/", "One"))
    tab = page.get_by_role("link", name="Three")
    expect(tab).to_have_attribute("aria-disabled", "true")
    assert tab.evaluate("(el) => el.tagName") == "A"
    assert tab.get_attribute("href") is None
    tab.click(force=True)
    expect(page).to_have_url(f"{ORIGIN}/")
    # Tab skips it: from Two, focus leaves the row.
    page.get_by_role("link", name="Two").focus()
    page.keyboard.press("Tab")
    expect(tab).not_to_be_focused()


def test_a_row_of_tabs_fits_a_phone(show: Show) -> None:
    page = show(_many_tabs(), width=390)
    assert page.evaluate("document.documentElement.scrollWidth") <= 390


def test_a_focused_tab_scrolls_fully_into_its_row(show: Show) -> None:
    page = show(_many_tabs(), width=390)
    page.get_by_role("link", name="Section 0").focus()
    for _ in range(11):
        page.keyboard.press("Tab")
        assert page.evaluate(
            """() => {
                const tab = document.activeElement;
                const row = tab.parentElement.getBoundingClientRect();
                const box = tab.getBoundingClientRect();
                return box.left >= row.left - 1 && box.right <= row.right + 1;
            }"""
        )


def test_the_focus_ring_is_drawn_inside_the_tab(show: Show) -> None:
    page = show(_many_tabs(), width=390)
    page.get_by_role("link", name="Section 0").focus()
    page.keyboard.press("Tab")
    shadow = page.evaluate("getComputedStyle(document.activeElement).boxShadow")
    assert "inset" in shadow
