"""
What a page's specimens show, in Chrome, where a frame's width and its
scripts decide it.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect


def test_the_live_drawer_slides_in_from_the_side_on_a_desktop(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/drawer/")
    docs.locator("#live").scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    frame.get_by_role("button", name="Open filters").click()
    panel = frame.get_by_role("dialog")
    expect(panel).to_be_visible()
    # A side panel runs the frame's full height; the phone's bottom sheet
    # stops short of the top.
    box = panel.bounding_box()
    frame_box = docs.locator("#live iframe").bounding_box()
    assert box is not None and frame_box is not None
    assert box["height"] >= frame_box["height"] * 0.95 - 1


def test_copying_the_share_link_says_so(docs: Page, site: str) -> None:
    docs.context.grant_permissions(["clipboard-read", "clipboard-write"])
    docs.goto(site + "/components/popover/")
    docs.locator("#live").scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    frame.get_by_role("button", name="Share project").click()
    frame.get_by_role("button", name="Copy").click()
    expect(frame.get_by_text("Copied to clipboard")).to_be_visible()


def test_tab_from_the_open_live_menu_moves_on_past_its_trigger(
    docs: Page, site: str
) -> None:
    docs.goto(site + "/components/dropdown-menu/")
    docs.locator("#live").scroll_into_view_if_needed()
    frame = docs.frame_locator("#live iframe")
    frame.get_by_role("button", name="Project actions").focus()
    docs.keyboard.press("ArrowDown")
    expect(frame.get_by_role("menuitem", name="Duplicate")).to_be_focused()
    docs.keyboard.press("Tab")
    expect(frame.get_by_role("menu")).to_be_hidden()
    expect(frame.get_by_role("button", name="Share")).to_be_focused()
