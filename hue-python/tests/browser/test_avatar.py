from playwright.sync_api import expect

from hue.ui import Avatar
from tests.browser.conftest import Show


def test_initials_show_when_the_picture_fails_to_load(show: Show) -> None:
    # Bytes that are not a picture: a 404 would fail the same way, but
    # Chrome also logs it as a console error.
    page = show(Avatar().name("Ada Lovelace").src("data:image/png;base64,AAAA"))
    expect(page.locator("img")).to_have_count(0)
    expect(page.get_by_text("AL")).to_be_visible()
