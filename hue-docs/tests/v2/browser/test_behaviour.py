"""
What the docs' own script does around the frames, driven with real keys and
pointer moves.
"""

from __future__ import annotations

import re

from playwright.sync_api import Page, expect

# How far the panel sits below the top of the window when the page scrolls
# to it, its scroll-mt-20.
LANDED = """
id => {
  const target = document.getElementById(id);
  const margin = parseFloat(getComputedStyle(target).scrollMarginTop);
  return Math.abs(target.getBoundingClientRect().top - margin) <= 2;
}
"""


def test_a_theme_switcher_in_a_frame_leaves_the_site_s_theme_alone(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/theme-switcher/")
    live = docs.locator("#live")
    live.scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    frame.get_by_role("button", name="Dark theme").click()
    expect(frame.locator("html")).to_have_attribute("data-theme", "dark")
    assert docs.evaluate("localStorage.getItem('hue-theme')") is None
    # The bar follows the frame's choice, and its own toggle still paints it.
    expect(live.get_by_role("button", name="Dark theme")).to_have_attribute(
        "aria-pressed", "true"
    )
    live.get_by_role("button", name="Light theme").click()
    expect(frame.locator("html")).to_have_attribute("data-theme", "light")


def test_escape_reaches_the_hovered_frame_while_focus_is_in_another(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/tooltip/")
    docs.locator("#anatomy").scroll_into_view_if_needed()
    docs.frame_locator("#anatomy iframe").get_by_role("button").first.focus()
    docs.locator("#live").scroll_into_view_if_needed()
    live = docs.frame_locator("#live iframe")
    live.get_by_role("button").first.hover()
    tip = live.locator("[role=tooltip]")
    expect(tip).to_be_visible()
    docs.keyboard.press("Escape")
    expect(tip).to_be_hidden()


def test_mod_k_inside_a_frame_opens_the_search(docs: Page, site: str) -> None:
    docs.goto(site + "/components/button/")
    docs.locator("#live").scroll_into_view_if_needed()
    docs.frame_locator("#live iframe").get_by_role("button").first.focus()
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()


def test_an_exact_title_match_is_the_first_result(docs: Page, site: str) -> None:
    docs.goto(site + "/")
    docs.keyboard.press("ControlOrMeta+k")
    docs.get_by_role("combobox", name="Search the docs").fill("button")
    expect(docs.locator("#docs-search-0 span").first).to_have_text("Button")


def test_a_link_to_a_panel_lands_on_it_once_the_frames_above_settle(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/tabs/#anatomy")
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function(LANDED, arg="anatomy", timeout=3000)


def test_a_reader_who_scrolls_is_not_taken_back_to_the_link_s_target(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/tabs/#anatomy", wait_until="commit")
    docs.wait_for_selector("#anatomy")
    docs.mouse.move(700, 400)
    docs.mouse.wheel(0, 600)
    docs.wait_for_load_state("networkidle")
    docs.wait_for_timeout(300)
    assert not docs.evaluate(LANDED, "anatomy")


def test_a_horizontal_field_has_room_in_its_layout_panel_on_a_phone(
    docs: Page, site: str
) -> None:
    docs.set_viewport_size({"width": 390, "height": 844})
    docs.goto(site + "/components/text-input/")
    docs.locator("#layout").scroll_into_view_if_needed()
    field = docs.frame_locator("#layout iframe").locator("input").first
    expect(field).to_be_visible()
    assert field.bounding_box()["width"] >= 160  # type: ignore[index]


def test_a_drawer_that_must_be_answered_opens_on_its_safe_action(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/drawer/")
    docs.locator("#states").scroll_into_view_if_needed()
    frame = docs.frame_locator("#states iframe")
    frame.get_by_role("button", name="Leave editor").click()
    expect(frame.get_by_role("button", name="Keep editing")).to_be_focused()


def test_the_split_button_s_chevron_opens_its_menu(docs: Page, site: str) -> None:
    docs.goto(site + "/components/button-group/")
    docs.locator("#live").scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    frame.get_by_role("button", name="Export options").click()
    expect(frame.get_by_role("menuitem", name="Export as CSV")).to_be_focused()


# What the docs keep of a reader's place. A link's target is settled on only
# when the reader arrives by it: Back and reload return to where they were.

WHERE = "() => Math.round(window.scrollY)"


def _scroll_by(docs: Page, distance: int) -> int:
    start = docs.evaluate(WHERE)
    docs.mouse.move(700, 400)
    docs.mouse.wheel(0, distance)
    docs.wait_for_function(f"() => window.scrollY >= {start + distance - 2}")
    return docs.evaluate(WHERE)


def _kept(docs: Page, y: int) -> None:
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function(f"() => Math.abs(scrollY - {y}) <= 2", timeout=3000)


def test_back_to_a_link_s_target_returns_to_where_the_reader_was(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/tabs/#anatomy")
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function(LANDED, arg="anatomy", timeout=3000)
    y = _scroll_by(docs, 2500)
    docs.locator("#docs-nav").get_by_role("link", name="Badge", exact=True).click()
    docs.wait_for_url("**/components/badge/")
    docs.go_back()
    _kept(docs, y)


def test_back_to_a_guide_s_section_returns_to_where_the_reader_was(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/forms/#how-form-fields-map-to-the-body")
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function(LANDED, arg="how-form-fields-map-to-the-body", timeout=3000)
    y = _scroll_by(docs, 1500)
    docs.locator("#docs-nav").get_by_role("link", name="Usage", exact=True).click()
    docs.wait_for_url("**/usage/")
    docs.go_back()
    _kept(docs, y)


def test_a_reload_keeps_the_reader_s_place(docs: Page, site: str) -> None:
    docs.goto(site + "/components/tabs/#anatomy")
    docs.wait_for_load_state("networkidle")
    docs.wait_for_function(LANDED, arg="anatomy", timeout=3000)
    y = _scroll_by(docs, 2000)
    docs.reload()
    _kept(docs, y)


# Search. A result on the page the reader is on goes there and closes the
# dialog, with focus on the section, by keys or by a click.


def _search_this_page(docs: Page, site: str) -> tuple[str, int]:
    docs.goto(site + "/forms/")
    docs.keyboard.press("ControlOrMeta+k")
    docs.get_by_role("combobox", name="Search the docs").fill("forms body")
    rows = docs.locator("#docs-search-results [role=option]")
    expect(rows.first).to_be_visible()
    hrefs = rows.locator("a").evaluate_all("as => as.map(a => a.pathname + a.hash)")
    index = next(i for i, href in enumerate(hrefs) if href.startswith("/forms/#"))
    return hrefs[index].split("#")[1], index


def _landed_on_the_section(docs: Page, section: str) -> None:
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_hidden()
    docs.wait_for_function("id => document.activeElement?.id === id", arg=section)
    assert docs.evaluate("location.hash") == f"#{section}"
    docs.keyboard.press("Tab")
    focused = "document.querySelector('#content').contains(document.activeElement)"
    assert docs.evaluate(focused)


def test_enter_on_a_result_on_this_page_closes_search_and_focuses_it(
    docs: Page, site: str
) -> None:
    section, index = _search_this_page(docs, site)
    for _ in range(index):
        docs.keyboard.press("ArrowDown")
    docs.keyboard.press("Enter")
    _landed_on_the_section(docs, section)


def test_a_click_on_a_result_on_this_page_closes_search_and_focuses_it(
    docs: Page, site: str
) -> None:
    section, index = _search_this_page(docs, site)
    docs.locator("#docs-search-results [role=option]").nth(index).click()
    _landed_on_the_section(docs, section)


# Escape pressed with focus outside a frame goes to the frame under the
# pointer only while something in it is open, to the overlay that is.


def _leave_and_hover(docs: Page, panel: str) -> None:
    docs.locator("h1").click()
    docs.locator(f"#{panel} iframe").hover()


def test_escape_closes_a_dialog_left_open_in_the_hovered_frame(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/dialog/")
    docs.locator("#live").scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    frame.get_by_role("button", name="Invite").click()
    dialog = frame.get_by_role("dialog")
    expect(dialog).to_be_visible()
    _leave_and_hover(docs, "live")
    # Leaving the frame is no answer to a modal.
    expect(dialog).to_be_visible()
    docs.keyboard.press("Escape")
    expect(dialog).to_be_hidden()


def test_a_menu_closes_when_the_reader_moves_on_to_the_page(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/dropdown-menu/")
    docs.locator("#live").scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    frame.get_by_role("button", name="Project actions").click()
    menu = frame.get_by_role("menu")
    expect(menu).to_be_visible()
    docs.locator("h1").click()
    expect(menu).to_be_hidden()


def test_escape_from_the_page_leaves_a_table_s_selection_alone(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/data-table/")
    docs.locator("#live").scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    row = frame.get_by_role("checkbox", name="Select INV-2050")
    row.check()
    _leave_and_hover(docs, "live")
    docs.keyboard.press("Escape")
    expect(row).to_be_checked()
    # Escape in the frame itself still clears it.
    row.focus()
    docs.keyboard.press("Escape")
    expect(row).not_to_be_checked()


# Keys pressed in a frame reach the site's shortcuts, and focus comes back
# to where it was after the search they open.


def test_mod_k_from_a_frame_gives_focus_back_to_what_had_it(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/button/")
    docs.locator("#live").scroll_into_view_if_needed()
    button = docs.frame_locator("#live iframe").get_by_role("button").first
    button.focus()
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()
    docs.keyboard.press("Escape")
    expect(button).to_be_focused()


def test_a_site_shortcut_works_with_focus_in_a_frame(docs: Page, site: str) -> None:
    docs.goto(site + "/components/button/")
    docs.locator("#live").scroll_into_view_if_needed()
    docs.frame_locator("#live iframe").get_by_role("button").first.focus()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    docs.wait_for_url("**/keyboard-shortcuts/")


def test_letters_typed_into_a_field_in_a_frame_stay_there(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/text-input/")
    docs.evaluate(WATCH)
    docs.locator("#live").scroll_into_view_if_needed()
    field = docs.frame_locator("#live iframe").locator("input").first
    field.focus()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    expect(field).to_have_value("gk")
    assert docs.evaluate("window.followed") is None


# The sidebar shows the current page's entry, beside the page and in the
# phone's drawer.

IN_VIEW = """
() => {
  const item = document.querySelector('#docs-nav [aria-current="page"]');
  const box = item.closest(".overflow-y-auto").getBoundingClientRect();
  const own = item.getBoundingClientRect();
  return own.height > 0 && own.top >= box.top && own.bottom <= box.bottom;
}
"""


def test_the_sidebar_shows_the_current_page(docs: Page, site: str) -> None:
    docs.set_viewport_size({"width": 1280, "height": 720})
    docs.goto(site + "/components/theme-switcher/")
    docs.wait_for_function(IN_VIEW)


def test_the_drawer_shows_the_current_page_when_it_opens(docs: Page, site: str) -> None:
    docs.set_viewport_size({"width": 390, "height": 844})
    docs.goto(site + "/components/tabs/")
    docs.get_by_role("button", name="Menu").click()
    docs.wait_for_function(IN_VIEW)


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


# From the review of the fixes above.

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


def test_site_letter_shortcuts_wait_while_a_frame_s_dialog_is_open(
    docs: Page, site: str
) -> None:
    # hue's shortcuts.js runs none outside an open modal. A dialog open in a
    # frame is the modal the reader is in, so G then K should not leave the
    # page from inside it.
    frame = _live(docs, site, "/components/dialog/")
    frame.get_by_role("button", name="Invite").click()
    dialog = frame.get_by_role("dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button").last.focus()
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    assert docs.evaluate("window.followed") is None
    assert docs.url == site + "/components/dialog/"


def test_mod_k_from_an_open_menu_in_a_frame_gives_focus_back_to_its_trigger(
    docs: Page, site: str
) -> None:
    frame = _live(docs, site, "/components/dropdown-menu/")
    trigger = frame.get_by_role("button", name="Project actions")
    trigger.click()
    expect(frame.get_by_role("menuitem").first).to_be_focused()
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()
    docs.keyboard.press("Escape")
    expect(trigger).to_be_focused()


def test_a_popover_in_a_frame_stays_open_while_another_window_has_focus(
    docs: Page, site: str
) -> None:
    frame = _live(docs, site, "/components/popover/")
    frame.get_by_role("button", name="Share project").click()
    panel = frame.get_by_role("dialog")
    expect(panel).to_be_visible()
    # The reader switches to another window: the docs page loses focus too.
    docs.evaluate("document.hasFocus = () => false")
    live = next(f for f in docs.frames if f.url.endswith("/popover/live/"))
    live.evaluate("window.dispatchEvent(new Event('blur'))")
    docs.evaluate(SETTLED)
    expect(panel).to_be_visible()
