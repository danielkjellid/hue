from htmy import html
from playwright.sync_api import Page, expect

from hue.js import unsafe
from hue.ui import Button, Card, CardBody, CardFooter, CardHeader, CardMedia
from tests.browser.conftest import Show


def _linked() -> Card:
    return (
        Card()
        .href("#go")
        .id("card")
        .content(
            CardHeader().title("Invoice 2050"),
            CardBody().content("Due in 14 days"),
            CardFooter().content(
                Button().content("Archive").on_click(unsafe("archived = true"))
            ),
        )
    )


def _ring_settles(page: Page, *, lit: bool) -> None:
    # The ring transitions in and out, so wait for where it ends up.
    page.wait_for_function(
        "lit => (getComputedStyle(document.getElementById('card')).boxShadow"
        " !== 'none') === lit && !document.getAnimations().length",
        arg=lit,
    )


def test_a_click_anywhere_on_a_linked_card_follows_it(show: Show) -> None:
    page = show(_linked())
    # A real pointer at the body text: Playwright's own click refuses an
    # element something else covers, and covering it is the point.
    box = page.get_by_text("Due in 14 days").bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + 4, box["y"] + box["height"] / 2)
    expect(page).to_have_url("http://hue.test/#go")


def test_the_title_is_the_one_tab_stop_and_the_name(show: Show) -> None:
    page = show(_linked())
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Invoice 2050")).to_be_focused()
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Archive")).to_be_focused()


def test_a_footer_button_stays_clickable_without_navigating(show: Show) -> None:
    page = show(html.div(_linked(), x_data="{archived: false}", id="scope"))
    page.get_by_role("button", name="Archive").click()
    page.wait_for_function(
        "() => Alpine.$data(document.getElementById('scope')).archived"
    )
    expect(page).to_have_url("http://hue.test/")


def test_the_ring_answers_the_title_only(show: Show) -> None:
    page = show(_linked())
    _ring_settles(page, lit=False)
    page.keyboard.press("Tab")
    _ring_settles(page, lit=True)
    page.keyboard.press("Tab")
    _ring_settles(page, lit=False)


def test_a_body_under_a_header_sits_right_under_it(show: Show) -> None:
    page = show(
        Card().content(CardHeader().title("T"), CardBody().content("x").id("b"))
    )
    padding = page.locator("#b").evaluate("el => getComputedStyle(el).paddingTop")
    assert padding == "0px"


def test_media_is_a_16_by_9_band(show: Show) -> None:
    page = show(
        Card()
        .class_("w-80")
        .content(CardMedia().id("m").content(html.div(class_="size-full")))
    )
    box = page.locator("#m").bounding_box()
    assert box is not None
    assert round(box["width"] / box["height"], 2) == round(16 / 9, 2)
