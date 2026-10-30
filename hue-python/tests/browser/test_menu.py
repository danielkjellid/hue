from playwright.sync_api import Page, expect

from hue.ui import Button, Dialog, DropdownMenu, MenuItem
from tests.browser.conftest import Show


def _menu() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(MenuItem().content("Rename"), MenuItem().content("Delete"))
    )


def _open(page: Page) -> None:
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()


def test_escape_returns_focus_to_the_trigger(show: Show) -> None:
    page = show(_menu())
    _open(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("menu")).to_be_hidden()
    expect(page.get_by_role("button", name="Actions")).to_be_focused()


def test_escape_in_a_dialog_closes_the_menu_first(show: Show) -> None:
    page = show(Dialog().title("Holder").open().content(_menu()))
    _open(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("menu")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()
