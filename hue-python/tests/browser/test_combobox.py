from playwright.sync_api import Locator, expect

from hue.ui import Combobox, SelectOption
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
