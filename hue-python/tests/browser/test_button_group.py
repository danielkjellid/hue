import pytest
from playwright.sync_api import Page, expect

from hue import html
from hue.ui import Button, ButtonGroup, DropdownMenu, MenuItem, Popover, Tooltip
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


# Whether the control draws over the column its next neighbour is pulled onto,
# which is where that neighbour would otherwise cover its ring.
ON_TOP = """
el => {
    const r = el.getBoundingClientRect();
    const y = (r.top + r.bottom) / 2;
    return el.contains(document.elementFromPoint(r.right - 0.5, y));
}
"""


def _on_top(page: Page, name: str) -> bool:
    control = page.get_by_role("button", name=name)
    expect(control).to_be_focused()
    return control.evaluate(ON_TOP)


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
    assert not page.get_by_role("button", name="More").evaluate(ON_TOP)
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    assert _on_top(page, "More")


def test_an_open_menu_does_not_lift_its_group(show: Show) -> None:
    # A lifted child is a stacking context, which would hold the menu's own
    # layer down to the group's.
    page = show(ButtonGroup().content(_menu("More"), Button().content("Share")))
    page.keyboard.press("Tab")
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    assert [c["z"] for c in _children(page)] == ["auto", "auto"]


def _split_with_a_tooltipped_chevron(tooltip_outside: bool) -> ButtonGroup:
    chevron = Button().variant("outline").icon_only("Export options").content("v")
    menu = DropdownMenu().label("Export options").content(MenuItem().content("CSV"))
    if tooltip_outside:
        middle = Tooltip().content("More").trigger(menu.trigger(chevron))
    else:
        middle = menu.trigger(Tooltip().content("More").trigger(chevron))
    return ButtonGroup().content(
        Button().variant("outline").content("Export"),
        middle,
        Button().variant("outline").content("Share"),
    )


@pytest.mark.parametrize("tooltip_outside", [False, True])
def test_a_tooltipped_menu_trigger_in_a_group_is_squared(
    show: Show, tooltip_outside: bool
) -> None:
    page = show(_split_with_a_tooltipped_chevron(tooltip_outside))
    assert page.evaluate(CONTROLS) == [[True, False], [False, False], [False, True]]


@pytest.mark.parametrize("tooltip_outside", [False, True])
def test_a_tooltipped_menu_trigger_in_a_group_is_lifted(
    show: Show, tooltip_outside: bool
) -> None:
    page = show(_split_with_a_tooltipped_chevron(tooltip_outside))
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    assert _on_top(page, "Export options")


def test_a_keyboard_opened_popover_in_a_group_stays_above_the_page(
    show: Show,
) -> None:
    # A fixed bar with its own layer under where the panel hangs, as a data
    # table's selection bar is (z-50). The panel is z-70, so it belongs above.
    page = show(
        ButtonGroup().content(
            Button().variant("outline").content("Export"),
            Popover()
            .title("Sharing")
            .trigger(Button().variant("outline").content("Share")),
        ),
        html.div().class_("fixed inset-x-0 top-20 z-50 h-40 bg-surface"),
    )
    page.get_by_role("button", name="Share").focus()
    page.keyboard.press("Enter")
    panel = page.get_by_role("dialog", name="Sharing")
    expect(panel).to_be_visible()
    page.wait_for_function(
        """el => {
            const r = el.getBoundingClientRect();
            return r.bottom > 100
                && el.contains(document.elementFromPoint(r.left + 20, r.bottom - 8));
        }""",
        arg=panel.element_handle(),
    )
