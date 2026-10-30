from playwright.sync_api import expect

from hue.ui import TextInput
from tests.browser.conftest import Show


def test_a_click_on_a_field_label_focuses_its_input(show: Show) -> None:
    page = show(TextInput().name("email").label("Email"))
    page.locator("label", has_text="Email").click()
    expect(page.get_by_label("Email")).to_be_focused()
