import pytest
from playwright.sync_api import Page, expect

from hue import html
from hue.ui import (
    Button,
    ButtonGroup,
    DropdownMenu,
    MenuItem,
    Popover,
    Select,
    SelectOption,
    Tooltip,
)
from hue.ui.base import ChainableComponent
from tests.browser.conftest import Show

CORNERS = """
sel => [...document.querySelectorAll(sel)].map(el => {
    const s = getComputedStyle(el);
    return [s.borderTopLeftRadius !== '0px', s.borderTopRightRadius !== '0px'];
})
"""

# Whether the control draws over the column it is pulled onto (start) and the
# one its neighbour after it is pulled onto (end).
DRAWS_OVER = """
el => {
    const r = el.getBoundingClientRect();
    const y = r.top + 4;
    const rtl = getComputedStyle(el).direction === 'rtl';
    const child = el.closest('main > div > *');
    const at = x => child.contains(document.elementFromPoint(x, y));
    return rtl ? [at(r.right - 0.5), at(r.left + 0.5)]
        : [at(r.left + 0.5), at(r.right - 0.5)];
}
"""


def _chevron(name: str, *, tooltip_outside: bool) -> ChainableComponent:
    chevron = Button().variant("outline").icon_only(name).content("v")
    menu = DropdownMenu().label(name).content(MenuItem().content("CSV"))
    if tooltip_outside:
        return Tooltip().content(name).trigger(menu.trigger(chevron))
    return menu.trigger(Tooltip().content(name).trigger(chevron))


# Every way a control sits in a group: wrapped in a Tooltip either way round
# with a menu, a plain button, a tooltipped one, a menu and a popover trigger.
NAMES = ["First", "Plain", "Middle", "Inner", "Pop", "Last"]


def _mixed() -> ButtonGroup:
    return ButtonGroup().content(
        _chevron("First", tooltip_outside=True),
        Button().variant("outline").content("Plain"),
        Tooltip()
        .placement("end")
        .content("More actions")
        .trigger(Button().variant("outline").content("Middle")),
        DropdownMenu()
        .label("Inner")
        .trigger(Button().variant("outline").content("Inner"))
        .content(MenuItem().content("Rename")),
        Popover().title("Sharing").trigger(Button().variant("outline").content("Pop")),
        _chevron("Last", tooltip_outside=False),
    )


# The controls a group draws, and their names, an icon's by its label.
CONTROLS = "main > div:first-child button:not([role=menu] *, [role=dialog] *)"
LABELS = (
    "sel => [...document.querySelectorAll(sel)]"
    ".map(b => b.getAttribute('aria-label') || b.textContent.trim())"
)


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
def test_only_the_outer_corners_are_rounded(show: Show, dir: str) -> None:
    page = show(_mixed(), dir=dir)
    corners = page.evaluate(CORNERS, CONTROLS)
    # Physical left/right: in rtl the first child sits on the right.
    first, last = [True, False], [False, True]
    if dir == "rtl":
        first, last = last, first
    square = [False, False]
    assert dict(zip(page.evaluate(LABELS, CONTROLS), corners, strict=True)) == {
        "First": first,
        "Plain": square,
        "Middle": square,
        "Inner": square,
        "Pop": square,
        "Last": last,
    }


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
def test_a_focused_control_draws_over_both_neighbours(show: Show, dir: str) -> None:
    page = show(_mixed(), dir=dir)
    # Unfocused, the next control is drawn over the shared column, so the
    # probe can tell the difference.
    assert page.get_by_role("button", name="Plain").evaluate(DRAWS_OVER) == [
        True,
        False,
    ]
    for name in NAMES:
        page.keyboard.press("Tab")
        control = page.get_by_role("button", name=name, exact=True)
        expect(control).to_be_focused()
        if name == "Middle" and dir == "ltr":
            # Its bubble hangs over the next button and stays on top of it.
            bubble = page.get_by_role("tooltip", name="More actions")
            page.wait_for_function(
                """el => {
                    const r = el.getBoundingClientRect();
                    return el.contains(document.elementFromPoint(
                        r.left + 4, (r.top + r.bottom) / 2));
                }""",
                arg=bubble.element_handle(),
            )
        # Clear of any tooltip bubble, which may sit on top of it until it has
        # faded out of the layout.
        page.keyboard.press("Escape")
        page.wait_for_function(
            "[...document.querySelectorAll('[role=tooltip]')]"
            ".every(t => !t.checkVisibility())"
        )
        start, end = control.evaluate(DRAWS_OVER)
        assert start or name == "First", name
        assert end or name == "Last", name


def test_the_documented_split_button_keeps_its_corners(show: Show) -> None:
    page = show(
        ButtonGroup().content(
            Button().variant("outline").size("sm").content("Export"),
            DropdownMenu()
            .label("Export options")
            .placement("bottom-end")
            .trigger(
                Button()
                .variant("outline")
                .size("sm")
                .icon_only("Export options")
                .class_("rounded-s-none")
                .content("v")
            )
            .content(MenuItem().content("Export as CSV")),
        )
    )
    assert page.evaluate(CORNERS, CONTROLS) == [[True, False], [False, True]]


def test_a_disabled_middle_button_keeps_square_corners(show: Show) -> None:
    page = show(
        ButtonGroup().content(
            Button().variant("outline").content("A"),
            Tooltip()
            .content("More actions")
            .trigger(Button().variant("outline").disabled().content("B")),
            Button().variant("outline").content("C"),
        )
    )
    assert page.evaluate(CORNERS, "main button") == [
        [True, False],
        [False, False],
        [False, True],
    ]
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="C")).to_be_focused()


def test_a_select_in_a_group_keeps_its_own_corners(show: Show) -> None:
    def select() -> Select:
        return (
            Select()
            .name("fruit")
            .label("Fruit")
            .content(SelectOption().value("apple").label("Apple"))
        )

    expected = show(select()).evaluate(CORNERS, "main [role=combobox]")
    page = show(
        ButtonGroup().content(Button().variant("outline").content("A"), select())
    )
    assert page.evaluate(CORNERS, "main [role=combobox]") == expected


ON_TOP = """
el => {
    const r = el.getBoundingClientRect();
    const pts = [[r.left + 10, r.bottom - 6], [r.right - 10, r.bottom - 6],
                 [(r.left + r.right) / 2, (r.top + r.bottom) / 2]];
    return pts.every(([x, y]) => el.contains(document.elementFromPoint(x, y)));
}
"""


def _open_panel(page: Page, popup: str) -> None:
    if popup == "popover":
        page.get_by_role("button", name="Pop").focus()
        page.keyboard.press("Enter")
        panel = page.get_by_role("dialog", name="Sharing")
    else:
        page.get_by_role("button", name="First").focus()
        page.keyboard.press("ArrowDown")
        panel = page.get_by_role("menu", name="First")
    expect(panel).to_be_visible()
    page.wait_for_function(ON_TOP, arg=panel.element_handle(), timeout=3000)


@pytest.mark.parametrize("popup", ["popover", "menu"])
def test_an_open_panel_from_a_group_is_above_a_fixed_layer(
    show: Show, popup: str
) -> None:
    # A fixed bar with its own layer under where the panel hangs, as a data
    # table's selection bar is (z-50).
    page = show(
        _mixed(),
        html.div().class_("fixed inset-x-0 top-20 z-50 h-60 bg-surface"),
    )
    _open_panel(page, popup)


@pytest.mark.parametrize("popup", ["popover", "menu"])
def test_an_open_panel_is_above_a_sibling_group(show: Show, popup: str) -> None:
    # A lifted child is a stacking context, which would hold the panel's own
    # layer down to the group's.
    below = ButtonGroup().content(
        *(Button().variant("outline").content(f"Below {i}") for i in range(6))
    )
    page = show(_mixed(), html.div().class_("h-1"), below)
    _open_panel(page, popup)
