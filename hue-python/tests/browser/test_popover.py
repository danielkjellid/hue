from playwright.sync_api import Page, expect

from hue import html
from hue.ui import Button, Dialog, Popover
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


def test_escape_in_a_dialog_closes_the_popover_first(show: Show) -> None:
    page = show(Dialog().title("Holder").open().content(_popover()))
    _open(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()
