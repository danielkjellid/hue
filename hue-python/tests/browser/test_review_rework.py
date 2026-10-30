"""
The tooltip's keyboard clicks and the ButtonGroup's lift on the wrapped
control, checked in the combinations the rework's own tests left out.
"""

from collections.abc import Callable

import pytest
from playwright.sync_api import Page, expect

from hue import html
from hue.js import unsafe
from hue.ui import (
    Button,
    ButtonGroup,
    Dialog,
    Drawer,
    DropdownMenu,
    MenuItem,
    Popover,
    Select,
    Tooltip,
)
from tests.browser.conftest import Show

SHOWN = "Alpine.$data(document.querySelector('[role=tooltip]')).shown"


def _labelled(control) -> Tooltip:  # type: ignore[no-untyped-def]
    return Tooltip().content("More actions").trigger(control)


# Keyboard clicks on a tooltipped control


@pytest.mark.parametrize("key", ["Enter", " "])
def test_a_keyboard_click_on_a_plain_button_keeps_the_label(
    show: Show, key: str
) -> None:
    page = show(_labelled(Button().content("Copy")))
    page.keyboard.press("Tab")
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press(key)
    page.evaluate("new Promise(r => setTimeout(r))")
    assert page.evaluate(SHOWN)
    expect(page.get_by_role("tooltip")).to_be_visible()


def test_a_keyboard_click_that_renames_the_button_keeps_its_description(
    show: Show,
) -> None:
    page = show(
        _labelled(
            Button().content("Copy").on_click(unsafe("$el.textContent = 'Copied'"))
        )
    )
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    copied = page.get_by_role("button", name="Copied")
    expect(copied).to_be_focused()
    expect(copied).to_have_accessible_description("More actions")
    page.evaluate("new Promise(r => setTimeout(r))")
    assert page.evaluate(SHOWN)


def test_a_pointer_click_on_a_tooltipped_link_puts_the_label_away(show: Show) -> None:
    page = show(_labelled(html.a("Docs").href("#docs")))
    link = page.get_by_role("link", name="Docs")
    expect(link).to_have_accessible_description("More actions")
    page.keyboard.press("Tab")
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Enter")
    page.wait_for_function("location.hash === '#docs'")
    assert page.evaluate(SHOWN)
    link.click()
    assert not page.evaluate(SHOWN)


# Each overlay a keyboard click opens: where focus goes, and the label gone.
POPUPS: dict[str, tuple[Callable[[], object], str, str]] = {
    "menu": (
        lambda: DropdownMenu().label("Actions").content(MenuItem().content("Rename")),
        "menu",
        "item",
    ),
    "popover": (lambda: Popover().title("Sharing"), "dialog", "trigger"),
    "dialog": (
        lambda: Dialog().title("Settings").content(Button().content("Inside")),
        "dialog",
        "inside",
    ),
    "drawer": (
        lambda: Drawer().title("Filters").content(Button().content("Inside")),
        "dialog",
        "inside",
    ),
}


@pytest.mark.parametrize("key", ["Enter", " "])
@pytest.mark.parametrize("around", [False, True])
@pytest.mark.parametrize("popup", list(POPUPS))
def test_a_keyboard_click_that_opens_a_popup_puts_the_label_away(
    show: Show, popup: str, around: bool, key: str
) -> None:
    build, role, focus = POPUPS[popup]
    overlay = build()
    if around:
        overlay.trigger(Button().content("Open"))  # type: ignore[attr-defined]
        component = _labelled(overlay)
    else:
        component = overlay.trigger(_labelled(Button().content("Open")))  # type: ignore[attr-defined]
    page = show(component)
    trigger = page.get_by_role("button", name="Open")
    page.keyboard.press("Tab")
    expect(trigger).to_be_focused()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press(key)
    opened = page.get_by_role(role)
    expect(opened).to_be_visible()
    if focus == "item":
        expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    elif focus == "trigger":
        expect(trigger).to_be_focused()
    else:
        page.wait_for_function(
            "document.querySelector('[role=dialog]').contains(document.activeElement)"
        )
    page.wait_for_function(f"!{SHOWN}")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("Escape")
    expect(opened).to_be_hidden()
    expect(trigger).to_be_focused()


def test_a_keyboard_click_on_an_open_popover_trigger_closes_it(show: Show) -> None:
    page = show(Popover().title("Sharing").trigger(_labelled(Button().content("Open"))))
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    panel = page.get_by_role("dialog", name="Sharing")
    expect(panel).to_be_visible()
    page.keyboard.press("Enter")
    expect(panel).to_be_hidden()
    expect(page.get_by_role("button", name="Open")).to_be_focused()


# ButtonGroup


CORNERS = """
sel => [...document.querySelectorAll(sel)].map(el => {
    const s = getComputedStyle(el);
    return [s.borderTopLeftRadius !== '0px', s.borderTopRightRadius !== '0px'];
})
"""

# Whether the control draws over the column its neighbour after it is
# pulled onto (end) and the one it is pulled onto itself (start).
DRAWS_OVER = """
el => {
    const r = el.getBoundingClientRect();
    const y = r.top + 4;
    const rtl = getComputedStyle(el).direction === 'rtl';
    const at = x => el.parentElement.contains(document.elementFromPoint(x, y));
    return rtl ? [at(r.right - 0.5), at(r.left + 0.5)]
        : [at(r.left + 0.5), at(r.right - 0.5)];
}
"""


def _chevron(name: str, *, tooltip_outside: bool) -> object:
    chevron = Button().variant("outline").icon_only(name).content("v")
    menu = DropdownMenu().label(name).content(MenuItem().content("CSV"))
    if tooltip_outside:
        return Tooltip().content(name).trigger(menu.trigger(chevron))
    return menu.trigger(Tooltip().content(name).trigger(chevron))


def _mixed() -> ButtonGroup:
    return ButtonGroup().content(
        _chevron("First", tooltip_outside=True),
        _labelled(Button().variant("outline").content("Middle")),
        Popover().title("Sharing").trigger(Button().variant("outline").content("Pop")),
        _chevron("Last", tooltip_outside=False),
    )


# The controls a group draws, and their names, an icon's by its label.
CONTROLS = (
    "main button[data-hue-trigger], "
    "main button[aria-describedby]:not([data-hue-trigger])"
)
NAMES = (
    "sel => [...document.querySelectorAll(sel)]"
    ".map(b => b.getAttribute('aria-label') || b.textContent.trim())"
)


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
def test_wrapped_controls_take_the_group_corners_in_either_direction(
    show: Show, dir: str
) -> None:
    page = show(_mixed(), dir=dir)
    corners = page.evaluate(CORNERS, CONTROLS)
    # Physical left/right: in rtl the first child sits on the right.
    first, last = (
        ([True, False], [False, True])
        if dir == "ltr"
        else ([False, True], [True, False])
    )
    by_name = dict(
        zip(
            page.evaluate(NAMES, CONTROLS),
            corners,
            strict=True,
        )
    )
    assert by_name == {
        "First": first,
        "Middle": [False, False],
        "Pop": [False, False],
        "Last": last,
    }


def test_the_lift_probe_sees_an_unfocused_neighbour_on_top(show: Show) -> None:
    # Without focus the next control is drawn over the shared column, so the
    # probe the lift tests use can tell the difference.
    page = show(_mixed())
    middle = page.get_by_role("button", name="Middle")
    assert middle.evaluate(DRAWS_OVER) == [True, False]


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
@pytest.mark.parametrize("name", ["First", "Middle", "Pop", "Last"])
def test_a_focused_wrapped_control_draws_over_both_neighbours(
    show: Show, dir: str, name: str
) -> None:
    page = show(_mixed(), dir=dir)
    control = page.get_by_role("button", name=name, exact=True)
    for _ in range(["First", "Middle", "Pop", "Last"].index(name) + 1):
        page.keyboard.press("Tab")
    expect(control).to_be_focused()
    # Clear of the tooltip bubble, which may sit on top of it.
    page.keyboard.press("Escape")
    page.wait_for_function(
        "[...document.querySelectorAll('[role=tooltip]')]"
        ".every(t => !t.checkVisibility({ opacityProperty: true }))"
    )
    start, end = control.evaluate(DRAWS_OVER)
    if name != "First":
        assert start
    if name != "Last":
        assert end


def test_a_disabled_middle_button_keeps_square_corners(show: Show) -> None:
    page = show(
        ButtonGroup().content(
            Button().variant("outline").content("A"),
            _labelled(Button().variant("outline").disabled().content("B")),
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
    alone = show(Select.example())
    expected = alone.evaluate(CORNERS, "main [role=combobox]")
    page = show(
        ButtonGroup().content(
            Button().variant("outline").content("A"), Select.example()
        )
    )
    assert page.evaluate(CORNERS, "main [role=combobox]") == expected


def _open_by_keyboard(page: Page, name: str, role: str) -> None:
    page.get_by_role("button", name=name, exact=True).focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role(role).first).to_be_visible()


ON_TOP = """
el => [...el.querySelectorAll('*')].concat([el]).length > 0 && (() => {
    const r = el.getBoundingClientRect();
    const pts = [[r.left + 10, r.bottom - 6], [r.right - 10, r.bottom - 6],
                 [(r.left + r.right) / 2, (r.top + r.bottom) / 2]];
    return pts.every(([x, y]) => el.contains(document.elementFromPoint(x, y)));
})()
"""


@pytest.mark.parametrize("popup", ["popover", "menu"])
def test_an_open_panel_from_a_group_is_above_a_fixed_layer(
    show: Show, popup: str
) -> None:
    page = show(
        _mixed(),
        html.div().class_("fixed inset-x-0 top-20 z-50 h-60 bg-surface"),
    )
    if popup == "popover":
        _open_by_keyboard(page, "Pop", "dialog")
        panel = page.get_by_role("dialog", name="Sharing")
    else:
        page.get_by_role("button", name="First").focus()
        page.keyboard.press("ArrowDown")
        panel = page.get_by_role("menu", name="First")
        expect(panel).to_be_visible()
    page.wait_for_function(ON_TOP, arg=panel.element_handle(), timeout=3000)


@pytest.mark.parametrize("popup", ["popover", "menu"])
def test_an_open_panel_is_above_a_sibling_group(show: Show, popup: str) -> None:
    below = ButtonGroup().content(
        *(Button().variant("outline").content(f"Below {i}") for i in range(6))
    )
    page = show(_mixed(), html.div().class_("h-1"), below)
    if popup == "popover":
        _open_by_keyboard(page, "Pop", "dialog")
        panel = page.get_by_role("dialog", name="Sharing")
    else:
        page.get_by_role("button", name="First").focus()
        page.keyboard.press("ArrowDown")
        panel = page.get_by_role("menu", name="First")
        expect(panel).to_be_visible()
    page.wait_for_function(ON_TOP, arg=panel.element_handle(), timeout=3000)
