from htmy import html
from playwright.sync_api import expect

from hue.ui import (
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    CardMedia,
    DropdownMenu,
    MenuItem,
    Text,
    TextInput,
)
from tests.browser.conftest import Show

_SHADOW = "el => getComputedStyle(el).boxShadow"


def test_a_focused_field_keeps_its_halo_in_dark(show: Show) -> None:
    page = show(TextInput().name("email").label("Email"), theme="dark")
    page.get_by_label("Email").focus()
    page.wait_for_function(
        "el => getComputedStyle(el).boxShadow.includes('0px 0px 0px 3px')"
        " && !document.getAnimations().length",
        arg=page.get_by_label("Email").element_handle(),
    )


def test_a_focused_grouped_field_keeps_its_halo_in_dark(show: Show) -> None:
    page = show(
        TextInput().name("site").label("Site").prefix("https://").id("g"),
        theme="dark",
    )
    page.get_by_label("Site").focus()
    # The halo sits on the frame around the input, not the input.
    page.wait_for_function(
        "() => [...document.querySelectorAll('*')].some(el =>"
        " el.contains(document.activeElement) && el !== document.activeElement"
        " && getComputedStyle(el).boxShadow.includes('0px 0px 0px 3px'))"
        " && !document.getAnimations().length"
    )


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
    assert "rgba(0, 0, 0, 0.3) 0px 0px 0px 1px" in page.locator("#c").evaluate(_SHADOW)


def test_a_button_in_a_plain_heading_takes_body_tracking(show: Show) -> None:
    page = show(html.h2("Members ", Button().content("Invite").id("b")))
    spacing = page.locator("#b").evaluate("el => getComputedStyle(el).letterSpacing")
    assert spacing == "normal"


def test_a_tracking_class_on_a_button_in_a_heading_still_wins(show: Show) -> None:
    page = show(
        html.h2("Members ", Button().content("Invite").class_("tracking-wide").id("b"))
    )
    spacing = page.locator("#b").evaluate("el => getComputedStyle(el).letterSpacing")
    assert spacing != "normal"


def test_text_centred_and_justified_in_rtl(show: Show) -> None:
    long = "שלום עולם " * 40
    page = show(
        Text("שלום").align("center").id("c").class_("w-80"),
        Text(long).align("justify").id("j").class_("w-80"),
        dir="rtl",
    )
    assert page.locator("#c").evaluate("el => getComputedStyle(el).textAlign") == (
        "center"
    )
    assert page.locator("#j").evaluate("el => getComputedStyle(el).textAlign") == (
        "justify"
    )


def test_a_body_under_header_under_media_sits_right_under_the_header(
    show: Show,
) -> None:
    page = show(
        Card()
        .class_("w-80")
        .content(
            CardMedia().content(html.div(class_="size-full")),
            CardHeader().title("T"),
            CardBody().content("x").id("b"),
        )
    )
    padding = page.locator("#b").evaluate("el => getComputedStyle(el).paddingTop")
    assert padding == "0px"


def test_a_menu_in_a_linked_card_opens_at_its_trigger(show: Show) -> None:
    page = show(
        Card()
        .href("#go")
        .content(
            CardHeader().title("Invoice"),
            CardBody().content("Due"),
            CardFooter().content(
                DropdownMenu()
                .label("Actions")
                .trigger(Button().content("Actions"))
                .content(MenuItem().content("Rename"))
            ),
        )
    )
    page.get_by_role("button", name="Actions").click()
    menu = page.get_by_role("menu")
    expect(menu).to_be_visible()
    assert menu.evaluate("el => getComputedStyle(el).position") == "fixed"
    page.get_by_role("menuitem", name="Rename").click()
    expect(page).to_have_url("http://hue.test/")


def test_a_click_on_a_linked_card_body_under_media_follows_it(show: Show) -> None:
    page = show(
        Card()
        .href("#go")
        .class_("w-80")
        .content(
            CardMedia().content(html.div(class_="size-full")),
            CardHeader().title("Invoice"),
            CardBody().content("Due in 14 days"),
        )
    )
    box = page.get_by_text("Due in 14 days").bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + 4, box["y"] + box["height"] / 2)
    expect(page).to_have_url("http://hue.test/#go")
