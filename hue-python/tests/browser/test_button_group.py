from playwright.sync_api import Page, expect

from hue.ui import Button, ButtonGroup, DropdownMenu, MenuItem
from tests.browser.conftest import Show

# Each child's computed stacking and corners, in order.
CHILDREN = """
() => [...document.querySelector('main > div').children].map(child => {
    const style = getComputedStyle(child);
    return {
        z: style.zIndex,
        start: style.borderTopLeftRadius,
        end: style.borderTopRightRadius,
    };
})
"""


def _children(page: Page) -> list[dict[str, str]]:
    return page.evaluate(CHILDREN)


def _three() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("outline").content("Export"),
        Button().variant("outline").content("Schedule"),
        Button().variant("outline").content("Share"),
    )


def test_only_the_outer_corners_are_rounded(show: Show) -> None:
    children = _children(show(_three()))
    rounded = [(c["start"] != "0px", c["end"] != "0px") for c in children]
    assert rounded == [(True, False), (False, False), (False, True)]


def test_a_focused_button_is_lifted_above_its_neighbours(show: Show) -> None:
    page = show(_three())
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Schedule")).to_be_focused()
    assert [c["z"] for c in _children(page)] == ["auto", "10", "auto"]


def _menu(name: str) -> DropdownMenu:
    return (
        DropdownMenu()
        .label(name)
        .trigger(Button().variant("outline").content(name))
        .content(MenuItem().content("Rename"))
    )


# Which corners of each control are rounded, start then end.
CONTROLS = """
() => [...document.querySelectorAll('main button')]
    .filter(button => !button.closest('[role=menu]'))
    .map(button => {
        const style = getComputedStyle(button);
        return [
            style.borderTopLeftRadius !== '0px',
            style.borderTopRightRadius !== '0px',
        ];
    })
"""


def test_a_menu_trigger_takes_the_corners_of_where_it_sits(show: Show) -> None:
    page = show(
        ButtonGroup().content(
            _menu("First"),
            Button().variant("outline").content("Middle"),
            _menu("Inner"),
            _menu("Last"),
        )
    )
    assert page.evaluate(CONTROLS) == [
        [True, False],
        [False, False],
        [False, False],
        [False, True],
    ]


def test_a_focused_menu_trigger_is_lifted_above_its_neighbours(show: Show) -> None:
    page = show(
        ButtonGroup().content(
            Button().variant("outline").content("Export"),
            _menu("More"),
            Button().variant("outline").content("Share"),
        )
    )
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="More")).to_be_focused()
    assert [c["z"] for c in _children(page)] == ["auto", "10", "auto"]


def test_an_open_menu_does_not_lift_its_group(show: Show) -> None:
    # A lifted child is a stacking context, which would hold the menu's own
    # layer down to the group's.
    page = show(ButtonGroup().content(_menu("More"), Button().content("Share")))
    page.keyboard.press("Tab")
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    assert [c["z"] for c in _children(page)] == ["auto", "auto"]
