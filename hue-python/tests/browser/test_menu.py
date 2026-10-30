from playwright.sync_api import Page, expect

from hue.ui import Button, Dialog, DropdownMenu, MenuItem, MenuLabel, MenuSeparator
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


def test_the_pointer_cannot_take_focus_while_it_fades(show: Show) -> None:
    page = show(Dialog().title("Holder").open().content(_menu()))
    _open(page)
    item = page.get_by_role("menuitem", name="Delete").bounding_box()
    assert item is not None
    page.keyboard.press("Escape")
    # Focus is back on the trigger, and then the pointer lands on an item
    # while the menu is still fading out.
    expect(page.get_by_role("button", name="Actions")).to_be_focused()
    page.mouse.move(item["x"] + 10, item["y"] + item["height"] / 2)
    expect(page.get_by_role("menu")).to_be_hidden()
    expect(page.get_by_role("button", name="Actions")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


def test_hovering_an_open_menu_moves_focus(show: Show) -> None:
    page = show(_menu())
    _open(page)
    page.get_by_role("menuitem", name="Delete").hover()
    expect(page.get_by_role("menuitem", name="Delete")).to_be_focused()
    page.keyboard.press("ArrowUp")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()


def _grouped() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(
            MenuItem().content("Open"),
            MenuSeparator(),
            MenuLabel().content("Project"),
            MenuItem().content("Rename"),
            MenuItem().content("Duplicate"),
            MenuSeparator(),
            MenuLabel().content("Sharing"),
            MenuItem().content("Invite"),
        )
    )


def test_the_arrow_keys_walk_across_labelled_runs_and_wrap(show: Show) -> None:
    page = show(_grouped())
    page.get_by_role("button", name="Actions").focus()
    page.keyboard.press("ArrowDown")
    order = ["Open", "Rename", "Duplicate", "Invite", "Open"]
    expect(page.get_by_role("menuitem", name=order[0])).to_be_focused()
    for name in order[1:]:
        page.keyboard.press("ArrowDown")
        expect(page.get_by_role("menuitem", name=name)).to_be_focused()
    page.keyboard.press("ArrowUp")
    expect(page.get_by_role("menuitem", name="Invite")).to_be_focused()
    page.keyboard.press("Home")
    expect(page.get_by_role("menuitem", name="Open")).to_be_focused()
    page.keyboard.press("End")
    expect(page.get_by_role("menuitem", name="Invite")).to_be_focused()
