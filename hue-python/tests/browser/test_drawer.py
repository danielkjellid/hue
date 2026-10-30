import pytest
from playwright.sync_api import Page, expect

from hue.ui import Button, Drawer
from hue.ui.molecules.drawer import DrawerSide
from tests.browser.conftest import Show

# The panel's edges on the first frame of its way in: every animation on the
# page held at its start.
FIRST_FRAME = """
() => {
    document.getAnimations().forEach(a => { a.pause(); a.currentTime = 0 });
    const r = document.querySelector('aside').getBoundingClientRect();
    return { left: r.left, right: r.right, settled: innerWidth };
}
"""


# The same on the last frame of its way out.
LAST_FRAME = """
() => {
    const out = document.getAnimations().find(
        a => a.animationName?.endsWith('-out')
    );
    document.getAnimations().forEach(a => a.pause());
    out.currentTime = out.effect.getComputedTiming().endTime - 0.01;
    const r = document.querySelector('aside').getBoundingClientRect();
    return { left: r.left, right: r.right, settled: innerWidth };
}
"""

SIDES = pytest.mark.parametrize(
    ("dir", "side", "edge"),
    [
        ("ltr", "end", "right"),
        ("ltr", "start", "left"),
        ("rtl", "end", "left"),
        ("rtl", "start", "right"),
    ],
)


def _opened(show: Show, dir: str, side: DrawerSide) -> Page:
    page = show(
        Drawer().title("Filters").side(side).trigger(Button().content("Open")),
        dir=dir,
    )
    page.get_by_role("button", name="Open").click()
    expect(page.get_by_role("dialog", name="Filters")).to_be_visible()
    return page


def _off_the(edge: str, frame: dict[str, float]) -> bool:
    if edge == "right":
        return frame["left"] >= frame["settled"] - 1
    return frame["right"] <= 1


@SIDES
def test_a_side_drawer_enters_from_its_own_edge(
    show: Show, dir: str, side: DrawerSide, edge: str
) -> None:
    page = _opened(show, dir, side)
    page.wait_for_function("document.getAnimations().length > 0")
    assert _off_the(edge, page.evaluate(FIRST_FRAME))


@SIDES
def test_a_side_drawer_leaves_by_its_own_edge(
    show: Show, dir: str, side: DrawerSide, edge: str
) -> None:
    page = _opened(show, dir, side)
    page.wait_for_function("document.getAnimations().length === 0")
    page.keyboard.press("Escape")
    page.wait_for_function(
        "document.getAnimations().some(a => a.animationName?.endsWith('-out'))"
    )
    assert _off_the(edge, page.evaluate(LAST_FRAME))
