from playwright.sync_api import expect

from hue.ui import Select, SelectOption, TextInput
from hue.ui.atoms.icon import HueIcon
from tests.browser._fields import css, still, token
from tests.browser.conftest import Show


def _fruit() -> Select:
    return (
        Select()
        .name("fruit")
        .label("Fruit")
        .content(
            SelectOption().value("apple").label("Apple").icon(HueIcon("eye")),
            SelectOption().value("banana").label("Banana"),
            SelectOption().value("bravo").label("Bravo"),
        )
    )


def test_option_icon_is_small_and_leaves_the_label_its_room(show: Show) -> None:
    page = show(_fruit(), width=320)
    page.get_by_role("combobox", name="Fruit").click()
    option = page.get_by_role("option", name="Apple")
    icon = option.locator("svg").bounding_box()
    assert icon is not None
    assert (icon["width"], icon["height"]) == (16, 16)
    label = option.get_by_text("Apple")
    assert label.evaluate("el => el.scrollWidth <= el.clientWidth")


def test_focus_leaving_closes_the_list(show: Show) -> None:
    page = show(_fruit(), TextInput().name("other").label("Other"))
    page.get_by_role("combobox", name="Fruit").click()
    expect(page.get_by_role("listbox")).to_be_visible()
    page.get_by_label("Other").focus()
    expect(page.get_by_role("listbox")).to_be_hidden()


def test_fast_typing_from_closed_keeps_letters_in_order(show: Show) -> None:
    page = show(_fruit())
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.type("br")
    page.keyboard.press("Enter")
    expect(page.locator("input[name=fruit]")).to_have_value("bravo")


def test_open_invalid_select_stays_red(show: Show) -> None:
    page = still(show(_fruit().error("Pick one")))
    trigger = page.get_by_role("combobox", name="Fruit")
    trigger.click()
    expect(trigger).to_have_attribute("aria-expanded", "true")
    expect(trigger).to_have_css("border-top-color", token(page, "danger"))
    assert token(page, "accent-subtle") not in css(trigger, "boxShadow")
