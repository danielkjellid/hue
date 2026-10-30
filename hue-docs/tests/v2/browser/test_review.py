"""
Review tests for the frame rework: modals in a frame keep letter shortcuts
to themselves and still take mod+K, focus comes back after the search
without taking it from where the reader clicked, and the click a frame is
sent when focus leaves it closes what a click outside would.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import FrameLocator, Locator, Page, expect

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

# Each modal in a frame: the page, its panel, the button that opens it and
# the role it opens with.
MODALS = {
    "drawer": ("/components/drawer/", "live", None, "dialog"),
    "alertdialog": ("/components/dialog/", "states", None, "alertdialog"),
    "command": ("/components/command/", "live", "Search", "dialog"),
}


def _frame(docs: Page, site: str, path: str, panel: str) -> FrameLocator:
    docs.goto(site + path)
    docs.evaluate(WATCH)
    docs.locator(f"#{panel}").scroll_into_view_if_needed()
    return docs.frame_locator(f"#{panel} iframe")


def _open_modal(docs: Page, site: str, name: str) -> Locator:
    path, panel, opener, role = MODALS[name]
    frame = _frame(docs, site, path, panel)
    buttons = frame.get_by_role("button")
    (buttons.filter(has_text=opener) if opener else buttons).first.click()
    modal = frame.get_by_role(role)
    expect(modal).to_be_visible()
    expect(modal.locator(":focus")).to_have_count(1)
    return modal


def _stays_open(modal: Locator) -> None:
    # Closing is a transition, so an open modal is only known to have stayed
    # open once it has had the time to close and has not.
    with pytest.raises(AssertionError):
        expect(modal).to_be_hidden(timeout=1000)


@pytest.mark.parametrize("name", MODALS)
def test_letter_shortcuts_wait_while_a_modal_is_open_in_a_frame(
    docs: Page, site: str, name: str
) -> None:
    _open_modal(docs, site, name)
    url = docs.url
    docs.keyboard.press("g")
    docs.keyboard.press("k")
    assert docs.evaluate("window.followed") is None
    assert docs.url == url


@pytest.mark.parametrize("name", MODALS)
def test_mod_k_from_a_modal_in_a_frame_opens_search_and_comes_back(
    docs: Page, site: str, name: str
) -> None:
    modal = _open_modal(docs, site, name)
    had = modal.locator(":focus")
    label = had.evaluate("el => el.outerHTML")
    # Off the frame, so Escape belongs to the search alone.
    docs.mouse.move(5, 5)
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()
    docs.keyboard.press("Escape")
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_hidden()
    _stays_open(modal)
    expect(had).to_have_count(1)
    assert had.evaluate("el => el.outerHTML") == label


def test_a_click_into_the_frame_after_the_search_keeps_its_focus(
    docs: Page, site: str
) -> None:
    buttons = _frame(docs, site, "/components/button/", "variants").get_by_role(
        "button"
    )
    buttons.first.focus()
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()
    docs.keyboard.press("Escape")
    buttons.nth(3).click()
    expect(buttons.nth(3)).to_be_focused()


def test_closing_the_search_by_its_backdrop_gives_the_frame_its_focus_back(
    docs: Page, site: str
) -> None:
    button = _frame(docs, site, "/components/button/", "live").get_by_role("button")
    button.first.focus()
    docs.keyboard.press("ControlOrMeta+k")
    expect(docs.get_by_role("combobox", name="Search the docs")).to_be_focused()
    docs.mouse.click(5, 890)
    expect(docs.get_by_role("dialog", name="Search the docs")).to_be_hidden()
    expect(button.first).to_be_focused()


def test_a_data_table_s_filter_panel_closes_when_the_reader_moves_on(
    docs: Page, site: str
) -> None:
    frame = _frame(docs, site, "/components/data-table/", "live")
    frame.get_by_role("button", name="Filter").click()
    paid = frame.get_by_role("checkbox", name="Paid")
    expect(paid).to_be_visible()
    docs.locator("h1").click()
    expect(paid).to_be_hidden()
    # The rows are as the panel left them, as after a click outside in the frame.
    expect(frame.locator("tbody tr")).to_have_count(3)
