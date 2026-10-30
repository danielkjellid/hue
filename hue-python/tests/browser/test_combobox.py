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
