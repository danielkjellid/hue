from playwright.sync_api import expect

from hue.ui import Alert, Banner, Button
from tests.browser.conftest import Show


def test_dismissing_hands_focus_to_the_next_button(show: Show) -> None:
    page = show(
        Alert().title("Saved").dismissible(),
        Button().content("Next"),
    )
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Next")).to_be_focused()


def test_dismissing_the_last_hands_focus_back(show: Show) -> None:
    page = show(
        Button().content("Before"),
        Banner().title("Saved").dismissible(),
    )
    page.get_by_role("button", name="Dismiss").focus()
    page.keyboard.press(" ")
    expect(page.get_by_text("Saved")).to_be_hidden()
    expect(page.get_by_role("button", name="Before")).to_be_focused()
