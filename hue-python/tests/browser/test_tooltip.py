import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import Button, Dialog, DropdownMenu, Kbd, MenuItem, Popover, Tooltip
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


def _in_dialog() -> Dialog:
    return Dialog().title("Holder").open().content(_tooltip())


def test_escape_in_a_dialog_closes_a_focused_tooltip_first(show: Show) -> None:
    page = show(_in_dialog())
    _shown(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


def test_escape_in_a_dialog_closes_a_hovered_tooltip_first(show: Show) -> None:
    page = show(_in_dialog())
    page.get_by_role("button", name="Close").focus()
    page.get_by_role("button", name="Copy").hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()


def test_escape_in_a_dialog_with_no_tooltip_closes_it(show: Show) -> None:
    page = show(_in_dialog())
    page.get_by_role("button", name="Close").focus()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


def test_escape_closes_a_hovered_tooltip_while_focus_is_elsewhere(show: Show) -> None:
    page = show(_tooltip(), Button().content("Elsewhere"))
    page.get_by_role("button", name="Elsewhere").focus()
    page.get_by_role("button", name="Copy").hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()


def test_escape_sent_to_the_window_closes_a_hovered_tooltip(show: Show) -> None:
    # A key event's target need not be an element: a page that passes
    # Escape on to a frame dispatches it on the frame's window.
    page = show(_tooltip())
    page.get_by_role("button", name="Copy").hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.evaluate(
        "() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))"
    )
    expect(page.get_by_role("tooltip")).to_be_hidden()


def test_escape_closes_a_focused_tooltip(show: Show) -> None:
    page = show(_tooltip())
    _shown(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    expect(page.get_by_role("button", name="Copy")).to_be_focused()


def test_escape_closes_what_the_trigger_opened_before_its_tooltip(show: Show) -> None:
    page = show(Popover().title("Sharing").trigger(_tooltip()))
    page.get_by_role("button", name="Copy").click()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()


def _description(page: Page) -> str:
    # Chrome's own computation, which is what a screen reader is handed.
    cdp = page.context.new_cdp_session(page)
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    node = cdp.send("DOM.querySelector", {"nodeId": root, "selector": "button"})
    tree = cdp.send("Accessibility.getPartialAXTree", {"nodeId": node["nodeId"]})
    return tree["nodes"][0]["description"]["value"]


def test_the_keys_are_described_once_while_hidden(show: Show) -> None:
    page = show(_tooltip().keys(Kbd("shift", "mod", "K")))
    expect(page.get_by_role("tooltip")).to_be_hidden()
    assert _description(page) == "Copy to clipboard Shift Command K"


def test_the_keys_are_described_once_while_shown(show: Show) -> None:
    page = show(_tooltip().keys(Kbd("shift", "mod", "K")))
    _shown(page)
    assert _description(page) == "Copy to clipboard Shift Command K"


def _menu_with_a_tooltip() -> DropdownMenu:
    return (
        DropdownMenu()
        .label("Actions")
        .trigger(Tooltip().content("More actions").trigger(Button().icon_only("More")))
        .content(MenuItem().content("Rename"), MenuItem().content("Delete"))
    )


def test_a_menu_opened_after_its_tooltip_closes_on_the_first_escape(
    show: Show,
) -> None:
    page = show(_menu_with_a_tooltip())
    trigger = page.get_by_role("button", name="More")
    trigger.hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    trigger.click()
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("Escape")
    expect(page.get_by_role("menu")).to_be_hidden()
    expect(trigger).to_be_focused()


def test_a_menu_opened_from_the_keyboard_hides_the_tooltip(show: Show) -> None:
    page = show(_menu_with_a_tooltip())
    page.keyboard.press("Tab")
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("Escape")
    expect(page.get_by_role("menu")).to_be_hidden()
