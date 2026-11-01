from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import ScrollArea
from tests.browser.conftest import Show


def _mask(page: Page) -> str:
    return page.get_by_role("region").evaluate("el => getComputedStyle(el).maskImage")


def test_the_fade_drops_while_a_link_inside_has_keyboard_focus(show: Show) -> None:
    links = [html.a(f"Release {n}", href=f"#r{n}", class_="block") for n in range(10)]
    page = show(
        ScrollArea().label("Releases").max_height("max-h-32").fade().content(*links)
    )
    page.keyboard.press("Tab")
    for _ in range(6):
        page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Release 5")).to_be_focused()
    expect(page.get_by_role("region")).to_have_attribute("data-scroll-below", "true")
    assert _mask(page) == "none"


def test_a_pointer_click_inside_keeps_the_fade(show: Show) -> None:
    buttons = [html.button(f"Row {n}", class_="block") for n in range(10)]
    page = show(
        ScrollArea().label("Rows").max_height("max-h-32").fade().content(*buttons)
    )
    page.get_by_role("button", name="Row 0").click()
    assert _mask(page) != "none"
