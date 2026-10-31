import pytest
from playwright.sync_api import Locator, Page, expect

from hue.js import unsafe
from hue.ui import Button, Command, CommandItem
from tests.browser._fields import contrast, still
from tests.browser.conftest import Show


def _palette() -> Command:
    return (
        Command()
        .trigger(Button().content("Open"))
        .content(
            CommandItem()
            .label("Archived reports")
            .disabled()
            .action(unsafe("window.ran = 'archived'")),
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


def test_escape_clears_the_text_then_closes_and_reopens_fresh(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    field.fill("delete")
    page.keyboard.press("Escape")
    expect(field).to_have_value("")
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_be_hidden()
    field = _open(page)
    expect(field).to_have_value("")
    expect(page.get_by_role("option", name="Delete workspace")).to_be_visible()
    expect(_active(page)).to_have_attribute("data-label", "Go to settings")
    page.keyboard.press("Enter")
    page.wait_for_function("window.ran === 'settings'")


def test_enter_with_no_match_runs_nothing(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    field.press_sequentially("zzz")
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_visible()
    assert page.evaluate("window.ran") is None


def test_typing_skips_a_disabled_first_match(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    # "Archived reports" is the first item with an "r", and it is disabled.
    field.press_sequentially("r")
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_hidden()
    assert page.evaluate("window.ran") not in (None, "archived")


def test_enter_straight_after_typing_runs_the_first_match(show: Show) -> None:
    page = show(_palette())
    _open(page)
    # "s" leaves Go to settings active, and "sh" filters it out.
    page.keyboard.type("share")
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_hidden()
    assert page.evaluate("window.ran") == "copy"


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("text", ["Anyone with the link can pay", "INV-2048"])
def test_text_on_the_active_row_is_legible(show: Show, theme: str, text: str) -> None:
    page = still(show(_palette(), theme=theme))
    _open(page)
    page.keyboard.press("ArrowDown")
    expect(_active(page)).to_have_attribute("data-label", "Copy invoice link")
    assert contrast(_active(page).get_by_text(text)) >= 4.5
