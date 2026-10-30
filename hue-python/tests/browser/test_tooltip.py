from collections.abc import Callable, Iterator
from typing import Any, Literal

import pytest
from htmy import html
from playwright.sync_api import Browser, Page, expect

from hue import assets
from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import (
    Button,
    Dialog,
    Drawer,
    DropdownMenu,
    Kbd,
    MenuItem,
    Popover,
    Tooltip,
)
from hue.ui.molecules.tooltip import TooltipPlacement
from tests.browser.conftest import ORIGIN, Show, render_page


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


@pytest.mark.parametrize(
    ("dir", "placement", "coloured"),
    [("ltr", "top", ["Top"]), ("rtl", "bottom", ["Bottom"])],
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


def test_escape_in_a_dialog_closes_the_tooltip_first(show: Show) -> None:
    page = show(_in_dialog())
    _shown(page)
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    expect(page.get_by_role("button", name="Copy")).to_be_focused()
    # Shown by hover, with focus on another control in the dialog.
    page.get_by_role("button", name="Close").focus()
    page.get_by_role("button", name="Copy").hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


def test_escape_closes_a_hovered_tooltip_while_focus_is_elsewhere(show: Show) -> None:
    page = show(_tooltip(), Button().content("Elsewhere"))
    page.get_by_role("button", name="Elsewhere").focus()
    page.get_by_role("button", name="Copy").hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    # A key event's target need not be an element: a page that passes
    # Escape on to a frame dispatches it on the frame's window.
    page.get_by_role("button", name="Elsewhere").hover()
    page.get_by_role("button", name="Copy").hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.evaluate(
        "() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))"
    )
    expect(page.get_by_role("tooltip")).to_be_hidden()


def _description(page: Page, selector: str = "button") -> str:
    # Chrome's own computation, which is what a screen reader is handed.
    cdp = page.context.new_cdp_session(page)
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    node = cdp.send("DOM.querySelector", {"nodeId": root, "selector": selector})
    tree = cdp.send("Accessibility.getPartialAXTree", {"nodeId": node["nodeId"]})
    return tree["nodes"][0]["description"]["value"]


def test_the_keys_are_described_once_hidden_or_shown(show: Show) -> None:
    page = show(_tooltip().keys(Kbd("shift", "mod", "K")))
    expect(page.get_by_role("tooltip")).to_be_hidden()
    assert _description(page) == "Copy to clipboard Shift Command K"
    _shown(page)
    assert _description(page) == "Copy to clipboard Shift Command K"


SHOWN = "Alpine.$data(document.querySelector('[role=tooltip]')).shown"

# Each overlay a tooltipped control opens: the role it opens, and whether the
# Tooltip wraps the overlay rather than the control, so both ways round are
# covered across the cases.
OPENED: dict[str, tuple[Callable[[], Any], Literal["menu", "dialog"], bool]] = {
    "menu": (
        lambda: DropdownMenu().label("Actions").content(MenuItem().content("Rename")),
        "menu",
        False,
    ),
    "popover": (lambda: Popover().title("Sharing"), "dialog", True),
    "dialog": (
        lambda: Dialog().title("Settings").content(Button().content("Inside")),
        "dialog",
        False,
    ),
    "drawer": (
        lambda: Drawer().title("Filters").content(Button().content("Inside")),
        "dialog",
        True,
    ),
}


@pytest.mark.parametrize("overlay", OPENED)
def test_what_a_tooltipped_control_opens_puts_the_label_away(
    show: Show, overlay: str
) -> None:
    build, role, around = OPENED[overlay]
    built = build()
    if around:
        built.trigger(Button().content("Open"))
        component = Tooltip().content("More actions").trigger(built)
    else:
        component = built.trigger(
            Tooltip().content("More actions").trigger(Button().content("Open"))
        )
    page = show(component)
    trigger = page.get_by_role("button", name="Open")
    # Described on the control itself, never on a wrapper around it.
    assert _description(page, "button[data-hue-trigger]") == "More actions"
    assert page.locator("[aria-describedby]").count() == 1

    page.keyboard.press("Tab")
    expect(trigger).to_be_focused()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Enter")
    opened = page.get_by_role(role)
    expect(opened).to_be_visible()
    if overlay == "menu":
        expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    elif overlay == "popover":
        expect(trigger).to_be_focused()
    else:
        page.wait_for_function(
            "document.querySelector('[role=dialog]').contains(document.activeElement)"
        )
    page.wait_for_function(f"!{SHOWN}")
    page.keyboard.press("Escape")
    expect(opened).to_be_hidden()
    expect(trigger).to_be_focused()

    # Pointer on and pressed at once, so the hover's open is still pending.
    page.clock.install()
    trigger.click()
    expect(opened).to_be_visible()
    page.clock.run_for(1000)
    assert not page.evaluate(SHOWN)
    page.keyboard.press("Escape")
    expect(opened).to_be_hidden()


def test_a_click_puts_the_label_away_until_the_next_hover_or_tab(
    show: Show,
) -> None:
    page = show(Button().content("Before"), _tooltip(), Button().content("Elsewhere"))
    trigger = page.get_by_role("button", name="Copy")
    trigger.hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    trigger.click()
    expect(page.get_by_role("tooltip")).to_be_hidden()
    expect(trigger).to_be_focused()
    page.get_by_role("button", name="Elsewhere").hover()
    trigger.hover()
    expect(page.get_by_role("tooltip")).to_be_visible()
    trigger.click()
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_role("button", name="Before")).to_be_focused()
    page.keyboard.press("Tab")
    expect(trigger).to_be_focused()
    expect(page.get_by_role("tooltip")).to_be_visible()


def test_focus_from_a_click_does_not_show_the_label(show: Show) -> None:
    page = show(_tooltip(), Button().content("Elsewhere"))
    page.clock.install()
    page.get_by_role("button", name="Copy").click()
    # Pointer away at once, so only the focus could show it.
    page.get_by_role("button", name="Elsewhere").hover()
    page.get_by_role("button", name="Copy").focus()
    page.clock.run_for(1000)
    expect(page.get_by_role("tooltip")).to_be_hidden()


def test_keyboard_activation_keeps_the_label_shown(show: Show) -> None:
    # Shown on keyboard focus, hidden when focus moves on: Enter is neither,
    # even when the click renames the control.
    page = show(
        Tooltip()
        .content("Copy to clipboard")
        .trigger(
            Button().content("Copy").on_click(unsafe("$el.textContent = 'Copied'"))
        )
    )
    page.keyboard.press("Tab")
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Enter")
    copied = page.get_by_role("button", name="Copied")
    expect(copied).to_be_focused()
    expect(copied).to_have_accessible_description("Copy to clipboard")
    # The click's check lands a tick later; the state rather than the bubble,
    # which takes a moment to fade out.
    page.evaluate("new Promise(r => setTimeout(r))")
    assert page.evaluate(SHOWN)


@pytest.fixture
def touch(browser: Browser) -> Iterator[Callable[..., Page]]:
    contexts = []

    def _open(*components: ComponentType) -> Page:
        context = browser.new_context(
            viewport={"width": 400, "height": 700}, has_touch=True, is_mobile=True
        )
        contexts.append(context)
        page = context.new_page()
        document = render_page(*components)

        def fulfil(route, request) -> None:  # type: ignore[no-untyped-def]
            path = request.url.removeprefix(ORIGIN).split("?")[0]
            if path in assets.ASSET_ROUTES:
                content, _ = assets.served_asset(path)
                route.fulfill(body=content, content_type=assets.ASSET_ROUTES[path][1])
            elif path == "/":
                route.fulfill(body=document, content_type="text/html")
            else:
                route.fulfill(status=404)

        page.route(f"{ORIGIN}/**", fulfil)
        page.goto(f"{ORIGIN}/")
        page.wait_for_function("() => window.Alpine && document.body._x_dataStack")
        return page

    yield _open
    for context in contexts:
        context.close()


def test_a_tap_never_opens_the_tooltip(touch: Callable[..., Page]) -> None:
    # On a touch device the tooltip does not open at all, and a tap on a
    # tooltipped menu trigger opens only the menu.
    page = touch(
        _tooltip(),
        DropdownMenu()
        .label("Actions")
        .trigger(Tooltip().content("More actions").trigger(Button().content("More")))
        .content(MenuItem().content("Rename")),
    )
    page.clock.install()
    page.get_by_role("button", name="Copy").tap()
    page.clock.run_for(1000)
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.get_by_role("button", name="More").tap()
    expect(page.get_by_role("menu")).to_be_visible()
    page.clock.run_for(1000)
    expect(page.get_by_role("tooltip")).to_be_hidden()
