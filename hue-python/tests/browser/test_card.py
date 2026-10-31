from htmy import html
from playwright.sync_api import Locator, Page, expect

from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import (
    Alert,
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    CardMedia,
    Checkbox,
    Command,
    CommandGroup,
    CommandItem,
    Dialog,
    DropdownMenu,
    MenuItem,
    Popover,
    ScrollArea,
    Stack,
    Switch,
    TextInput,
)
from tests.browser.conftest import Show

HOME = "http://hue.test/"


def _media() -> CardMedia:
    return CardMedia().content(html.div(class_="size-full"))


def _linked() -> Card:
    return (
        Card()
        .href("#go")
        .id("card")
        .class_("w-80")
        .content(
            _media(),
            CardHeader().title("Invoice 2050"),
            CardBody().content("Due in 14 days"),
            CardFooter().content(
                Button().content("Archive").on_click(unsafe("archived = true"))
            ),
        )
    )


def _linked_with(*body: ComponentType, footer: ComponentType = "") -> Card:
    return (
        Card()
        .href("#go")
        .class_("w-96")
        .content(
            CardHeader().title("Invoice"),
            CardBody().content(*body),
            CardFooter().content(footer),
        )
    )


def _click_middle(page: Page, target: Locator) -> None:
    # A real pointer: Playwright's own click refuses an element something
    # else covers, and covering it is the point.
    box = target.bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


_ON_TOP = (
    "el => { const r = el.getBoundingClientRect();"
    " return el.contains(document.elementFromPoint("
    "r.x + r.width / 2, r.y + r.height / 2)) }"
)

# Each edge's midpoint, just inside it, is the panel itself and not whatever
# shows through where a clipping ancestor cut it off.
_WHOLE = """
el => {
    const r = el.getBoundingClientRect();
    const x = (r.left + r.right) / 2, y = (r.top + r.bottom) / 2;
    return r.width > 0 && [
        [x, r.top + 2], [x, r.bottom - 2], [r.left + 2, y], [r.right - 2, y],
    ].every(([px, py]) => el.contains(document.elementFromPoint(px, py)));
}
"""


def _ring_settles(page: Page, *, lit: bool) -> None:
    # The ring transitions in and out, so wait for where it ends up.
    page.wait_for_function(
        "lit => (getComputedStyle(document.getElementById('card')).boxShadow"
        " !== 'none') === lit && !document.getAnimations().length",
        arg=lit,
    )


def test_a_click_anywhere_on_a_linked_card_follows_it(show: Show) -> None:
    page = show(_linked())
    _click_middle(page, page.get_by_text("Due in 14 days"))
    expect(page).to_have_url(f"{HOME}#go")


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
    expect(page).to_have_url(HOME)


def test_the_ring_answers_the_title_only(show: Show) -> None:
    page = show(_linked())
    _ring_settles(page, lit=False)
    page.keyboard.press("Tab")
    _ring_settles(page, lit=True)
    page.keyboard.press("Tab")
    _ring_settles(page, lit=False)
    # The footer button draws its own ring, above the link: ring-2 outside a
    # 2px offset.
    button = page.get_by_role("button", name="Archive")
    page.wait_for_function(
        "el => getComputedStyle(el).boxShadow.includes('0px 0px 0px 4px')"
        " && !document.getAnimations().length",
        arg=button.element_handle(),
    )
    assert button.evaluate(_ON_TOP)


def test_the_parts_space_themselves_by_what_sits_above(show: Show) -> None:
    page = show(
        Card().content(CardHeader().title("T"), CardBody().content("x").id("h")),
        Card()
        .class_("w-80")
        .content(_media().id("media"), CardBody().content("x").id("m")),
        Card()
        .class_("w-80")
        .content(_media(), CardHeader().title("T"), CardBody().content("x").id("mh")),
    )
    media = page.locator("#media").bounding_box()
    assert media is not None
    assert round(media["width"] / media["height"], 2) == round(16 / 9, 2)

    def padding(selector: str) -> str:
        return page.locator(selector).evaluate("el => getComputedStyle(el).paddingTop")

    assert (padding("#h"), padding("#m"), padding("#mh")) == ("0px", "20px", "0px")


def test_a_nested_dark_scope_takes_the_dark_raised_shadow(show: Show) -> None:
    page = show(
        html.div(
            Card()
            .variant("raised")
            .id("c")
            .content(CardHeader().title("T"), CardBody().content("x")),
            data_theme="dark",
        )
    )
    shadow = page.locator("#c").evaluate("el => getComputedStyle(el).boxShadow")
    assert "rgba(0, 0, 0, 0.3) 0px 0px 0px 1px" in shadow


# The lift raises controls above the title's overlay, and must never undo
# a control's own positioning.
def test_every_control_in_a_linked_card_is_on_top(show: Show) -> None:
    page = show(
        _linked_with(
            TextInput().name("q").label("Query"),
            Checkbox().name("done").label("Done"),
            Switch().name("on").label("On"),
            html.span("Focusable", tabindex="0", id="t"),
            html.div("Acts", role="button", tabindex="0", id="b"),
            footer=Button().content("Archive"),
        )
    )
    for target in (
        page.get_by_role("textbox", name="Query"),
        page.get_by_text("Done"),
        page.get_by_role("switch", name="On"),
        page.get_by_role("button", name="Archive"),
        page.locator("#t"),
        page.locator("#b"),
    ):
        assert target.evaluate(_ON_TOP), target


def test_positioned_controls_in_a_linked_card_keep_their_position(
    show: Show,
) -> None:
    page = show(
        _linked_with(
            Alert().title("Heads up").dismissible(),
            html.input_(type="checkbox", class_="sr-only", id="sr"),
            # Plain markup: hue's Button carries its own relative.
            html.button("x", type="button", class_="absolute top-2 end-2", id="x"),
        )
    )
    for selector in ("#sr", "#x"):
        position = page.locator(selector).evaluate(
            "el => getComputedStyle(el).position"
        )
        assert position == "absolute", selector
    x = page.locator("#x")
    assert x.evaluate(_ON_TOP)
    x.click()
    page.get_by_role("button", name="Dismiss").click()
    expect(page.get_by_text("Heads up")).to_be_hidden()
    expect(page).to_have_url(HOME)


def test_a_hidden_label_takes_no_room_in_a_linked_card(show: Show) -> None:
    def input_top(linked: bool) -> float:
        card = Card().id("c")
        if linked:
            card = card.href("#go")
        page = show(
            card.content(
                CardHeader().title("Search"),
                CardBody().content(TextInput().name("q").label("Query").hidden_label()),
            )
        )
        box = page.get_by_role("textbox").bounding_box()
        card_box = page.locator("#c").bounding_box()
        assert box is not None and card_box is not None
        return box["y"] - card_box["y"]

    assert input_top(linked=True) == input_top(linked=False)


def test_a_scroll_area_in_a_linked_card_scrolls_rather_than_links(
    show: Show,
) -> None:
    # A tab stop of its own, which the wheel and a click must reach.
    rows = [html.p(f"Row {n}") for n in range(20)]
    area = ScrollArea().label("Notes").max_height("max-h-32").content(*rows)
    page = show(_linked_with(area.id("s")))
    area = page.locator("#s")
    _click_middle(page, area)
    expect(page).to_have_url(HOME)
    page.mouse.wheel(0, 200)
    page.wait_for_function("() => document.getElementById('s').scrollTop > 0")


def test_a_focus_target_in_a_linked_card_stays_under_the_link(show: Show) -> None:
    # tabindex -1, as on a chart's figure, is where focus can be sent, not a
    # control, so a click on it is a click on the card.
    page = show(_linked_with(html.figure("Chart", tabindex="-1", id="f")))
    _click_middle(page, page.locator("#f"))
    expect(page).to_have_url(f"{HOME}#go")


def _covers_viewport(scrim: Locator) -> None:
    assert scrim.evaluate("el => getComputedStyle(el).position") == "fixed"
    assert scrim.bounding_box() == {"x": 0, "y": 0, "width": 1000, "height": 700}


def test_an_overlay_from_a_linked_card_covers_the_viewport(show: Show) -> None:
    command = (
        Command()
        .trigger(Button().content("Commands"))
        .content(
            CommandGroup()
            .label("Navigate")
            .content(CommandItem().label("Go to Billing").href("#billing"))
        )
    )
    dialog = Dialog().title("Delete invoice").trigger(Button().content("Delete"))
    page = show(
        _linked_with("Due", footer=html.div(dialog, command)), width=1000, height=700
    )
    page.get_by_role("button", name="Delete").click()
    panel = page.get_by_role("dialog", name="Delete invoice")
    expect(panel).to_be_visible()
    # The scrim is the dialog's parent, fixed over the whole viewport.
    _covers_viewport(panel.locator("xpath=.."))
    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()

    page.get_by_role("button", name="Commands").click()
    search = page.get_by_role("combobox")
    expect(search).to_be_focused()
    _covers_viewport(page.locator("[x-show='open']").filter(has=search).last)
    expect(page).to_have_url(HOME)


def test_a_floating_panel_from_a_linked_card_is_whole_and_inert_to_the_link(
    show: Show,
) -> None:
    menu = (
        DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(MenuItem().content("Rename"))
    )
    popover = (
        Popover()
        .title("Sharing")
        .description("Anyone with the link can view.")
        .trigger(Button().content("Share"))
    )
    page = show(_linked_with("Due", footer=html.div(menu, popover)))
    for trigger, panel in (
        ("Actions", page.get_by_role("menu")),
        ("Share", page.get_by_role("dialog", name="Sharing")),
    ):
        page.get_by_role("button", name=trigger).click()
        expect(panel).to_be_visible()
        page.wait_for_function(_WHOLE, arg=panel.element_handle())
        # A click inside the panel lands on the panel, not the card's link.
        _click_middle(page, panel)
        expect(page).to_have_url(HOME)
        page.keyboard.press("Escape")
        expect(panel).to_be_hidden()


def test_cards_in_a_row_shrink_and_clip_on_a_phone(show: Show) -> None:
    page = show(
        Stack()
        .horizontal()
        .content(
            Card()
            .id("one")
            .href("/elsewhere")
            .class_("flex-1")
            .content(
                CardHeader().title("A title long enough to want more room"),
                CardBody().content(html.div(style="width: 2000px", class_="h-10")),
            ),
            Card().id("two").class_("flex-1").content(CardBody().content("Two")),
        ),
        width=320,
    )
    assert page.evaluate("document.documentElement.scrollWidth") <= 320
    widths = page.evaluate(
        "['one', 'two'].map((id) =>"
        " document.getElementById(id).getBoundingClientRect().width)"
    )
    assert abs(widths[0] - widths[1]) < 1
    # Shrunk, the linked card still takes a click anywhere on it.
    hits = page.evaluate(
        "(() => { const b = document.getElementById('one').getBoundingClientRect();"
        " return [[b.left + 10, b.bottom - 10], [b.right - 10, b.top + 10],"
        " [b.right - 10, b.bottom - 10]].map(([x, y]) =>"
        " !!document.elementFromPoint(x, y).closest('[data-card-link]')) })()"
    )
    assert hits == [True, True, True]
