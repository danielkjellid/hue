"""
What the group height and Combobox scroll rework could have broken.
"""

import pytest
from htmy import html
from playwright.sync_api import Locator, Page, expect

from hue.ui import (
    Button,
    Combobox,
    Dialog,
    NumberInput,
    PasswordInput,
    SelectOption,
    Text,
    TextInput,
)
from hue.ui._styles import ControlSize
from hue.ui.atoms.icon import HueIcon
from tests.browser.conftest import Show

_FRAMES = (
    "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
)


def _box(locator: Locator) -> dict[str, float]:
    box = locator.bounding_box()
    assert box is not None
    return box


def _long(value: str | None = "v39", multiple: bool = False) -> Combobox:
    combobox = (
        Combobox()
        .name("fruit")
        .label("Fruit")
        .content(
            *(SelectOption().value(f"v{i}").label(f"Option {i:02}") for i in range(40))
        )
    )
    if multiple:
        combobox = combobox.multiple()
    return combobox.value(value) if value else combobox


def _list(page: Page) -> Locator:
    return page.get_by_role("listbox")


def _in_view(page: Page, value: str) -> bool:
    return page.evaluate(
        """value => {
            const o = document.querySelector(`[role=option][data-value=${value}]`);
            const l = document.querySelector('[role=listbox]');
            const a = o.getBoundingClientRect(), b = l.getBoundingClientRect();
            return a.height > 0 && a.top >= b.top - 1 && a.bottom <= b.bottom + 1;
        }""",
        value,
    )


def _settle(page: Page) -> None:
    for _ in range(3):
        page.evaluate(_FRAMES)


def test_focus_open_scrolls_to_the_chosen_option(show: Show) -> None:
    page = show(_long())
    page.get_by_role("combobox", name="Fruit").focus()
    page.wait_for_function(
        "() => document.querySelector('[role=listbox]').scrollTop > 0"
    )
    assert _in_view(page, "v39")


def test_wheel_scrolling_an_open_list_stays_put(show: Show) -> None:
    page = show(_long())
    page.get_by_role("combobox", name="Fruit").focus()
    page.wait_for_function(
        "() => document.querySelector('[role=listbox]').scrollTop > 0"
    )
    _settle(page)
    bottom = _list(page).evaluate("el => el.scrollTop")
    box = _box(_list(page))
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.wheel(0, -600)
    page.wait_for_function(
        f"() => document.querySelector('[role=listbox]').scrollTop < {bottom}"
    )
    _settle(page)
    wheeled = _list(page).evaluate("el => el.scrollTop")
    assert wheeled < bottom
    # Dragging the scrollbar sets scrollTop the same way.
    _list(page).evaluate("el => { el.scrollTop = 0 }")
    _settle(page)
    assert _list(page).evaluate("el => el.scrollTop") == 0


def test_a_viewport_resize_while_open_keeps_the_users_scroll(show: Show) -> None:
    page = show(_long(), height=800)
    page.get_by_role("combobox", name="Fruit").focus()
    page.wait_for_function(
        "() => document.querySelector('[role=listbox]').scrollTop > 0"
    )
    _settle(page)
    _list(page).evaluate("el => { el.scrollTop = 0 }")
    page.set_viewport_size({"width": 1000, "height": 500})
    _settle(page)
    assert _list(page).evaluate("el => el.scrollTop") == 0


def test_filtering_scrolls_the_first_match_into_view(show: Show) -> None:
    page = show(_long(value=None))
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    field.press_sequentially("Option 3")
    page.wait_for_function("() => document.querySelector('[data-active]') !== null")
    _settle(page)
    expect(page.locator("[role=option][data-active]")).to_have_attribute(
        "data-value", "v30"
    )
    assert _in_view(page, "v30")


def test_focus_open_does_not_scroll_the_page(show: Show) -> None:
    page = show(
        html.div(style="height: 1000px"),
        _long(),
        html.div(style="height: 1500px"),
        height=800,
    )
    # The field near the bottom of the viewport, so the list overflows it.
    page.evaluate("window.scrollTo(0, 300)")
    _settle(page)
    page.get_by_role("combobox", name="Fruit").evaluate(
        "el => el.focus({ preventScroll: true })"
    )
    page.wait_for_function(
        "() => document.querySelector('[role=listbox]').scrollTop > 0"
    )
    _settle(page)
    assert page.evaluate("window.scrollY") == 300


def test_open_in_a_scrolled_container_leaves_the_container_alone(show: Show) -> None:
    page = show(
        html.div(
            html.div(style="height: 300px"),
            _long(),
            html.div(style="height: 900px"),
            id="box",
            style="height: 400px; overflow: auto",
        )
    )
    page.evaluate("document.getElementById('box').scrollTop = 200")
    page.get_by_role("combobox", name="Fruit").focus()
    page.wait_for_function(
        "() => document.querySelector('[role=listbox]').scrollTop > 0"
    )
    _settle(page)
    assert page.evaluate("document.getElementById('box').scrollTop") == 200
    assert page.evaluate("window.scrollY") == 0
    assert _in_view(page, "v39")


def test_open_in_a_dialog_scrolls_to_the_chosen_option(show: Show) -> None:
    dialog = Dialog().title("Pick").trigger(Button().content("Open")).content(_long())
    page = show(dialog)
    page.get_by_role("button", name="Open").click()
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    expect(field).to_have_attribute("aria-expanded", "true")
    page.wait_for_function(
        "() => document.querySelector('[role=listbox]').scrollTop > 0"
    )
    assert _in_view(page, "v39")
    expect(page.get_by_role("dialog")).to_be_visible()


def test_multiple_choosing_far_down_keeps_the_option_in_view(show: Show) -> None:
    page = show(_long(value=None, multiple=True), width=420)
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    for _ in range(35):
        page.keyboard.press("ArrowDown")
    for _ in range(3):
        page.keyboard.press("Enter")
        page.keyboard.press("ArrowDown")
    expect(page.get_by_role("button", name="Remove Option 35")).to_be_visible()
    _settle(page)
    active = page.locator("[role=option][data-active]").get_attribute("data-value")
    assert active is not None
    assert _in_view(page, active)
    # The user's own scroll survives the tokens settling.
    _list(page).evaluate("el => { el.scrollTop = 0 }")
    _settle(page)
    assert _list(page).evaluate("el => el.scrollTop") == 0


# Groups


def _plain_and(size: ControlSize, field: TextInput) -> list[object]:
    return [TextInput().name("plain").label("Plain").size(size), field]


def _group(page: Page) -> Locator:
    return page.locator("div:has(> input[name=g])")


def _check_group(page: Page) -> None:
    group = _box(_group(page))
    assert group["height"] == _box(page.get_by_label("Plain"))["height"]
    assert _box(page.locator("input[name=g]"))["height"] == group["height"] - 2
    for part in _group(page).locator("button").all():
        box = _box(part)
        assert box["y"] >= group["y"]
        assert box["y"] + box["height"] <= group["y"] + group["height"]


def _coarse(page: Page) -> None:
    session = page.context.new_cdp_session(page)
    session.send(
        "Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1}
    )
    assert page.evaluate("matchMedia('(pointer: coarse)').matches")


_FIELDS = {
    "labelled xs": lambda s: TextInput()
    .name("g")
    .label("G")
    .size(s)
    .action(Button().size("xs").content(Text("Go"))),
    "labelled lg": lambda s: TextInput()
    .name("g")
    .label("G")
    .size(s)
    .action(Button().size("lg").content(Text("Go"))),
    "icon xs": lambda s: TextInput()
    .name("g")
    .label("G")
    .size(s)
    .action(
        Button().variant("ghost").size("xs").icon_only("Clear").content(HueIcon("x"))
    ),
    "password": lambda s: PasswordInput().name("g").label("G").size(s).revealable(),
    "password readonly": lambda s: PasswordInput()
    .name("g")
    .label("G")
    .size(s)
    .readonly()
    .revealable(),
    "password disabled": lambda s: PasswordInput()
    .name("g")
    .label("G")
    .size(s)
    .disabled()
    .revealable(),
    "number both": lambda s: NumberInput()
    .name("g")
    .label("G")
    .size(s)
    .prefix("$")
    .suffix("kg"),
}


@pytest.mark.parametrize("kind", list(_FIELDS))
@pytest.mark.parametrize("size", ["sm", "md", "lg"])
@pytest.mark.parametrize("pointer", ["fine", "coarse"])
@pytest.mark.parametrize("dir", [None, "rtl"], ids=["ltr", "rtl"])
def test_group_heights(
    show: Show, kind: str, size: ControlSize, pointer: str, dir: str | None
) -> None:
    page = show(*_plain_and(size, _FIELDS[kind](size)), dir=dir)  # type: ignore[arg-type]
    if pointer == "coarse":
        _coarse(page)
    _check_group(page)


def test_a_taller_input_grows_its_group(show: Show) -> None:
    page = show(TextInput().name("g").label("G").prefix("$").class_("h-12"))
    group = _box(_group(page))
    control = _box(page.locator("input[name=g]"))
    assert control["y"] >= group["y"]
    assert control["y"] + control["height"] <= group["y"] + group["height"]


def test_number_steppers_still_step(show: Show) -> None:
    page = show(NumberInput().name("g").label("G").suffix("kg").value("1"))
    field = page.locator("input[name=g]")
    field.focus()
    page.keyboard.press("ArrowUp")
    expect(field).to_have_value("2")


@pytest.mark.parametrize("size", ["sm", "md", "lg"])
def test_password_toggle_matches_other_small_icon_buttons_on_touch(
    show: Show, size: ControlSize
) -> None:
    # The toggle is at least as large as the xs buttons hue uses elsewhere,
    # and at least 24px, the WCAG 2.2 AA target minimum.
    page = show(PasswordInput().name("g").label("G").size(size).revealable())
    _coarse(page)
    toggle = _box(page.get_by_role("button", name="Show password"))
    assert toggle["height"] >= 24 and toggle["width"] >= 24
    page.get_by_role("button", name="Show password").click()
    expect(page.locator("input[name=g]")).to_have_attribute("type", "text")
