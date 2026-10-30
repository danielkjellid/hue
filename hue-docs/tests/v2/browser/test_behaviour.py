"""
What the docs' own script does around the frames, driven with real keys and
pointer moves.
"""

from __future__ import annotations

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
