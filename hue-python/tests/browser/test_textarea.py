from htmy import html
from playwright.sync_api import Locator, Page, expect

from hue.js import unsafe
from hue.ui import Button, Stack, Textarea
from tests.browser.conftest import Show

_FRAMES = (
    "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
)


def _bio() -> Textarea:
    return Textarea().name("bio").label("Bio").autosize()


def _height(field: Locator) -> float:
    return field.evaluate("el => el.offsetHeight")


def _fits(field: Locator) -> bool:
    return field.evaluate("el => el.scrollHeight <= el.clientHeight")


def _frames(page: Page) -> None:
    page.evaluate(_FRAMES)


def test_an_emoji_counts_as_one_character(show: Show) -> None:
    page = show(Textarea().name("bio").label("Bio").max_length(10))
    page.get_by_label("Bio").fill("😀")
    expect(page.get_by_text("1 / 10")).to_be_visible()


def test_a_leading_newline_is_kept(show: Show) -> None:
    page = show(Textarea().name("bio").label("Bio").value("\nhello"))
    expect(page.get_by_label("Bio")).to_have_value("\nhello")


def test_autosize_follows_a_width_change_both_ways(show: Show) -> None:
    page = show(html.div(_bio(), id="box", style="width: 400px"))
    field = page.get_by_label("Bio")
    start = _height(field)
    field.fill("word " * 60)
    assert _fits(field)
    page.evaluate("document.getElementById('box').style.width = '250px'")
    page.wait_for_function(
        "() => { const el = document.querySelector('textarea');"
        " return el.scrollHeight <= el.clientHeight && el.offsetWidth < 300 }"
    )
    _frames(page)
    field.fill("short")
    assert _height(field) == start


def test_autosize_leaves_a_height_dragged_straight_away_alone(show: Show) -> None:
    page = show(_bio())
    field = page.get_by_label("Bio")
    # Before the resize observer's first callback, which must not resize.
    field.evaluate("el => { el.style.height = '300px' }")
    _frames(page)
    expect(field).to_have_css("height", "300px")


def test_autosize_shrinks_when_text_is_taken_out(show: Show) -> None:
    page = show(_bio())
    field = page.get_by_label("Bio")
    start = _height(field)
    field.fill("\n".join(["line"] * 8))
    assert _height(field) > start
    assert _fits(field)
    field.fill("short")
    assert _height(field) == start


def test_autosize_rendered_with_long_text_shrinks_when_emptied(show: Show) -> None:
    page = show(_bio().value("\n".join(["line"] * 10)))
    field = page.get_by_label("Bio")
    tall = _height(field)
    field.fill("")
    assert _height(field) < tall


def test_autosize_keeps_a_dragged_height_as_a_floor(show: Show) -> None:
    page = show(_bio())
    field = page.get_by_label("Bio")
    field.fill("short")
    # What dragging the resize handle does.
    field.evaluate("el => { el.style.height = '300px' }")
    field.press("a")
    expect(field).to_have_css("height", "300px")
    # Taller text still grows it past the dragged height.
    field.fill("\n".join(["line"] * 20))
    assert _height(field) > 300
    assert _fits(field)
    # And taking the text out again stops at the dragged height.
    field.fill("short")
    expect(field).to_have_css("height", "300px")


def test_autosize_dragged_shorter_than_its_text_grows_back_to_fit(
    show: Show,
) -> None:
    page = show(_bio())
    field = page.get_by_label("Bio")
    field.fill("\n".join(["line"] * 8))
    tall = _height(field)
    field.evaluate("el => { el.style.height = '90px' }")
    field.press("End")
    field.press("a")
    assert _height(field) == tall
    assert _fits(field)


def test_autosize_shrinks_after_a_form_reset(show: Show) -> None:
    page = show(html.form(_bio(), id="f"))
    field = page.get_by_label("Bio")
    start = _height(field)
    field.fill("\n".join(["line"] * 8))
    page.evaluate("document.getElementById('f').reset()")
    field.press("a")
    assert _height(field) == start


def test_autosize_set_through_x_model_then_typed_in_shrinks(show: Show) -> None:
    page = show(
        Stack()
        .x_data({"bio": ""})
        .content(
            _bio().x_model(unsafe("bio")),
            Button().content("Fill").on_click(unsafe("bio = 'a\\n'.repeat(10)")),
        )
    )
    field = page.get_by_label("Bio")
    start = _height(field)
    page.get_by_role("button", name="Fill").click()
    expect(field).to_have_value("a\n" * 10)
    field.fill("x")
    assert _height(field) == start
