from playwright.sync_api import Page, expect

from hue import html
from hue.ui import Button, Dialog, Popover, Tooltip
from tests.browser.conftest import Show


def _popover() -> Popover:
    return (
        Popover()
        .title("Sharing")
        .trigger(Button().content("Share"))
        .content(Button().content("Copy link"))
    )


def _open(page: Page) -> None:
    page.get_by_role("button", name="Share").click()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()


def test_tabbing_away_closes_it(show: Show) -> None:
    page = show(_popover(), Button().content("After"))
    _open(page)
    page.keyboard.press("Tab")  # into the panel
    page.keyboard.press("Tab")  # out past it
    expect(page.get_by_role("button", name="After")).to_be_focused()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()


def test_a_click_outside_closes_it(show: Show) -> None:
    page = show(_popover(), html.p("Elsewhere"))
    _open(page)
    page.get_by_text("Elsewhere").click()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()


def test_escape_returns_focus_to_the_trigger(show: Show) -> None:
    page = show(_popover())
    _open(page)
    page.get_by_role("button", name="Copy link").focus()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()
    expect(page.get_by_role("button", name="Share")).to_be_focused()


def test_escape_closes_the_popover_then_its_tooltip_then_the_dialog(
    show: Show,
) -> None:
    page = show(
        Dialog()
        .title("Holder")
        .open()
        .content(
            Popover()
            .title("Sharing")
            .trigger(Tooltip().content("Sharing").trigger(Button().content("Share")))
        )
    )
    trigger = page.get_by_role("button", name="Share")
    trigger.focus()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()
    # The popup is what the control is about now, so the label steps aside.
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    expect(trigger).to_be_focused()
    if page.get_by_role("tooltip").is_visible():
        page.keyboard.press("Escape")
        expect(page.get_by_role("tooltip")).to_be_hidden()
        expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


def test_enter_on_the_trigger_of_an_open_popover_closes_it(show: Show) -> None:
    # Through a Tooltip, whose own click handling must not swallow the toggle.
    page = show(
        Popover()
        .title("Sharing")
        .trigger(Tooltip().content("More actions").trigger(Button().content("Open")))
    )
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    panel = page.get_by_role("dialog", name="Sharing")
    expect(panel).to_be_visible()
    page.keyboard.press("Enter")
    expect(panel).to_be_hidden()
    expect(page.get_by_role("button", name="Open")).to_be_focused()
