import pytest
from playwright.sync_api import expect

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


@pytest.mark.parametrize(
    ("dir", "side", "edge"),
    [
        ("ltr", "end", "right"),
        ("ltr", "start", "left"),
    ],
)
def test_a_side_drawer_enters_from_its_own_edge(
    show: Show, dir: str, side: DrawerSide, edge: str
) -> None:
    page = show(
        Drawer().title("Filters").side(side).trigger(Button().content("Open")),
        dir=dir,
    )
    page.get_by_role("button", name="Open").click()
    expect(page.get_by_role("dialog", name="Filters")).to_be_visible()
    page.wait_for_function("document.getAnimations().length > 0")
    frame = page.evaluate(FIRST_FRAME)
    if edge == "right":
        assert frame["left"] >= frame["settled"] - 1
    else:
        assert frame["right"] <= 1
