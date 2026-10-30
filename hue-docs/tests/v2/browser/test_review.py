"""
Review tests for the frame, search and scroll fixes: the side effects of
forwarding keys out of a frame, of closing a frame's overlays when focus
leaves it, and of keeping the reader's place on Back.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect

# A frame later than the growth, so a resize observer has had its turn.
SETTLED = "() => new Promise((done) => requestAnimationFrame(() => setTimeout(done)))"

GROW = """
() => document.body.appendChild(
  Object.assign(document.createElement("div"), { style: "height: 400px" })
)
"""


def _live(docs: Page, site: str, path: str):
    docs.goto(site + path)
    docs.evaluate(WATCH)
    docs.locator("#live").scroll_into_view_if_needed()
    return docs.frame_locator("#live iframe")


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


def _stayed(docs: Page, url: str) -> None:
    assert docs.evaluate("window.followed") is None
    assert docs.url == url


def test_letter_shortcuts_switched_off_stay_off_in_a_frame(
    docs: Page, site: str
) -> None:
    frame = _live(docs, site, "/components/button/")
    docs.evaluate("Alpine.store('shortcuts').letters = false")
    frame.get_by_role("button").first.focus()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    _stayed(docs, site + "/components/button/")


def test_mod_k_from_a_field_in_a_frame_gives_the_field_its_focus_back(
    docs: Page, site: str
) -> None:
    field = _live(docs, site, "/components/text-input/").locator("input").first
    field.fill("ada")
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()
    docs.keyboard.press("Escape")
    expect(field).to_be_focused()
    expect(field).to_have_value("ada")


def test_typeahead_in_an_open_select_in_a_frame_stays_there(
    docs: Page, site: str
) -> None:
    frame = _live(docs, site, "/components/select/")
    frame.get_by_role("combobox").first.click()
    listbox = frame.get_by_role("listbox").first
    expect(listbox).to_be_visible()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    _stayed(docs, site + "/components/select/")
    expect(listbox).to_be_visible()


def test_letters_in_an_open_menu_in_a_frame_stay_there(docs: Page, site: str) -> None:
    frame = _live(docs, site, "/components/dropdown-menu/")
    frame.get_by_role("button", name="Project actions").click()
    expect(frame.get_by_role("menuitem").first).to_be_focused()
    docs.keyboard.press("g")
    docs.keyboard.press("h")
    _stayed(docs, site + "/components/dropdown-menu/")


def test_a_menu_closes_when_focus_moves_into_another_frame(
    docs: Page, site: str
) -> None:
    frame = _live(docs, site, "/components/dropdown-menu/")
    frame.get_by_role("button", name="Project actions").click()
    menu = frame.get_by_role("menu")
    expect(menu).to_be_visible()
    other = docs.frame_locator("section:not(#live) iframe").first
    button = other.get_by_role("button").first
    button.click()
    expect(menu).to_be_hidden()
    expect(other.get_by_role("menu").first).to_be_visible()


def test_a_select_s_value_survives_focus_leaving_its_frame(
    docs: Page, site: str
) -> None:
    frame = _live(docs, site, "/components/select/")
    trigger = frame.get_by_role("combobox").first
    trigger.click()
    docs.keyboard.press("ArrowDown")
    docs.keyboard.press("Enter")
    # The submitted value, which the trigger's text is drawn from.
    value = frame.locator("input[type=hidden]").first
    chosen = value.input_value()
    assert chosen
    trigger.click()
    expect(frame.get_by_role("listbox").first).to_be_visible()
    docs.locator("h1").click()
    expect(frame.get_by_role("listbox").first).to_be_hidden()
    expect(value).to_have_value(chosen)


def test_a_combobox_s_value_survives_focus_leaving_its_frame(
    docs: Page, site: str
) -> None:
    field = _live(docs, site, "/components/combobox/").get_by_role("combobox").first
    field.click()
    docs.keyboard.press("ArrowDown")
    docs.keyboard.press("Enter")
    chosen = field.input_value()
    assert chosen
    docs.locator("h1").click()
    expect(field).to_have_value(chosen)


def test_a_modified_click_on_a_search_result_opens_a_tab(docs: Page, site: str) -> None:
    docs.goto(site + "/forms/")
    docs.keyboard.press("ControlOrMeta+k")
    docs.get_by_role("combobox", name="Search the docs").fill("forms body")
    row = docs.locator("#docs-search-results [role=option]").first
    expect(row).to_be_visible()
    with docs.context.expect_page() as opened:
        row.click(modifiers=["ControlOrMeta"])
    opened.value.close()
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_visible()
    assert docs.url == site + "/forms/"


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


def test_the_favicon_ico_request_gets_the_svg(docs: Page, site: str) -> None:
    response = docs.request.get(site + "/favicon.ico")
    assert response.ok
    assert response.url.endswith("/static/favicon.svg")
    assert "svg" in response.headers["content-type"]
