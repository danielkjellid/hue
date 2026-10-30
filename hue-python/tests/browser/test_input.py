import pytest
from playwright.sync_api import Locator, Page, expect

from hue.ui import Button, PasswordInput, Text, TextInput
from hue.ui._styles import ControlSize
from tests.browser._fields import css, still, token
from tests.browser.conftest import Show


def test_hover_keeps_an_invalid_border_red(show: Show) -> None:
    page = still(show(TextInput().name("email").label("Email").error("Required")))
    field = page.get_by_label("Email")
    field.hover()
    expect(field).to_have_css("border-top-color", token(page, "danger"))


def test_focused_invalid_group_is_not_accent(show: Show) -> None:
    page = still(
        show(TextInput().name("site").label("Site").prefix("https://").error("Bad"))
    )
    page.get_by_label("Site").click()
    group = page.locator("div:has(> input[name=site])")
    expect(group).to_have_css("border-top-color", token(page, "danger"))
    assert token(page, "accent-subtle") not in css(group, "boxShadow")


def _password() -> PasswordInput:
    return PasswordInput().name("password").label("Password").revealable()


def test_reveal_toggle_shows_the_password(show: Show) -> None:
    page = show(_password())
    page.get_by_role("button", name="Show password").click()
    expect(page.get_by_label("Password", exact=True)).to_have_attribute("type", "text")


def test_disabled_password_cannot_be_revealed(show: Show) -> None:
    page = show(_password().disabled())
    toggle = page.get_by_role("button", name="Show password")
    expect(toggle).to_be_disabled()
    toggle.click(force=True)
    expect(page.get_by_label("Password", exact=True)).to_have_attribute(
        "type", "password"
    )


def _group(page: Page, name: str) -> Locator:
    return page.locator(f"div:has(> input[name={name}])")


def _ring(page: Page, colour: str, width: int) -> str:
    return f"{token(page, colour)} 0px 0px 0px {width}px"


def test_focus_outranks_hover(show: Show) -> None:
    page = still(show(TextInput().name("email").label("Email")))
    field = page.get_by_label("Email")
    field.click()
    field.hover()
    expect(field).to_have_css("border-top-color", token(page, "accent"))


def test_focus_outranks_hover_in_a_group(show: Show) -> None:
    page = still(show(TextInput().name("site").label("Site").prefix("https://")))
    field = page.get_by_label("Site")
    field.click()
    field.hover()
    expect(_group(page, "site")).to_have_css("border-top-color", token(page, "accent"))


def test_hover_without_focus_still_shows(show: Show) -> None:
    page = still(show(TextInput().name("email").label("Email")))
    field = page.get_by_label("Email")
    field.hover()
    expect(field).to_have_css("border-top-color", token(page, "border-hover"))


def test_hover_without_focus_still_shows_in_a_group(show: Show) -> None:
    page = still(show(TextInput().name("site").label("Site").prefix("https://")))
    page.get_by_label("Site").hover()
    expect(_group(page, "site")).to_have_css(
        "border-top-color", token(page, "border-hover")
    )


def test_valid_focus_keeps_its_halo(show: Show) -> None:
    page = still(show(TextInput().name("email").label("Email")))
    field = page.get_by_label("Email")
    field.click()
    assert _ring(page, "accent-subtle", 3) in css(field, "boxShadow")


def test_invalid_focus_is_a_solid_danger_ring(show: Show) -> None:
    page = still(show(TextInput().name("email").label("Email").error("Required")))
    field = page.get_by_label("Email")
    field.click()
    expect(field).to_have_css("border-top-color", token(page, "danger"))
    assert _ring(page, "danger", 2) in css(field, "boxShadow")


def test_invalid_focus_in_a_group_is_a_solid_danger_ring(show: Show) -> None:
    page = still(
        show(TextInput().name("site").label("Site").prefix("https://").error("Bad"))
    )
    page.get_by_label("Site").click()
    assert _ring(page, "danger", 2) in css(_group(page, "site"), "boxShadow")


def test_disabled_group_ignores_hover(show: Show) -> None:
    page = still(
        show(TextInput().name("site").label("Site").prefix("https://").disabled())
    )
    page.get_by_label("Site").hover(force=True)
    expect(_group(page, "site")).to_have_css(
        "border-top-color", token(page, "border-input")
    )


def _height(locator: Locator) -> float:
    box = locator.bounding_box()
    assert box is not None
    return box["height"]


@pytest.mark.parametrize("size", ["sm", "md", "lg"])
def test_a_group_is_as_tall_as_a_plain_field(show: Show, size: ControlSize) -> None:
    page = show(
        TextInput().name("plain").label("Plain").size(size),
        TextInput().name("site").label("Site").size(size).prefix("https://"),
    )
    assert _height(_group(page, "site")) == _height(page.get_by_label("Plain"))


def test_an_attached_button_fills_the_group(show: Show) -> None:
    action = Button().content(Text("Copy"))
    page = show(TextInput().name("key").label("Key").action(action))
    group = _group(page, "key")
    button = page.get_by_role("button", name="Copy")
    assert _height(button) == _height(group) - 2
