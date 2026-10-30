from playwright.sync_api import expect

from hue.ui import PasswordInput, TextInput
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
