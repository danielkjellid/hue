from playwright.sync_api import Page, expect

from hue.ui import Button, ButtonGroup
from tests.browser.conftest import Show

# Each child's computed stacking and corners, in order.
CHILDREN = """
() => [...document.querySelector('main > div').children].map(child => {
    const style = getComputedStyle(child);
    return {
        z: style.zIndex,
        start: style.borderTopLeftRadius,
        end: style.borderTopRightRadius,
    };
})
"""


def _children(page: Page) -> list[dict[str, str]]:
    return page.evaluate(CHILDREN)


def _three() -> ButtonGroup:
    return ButtonGroup().content(
        Button().variant("outline").content("Export"),
        Button().variant("outline").content("Schedule"),
        Button().variant("outline").content("Share"),
    )


def test_only_the_outer_corners_are_rounded(show: Show) -> None:
    children = _children(show(_three()))
    rounded = [(c["start"] != "0px", c["end"] != "0px") for c in children]
    assert rounded == [(True, False), (False, False), (False, True)]


def test_a_focused_button_is_lifted_above_its_neighbours(show: Show) -> None:
    page = show(_three())
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Schedule")).to_be_focused()
    assert [c["z"] for c in _children(page)] == ["auto", "10", "auto"]
