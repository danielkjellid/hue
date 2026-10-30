from collections.abc import Callable

import pytest
from playwright.sync_api import Locator, Page, expect

from hue import html
from hue.types.core import ComponentType
from hue.ui import (
    Alert,
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    Checkbox,
    Command,
    CommandGroup,
    CommandItem,
    Drawer,
    ScrollArea,
    Switch,
    TextInput,
)
from tests.browser.conftest import Show
from tests.browser.test_dialog import FULLY_VISIBLE, PANELS

HOME = "http://hue.test/"


def _linked(*body: ComponentType, footer: ComponentType | None = None) -> Card:
    parts: list[ComponentType] = [
        CardHeader().title("Invoice"),
        CardBody().content(*body),
    ]
    if footer is not None:
        parts.append(CardFooter().content(footer))
    return Card().href("#go").class_("w-96").content(*parts)


def _covers_viewport(scrim: Locator) -> None:
    assert scrim.evaluate("el => getComputedStyle(el).position") == "fixed"
    assert scrim.bounding_box() == {"x": 0, "y": 0, "width": 1000, "height": 700}


def test_a_drawer_from_a_linked_card_covers_the_viewport(show: Show) -> None:
    page = show(
        _linked(
            "Due",
            footer=Drawer().title("Details").trigger(Button().content("Open")),
        ),
        width=1000,
        height=700,
    )
    page.get_by_role("button", name="Open").click()
    drawer = page.get_by_role("dialog", name="Details")
    expect(drawer).to_be_visible()
    _covers_viewport(drawer.locator("xpath=.."))
    expect(page).to_have_url(HOME)


def test_a_command_from_a_linked_card_covers_the_viewport(show: Show) -> None:
    page = show(
        _linked(
            "Due",
            footer=Command()
            .trigger(Button().content("Commands"))
            .content(
                CommandGroup()
                .label("Navigate")
                .content(CommandItem().label("Go to Billing").href("#billing"))
            ),
        ),
        width=1000,
        height=700,
    )
    page.get_by_role("button", name="Commands").click()
    search = page.get_by_role("combobox")
    expect(search).to_be_focused()
    _covers_viewport(page.locator("[x-show='open']").filter(has=search).last)
    expect(page).to_have_url(HOME)


@pytest.mark.parametrize("panel", PANELS)
def test_a_panel_from_a_linked_card_is_whole_and_inert_to_the_link(
    show: Show, panel: str
) -> None:
    build: Callable[[], ComponentType]
    open_panel: Callable[[Page], Locator]
    build, open_panel = PANELS[panel]
    page = show(_linked("Due", footer=build()))
    floating = open_panel(page)
    expect(floating).to_be_visible()
    page.wait_for_function(FULLY_VISIBLE, arg=floating.element_handle())
    # A click inside the panel lands on the panel, not the card's link.
    box = floating.bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    expect(page).to_have_url(HOME)


_ON_TOP = (
    "el => { const r = el.getBoundingClientRect();"
    " return el.contains(document.elementFromPoint("
    "r.x + r.width / 2, r.y + r.height / 2)) }"
)


def test_every_control_in_a_linked_card_is_on_top(show: Show) -> None:
    page = show(
        _linked(
            TextInput().name("q").label("Query"),
            Checkbox().name("done").label("Done"),
            Switch().name("on").label("On"),
            footer=Button().content("Archive"),
        )
    )
    for target in (
        page.get_by_role("textbox", name="Query"),
        page.get_by_text("Done"),
        page.get_by_role("switch", name="On"),
        page.get_by_role("button", name="Archive"),
    ):
        assert target.evaluate(_ON_TOP), target


def test_a_footer_button_draws_its_focus_ring_above_the_link(show: Show) -> None:
    page = show(_linked("Due", footer=Button().content("Archive")))
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    button = page.get_by_role("button", name="Archive")
    expect(button).to_be_focused()
    # The ring is a box-shadow: ring-2 outside a 2px offset.
    page.wait_for_function(
        "el => getComputedStyle(el).boxShadow.includes('0px 0px 0px 4px')"
        " && !document.getAnimations().length",
        arg=button.element_handle(),
    )
    assert button.evaluate(_ON_TOP)


def test_a_click_in_a_text_input_in_a_linked_card_focuses_it(show: Show) -> None:
    page = show(_linked(TextInput().name("q").label("Query")))
    box = page.get_by_role("textbox").bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + 8, box["y"] + box["height"] / 2)
    expect(page.get_by_role("textbox")).to_be_focused()
    expect(page).to_have_url(HOME)


def test_the_wheel_scrolls_a_scroll_area_in_a_linked_card(show: Show) -> None:
    page = show(_linked(ScrollArea.example().id("s")))
    box = page.locator("#s").bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.wheel(0, 200)
    page.wait_for_function("() => document.getElementById('s').scrollTop > 0")


def test_an_absolute_dismiss_button_in_a_linked_card_stays_put(show: Show) -> None:
    page = show(
        _linked(
            "Due",
            # Plain markup: hue's Button carries its own relative.
            html.button("x").type("button").class_("absolute top-2 end-2").id("x"),
        )
    )
    x = page.locator("#x")
    assert x.evaluate("el => getComputedStyle(el).position") == "absolute"
    assert x.evaluate(_ON_TOP)
    x.click()
    expect(page).to_have_url(HOME)


def test_an_alert_dismiss_in_a_linked_card_works(show: Show) -> None:
    page = show(_linked(Alert().title("Heads up").dismissible()))
    page.get_by_role("button", name="Dismiss").click()
    expect(page.get_by_text("Heads up")).to_be_hidden()
    expect(page).to_have_url(HOME)
