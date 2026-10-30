from htmy import html
from playwright.sync_api import Page, expect

from hue.js import unsafe
from hue.ui import (
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    CardMedia,
    Checkbox,
    Dialog,
    ScrollArea,
    TextInput,
)
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


def test_a_checkbox_label_in_a_linked_card_checks_the_box(show: Show) -> None:
    page = show(
        Card()
        .href("#go")
        .content(
            CardHeader().title("Task"),
            CardBody().content(Checkbox().name("done").label("Mark as done")),
        )
    )
    # A real pointer, since the bug is what sits on top at that point.
    box = page.get_by_text("Mark as done").bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    expect(page.get_by_role("checkbox", name="Mark as done")).to_be_checked()
    expect(page).to_have_url("http://hue.test/")


def test_other_controls_in_a_linked_card_are_not_covered(show: Show) -> None:
    page = show(
        Card()
        .href("#go")
        .content(
            CardHeader().title("Task"),
            CardBody().content(
                html.span("Focusable", tabindex="0", id="t"),
                html.div("Acts", role="button", tabindex="0", id="b"),
            ),
        )
    )
    for selector in ("#t", "#b"):
        hit = page.locator(selector).evaluate(
            "el => { const r = el.getBoundingClientRect();"
            " return document.elementFromPoint(r.x + 2, r.y + r.height / 2) === el }"
        )
        assert hit, selector


def test_a_body_under_media_is_padded_from_it(show: Show) -> None:
    page = show(
        Card()
        .class_("w-80")
        .content(
            CardMedia().id("m").content(html.div(class_="size-full")),
            CardBody().content("x").id("b"),
        )
    )
    padding = page.locator("#b").evaluate("el => getComputedStyle(el).paddingTop")
    assert padding == "20px"


# The lift raises controls above the title's overlay, and must never undo
# a control's own positioning.
def test_a_dialog_in_a_linked_card_covers_the_viewport(show: Show) -> None:
    page = show(
        Card()
        .href("#go")
        .class_("w-80")
        .content(
            CardHeader().title("Invoice"),
            CardBody().content("Due"),
            CardFooter().content(
                Dialog().title("Delete invoice").trigger(Button().content("Delete"))
            ),
        ),
        width=1000,
        height=700,
    )
    page.get_by_role("button", name="Delete").click()
    dialog = page.get_by_role("dialog", name="Delete invoice")
    expect(dialog).to_be_visible()
    # The scrim is the dialog's parent, fixed over the whole viewport.
    scrim = dialog.locator("xpath=..")
    position = scrim.evaluate("el => getComputedStyle(el).position")
    box = scrim.bounding_box()
    assert (position, box) == (
        "fixed",
        {"x": 0, "y": 0, "width": 1000, "height": 700},
    )


def _input_top(show: Show, card: Card) -> float:
    page = show(card)
    box = page.get_by_role("textbox").bounding_box()
    card_box = page.locator("#c").bounding_box()
    assert box is not None and card_box is not None
    return box["y"] - card_box["y"]


def test_a_hidden_label_takes_no_room_in_a_linked_card(show: Show) -> None:
    def card(linked: bool) -> Card:
        c = Card().id("c")
        if linked:
            c = c.href("#go")
        return c.content(
            CardHeader().title("Search"),
            CardBody().content(TextInput().name("q").label("Query").hidden_label()),
        )

    assert _input_top(show, card(linked=True)) == _input_top(show, card(linked=False))


def test_a_visually_hidden_input_stays_out_of_the_flow(show: Show) -> None:
    page = show(
        Card()
        .href("#go")
        .content(
            CardHeader().title("Task"),
            CardBody().content(html.input_(type="checkbox", class_="sr-only", id="x")),
        )
    )
    position = page.locator("#x").evaluate("el => getComputedStyle(el).position")
    assert position == "absolute"


def _click_middle(page: Page, selector: str) -> None:
    box = page.locator(selector).bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def test_a_scroll_area_in_a_linked_card_scrolls_rather_than_links(
    show: Show,
) -> None:
    # A tab stop of its own, which the wheel and a click must reach.
    page = show(
        Card()
        .href("#go")
        .content(
            CardHeader().title("Notes"),
            CardBody().content(ScrollArea.example().id("s")),
        )
    )
    _click_middle(page, "#s")
    expect(page).to_have_url("http://hue.test/")


def test_a_focus_target_in_a_linked_card_stays_under_the_link(show: Show) -> None:
    # tabindex -1, as on a chart's figure, is where focus can be sent, not a
    # control, so a click on it is a click on the card.
    page = show(
        Card()
        .href("#go")
        .content(
            CardHeader().title("Revenue"),
            CardBody().content(html.figure("Chart", tabindex="-1", id="f")),
        )
    )
    _click_middle(page, "#f")
    expect(page).to_have_url("http://hue.test/#go")
