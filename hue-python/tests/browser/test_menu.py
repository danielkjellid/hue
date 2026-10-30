from playwright.sync_api import Page, expect

from hue.js import unsafe
from hue.ui import (
    Button,
    Dialog,
    Drawer,
    DropdownMenu,
    MenuItem,
    MenuLabel,
    MenuSeparator,
)
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
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
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
            MenuItem()
            .disabled()
            .on_click(unsafe("window.hit = true"))
            .content("Duplicate"),
            # A label with no separator before it starts a run of its own.
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
        if name == "Duplicate":
            # Reached by the arrows, and does nothing.
            page.keyboard.press("Enter")
            expect(page.get_by_role("menu")).to_be_visible()
            assert page.evaluate("window.hit") is None
    page.keyboard.press("ArrowUp")
    expect(page.get_by_role("menuitem", name="Invite")).to_be_focused()
    page.keyboard.press("Home")
    expect(page.get_by_role("menuitem", name="Open")).to_be_focused()
    page.keyboard.press("End")
    expect(page.get_by_role("menuitem", name="Invite")).to_be_focused()


def test_a_label_names_the_run_of_items_under_it(show: Show) -> None:
    # Twice on the page, so a label id shared between menus would show up.
    page = show(_grouped(), _grouped())
    page.get_by_role("button", name="Actions").first.click()
    menu = page.get_by_role("menu").first
    project = menu.get_by_role("group", name="Project")
    sharing = menu.get_by_role("group", name="Sharing")
    expect(project.get_by_role("menuitem")).to_have_text(["Rename", "Duplicate"])
    expect(sharing.get_by_role("menuitem")).to_have_text(["Invite"])
    # Before any label, an item belongs to no group.
    grouped = menu.get_by_role("group").get_by_role("menuitem", name="Open")
    expect(grouped).to_have_count(0)
    ids = page.evaluate(
        "[...document.querySelectorAll('[role=group]')]"
        ".map(g => g.getAttribute('aria-labelledby'))"
    )
    assert len(set(ids)) == 4


def test_a_menu_in_an_rtl_drawer_stays_on_screen_and_closes_first(
    show: Show,
) -> None:
    page = show(
        Drawer().title("Filters").trigger(Button().content("Open")).content(_menu()),
        dir="rtl",
    )
    page.get_by_role("button", name="Open").click()
    drawer = page.get_by_role("dialog", name="Filters")
    expect(drawer).to_be_visible()
    actions = page.get_by_role("button", name="Actions")
    actions.focus()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    menu = page.get_by_role("menu")
    page.wait_for_function(
        """el => {
            const r = el.getBoundingClientRect();
            return r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight
                && document.elementFromPoint((r.left + r.right) / 2,
                    r.top + 10)?.closest('[role=menu]') === el;
        }""",
        arg=menu.element_handle(),
    )
    page.keyboard.press("Escape")
    expect(menu).to_be_hidden()
    expect(drawer).to_be_visible()
    expect(actions).to_be_focused()
    page.keyboard.press("Escape")
    expect(drawer).to_be_hidden()
    expect(page.get_by_role("button", name="Open")).to_be_focused()
