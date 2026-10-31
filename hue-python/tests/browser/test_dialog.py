from collections.abc import Callable

import pytest
from playwright.sync_api import Locator, Page, expect

from hue.types.core import ComponentType
from hue.ui import (
    Button,
    Combobox,
    Dialog,
    Drawer,
    DropdownMenu,
    MenuItem,
    Popover,
    Select,
    SelectOption,
    Tooltip,
)
from tests.browser.conftest import TRAPPED, Show

# Each edge's midpoint, just inside it, is the panel itself and not whatever
# would show through where a clipping ancestor cut it off. Midpoints, because
# a rounded corner is not the panel's to hit.
FULLY_VISIBLE = """
el => {
    const r = el.getBoundingClientRect();
    const x = (r.left + r.right) / 2, y = (r.top + r.bottom) / 2;
    return r.width > 0 && [
        [x, r.top + 2], [x, r.bottom - 2], [r.left + 2, y], [r.right - 2, y],
    ].every(([px, py]) => el.contains(document.elementFromPoint(px, py)));
}
"""


def _options() -> tuple[SelectOption, ...]:
    return (
        SelectOption().value("apple").label("Apple"),
        SelectOption().value("banana").label("Banana"),
        SelectOption().value("cherry").label("Cherry"),
    )


def _select(page: Page) -> Locator:
    page.get_by_role("combobox", name="Fruit").click()
    return page.get_by_role("listbox")


def _menu(page: Page) -> Locator:
    page.get_by_role("button", name="Actions").click()
    return page.get_by_role("menu")


def _popover(page: Page) -> Locator:
    page.get_by_role("button", name="Share").click()
    return page.get_by_role("dialog", name="Sharing")


def _tooltip(page: Page) -> Locator:
    page.get_by_role("button", name="Copy").focus()
    return page.get_by_role("tooltip")


PANELS: dict[str, tuple[Callable[[], ComponentType], Callable[[Page], Locator]]] = {
    "select": (
        lambda: Select().name("fruit").label("Fruit").content(*_options()),
        _select,
    ),
    "combobox": (
        lambda: Combobox().name("fruit").label("Fruit").content(*_options()),
        _select,
    ),
    "menu": (
        lambda: DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(MenuItem().content("Rename"), MenuItem().content("Delete")),
        _menu,
    ),
    "popover": (
        lambda: Popover()
        .title("Sharing")
        .description("Anyone with the link can view.")
        .trigger(Button().content("Share")),
        _popover,
    ),
    "tooltip": (
        lambda: Tooltip()
        .placement("bottom")
        .content("Copy to clipboard")
        .trigger(Button().content("Copy")),
        _tooltip,
    ),
}


# Each panel once, and each holder more than once.
@pytest.mark.parametrize(
    ("panel", "overlay"),
    [
        ("select", "dialog"),
        ("combobox", "drawer"),
        ("menu", "drawer"),
        ("popover", "drawer"),
        ("tooltip", "dialog"),
    ],
)
def test_a_panel_inside_is_not_clipped(show: Show, panel: str, overlay: str) -> None:
    # The control sits last in the body, so its panel hangs past the bottom
    # of the overlay that holds it.
    build, open_panel = PANELS[panel]
    holder = Dialog() if overlay == "dialog" else Drawer().side("bottom")
    page = show(holder.title("Holder").open().content(build()))
    floating = open_panel(page)
    expect(floating).to_be_visible()
    page.wait_for_function(FULLY_VISIBLE, arg=floating.element_handle())


def test_escape_returns_focus_to_the_trigger(show: Show) -> None:
    page = show(Dialog().title("Invite").trigger(Button().content("Invite")))
    trigger = page.get_by_role("button", name="Invite")
    trigger.click()
    expect(page.get_by_role("dialog", name="Invite")).to_be_visible()
    page.wait_for_function(TRAPPED)
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Invite")).to_be_hidden()
    expect(trigger).to_be_focused()
