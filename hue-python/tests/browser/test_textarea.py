from playwright.sync_api import Locator, expect

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


def _fits(field: Locator) -> bool:
    return field.evaluate("el => el.scrollHeight <= el.clientHeight")


def test_autosize_follows_a_narrower_width(show: Show) -> None:
    page = show(Textarea().name("bio").label("Bio").autosize(), width=900)
    field = page.get_by_label("Bio")
    field.fill("word " * 120)
    assert _fits(field)
    page.set_viewport_size({"width": 360, "height": 800})
    page.wait_for_function(
        "el => el.scrollHeight <= el.clientHeight",
        arg=field.element_handle(),
        timeout=5000,
    )


def test_autosize_leaves_a_dragged_height_alone(show: Show) -> None:
    page = show(Textarea().name("bio").label("Bio").autosize())
    field = page.get_by_label("Bio")
    field.fill("short")
    # What dragging the resize handle does.
    field.evaluate("el => { el.style.height = '300px' }")
    # Two frames: the observer's callback, then the one it would resize in.
    page.evaluate(
        "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )
    expect(field).to_have_css("height", "300px")
