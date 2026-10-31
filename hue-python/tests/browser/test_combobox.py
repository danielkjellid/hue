import re

import pytest
from htmy import html
from playwright.sync_api import Locator, Page, expect

from hue.js import unsafe
from hue.ui import Button, Combobox, Dialog, SelectOption, Stack, Text
from tests.browser._fields import contrast, css, still, token
from tests.browser.conftest import Show

_FRAMES = (
    "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
)


def _fruit() -> Combobox:
    return (
        Combobox()
        .name("fruit")
        .label("Fruit")
        .content(
            SelectOption().value("apple").label("Apple"),
            SelectOption().value("banana").label("Banana"),
            SelectOption().value("cherry").label("Cherry"),
        )
    )


def _sent(page: Page) -> Locator:
    return page.locator("input[type=hidden][name=fruit]")


def test_typing_activates_the_first_match(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.fill("ban")
    page.keyboard.press("Enter")
    expect(_sent(page)).to_have_value("banana")


def test_click_on_an_option_chooses_it(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.click()
    page.get_by_role("option", name="Cherry").click()
    expect(_sent(page)).to_have_value("cherry")
    expect(field).to_have_value("Cherry")
    expect(field).to_have_attribute("aria-expanded", "false")


def _place() -> Combobox:
    return (
        Combobox()
        .name("place")
        .label("Place")
        .content(
            SelectOption()
            .value("long")
            .label("Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch"),
        )
    )


def _right(locator: Locator) -> float:
    box = locator.bounding_box()
    assert box is not None
    return box["x"] + box["width"]


def _left(locator: Locator) -> float:
    box = locator.bounding_box()
    assert box is not None
    return box["x"]


def test_a_narrow_field_stops_short_of_the_chevron(show: Show) -> None:
    page = show(_place().value("long"), width=200)
    field = page.get_by_role("combobox", name="Place")
    chevron = page.get_by_role("button", name="Place")
    assert _right(field) <= _left(chevron)


def test_a_long_token_truncates_inside_the_field(show: Show) -> None:
    page = show(_place().multiple().value("long"), width=320)
    token = page.locator('[x-text="item.label"]')
    chevron = page.get_by_role("button", name="Place")
    assert _right(token) <= _left(chevron)
    assert token.evaluate("el => el.scrollWidth > el.clientWidth")


def test_enter_on_a_cleared_field_picks_nothing_and_arrows_still_move(
    show: Show,
) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.fill("ban")
    field.fill("")
    page.keyboard.press("Enter")
    # Nothing chosen submits no field at all.
    expect(_sent(page)).to_have_count(0)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(_sent(page)).to_have_value("apple")


def test_enter_on_a_cleared_multiple_field_keeps_its_tokens(show: Show) -> None:
    page = show(_fruit().multiple().value("apple"))
    field = page.get_by_role("combobox", name="Fruit")
    field.fill("app")
    field.fill("")
    page.keyboard.press("Enter")
    expect(_sent(page)).to_have_value("apple")


def test_focused_invalid_combobox_draws_a_solid_danger_ring(show: Show) -> None:
    page = still(show(_fruit().error("Pick one")))
    page.get_by_role("combobox", name="Fruit").click()
    shell = page.locator("[x-ref=shell]")
    expect(shell).to_have_css("border-top-color", token(page, "danger"))
    assert f"{token(page, 'danger')} 0px 0px 0px 2px" in css(shell, "boxShadow")


# Counts submits and keeps what was sent, without leaving the page.
_COUNT_SUBMITS = (
    "event.preventDefault(); window.submits = (window.submits || 0) + 1; "
    "window.sent = new FormData(this).getAll('fruit')"
)


def _in_a_form(combobox: Combobox) -> html.form:
    return html.form(combobox, onsubmit=_COUNT_SUBMITS)


def _option_id(page: Page, name: str) -> str:
    option_id = page.get_by_role("option", name=name).get_attribute("id")
    assert option_id is not None
    return option_id


def _closed(page: Page) -> Locator:
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    page.keyboard.press("Escape")
    expect(field).to_have_attribute("aria-expanded", "false")
    return field


def test_focus_then_enter_keeps_the_choice_and_next_enter_submits(
    show: Show,
) -> None:
    page = show(_in_a_form(_fruit().value("banana")))
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    expect(field).to_have_attribute("aria-activedescendant", _option_id(page, "Banana"))
    page.keyboard.press("Enter")
    expect(field).to_have_attribute("aria-expanded", "false")
    assert page.evaluate("window.submits") is None
    page.keyboard.press("Enter")
    page.wait_for_function("window.submits === 1")
    assert page.evaluate("window.sent") == ["banana"]


def test_focus_skips_a_disabled_first_option(show: Show) -> None:
    combobox = (
        Combobox()
        .name("fruit")
        .label("Fruit")
        .content(
            SelectOption().value("apple").label("Apple").disabled(),
            SelectOption().value("banana").label("Banana"),
        )
    )
    page = show(combobox)
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    expect(field).to_have_attribute("aria-activedescendant", _option_id(page, "Banana"))


def test_tab_away_keeps_the_value(show: Show) -> None:
    page = show(_fruit().value("banana"), Button().content("After"))
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="After")).to_be_focused()
    expect(_sent(page)).to_have_value("banana")


def test_down_opens_on_the_chosen_option(show: Show) -> None:
    page = show(_fruit().value("banana"))
    field = _closed(page)
    page.keyboard.press("ArrowDown")
    expect(field).to_have_attribute("aria-activedescendant", _option_id(page, "Banana"))


def test_up_opens_on_the_last_option(show: Show) -> None:
    page = show(_fruit())
    field = _closed(page)
    page.keyboard.press("ArrowUp")
    expect(field).to_have_attribute("aria-activedescendant", _option_id(page, "Cherry"))


def test_alt_down_opens_with_nothing_active(show: Show) -> None:
    page = show(_fruit())
    field = _closed(page)
    page.keyboard.press("Alt+ArrowDown")
    expect(field).to_have_attribute("aria-expanded", "true")
    expect(field).not_to_have_attribute("aria-activedescendant", re.compile(".*"))


def test_escape_closes_the_list(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    expect(page.get_by_role("listbox")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("listbox")).to_be_hidden()
    expect(field).to_be_focused()


@pytest.mark.parametrize("query", ["", "x"], ids=["cleared", "no match"])
def test_enter_with_the_list_open_never_submits(show: Show, query: str) -> None:
    page = show(_in_a_form(_fruit().value("apple")))
    field = page.get_by_role("combobox", name="Fruit")
    field.fill(query)
    # Implicit submission is the Enter's default action, so it has happened
    # by the time the press returns.
    page.keyboard.press("Enter")
    assert page.evaluate("window.submits") is None
    expect(field).to_have_attribute("aria-expanded", "true")


def test_down_then_enter_straight_away_chooses(show: Show) -> None:
    page = show(_in_a_form(_fruit()))
    _closed(page)
    # Back to back, before anything waits a tick.
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(_sent(page)).to_have_value("apple")
    assert page.evaluate("window.submits") is None


def test_escape_straight_after_focus_leaves_nothing_active(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    # In one task, so the Escape arrives before anything waits a tick.
    field.evaluate(
        """el => {
            el.focus();
            el.dispatchEvent(
                new KeyboardEvent("keydown", { key: "Escape", bubbles: true })
            );
        }"""
    )
    expect(field).to_have_attribute("aria-expanded", "false")
    page.keyboard.press("Alt+ArrowDown")
    expect(field).to_have_attribute("aria-expanded", "true")
    expect(field).not_to_have_attribute("aria-activedescendant", re.compile(".*"))


def test_multiple_enter_toggles_and_backspace_removes_the_last(show: Show) -> None:
    page = show(_in_a_form(_fruit().multiple()))
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(field).to_have_attribute("aria-expanded", "true")
    expect(page.get_by_role("button", name="Remove Apple")).to_be_visible()
    expect(page.get_by_role("button", name="Remove Banana")).to_be_visible()
    # Enter again on Banana takes it away.
    page.keyboard.press("Enter")
    expect(page.get_by_role("button", name="Remove Banana")).to_have_count(0)
    assert page.evaluate("window.submits") is None
    page.keyboard.press("Backspace")
    expect(page.get_by_role("button", name="Remove Apple")).to_have_count(0)


def test_multiple_escape_then_enter_submits_every_value(show: Show) -> None:
    page = show(_in_a_form(_fruit().multiple().value("apple", "cherry")))
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.press("Escape")
    page.keyboard.press("Enter")
    page.wait_for_function("window.submits === 1")
    assert page.evaluate("window.sent") == ["apple", "cherry"]


def test_x_model_works_both_ways(show: Show) -> None:
    page = show(
        Stack()
        .x_data({"fruit": "apple"})
        .content(
            _fruit().x_model(unsafe("fruit")),
            Button().content("Pick cherry").on_click(unsafe("fruit = 'cherry'")),
            Text().x_text(unsafe("'Chosen: ' + fruit")),
        )
    )
    field = page.get_by_role("combobox", name="Fruit")
    expect(field).to_have_value("Apple")
    page.get_by_role("button", name="Pick cherry").click()
    expect(field).to_have_value("Cherry")
    field.focus()
    field.fill("ban")
    page.keyboard.press("Enter")
    expect(page.get_by_text("Chosen: banana")).to_be_visible()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_meta_on_selected_and_active_rows_is_legible(show: Show, theme: str) -> None:
    combobox = (
        Combobox()
        .name("country")
        .label("Country")
        .value("se")
        .content(
            SelectOption().value("no").label("Norway").meta("NO"),
            SelectOption().value("se").label("Sweden").meta("SE"),
        )
    )
    page = still(show(combobox, theme=theme))
    page.get_by_role("combobox", name="Country").focus()
    # Sweden is chosen; moving up leaves it selected but not active.
    page.keyboard.press("ArrowUp")
    expect(page.get_by_role("option", name="Norway")).to_have_attribute(
        "data-active", "true"
    )
    listbox = page.get_by_role("listbox")
    assert contrast(listbox.get_by_text("SE", exact=True)) >= 4.5
    assert contrast(listbox.get_by_text("NO", exact=True)) >= 4.5


# Scrolling a long list


def _long(value: str | None = "v39", multiple: bool = False) -> Combobox:
    combobox = (
        Combobox()
        .name("fruit")
        .label("Fruit")
        .content(
            *(SelectOption().value(f"v{i}").label(f"Option {i:02}") for i in range(40))
        )
    )
    if multiple:
        combobox = combobox.multiple()
    return combobox.value(value) if value else combobox


def _list(page: Page) -> Locator:
    return page.get_by_role("listbox")


def _in_view(page: Page, value: str) -> bool:
    return page.evaluate(
        """value => {
            const o = document.querySelector(`[role=option][data-value=${value}]`);
            const l = document.querySelector('[role=listbox]');
            const a = o.getBoundingClientRect(), b = l.getBoundingClientRect();
            return a.height > 0 && a.top >= b.top - 1 && a.bottom <= b.bottom + 1;
        }""",
        value,
    )


def _settle(page: Page) -> None:
    for _ in range(3):
        page.evaluate(_FRAMES)


def _scrolled(page: Page) -> None:
    page.wait_for_function(
        "() => document.querySelector('[role=listbox]').scrollTop > 0"
    )


def test_focus_opens_scrolled_to_the_chosen_option_and_keeps_the_users_scroll(
    show: Show,
) -> None:
    page = show(_long(), height=800)
    page.get_by_role("combobox", name="Fruit").focus()
    _scrolled(page)
    assert _in_view(page, "v39")
    _settle(page)
    bottom = _list(page).evaluate("el => el.scrollTop")
    box = page.get_by_role("listbox").bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.wheel(0, -600)
    page.wait_for_function(
        f"() => document.querySelector('[role=listbox]').scrollTop < {bottom}"
    )
    # Dragging the scrollbar sets scrollTop the same way.
    _list(page).evaluate("el => { el.scrollTop = 0 }")
    _settle(page)
    assert _list(page).evaluate("el => el.scrollTop") == 0
    # A viewport resize while open does not scroll it back either.
    page.set_viewport_size({"width": 1000, "height": 500})
    _settle(page)
    assert _list(page).evaluate("el => el.scrollTop") == 0


def test_filtering_scrolls_the_first_match_into_view(show: Show) -> None:
    page = show(_long(value=None))
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    field.press_sequentially("Option 3")
    page.wait_for_function("() => document.querySelector('[data-active]') !== null")
    _settle(page)
    expect(page.locator("[role=option][data-active]")).to_have_attribute(
        "data-value", "v30"
    )
    assert _in_view(page, "v30")


def test_focus_open_does_not_scroll_the_page(show: Show) -> None:
    page = show(
        html.div(style="height: 1000px"),
        _long(),
        html.div(style="height: 1500px"),
        height=800,
    )
    # The field near the bottom of the viewport, so the list overflows it.
    page.evaluate("window.scrollTo(0, 300)")
    _settle(page)
    page.get_by_role("combobox", name="Fruit").evaluate(
        "el => el.focus({ preventScroll: true })"
    )
    _scrolled(page)
    _settle(page)
    assert page.evaluate("window.scrollY") == 300


def test_open_in_a_scrolled_container_leaves_the_container_alone(show: Show) -> None:
    page = show(
        html.div(
            html.div(style="height: 300px"),
            _long(),
            html.div(style="height: 900px"),
            id="box",
            style="height: 400px; overflow: auto",
        )
    )
    page.evaluate("document.getElementById('box').scrollTop = 200")
    page.get_by_role("combobox", name="Fruit").focus()
    _scrolled(page)
    _settle(page)
    assert page.evaluate("document.getElementById('box').scrollTop") == 200
    assert page.evaluate("window.scrollY") == 0
    assert _in_view(page, "v39")


def test_open_in_a_dialog_scrolls_to_the_chosen_option(show: Show) -> None:
    dialog = Dialog().title("Pick").trigger(Button().content("Open")).content(_long())
    page = show(dialog)
    page.get_by_role("button", name="Open").click()
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    expect(field).to_have_attribute("aria-expanded", "true")
    _scrolled(page)
    assert _in_view(page, "v39")
    expect(page.get_by_role("dialog")).to_be_visible()


def test_multiple_choosing_far_down_keeps_the_option_in_view(show: Show) -> None:
    page = show(_long(value=None, multiple=True), width=420)
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    for _ in range(35):
        page.keyboard.press("ArrowDown")
    for _ in range(3):
        page.keyboard.press("Enter")
        page.keyboard.press("ArrowDown")
    expect(page.get_by_role("button", name="Remove Option 35")).to_be_visible()
    _settle(page)
    active = page.locator("[role=option][data-active]").get_attribute("data-value")
    assert active is not None
    assert _in_view(page, active)
    # The user's own scroll survives the tokens settling.
    _list(page).evaluate("el => { el.scrollTop = 0 }")
    _settle(page)
    assert _list(page).evaluate("el => el.scrollTop") == 0
