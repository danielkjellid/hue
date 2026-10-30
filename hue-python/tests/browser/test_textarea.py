from playwright.sync_api import expect

from hue.ui import Textarea
from tests.browser.conftest import Show


def test_an_emoji_counts_as_one_character(show: Show) -> None:
    page = show(Textarea().name("bio").label("Bio").max_length(10))
    page.get_by_label("Bio").fill("😀")
    expect(page.get_by_text("1 / 10")).to_be_visible()


def test_a_leading_newline_is_kept(show: Show) -> None:
    page = show(Textarea().name("bio").label("Bio").value("\nhello"))
    expect(page.get_by_label("Bio")).to_have_value("\nhello")


def test_autosize_leaves_nothing_to_scroll(show: Show) -> None:
    page = show(Textarea().name("bio").label("Bio").autosize())
    field = page.get_by_label("Bio")
    field.fill("\n".join(["line"] * 8))
    assert field.evaluate("el => el.scrollHeight <= el.clientHeight")
