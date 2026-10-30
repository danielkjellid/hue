import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import Button, Tooltip
from hue.ui.molecules.tooltip import TooltipPlacement
from tests.browser.conftest import Show


def _tooltip(placement: TooltipPlacement = "top") -> Tooltip:
    return (
        Tooltip()
        .placement(placement)
        .content("Copy to clipboard")
        .trigger(Button().content("Copy"))
    )


def _centred(placement: TooltipPlacement, dir: str) -> html.div:
    # Room on every side, so the bubble never has to shift onto the trigger.
    # The direction is set here rather than through show(dir=), which does not
    # reach the page's html element.
    return html.div(_tooltip(placement), dir=dir, class_="flex justify-center py-16")


def _shown(page: Page) -> None:
    page.get_by_role("button", name="Copy").focus()
    expect(page.get_by_role("tooltip")).to_be_visible()
    # The anchor places it a frame after it shows.
    page.evaluate(
        "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )


# Where the bubble sits beside the trigger, and the arrow between the two with
# its coloured side towards the bubble, so the triangle points at the trigger.
WHERE = """
() => {
    const trigger = document.querySelector('button').getBoundingClientRect();
    const bubble = document.querySelector('[role=tooltip]');
    const box = bubble.getBoundingClientRect();
    const arrow = bubble.querySelector('[aria-hidden]');
    const tip = arrow.getBoundingClientRect();
    const style = getComputedStyle(arrow);
    const coloured = ['Top', 'Right', 'Bottom', 'Left'].filter(
        side => parseFloat(style[`border${side}Width`]) > 0
            && style[`border${side}Color`] !== 'rgba(0, 0, 0, 0)'
    );
    const side = box.right <= trigger.left ? 'left'
        : box.left >= trigger.right ? 'right'
        : box.bottom <= trigger.top ? 'top' : 'bottom';
    return {
        side,
        coloured,
        arrowCentre: Math.round((tip.left + tip.right) / 2),
        triggerCentre: Math.round((trigger.left + trigger.right) / 2),
        arrowBetween: side === 'left' ? tip.left >= box.right - 1
            && tip.right <= trigger.left + 1
            : side === 'right' ? tip.right <= box.left + 1
            && tip.left >= trigger.right - 1
            : true,
    };
}
"""


@pytest.mark.parametrize(
    ("dir", "placement", "side", "coloured"),
    [
        ("ltr", "start", "left", ["Left"]),
        ("ltr", "end", "right", ["Right"]),
        ("rtl", "start", "right", ["Right"]),
        ("rtl", "end", "left", ["Left"]),
    ],
)
def test_start_and_end_follow_the_direction(
    show: Show, dir: str, placement: TooltipPlacement, side: str, coloured: list[str]
) -> None:
    page = show(_centred(placement, dir))
    _shown(page)
    where = page.evaluate(WHERE)
    assert where["side"] == side
    assert where["arrowBetween"]
    # Coloured on the side away from the trigger is the side the bubble is on.
    assert where["coloured"] == coloured


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
@pytest.mark.parametrize(
    ("placement", "coloured"), [("top", ["Top"]), ("bottom", ["Bottom"])]
)
def test_top_and_bottom_point_at_the_trigger(
    show: Show, dir: str, placement: TooltipPlacement, coloured: list[str]
) -> None:
    page = show(_centred(placement, dir))
    _shown(page)
    where = page.evaluate(WHERE)
    assert where["side"] == placement
    assert where["coloured"] == coloured
    assert abs(where["arrowCentre"] - where["triggerCentre"]) <= 1


@pytest.mark.parametrize("dir", ["ltr", "rtl"])
def test_the_pointer_can_cross_into_the_bubble(show: Show, dir: str) -> None:
    page = show(_centred("start", dir))
    trigger = page.get_by_role("button", name="Copy")
    trigger.hover()
    bubble = page.get_by_role("tooltip")
    expect(bubble).to_be_visible()
    into, out_of = bubble.bounding_box(), trigger.bounding_box()
    assert into is not None and out_of is not None
    # Near the top edge, clear of the arrow, which would cover the gap anyway.
    y = into["y"] + 3
    page.mouse.move(out_of["x"] + out_of["width"] / 2, y)
    page.mouse.move(into["x"] + into["width"] / 2, y, steps=40)
    # Still meant to be open, rather than fading out.
    assert bubble.evaluate("el => Alpine.$data(el).shown")
