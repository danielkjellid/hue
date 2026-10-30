import re

from htmy import html
from playwright.sync_api import Locator, Page, expect

from hue.ui import Combobox, SelectOption
from tests.browser._fields import css, still, token
from tests.browser.conftest import Show


def _fruit() -> Combobox:
    return (
        Combobox()
        .name("fruit")
        .label("Fruit")
        .content(
            SelectOption().value("apple").label("Apple"),
            SelectOption().value("banana").label("Banana"),
        )
    )


def test_typing_activates_the_first_match(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.fill("ban")
    page.keyboard.press("Enter")
    assert page.locator("input[type=hidden][name=fruit]").input_value() == "banana"


def _long() -> Combobox:
    return (
        Combobox()
        .name("place")
        .label("Place")
        .content(
            SelectOption()
            .value("long")
            .label("Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch"),
        )
    )


def _right(locator: Locator) -> float:
    box = locator.bounding_box()
    assert box is not None
    return box["x"] + box["width"]


def _left(locator: Locator) -> float:
    box = locator.bounding_box()
    assert box is not None
    return box["x"]


def test_a_narrow_field_stops_short_of_the_chevron(show: Show) -> None:
    page = show(_long().value("long"), width=200)
    field = page.get_by_role("combobox", name="Place")
    chevron = page.get_by_role("button", name="Place")
    assert _right(field) <= _left(chevron)


def test_a_long_token_truncates_inside_the_field(show: Show) -> None:
    page = show(_long().multiple().value("long"), width=320)
    token = page.locator('[x-text="item.label"]')
    chevron = page.get_by_role("button", name="Place")
    assert _right(token) <= _left(chevron)
    assert token.evaluate("el => el.scrollWidth > el.clientWidth")


def test_enter_on_a_cleared_field_picks_nothing(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.fill("ban")
    field.fill("")
    page.keyboard.press("Enter")
    # Nothing chosen submits no field at all.
    expect(page.locator("input[type=hidden][name=fruit]")).to_have_count(0)


def test_enter_on_a_cleared_multiple_field_keeps_its_tokens(show: Show) -> None:
    page = show(_fruit().multiple().value("apple"))
    field = page.get_by_role("combobox", name="Fruit")
    field.fill("app")
    field.fill("")
    page.keyboard.press("Enter")
    expect(page.locator("input[type=hidden][name=fruit]")).to_have_value("apple")


def test_arrows_after_clearing_still_move(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.fill("ban")
    field.fill("")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(page.locator("input[type=hidden][name=fruit]")).to_have_value("apple")


def test_backspace_on_an_empty_multiple_field_removes_the_last_token(
    show: Show,
) -> None:
    page = show(_fruit().multiple().value("apple", "banana"))
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.press("Backspace")
    expect(page.locator("input[type=hidden][name=fruit]")).to_have_count(1)
    expect(page.locator("input[type=hidden][name=fruit]")).to_have_value("apple")


def test_focused_invalid_combobox_draws_a_solid_danger_ring(show: Show) -> None:
    page = still(show(_fruit().error("Pick one")))
    page.get_by_role("combobox", name="Fruit").click()
    shell = page.locator("[x-ref=shell]")
    expect(shell).to_have_css("border-top-color", token(page, "danger"))
    assert f"{token(page, 'danger')} 0px 0px 0px 2px" in css(shell, "boxShadow")


# Counts submits and keeps what was sent, without leaving the page.
_COUNT_SUBMITS = (
    "event.preventDefault(); window.submits = (window.submits || 0) + 1; "
    "window.sent = new FormData(this).getAll('fruit')"
)


def _in_a_form(combobox: Combobox) -> html.form:
    return html.form(combobox, onsubmit=_COUNT_SUBMITS)


def _option_id(page: Page, name: str) -> str:
    option_id = page.get_by_role("option", name=name).get_attribute("id")
    assert option_id is not None
    return option_id


def _closed(page: Page) -> Locator:
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    page.keyboard.press("Escape")
    expect(field).to_have_attribute("aria-expanded", "false")
    return field


def test_enter_with_the_list_closed_submits_the_form(show: Show) -> None:
    page = show(_in_a_form(_fruit().value("apple")))
    _closed(page)
    page.keyboard.press("Enter")
    page.wait_for_function("window.submits === 1")
    assert page.evaluate("window.sent") == ["apple"]


def test_down_opens_on_the_chosen_option(show: Show) -> None:
    page = show(_fruit().value("banana"))
    field = _closed(page)
    page.keyboard.press("ArrowDown")
    expect(field).to_have_attribute("aria-activedescendant", _option_id(page, "Banana"))


def test_up_opens_on_the_last_option(show: Show) -> None:
    page = show(_fruit())
    field = _closed(page)
    page.keyboard.press("ArrowUp")
    expect(field).to_have_attribute("aria-activedescendant", _option_id(page, "Banana"))


def test_alt_down_opens_with_nothing_active(show: Show) -> None:
    page = show(_fruit())
    field = _closed(page)
    page.keyboard.press("Alt+ArrowDown")
    expect(field).to_have_attribute("aria-expanded", "true")
    expect(field).not_to_have_attribute("aria-activedescendant", re.compile(".*"))


def test_escape_closes_the_list(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    expect(page.get_by_role("listbox")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("listbox")).to_be_hidden()
    expect(field).to_be_focused()
