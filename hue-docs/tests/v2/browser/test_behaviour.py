"""
What the docs' own script does around the frames, driven with real keys and
pointer moves.
"""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import FrameLocator, Page, expect

# How far the panel sits below the top of the window when the page scrolls
# to it, its scroll-mt-20.
LANDED = """
id => {
  const target = document.getElementById(id);
  const margin = parseFloat(getComputedStyle(target).scrollMarginTop);
  return Math.abs(target.getBoundingClientRect().top - margin) <= 2;
}
"""

# A shortcut with an href clicks its link while the key is dispatched, and a
# forwarded key is dispatched before the frame's keydown returns, so a link
# clicked is known by the time the press is.
WATCH = """
() => {
  window.followed = null;
  document.addEventListener(
    "click",
    (event) => (window.followed = event.target.closest("a")?.pathname ?? null),
    true,
  );
}
"""


def _frame(docs: Page, site: str, path: str, panel: str = "live") -> FrameLocator:
    docs.goto(site + path)
    docs.evaluate(WATCH)
    docs.locator(f"#{panel}").scroll_into_view_if_needed()
    return docs.frame_locator(f"#{panel} iframe")


def _open_search(docs: Page) -> None:
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()


def _stayed(docs: Page, url: str) -> None:
    assert docs.evaluate("window.followed") is None
    assert docs.url == url


def test_a_theme_switcher_in_a_frame_leaves_the_site_s_theme_alone(
    docs: Page, site: str
) -> None:
    frame = _frame(docs, site, "/components/theme-switcher/")
    frame.get_by_role("button", name="Dark theme").click()
    expect(frame.locator("html")).to_have_attribute("data-theme", "dark")
    assert docs.evaluate("localStorage.getItem('hue-theme')") is None
    # The bar follows the frame's choice, and its own toggle still paints it.
    live = docs.locator("#live")
    expect(live.get_by_role("button", name="Dark theme")).to_have_attribute(
        "aria-pressed", "true"
    )
    live.get_by_role("button", name="Light theme").click()
    expect(frame.locator("html")).to_have_attribute("data-theme", "light")


def test_search_opens_from_a_frame_and_gives_the_frame_its_focus_back(
    docs: Page, site: str
) -> None:
    field = _frame(docs, site, "/components/text-input/").locator("input").first
    field.fill("ada")
    _open_search(docs)
    docs.keyboard.press("Escape")
    expect(field).to_be_focused()
    expect(field).to_have_value("ada")
    # Closed by its backdrop instead.
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_hidden()
    _open_search(docs)
    docs.mouse.click(5, 890)
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_hidden()
    expect(field).to_be_focused()


def test_a_search_result_on_this_page_closes_search_and_focuses_its_section(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/forms/")
    _open_search(docs)
    search = docs.get_by_role("combobox", name="Search the docs")
    search.fill("button")
    expect(docs.locator("#docs-search-0 span").first).to_have_text("Button")
    search.fill("forms body")
    rows = docs.locator("#docs-search-results [role=option]")
    expect(rows.locator('a[href*="/forms/#"]').first).to_be_attached()
    hrefs = rows.locator("a").evaluate_all("as => as.map(a => a.pathname + a.hash)")
    index = next(i for i, href in enumerate(hrefs) if href.startswith("/forms/#"))
    section = hrefs[index].split("#")[1]
    for _ in range(index):
        docs.keyboard.press("ArrowDown")
    docs.keyboard.press("Enter")
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_hidden()
    docs.wait_for_function("id => document.activeElement?.id === id", arg=section)
    assert docs.evaluate("location.hash") == f"#{section}"
    docs.keyboard.press("Tab")
    focused = "document.querySelector('#content').contains(document.activeElement)"
    assert docs.evaluate(focused)


def test_a_site_shortcut_works_with_focus_in_a_frame(docs: Page, site: str) -> None:
    _frame(docs, site, "/components/button/").get_by_role("button").first.focus()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    docs.wait_for_url("**/keyboard-shortcuts/")


def test_letters_stay_in_a_frame_s_field_or_open_modal(docs: Page, site: str) -> None:
    field = _frame(docs, site, "/components/text-input/").locator("input").first
    field.focus()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    expect(field).to_have_value("gk")
    _stayed(docs, site + "/components/text-input/")

    frame = _frame(docs, site, "/components/dialog/")
    frame.get_by_role("button", name="Invite").click()
    dialog = frame.get_by_role("dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button").last.focus()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    _stayed(docs, site + "/components/dialog/")


def _leave_and_hover(docs: Page, panel: str) -> None:
    docs.locator("h1").click()
    docs.locator(f"#{panel} iframe").hover()


def test_escape_from_the_page_reaches_only_an_open_overlay_in_the_hovered_frame(
    docs: Page, site: str
) -> None:
    frame = _frame(docs, site, "/components/dialog/")
    frame.get_by_role("button", name="Invite").click()
    dialog = frame.get_by_role("dialog")
    expect(dialog).to_be_visible()
    _leave_and_hover(docs, "live")
    # Leaving the frame is no answer to a modal.
    expect(dialog).to_be_visible()
    docs.keyboard.press("Escape")
    expect(dialog).to_be_hidden()

    # With nothing open in the frame, Escape leaves its state alone.
    frame = _frame(docs, site, "/components/data-table/")
    row = frame.get_by_role("checkbox", name="Select INV-2050")
    row.check()
    _leave_and_hover(docs, "live")
    docs.keyboard.press("Escape")
    expect(row).to_be_checked()


def test_escape_that_closes_the_search_leaves_a_frame_s_modal_open(
    docs: Page, site: str
) -> None:
    frame = _frame(docs, site, "/components/drawer/")
    frame.get_by_role("button").first.click()
    modal = frame.get_by_role("dialog")
    expect(modal).to_be_visible()
    had = modal.locator(":focus")
    expect(had).to_have_count(1)
    label = had.evaluate("el => el.outerHTML")
    _open_search(docs)
    # The docs page still takes the pointer to be over the frame, as it does
    # until the pointer moves, and one Escape should close one overlay.
    docs.locator("#live iframe").dispatch_event("mouseover")
    docs.keyboard.press("Escape")
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_hidden()
    # Closing is a transition, so the modal is only known to have stayed open
    # once it has had the time to close and has not.
    with pytest.raises(AssertionError):
        expect(modal).to_be_hidden(timeout=1000)
    expect(had).to_have_count(1)
    assert had.evaluate("el => el.outerHTML") == label


WHERE = "() => Math.round(window.scrollY)"


def _kept(docs: Page, y: int) -> None:
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function(f"() => Math.abs(scrollY - {y}) <= 2", timeout=3000)


def test_a_link_lands_on_its_panel_and_back_or_reload_keeps_the_reader_s_place(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/tabs/#anatomy")
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function(LANDED, arg="anatomy", timeout=3000)
    docs.mouse.move(700, 400)
    docs.mouse.wheel(0, 2500)
    docs.wait_for_function("() => window.scrollY >= 2400")
    y = docs.evaluate(WHERE)
    docs.locator("#docs-nav").get_by_role("link", name="Badge", exact=True).click()
    docs.wait_for_url("**/components/badge/")
    docs.go_back()
    _kept(docs, y)
    docs.reload()
    _kept(docs, y)


SETTLED = "() => new Promise((done) => requestAnimationFrame(() => setTimeout(done)))"

GROW = """
() => document.body.appendChild(
  Object.assign(document.createElement("div"), { style: "height: 400px" })
)
"""


def test_back_lets_the_reader_scroll_away_from_the_restored_place(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/tabs/")
    docs.wait_for_load_state("networkidle")
    docs.mouse.move(700, 400)
    docs.mouse.wheel(0, 2000)
    docs.wait_for_function("() => scrollY >= 1998")
    docs.locator("#docs-nav").get_by_role("link", name="Badge", exact=True).click()
    docs.wait_for_url("**/components/badge/")
    docs.go_back()
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function("() => Math.abs(scrollY - 2000) <= 2", timeout=3000)
    docs.mouse.move(700, 400)
    docs.mouse.wheel(0, -800)
    docs.wait_for_function("() => scrollY <= 1202")
    left = docs.evaluate("Math.round(scrollY)")
    # Something on the page growing after the reader moved on, as a frame would.
    docs.evaluate(GROW)
    docs.evaluate(SETTLED)
    assert abs(docs.evaluate("Math.round(scrollY)") - left) <= 2


IN_VIEW = """
() => {
  const item = document.querySelector('#docs-nav [aria-current="page"]');
  const box = item.closest(".overflow-y-auto").getBoundingClientRect();
  const own = item.getBoundingClientRect();
  return own.height > 0 && own.top >= box.top && own.bottom <= box.bottom;
}
"""


def test_the_sidebar_and_the_drawer_show_the_current_page(
    docs: Page, site: str
) -> None:
    docs.set_viewport_size({"width": 1280, "height": 720})
    docs.goto(site + "/components/theme-switcher/")
    docs.wait_for_function(IN_VIEW)
    docs.set_viewport_size({"width": 390, "height": 844})
    docs.goto(site + "/components/tabs/")
    docs.get_by_role("button", name="Menu").click()
    docs.wait_for_function(IN_VIEW)


def test_a_menu_closes_when_the_reader_moves_on_to_another_frame_or_the_page(
    docs: Page, site: str
) -> None:
    frame = _frame(docs, site, "/components/dropdown-menu/")
    frame.get_by_role("button", name="Project actions").click()
    menu = frame.get_by_role("menu")
    expect(menu).to_be_visible()
    other = docs.frame_locator("section:not(#live) iframe").first
    other.get_by_role("button").first.click()
    expect(menu).to_be_hidden()
    other_menu = other.get_by_role("menu").first
    expect(other_menu).to_be_visible()
    docs.locator("h1").click()
    expect(other_menu).to_be_hidden()


def test_fill_brings_a_resized_preview_back_on_a_phone(docs: Page, site: str) -> None:
    docs.set_viewport_size({"width": 390, "height": 844})
    docs.goto(site + "/components/button/")
    live = docs.locator("#live")
    handle = live.get_by_role("separator", name="Preview width")
    handle.focus()
    docs.keyboard.press("End")
    expect(handle).to_have_attribute("aria-valuetext", re.compile("%"))
    live.get_by_role("button", name="Fill").click()
    expect(handle).not_to_have_attribute("aria-valuetext", re.compile("%"))


def test_the_favicon_ico_request_gets_the_svg(docs: Page, site: str) -> None:
    response = docs.request.get(site + "/favicon.ico")
    assert response.ok
    assert response.url.endswith("/static/favicon.svg")
    assert "svg" in response.headers["content-type"]
