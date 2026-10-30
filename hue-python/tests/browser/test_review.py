"""
What the overlay fixes promise in combinations their own tests left out:
tooltips meeting clicks, touch and nested overlays, every overlay's trigger
described by a Tooltip, menus in drawers and button groups.
"""

from collections.abc import Callable, Iterator

import pytest
from playwright.sync_api import Browser, Page, expect

from hue import assets, html
from hue.js import unsafe
from hue.ui import (
    Button,
    ButtonGroup,
    Dialog,
    Drawer,
    DropdownMenu,
    MenuItem,
    MenuLabel,
    Popover,
    Tooltip,
)
from tests.browser.conftest import ORIGIN, Show, render_page


def _tooltip(name: str = "Copy", text: str = "Copy to clipboard") -> Tooltip:
    return Tooltip().content(text).trigger(Button().content(name))


def _described(page: Page, selector: str = "button") -> tuple[str, str]:
    # Chrome's own name and description, which is what a screen reader reads.
    cdp = page.context.new_cdp_session(page)
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    node = cdp.send("DOM.querySelector", {"nodeId": root, "selector": selector})
    tree = cdp.send("Accessibility.getPartialAXTree", {"nodeId": node["nodeId"]})
    ax = tree["nodes"][0]
    return ax["name"]["value"], ax.get("description", {}).get("value", "")


# Tooltip on a plain control


def test_a_click_then_the_keyboard_shows_the_label(show: Show) -> None:
    page = show(Button().content("Before"), _tooltip())
    trigger = page.get_by_role("button", name="Copy")
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


def test_a_label_put_away_by_a_click_comes_back_on_the_next_hover(
    show: Show,
) -> None:
    page = show(_tooltip(), Button().content("Elsewhere"))
    page.keyboard.press("Tab")
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.get_by_role("button", name="Copy").click()
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.get_by_role("button", name="Elsewhere").hover()
    page.get_by_role("button", name="Copy").hover()
    expect(page.get_by_role("tooltip")).to_be_visible()


@pytest.fixture
def touch(browser: Browser) -> Iterator[Callable[..., Page]]:
    contexts = []

    def _open(*components) -> Page:  # type: ignore[no-untyped-def]
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
    # The docstring: on a touch device the tooltip does not open at all.
    page = touch(_tooltip())
    page.clock.install()
    page.get_by_role("button", name="Copy").tap()
    page.clock.run_for(1000)
    expect(page.get_by_role("tooltip")).to_be_hidden()


def test_a_tap_on_a_tooltipped_menu_trigger_opens_only_the_menu(
    touch: Callable[..., Page],
) -> None:
    page = touch(
        DropdownMenu()
        .label("Actions")
        .trigger(_tooltip("More", "More actions"))
        .content(MenuItem().content("Rename"))
    )
    page.clock.install()
    page.get_by_role("button", name="More").tap()
    expect(page.get_by_role("menu")).to_be_visible()
    page.clock.run_for(1000)
    expect(page.get_by_role("tooltip")).to_be_hidden()


# Escape through nested overlays


def test_escape_closes_popover_then_tooltip_then_dialog(show: Show) -> None:
    page = show(
        Dialog()
        .title("Holder")
        .open()
        .content(Popover().title("Sharing").trigger(_tooltip("Share", "Sharing")))
    )
    trigger = page.get_by_role("button", name="Share")
    trigger.focus()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    expect(trigger).to_be_focused()
    if page.get_by_role("tooltip").is_visible():
        page.keyboard.press("Escape")
        expect(page.get_by_role("tooltip")).to_be_hidden()
        expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


def test_a_tooltip_inside_a_popover_in_a_dialog_closes_first(show: Show) -> None:
    page = show(
        Dialog()
        .title("Holder")
        .open()
        .content(
            Popover()
            .title("Sharing")
            .trigger(Button().content("Share"))
            .content(_tooltip())
        )
    )
    page.get_by_role("button", name="Share").click()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Copy")).to_be_focused()
    expect(page.get_by_role("tooltip")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("tooltip")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Sharing")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Sharing")).to_be_hidden()
    expect(page.get_by_role("dialog", name="Holder")).to_be_visible()
    expect(page.get_by_role("button", name="Share")).to_be_focused()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Holder")).to_be_hidden()


# Every overlay's trigger, described by a Tooltip either way round


def _overlays() -> dict[str, Callable[[], object]]:
    return {
        "menu": lambda: DropdownMenu()
        .label("Actions")
        .content(MenuItem().content("Rename")),
        "popover": lambda: Popover().title("Sharing"),
        "dialog": lambda: Dialog().title("Settings"),
        "drawer": lambda: Drawer().title("Filters"),
    }


ROLES = {"menu": "menu", "popover": "dialog", "dialog": "dialog", "drawer": "dialog"}


@pytest.mark.parametrize("around", [False, True])
@pytest.mark.parametrize("overlay", list(ROLES))
def test_the_overlay_trigger_is_described_by_its_tooltip(
    show: Show, overlay: str, around: bool
) -> None:
    built = _overlays()[overlay]()
    if around:
        built.trigger(Button().content("Open"))  # type: ignore[attr-defined]
        component = Tooltip().content("More actions").trigger(built)  # type: ignore[arg-type]
    else:
        component = built.trigger(_tooltip("Open", "More actions"))  # type: ignore[attr-defined]
    page = show(component)
    assert _described(page, "button[data-hue-trigger]") == ("Open", "More actions")
    # Only the control carries it, never a wrapper around it.
    assert page.locator("[aria-describedby]").count() == 1


@pytest.mark.parametrize("around", [False, True])
def test_a_quick_click_on_a_tooltipped_drawer_trigger(show: Show, around: bool) -> None:
    drawer = Drawer().title("Filters")
    if around:
        drawer.trigger(Button().content("Open"))
        component = Tooltip().content("More actions").trigger(drawer)
    else:
        component = drawer.trigger(_tooltip("Open", "More actions"))
    page = show(component)
    page.clock.install()
    page.get_by_role("button", name="Open").click()
    expect(page.get_by_role("dialog", name="Filters")).to_be_visible()
    page.clock.run_for(1000)
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog", name="Filters")).to_be_hidden()
    expect(page.get_by_role("button", name="Open")).to_be_focused()


# DropdownMenu inside a Drawer in a right-to-left page


def test_a_menu_in_a_drawer_in_rtl_closes_before_the_drawer(show: Show) -> None:
    page = show(
        Drawer()
        .title("Filters")
        .trigger(Button().content("Open"))
        .content(
            DropdownMenu()
            .label("Actions")
            .trigger(_tooltip("More", "More actions"))
            .content(
                MenuLabel().content("Row"),
                MenuItem().content("Rename"),
                MenuItem().content("Delete"),
            )
        ),
        dir="rtl",
    )
    page.get_by_role("button", name="Open").click()
    drawer = page.get_by_role("dialog", name="Filters")
    expect(drawer).to_be_visible()
    more = page.get_by_role("button", name="More")
    more.focus()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    expect(page.get_by_role("tooltip")).to_be_hidden()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Delete")).to_be_focused()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    menu = page.get_by_role("menu")
    page.wait_for_function(
        """el => {
            const r = el.getBoundingClientRect();
            return r.left >= 0 && r.right <= innerWidth && r.bottom <= innerHeight
                && document.elementFromPoint((r.left + r.right) / 2,
                    r.top + 10)?.closest('[role=menu]') === el;
        }""",
        arg=menu.element_handle(),
    )
    page.keyboard.press("Escape")
    expect(menu).to_be_hidden()
    expect(drawer).to_be_visible()
    expect(more).to_be_focused()
    if page.get_by_role("tooltip").is_visible():
        page.keyboard.press("Escape")
        expect(drawer).to_be_visible()
    page.keyboard.press("Escape")
    expect(drawer).to_be_hidden()
    expect(page.get_by_role("button", name="Open")).to_be_focused()


def test_a_narrow_rtl_side_drawer_is_still_a_bottom_sheet(show: Show) -> None:
    page = show(
        Drawer().title("Filters").side("end").trigger(Button().content("Open")),
        width=500,
        dir="rtl",
    )
    page.get_by_role("button", name="Open").click()
    expect(page.get_by_role("dialog", name="Filters")).to_be_visible()
    page.wait_for_function("document.getAnimations().length === 0")
    box = page.locator("aside").bounding_box()
    assert box is not None
    assert box["x"] == 0 and box["width"] == 500
    assert abs(box["y"] + box["height"] - 800) <= 1


# Menu labels and disabled items


def test_labels_without_separators_each_name_their_own_run(show: Show) -> None:
    menu = lambda: (  # noqa: E731
        DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(
            MenuLabel().content("Project"),
            MenuItem().content("Rename"),
            MenuLabel().content("Sharing"),
            MenuItem().checkable().content("Public"),
        )
    )
    page = show(menu(), menu())
    page.get_by_role("button", name="Actions").first.click()
    first = page.get_by_role("menu").first
    expect(
        first.get_by_role("group", name="Project").get_by_role("menuitem")
    ).to_have_text(["Rename"])
    expect(
        first.get_by_role("group", name="Sharing").get_by_role("menuitemcheckbox")
    ).to_have_text(["Public"])
    ids = page.evaluate(
        "[...document.querySelectorAll('[role=group] > div')].map(l => l.id)"
    )
    assert len(ids) == 4 and len(set(ids)) == 4 and all(ids)
    # A checkable item in a group still toggles and keeps the menu open.
    expect(first.get_by_role("menuitem", name="Rename")).to_be_focused()
    page.keyboard.press("End")
    expect(first.get_by_role("menuitemcheckbox", name="Public")).to_be_focused()
    page.keyboard.press("Enter")
    expect(first.get_by_role("menuitemcheckbox", name="Public")).to_have_attribute(
        "aria-checked", "true"
    )
    expect(first).to_be_visible()


def test_a_disabled_item_is_reached_by_the_arrows_and_does_nothing(
    show: Show,
) -> None:
    page = show(
        DropdownMenu()
        .label("Actions")
        .trigger(Button().content("Actions"))
        .content(
            MenuLabel().content("Project"),
            MenuItem().content("Rename"),
            MenuItem()
            .disabled()
            .on_click(unsafe("window.hit = true"))
            .content("Transfer"),
        )
    )
    page.get_by_role("button", name="Actions").focus()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="Rename")).to_be_focused()
    page.keyboard.press("ArrowDown")
    transfer = page.get_by_role("menuitem", name="Transfer")
    expect(transfer).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_role("menu")).to_be_visible()
    assert page.evaluate("window.hit") is None


# ButtonGroup with wrapped controls


CONTROLS = """
() => [...document.querySelectorAll('main > div:first-child button')]
    .filter(button => !button.closest('[role=menu],[role=dialog]'))
    .map(button => {
        const style = getComputedStyle(button);
        return [
            style.borderTopLeftRadius !== '0px',
            style.borderTopRightRadius !== '0px',
        ];
    })
"""


def _icon(name: str) -> Button:
    return Button().variant("outline").icon_only(name).content(name[0])


def test_tooltipped_icon_buttons_take_the_group_corners_and_lift(show: Show) -> None:
    page = show(
        ButtonGroup()
        .label("Selection")
        .content(
            Tooltip().placement("end").content("Add a row").trigger(_icon("Add")),
            Tooltip().placement("end").content("Copy rows").trigger(_icon("Copy")),
            Tooltip().placement("end").content("Delete rows").trigger(_icon("Delete")),
        )
    )
    assert page.evaluate(CONTROLS) == [[True, False], [False, False], [False, True]]
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Copy")).to_be_focused()
    bubble = page.get_by_role("tooltip", name="Copy rows")
    expect(bubble).to_be_visible()
    # Lifted itself rather than through its span, so the column the next
    # button is pulled onto is the focused one's, or its own bubble's.
    assert page.get_by_role("button", name="Copy").evaluate(
        """el => {
            const r = el.getBoundingClientRect();
            const y = (r.top + r.bottom) / 2;
            const hit = document.elementFromPoint(r.right - 0.5, y);
            return el.parentElement.contains(hit);
        }"""
    )
    # The bubble hangs over the next button and stays on top of it.
    page.wait_for_function(
        """el => {
            const r = el.getBoundingClientRect();
            const hit = document.elementFromPoint(r.left + 4, (r.top + r.bottom) / 2);
            return el.contains(hit);
        }""",
        arg=bubble.element_handle(),
    )


def test_the_documented_split_button_keeps_its_corners(show: Show) -> None:
    page = show(
        ButtonGroup().content(
            Button().variant("outline").size("sm").content("Export"),
            DropdownMenu()
            .label("Export options")
            .placement("bottom-end")
            .trigger(
                Button()
                .variant("outline")
                .size("sm")
                .icon_only("Export options")
                .class_("rounded-s-none")
                .content("v")
            )
            .content(MenuItem().content("Export as CSV")),
        )
    )
    assert page.evaluate(CONTROLS) == [[True, False], [False, True]]


def test_an_open_menu_in_a_group_is_not_covered(show: Show) -> None:
    def group(name: str) -> ButtonGroup:
        return ButtonGroup().content(
            Button().variant("outline").content(f"{name} export"),
            DropdownMenu()
            .label(f"{name} options")
            .trigger(Button().variant("outline").content(f"{name} options"))
            .content(*(MenuItem().content(f"{name} item {i}") for i in range(4))),
        )

    page = show(group("First"), html.div().class_("h-2"), group("Second"))
    page.get_by_role("button", name="First options").focus()
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("menuitem", name="First item 0")).to_be_focused()
    page.wait_for_function(
        """() => [...document.querySelectorAll('[role=menu]')][0]
            .querySelectorAll('[role=menuitem]').length === 4
          && [...[...document.querySelectorAll('[role=menu]')][0]
            .querySelectorAll('[role=menuitem]')].every(item => {
                const r = item.getBoundingClientRect();
                return item.contains(document.elementFromPoint(
                    (r.left + r.right) / 2, (r.top + r.bottom) / 2));
            })"""
    )
