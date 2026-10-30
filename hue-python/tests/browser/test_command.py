from playwright.sync_api import Locator, Page, expect

from hue.js import unsafe
from hue.ui import Button, Command, CommandItem
from tests.browser.conftest import Show


def _palette() -> Command:
    return (
        Command()
        .trigger(Button().content("Open"))
        .content(
            CommandItem()
            .label("Go to settings")
            .action(unsafe("window.ran = 'settings'")),
            CommandItem()
            .label("Copy invoice link")
            .description("Anyone with the link can pay")
            .meta("INV-2048")
            .keywords("share")
            .action(unsafe("window.ran = 'copy'")),
            CommandItem()
            .label("Delete workspace")
            .action(unsafe("window.ran = 'delete'")),
        )
    )


def _open(page: Page) -> Locator:
    page.get_by_role("button", name="Open").click()
    field = page.get_by_role("combobox", name="Command palette")
    expect(field).to_be_focused()
    return field


def _active(page: Page) -> Locator:
    return page.locator("[role=option][data-active]")


def test_enter_runs_the_active_item_and_closes(show: Show) -> None:
    page = show(_palette())
    _open(page)
    expect(_active(page)).to_have_attribute("data-label", "Go to settings")
    page.keyboard.press("ArrowDown")
    expect(_active(page)).to_have_attribute("data-label", "Copy invoice link")
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_hidden()
    assert page.evaluate("window.ran") == "copy"
    expect(page.get_by_role("button", name="Open")).to_be_focused()


def test_arrows_stop_at_either_end(show: Show) -> None:
    page = show(_palette())
    _open(page)
    expect(_active(page)).to_have_attribute("data-label", "Go to settings")
    page.keyboard.press("ArrowUp")
    expect(_active(page)).to_have_attribute("data-label", "Go to settings")
    for _ in range(3):
        page.keyboard.press("ArrowDown")
    expect(_active(page)).to_have_attribute("data-label", "Delete workspace")


def test_a_keyword_and_enter_runs_the_first_match(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    field.fill("share")
    expect(_active(page)).to_have_attribute("data-label", "Copy invoice link")
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_hidden()
    assert page.evaluate("window.ran") == "copy"


def test_escape_clears_the_text_then_closes(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    field.fill("share")
    page.keyboard.press("Escape")
    expect(field).to_have_value("")
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_be_hidden()
