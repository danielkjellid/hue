import pytest
from playwright.sync_api import Page, expect

from hue.ui import ScrollArea
from tests.browser.conftest import Show


def _beside(page: Page) -> bytes:
    # A strip just outside the area's left edge, where the ring is drawn.
    box = page.get_by_role("region").bounding_box()
    assert box is not None
    clip = {"x": box["x"] - 4, "y": box["y"], "width": 3, "height": box["height"]}
    return page.screenshot(clip=clip)


@pytest.mark.parametrize("fade", [True, False])
def test_the_focus_ring_shows_outside_the_area(show: Show, fade: bool) -> None:
    page = show(ScrollArea.example().fade(fade))
    before = _beside(page)
    page.keyboard.press("Tab")
    expect(page.get_by_role("region")).to_be_focused()
    assert _beside(page) != before, "no ring beside the area"


def test_the_fade_shows_while_the_area_is_not_focused(show: Show) -> None:
    page = show(ScrollArea.example())
    area = page.get_by_role("region")
    expect(area).to_have_attribute("data-scroll-below", "true")
    assert area.evaluate("el => getComputedStyle(el).maskImage") != "none"


def test_the_top_fades_only_once_there_is_something_above(show: Show) -> None:
    page = show(ScrollArea.example())
    area = page.get_by_role("region")
    expect(area).not_to_have_attribute("data-scroll-above", "true")
    area.evaluate("el => el.scrollTo(0, el.scrollHeight)")
    expect(area).to_have_attribute("data-scroll-above", "true")
    expect(area).not_to_have_attribute("data-scroll-below", "true")


def test_the_keyboard_scrolls_the_area(show: Show) -> None:
    page = show(ScrollArea.example())
    page.keyboard.press("Tab")
    expect(page.get_by_role("region")).to_be_focused()
    page.keyboard.press("PageDown")
    page.wait_for_function(
        "() => document.querySelector('[role=region]').scrollTop > 0"
    )
