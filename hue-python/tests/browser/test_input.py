from collections.abc import Callable

import pytest
from playwright.sync_api import Locator, Page, expect

from hue.ui import (
    Button,
    NativeSelect,
    NumberInput,
    PasswordInput,
    Select,
    SelectOption,
    Text,
    TextInput,
)
from hue.ui._styles import ControlSize
from hue.ui.atoms.icon import HueIcon
from tests.browser._fields import css, row_of_pixels, still, token
from tests.browser.conftest import Show


def _group(page: Page, name: str) -> Locator:
    return page.locator(f"div:has(> input[name={name}])")


def _ring(page: Page, colour: str, width: int) -> str:
    return f"{token(page, colour)} 0px 0px 0px {width}px"


def _box(locator: Locator) -> dict[str, float]:
    box = locator.bounding_box()
    assert box is not None
    return box


def _pixel(page: Page, x: float, y: float) -> str:
    return row_of_pixels(page, x, round(y), 1)[0]


def _coarse(page: Page) -> None:
    session = page.context.new_cdp_session(page)
    session.send(
        "Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1}
    )
    assert page.evaluate("matchMedia('(pointer: coarse)').matches")


@pytest.mark.parametrize("grouped", [False, True], ids=["plain", "group"])
def test_hover_shows_and_focus_outranks_it(show: Show, grouped: bool) -> None:
    field = TextInput().name("site").label("Site")
    page = still(show(field.prefix("https://") if grouped else field))
    control = page.get_by_label("Site")
    border = _group(page, "site") if grouped else control
    control.hover()
    expect(border).to_have_css("border-top-color", token(page, "border-hover"))
    control.click()
    control.hover()
    expect(border).to_have_css("border-top-color", token(page, "accent"))


@pytest.mark.parametrize("grouped", [False, True], ids=["plain", "group"])
def test_an_invalid_field_stays_red_on_hover_and_focus(
    show: Show, grouped: bool
) -> None:
    field = TextInput().name("site").label("Site").error("Bad")
    page = still(show(field.prefix("https://") if grouped else field))
    control = page.get_by_label("Site")
    border = _group(page, "site") if grouped else control
    control.hover()
    expect(border).to_have_css("border-top-color", token(page, "danger"))
    control.click()
    expect(border).to_have_css("border-top-color", token(page, "danger"))
    shadow = css(border, "boxShadow")
    assert _ring(page, "danger", 2) in shadow
    assert token(page, "accent-subtle") not in shadow


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_valid_focus_keeps_its_halo(show: Show, theme: str) -> None:
    page = still(show(TextInput().name("email").label("Email"), theme=theme))
    field = page.get_by_label("Email")
    field.click()
    assert _ring(page, "accent-subtle", 3) in css(field, "boxShadow")


def test_a_focused_group_draws_its_halo_all_round(show: Show) -> None:
    page = still(show(TextInput().name("g").label("G").prefix("https://")))
    page.locator("input[name=g]").click()
    group = _box(_group(page, "g"))
    halo = token(page, "accent-subtle")
    middle = group["x"] + group["width"] / 2
    assert _pixel(page, middle, group["y"] - 2) == halo
    assert _pixel(page, middle, group["y"] + group["height"] + 1) == halo


def test_disabled_group_ignores_hover(show: Show) -> None:
    page = still(
        show(TextInput().name("site").label("Site").prefix("https://").disabled())
    )
    page.get_by_label("Site").hover(force=True)
    expect(_group(page, "site")).to_have_css(
        "border-top-color", token(page, "border-input")
    )


@pytest.mark.parametrize("state", ["disabled", "readonly"])
def test_a_disabled_or_readonly_group_is_sunken_behind_the_input(
    show: Show, state: str
) -> None:
    field = TextInput().name("g").label("G").prefix("https://")
    field = field.disabled() if state == "disabled" else field.readonly()
    page = still(show(field))
    control = _box(page.locator("input[name=g]"))
    # Away from the text, near the end of the input.
    x = control["x"] + control["width"] - 6
    assert _pixel(page, x, control["y"] + control["height"] / 2) == token(
        page, "surface-sunken"
    )


def test_reveal_toggle_is_a_touch_target_and_shows_the_password(show: Show) -> None:
    # The smallest size, where the toggle is likeliest to fall under 24px.
    page = show(PasswordInput().name("g").label("G").size("sm").revealable())
    _coarse(page)
    toggle = page.get_by_role("button", name="Show password")
    box = _box(toggle)
    assert box["height"] >= 24 and box["width"] >= 24
    toggle.click()
    expect(page.locator("input[name=g]")).to_have_attribute("type", "text")


def test_disabled_password_cannot_be_revealed(show: Show) -> None:
    page = show(
        PasswordInput().name("password").label("Password").revealable().disabled()
    )
    toggle = page.get_by_role("button", name="Show password")
    expect(toggle).to_be_disabled()
    toggle.click(force=True)
    expect(page.get_by_label("Password", exact=True)).to_have_attribute(
        "type", "password"
    )


_GROUPED: list[Callable[[str, ControlSize], TextInput]] = [
    lambda n, s: TextInput().name(n).label(n).size(s).prefix("https://"),
    lambda n, s: TextInput().name(n).label(n).size(s).suffix(".com"),
    lambda n, s: TextInput().name(n).label(n).size(s).prefix("$").suffix("USD"),
    lambda n, s: TextInput()
    .name(n)
    .label(n)
    .size(s)
    .action(Button().size("xs").content(Text("Go"))),
    lambda n, s: TextInput()
    .name(n)
    .label(n)
    .size(s)
    .action(Button().size("lg").content(Text("Go"))),
    lambda n, s: TextInput()
    .name(n)
    .label(n)
    .size(s)
    .action(
        Button().variant("ghost").size("xs").icon_only("Clear").content(HueIcon("x"))
    ),
    lambda n, s: PasswordInput().name(n).label(n).size(s).revealable(),
    lambda n, s: PasswordInput().name(n).label(n).size(s).readonly().revealable(),
    lambda n, s: PasswordInput().name(n).label(n).size(s).disabled().revealable(),
    lambda n, s: NumberInput().name(n).label(n).size(s).prefix("$").suffix("kg"),
]


@pytest.mark.parametrize("size", ["sm", "lg"])
@pytest.mark.parametrize("pointer", ["fine", "coarse"])
def test_every_control_is_as_tall_as_a_plain_field(
    show: Show, size: ControlSize, pointer: str
) -> None:
    names = [f"g{i}" for i in range(len(_GROUPED))]
    page = show(
        TextInput().name("plain").label("Plain").size(size),
        NativeSelect().name("n").label("Native").size(size).options([("a", "A")]),
        Select()
        .name("s")
        .label("Custom")
        .size(size)
        .content(SelectOption().value("a").label("A")),
        *(make(name, size) for make, name in zip(_GROUPED, names, strict=True)),
    )
    if pointer == "coarse":
        _coarse(page)
    plain = _box(page.get_by_label("Plain"))["height"]
    assert _box(page.get_by_label("Native"))["height"] == plain
    assert _box(page.get_by_role("combobox", name="Custom"))["height"] == plain
    for name in names:
        group = _box(_group(page, name))
        assert group["height"] == plain, name
        # The input fills the inside of the border.
        control = _box(page.locator(f"input[name={name}]"))
        assert control["height"] == group["height"] - 2, name
        # Nothing attached pokes out past the group's border.
        for part in _group(page, name).locator("button").all():
            box = _box(part)
            assert box["y"] >= group["y"], name
            assert box["y"] + box["height"] <= group["y"] + group["height"], name


def test_an_attached_button_fills_the_group(show: Show) -> None:
    action = Button().content(Text("Copy"))
    page = show(TextInput().name("key").label("Key").action(action))
    group = _box(_group(page, "key"))
    button = _box(page.get_by_role("button", name="Copy"))
    assert button["height"] == group["height"] - 2


@pytest.mark.parametrize(
    ("field", "dir"),
    [
        (PasswordInput().name("g").label("G").revealable(), None),
        (PasswordInput().name("g").label("G").revealable(), "rtl"),
        (TextInput().name("g").label("G").prefix("https://"), "rtl"),
        (TextInput().name("g").label("G").leading_icon(Text("@")), "rtl"),
    ],
    ids=["input first", "input first rtl", "input last rtl", "icon first rtl"],
)
def test_a_fill_on_a_grouped_input_leaves_the_border_alone(
    show: Show, field: TextInput, dir: str | None
) -> None:
    page = still(show(field, dir=dir))
    group = _box(_group(page, "g"))
    top, bottom = group["y"], group["y"] + group["height"] - 1
    # Just inside the group's top corners, outside their curve.
    corners = [(group["x"] + 1, top), (group["x"] + group["width"] - 2, top)]
    before = [_pixel(page, x, y) for x, y in corners]
    control = page.locator("input[name=g]")
    # Chrome's autofill colour, painted the way autofill paints it.
    control.evaluate("el => { el.style.background = 'rgb(232, 240, 254)' }")
    box = _box(control)
    middle = box["x"] + box["width"] / 2
    border = token(page, "border-input")
    assert _pixel(page, middle, top) == border
    assert _pixel(page, middle, bottom) == border
    assert [_pixel(page, x, y) for x, y in corners] == before


# The group's height is a minimum, so a taller input grows it.
def test_a_taller_grouped_input_stays_inside_its_group(show: Show) -> None:
    page = show(TextInput().name("g").label("G").prefix("$").class_("h-12"))
    group = _box(_group(page, "g"))
    control = _box(page.locator("input[name=g]"))
    assert control["y"] >= group["y"]
    assert control["y"] + control["height"] <= group["y"] + group["height"]
