"""
What the input fixes could have broken, from what the docs promise.
"""

from datetime import date

import pytest
from htmy import html
from playwright.sync_api import Locator, Page, expect

from hue.js import unsafe
from hue.ui import (
    Button,
    Combobox,
    Command,
    CommandItem,
    DatePicker,
    Label,
    NativeSelect,
    NumberInput,
    PasswordInput,
    Select,
    SelectOption,
    Stack,
    Text,
    Textarea,
    TextInput,
)
from hue.ui._styles import ControlSize
from tests.browser._fields import contrast, row_of_pixels, still, token
from tests.browser.conftest import Show

_COUNT_SUBMITS = (
    "event.preventDefault(); window.submits = (window.submits || 0) + 1; "
    "window.sent = [...new FormData(this).entries()].map(([k, v]) => k + '=' + v)"
)


def _form(*children: object) -> html.form:
    return html.form(*children, onsubmit=_COUNT_SUBMITS)  # type: ignore[arg-type]


def _box(locator: Locator) -> dict[str, float]:
    box = locator.bounding_box()
    assert box is not None
    return box


# Combobox


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


def test_combobox_click_on_an_option_chooses_it(show: Show) -> None:
    page = show(_fruit())
    field = page.get_by_role("combobox", name="Fruit")
    field.click()
    page.get_by_role("option", name="Cherry").click()
    expect(page.locator("input[type=hidden][name=fruit]")).to_have_value("cherry")
    expect(field).to_have_value("Cherry")
    expect(field).to_have_attribute("aria-expanded", "false")


def test_combobox_focus_then_enter_keeps_the_choice_and_next_enter_submits(
    show: Show,
) -> None:
    page = show(_form(_fruit().value("banana")))
    field = page.get_by_role("combobox", name="Fruit")
    field.focus()
    banana = page.get_by_role("option", name="Banana").get_attribute("id")
    expect(field).to_have_attribute("aria-activedescendant", banana or "")
    page.keyboard.press("Enter")
    expect(field).to_have_attribute("aria-expanded", "false")
    assert page.evaluate("window.submits") is None
    page.keyboard.press("Enter")
    page.wait_for_function("window.submits === 1")
    assert page.evaluate("window.sent") == ["fruit=banana"]


def test_combobox_tab_away_keeps_the_value(show: Show) -> None:
    page = show(_fruit().value("banana"), Button().content("After"))
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="After")).to_be_focused()
    expect(page.locator("input[type=hidden][name=fruit]")).to_have_value("banana")


def test_combobox_focus_skips_a_disabled_first_option(show: Show) -> None:
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
    banana = page.get_by_role("option", name="Banana").get_attribute("id")
    expect(field).to_have_attribute("aria-activedescendant", banana or "")


def test_combobox_multiple_enter_toggles_and_keeps_the_list_open(show: Show) -> None:
    page = show(_form(_fruit().multiple()))
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


def test_combobox_multiple_escape_then_enter_submits_every_value(show: Show) -> None:
    page = show(_form(_fruit().multiple().value("apple", "cherry")))
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.press("Escape")
    page.keyboard.press("Enter")
    page.wait_for_function("window.submits === 1")
    assert page.evaluate("window.sent") == ["fruit=apple", "fruit=cherry"]


def test_combobox_x_model_works_both_ways(show: Show) -> None:
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


# DatePicker


def _picker() -> DatePicker:
    return DatePicker().name("day").label("Day").value(date(2026, 10, 14))


def _sent_days(page: Page) -> list[str]:
    return page.evaluate(
        "[...document.querySelectorAll('input[type=hidden][name=day]')]"
        ".map(input => input.value)"
    )


@pytest.mark.parametrize("key", ["Enter", " "], ids=["enter", "space"])
def test_date_picker_leading_blank_cell_picks_nothing(show: Show, key: str) -> None:
    page = show(_picker())
    page.locator('td[data-date="2026-10-14"]').focus()
    page.keyboard.press("ArrowRight")
    expect(page.locator('td[data-date="2026-10-15"]')).to_be_focused()
    # October 2026 starts on a Thursday, so a Monday week opens with blanks.
    page.locator("td:not([data-date])").first.click()
    page.keyboard.press(key)
    assert _sent_days(page) == ["2026-10-14"]


def test_date_picker_enter_in_a_form_picks_and_does_not_submit(show: Show) -> None:
    page = show(_form(_picker()))
    page.locator('td[data-date="2026-10-14"]').focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Enter")
    expect(page.locator('td[data-date="2026-10-15"]')).to_have_attribute(
        "aria-selected", "true"
    )
    assert page.evaluate("window.submits") is None


def test_date_picker_enter_on_a_blank_cell_in_a_form_does_not_submit(
    show: Show,
) -> None:
    page = show(_form(_picker()))
    page.locator("td:not([data-date])").last.click()
    page.keyboard.press("Enter")
    assert page.evaluate("window.submits") is None
    assert _sent_days(page) == ["2026-10-14"]


def test_date_picker_enter_on_a_refused_day_picks_nothing(show: Show) -> None:
    picker = _picker().max(date(2026, 10, 15)).unavailable("saturday")
    page = show(picker)
    page.locator('td[data-date="2026-10-14"]').focus()
    # The 16th is past max(), and the 17th is a Saturday.
    for _ in range(2):
        page.keyboard.press("ArrowRight")
    expect(page.locator('td[data-date="2026-10-16"]')).to_be_focused()
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowRight")
    expect(page.locator('td[data-date="2026-10-17"]')).to_be_focused()
    page.keyboard.press(" ")
    assert _sent_days(page) == ["2026-10-14"]


def test_date_picker_enter_straight_after_a_move_onto_a_refused_day(
    show: Show,
) -> None:
    page = show(_picker().unavailable("thursday"))
    cell = page.locator('td[data-date="2026-10-14"]')
    cell.focus()
    # Wednesday the 14th, then Thursday the 15th and Enter in one task.
    cell.evaluate(
        """el => {
            for (const key of ["ArrowRight", "Enter"]) {
                el.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
            }
        }"""
    )
    expect(page.locator('td[data-date="2026-10-15"]')).to_be_focused()
    assert _sent_days(page) == ["2026-10-14"]


def test_date_picker_keys_in_one_of_two_pickers_leave_the_other_alone(
    show: Show,
) -> None:
    other = DatePicker().name("other").label("Other").value(date(2026, 10, 14))
    page = show(_picker(), other)
    first = page.locator('td[data-date="2026-10-14"]').first
    blank = page.locator("fieldset").nth(1).locator("td:not([data-date])").last
    blank.click()
    # A move in the first picker and Enter on the second's blank in one task.
    first.evaluate(
        """(el, blank) => {
            el.dispatchEvent(
                new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true })
            );
            blank.dispatchEvent(
                new KeyboardEvent("keydown", { key: "Enter", bubbles: true })
            );
        }""",
        blank.element_handle(),
    )
    assert page.evaluate(
        "[...document.querySelectorAll('input[type=hidden][name=other]')]"
        ".map(input => input.value)"
    ) == ["2026-10-14"]


# Command


def _palette() -> Command:
    return (
        Command()
        .trigger(Button().content("Open"))
        .content(
            CommandItem()
            .label("Archived reports")
            .disabled()
            .action(unsafe("window.ran = 'archived'")),
            CommandItem().label("Go to settings").action(unsafe("window.ran = 'go'")),
            CommandItem()
            .label("Delete workspace")
            .action(unsafe("window.ran = 'del'")),
        )
    )


def _open(page: Page) -> Locator:
    page.get_by_role("button", name="Open").click()
    field = page.get_by_role("combobox", name="Command palette")
    expect(field).to_be_focused()
    return field


def test_command_enter_with_no_match_runs_nothing(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    field.press_sequentially("zzz")
    page.keyboard.press("Enter")
    expect(page.get_by_role("dialog")).to_be_visible()
    assert page.evaluate("window.ran") is None
    # Clearing the text brings back a first match for Enter.
    page.keyboard.press("Escape")
    page.keyboard.press("Enter")
    page.wait_for_function("window.ran === 'go'")


def test_command_typing_skips_a_disabled_first_match(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    # Both "Archived reports" and "Delete workspace" contain an "r".
    field.press_sequentially("r")
    page.keyboard.press("Enter")
    page.wait_for_function("window.ran === 'go' || window.ran === 'del'")
    assert page.evaluate("window.ran") != "archived"


def test_command_reopened_after_a_search_runs_the_first_item(show: Show) -> None:
    page = show(_palette())
    field = _open(page)
    field.press_sequentially("delete")
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_be_hidden()
    field = _open(page)
    expect(field).to_have_value("")
    expect(page.get_by_role("option", name="Delete workspace")).to_be_visible()
    expect(page.locator("[role=option][data-active]")).to_have_text("Go to settings")
    page.keyboard.press("Enter")
    page.wait_for_function("window.ran === 'go'")


# Select


def _plans() -> Select:
    return (
        Select()
        .name("plan")
        .label("Plan")
        .content(
            SelectOption().value("free").label("Free"),
            SelectOption().value("team").label("Team").disabled(),
            SelectOption().value("pro").label("Pro"),
            SelectOption().value("max").label("Max"),
        )
    )


def _active_option(page: Page) -> Locator:
    return page.locator("[role=option][data-active]")


def test_select_home_end_and_disabled_options(show: Show) -> None:
    page = show(_plans())
    page.get_by_role("combobox", name="Plan").focus()
    page.keyboard.press("End")
    expect(_active_option(page)).to_have_attribute("data-value", "max")
    page.keyboard.press("Home")
    expect(_active_option(page)).to_have_attribute("data-value", "free")
    page.keyboard.press("ArrowDown")
    expect(_active_option(page)).to_have_attribute("data-value", "pro")
    page.keyboard.press("PageDown")
    expect(_active_option(page)).to_have_attribute("data-value", "max")
    page.keyboard.press("PageUp")
    expect(_active_option(page)).to_have_attribute("data-value", "free")
    page.keyboard.press("Enter")
    expect(page.locator("input[name=plan]")).to_have_value("free")


def test_select_typeahead_moves_to_the_match(show: Show) -> None:
    page = show(_plans())
    page.get_by_role("combobox", name="Plan").focus()
    page.keyboard.press("Enter")
    page.keyboard.type("ma")
    expect(_active_option(page)).to_have_attribute("data-value", "max")
    page.keyboard.press("Tab")
    expect(page.locator("input[name=plan]")).to_have_value("max")


_RECORD_REJECTION = """reason => new Promise(done => {
    window.addEventListener("unhandledrejection", (event) => {
        // Read after every listener before this one has had its say, then
        // handled here so the test's own fixture does not see it.
        const prevented = event.defaultPrevented;
        event.preventDefault();
        done(prevented);
    }, { once: true });
    Promise.reject(reason === "cancelled" ? { isFromCancelledTransition: true }
        : new Error("real"));
})"""


@pytest.mark.parametrize("with_select", [True, False], ids=["select", "no select"])
def test_a_real_rejection_is_not_swallowed(show: Show, with_select: bool) -> None:
    page = show(_plans() if with_select else Text("Plain"))
    assert page.evaluate(_RECORD_REJECTION, "real") is False


def test_a_cancelled_transition_rejection_is_handled(show: Show) -> None:
    page = show(_plans())
    assert page.evaluate(_RECORD_REJECTION, "cancelled") is True


# Contrast on lit rows


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_combobox_meta_on_a_selected_row_is_legible(show: Show, theme: str) -> None:
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


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_select_meta_on_a_plain_row_is_unchanged(show: Show, theme: str) -> None:
    select = (
        Select()
        .name("plan")
        .label("Plan")
        .content(
            SelectOption().value("free").label("Free").meta("$0"),
            SelectOption().value("pro").label("Pro").meta("$9"),
        )
    )
    page = still(show(select, theme=theme))
    page.get_by_role("combobox", name="Plan").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("option", name="Free")).to_have_attribute(
        "data-active", "true"
    )
    meta = page.get_by_role("listbox").get_by_text("$9")
    expect(meta).to_have_css("color", token(page, "fg-subtle"))


# Textarea


def _bio() -> Textarea:
    return Textarea().name("bio").label("Bio").autosize()


def _height(locator: Locator) -> float:
    return locator.evaluate("el => el.offsetHeight")


def test_textarea_dragged_shorter_than_its_text_grows_back_to_fit(
    show: Show,
) -> None:
    page = show(_bio())
    field = page.get_by_label("Bio")
    field.fill("\n".join(["line"] * 8))
    tall = _height(field)
    field.evaluate("el => { el.style.height = '90px' }")
    field.press("End")
    field.press("a")
    assert _height(field) == tall
    assert field.evaluate("el => el.scrollHeight <= el.clientHeight")


def test_textarea_rendered_with_long_text_shrinks_when_emptied(show: Show) -> None:
    page = show(_bio().value("\n".join(["line"] * 10)))
    field = page.get_by_label("Bio")
    tall = _height(field)
    field.fill("")
    assert _height(field) < tall


def test_textarea_shrinks_after_a_width_change(show: Show) -> None:
    page = show(html.div(_bio(), id="box", style="width: 400px"))
    field = page.get_by_label("Bio")
    start = _height(field)
    field.fill("word " * 60)
    page.evaluate("document.getElementById('box').style.width = '250px'")
    page.wait_for_function(
        "() => { const el = document.querySelector('textarea');"
        " return el.scrollHeight <= el.clientHeight && el.offsetWidth < 300 }"
    )
    page.evaluate(
        "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
    )
    field.fill("short")
    assert _height(field) == start


def test_textarea_shrinks_after_a_form_reset(show: Show) -> None:
    page = show(html.form(_bio(), id="f"))
    field = page.get_by_label("Bio")
    start = _height(field)
    field.fill("\n".join(["line"] * 8))
    page.evaluate("document.getElementById('f').reset()")
    field.press("a")
    assert _height(field) == start


def test_textarea_set_through_x_model_then_typed_in_shrinks(show: Show) -> None:
    page = show(
        Stack()
        .x_data({"bio": ""})
        .content(
            _bio().x_model(unsafe("bio")),
            Button().content("Fill").on_click(unsafe("bio = 'a\\n'.repeat(10)")),
        )
    )
    field = page.get_by_label("Bio")
    start = _height(field)
    page.get_by_role("button", name="Fill").click()
    expect(field).to_have_value("a\n" * 10)
    field.fill("x")
    assert _height(field) == start


# Grouped inputs


_GROUPED = {
    "prefix": lambda size: TextInput()
    .name("g")
    .label("G")
    .size(size)
    .prefix("https://"),
    "suffix": lambda size: TextInput().name("g").label("G").size(size).suffix(".com"),
    "both": lambda size: TextInput()
    .name("g")
    .label("G")
    .size(size)
    .prefix("$")
    .suffix("USD"),
    "button": lambda size: TextInput()
    .name("g")
    .label("G")
    .size(size)
    .action(Button().content(Text("Copy"))),
    "password": lambda size: PasswordInput()
    .name("g")
    .label("G")
    .size(size)
    .revealable(),
    "number": lambda size: NumberInput().name("g").label("G").size(size).suffix("kg"),
}


def _group(page: Page) -> Locator:
    return page.locator("div:has(> input[name=g])")


@pytest.mark.parametrize("kind", list(_GROUPED))
@pytest.mark.parametrize("size", ["sm", "md", "lg"])
@pytest.mark.parametrize("pointer", ["fine", "coarse"])
def test_a_group_matches_a_plain_field_and_holds_its_parts(
    show: Show, kind: str, size: ControlSize, pointer: str
) -> None:
    page = show(
        TextInput().name("plain").label("Plain").size(size),
        _GROUPED[kind](size),
    )
    if pointer == "coarse":
        session = page.context.new_cdp_session(page)
        session.send(
            "Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 1}
        )
        assert page.evaluate("matchMedia('(pointer: coarse)').matches")
    group = _box(_group(page))
    assert group["height"] == _box(page.get_by_label("Plain"))["height"]
    # The input fills the inside of the border.
    control = _box(page.locator("input[name=g]"))
    assert control["height"] == group["height"] - 2
    # Nothing attached pokes out past the group's border.
    for part in page.locator("div:has(> input[name=g]) button").all():
        box = _box(part)
        assert box["y"] >= group["y"], kind
        assert box["y"] + box["height"] <= group["y"] + group["height"], kind


@pytest.mark.parametrize("size", ["sm", "md", "lg"])
def test_native_select_and_select_heights_match_a_text_input(
    show: Show, size: ControlSize
) -> None:
    page = show(
        TextInput().name("plain").label("Plain").size(size),
        NativeSelect().name("n").label("Native").size(size).options([("a", "A")]),
        Select()
        .name("s")
        .label("Custom")
        .size(size)
        .content(SelectOption().value("a").label("A")),
    )
    plain = _box(page.get_by_label("Plain"))["height"]
    assert _box(page.get_by_label("Native"))["height"] == plain
    assert _box(page.get_by_role("combobox", name="Custom"))["height"] == plain


def _pixel(page: Page, x: float, y: float) -> str:
    return row_of_pixels(page, x, round(y), 1)[0]


@pytest.mark.parametrize(
    "field",
    [
        PasswordInput().name("g").label("G").revealable(),
        TextInput().name("g").label("G").prefix("https://"),
        TextInput().name("g").label("G").leading_icon(Text("@")),
    ],
    ids=["input first", "input last", "icon first"],
)
def test_a_fill_in_rtl_leaves_the_border_and_corners_alone(
    show: Show, field: TextInput
) -> None:
    page = still(show(field, dir="rtl"))
    group = _box(_group(page))
    top, bottom = group["y"], group["y"] + group["height"] - 1
    corners = [(group["x"] + 1, top), (group["x"] + group["width"] - 2, top)]
    before = [_pixel(page, x, y) for x, y in corners]
    control = page.locator("input[name=g]")
    control.evaluate("el => { el.style.background = 'rgb(232, 240, 254)' }")
    middle = _box(control)["x"] + _box(control)["width"] / 2
    border = token(page, "border-input")
    assert _pixel(page, middle, top) == border
    assert _pixel(page, middle, bottom) == border
    assert [_pixel(page, x, y) for x, y in corners] == before


@pytest.mark.parametrize("state", ["disabled", "readonly"])
def test_a_disabled_or_readonly_group_is_sunken_behind_the_input(
    show: Show, state: str
) -> None:
    field = TextInput().name("g").label("G").prefix("https://")
    field = field.disabled() if state == "disabled" else field.readonly()
    page = still(show(field))
    control = _box(page.locator("input[name=g]"))
    # Away from the text, near the end of the input.
    x = control["x"] + control["width"] - 6
    assert _pixel(page, x, control["y"] + control["height"] / 2) == token(
        page, "surface-sunken"
    )


def test_a_focused_group_draws_its_halo_all_round(show: Show) -> None:
    page = still(show(TextInput().name("g").label("G").prefix("https://")))
    page.locator("input[name=g]").click()
    group = _box(_group(page))
    halo = token(page, "accent-subtle")
    middle = group["x"] + group["width"] / 2
    assert _pixel(page, middle, group["y"] - 2) == halo
    assert _pixel(page, middle, group["y"] + group["height"] + 1) == halo


# Label


def test_a_field_label_shows_the_pointer_and_focuses_its_input(show: Show) -> None:
    page = show(TextInput().name("email").label("Email"))
    label = page.locator("label", has_text="Email")
    expect(label).to_have_css("cursor", "pointer")
    label.click()
    expect(page.get_by_label("Email")).to_be_focused()


def test_a_disabled_field_label_has_no_pointer(show: Show) -> None:
    page = show(TextInput().name("email").label("Email").disabled())
    expect(page.locator("label", has_text="Email")).not_to_have_css("cursor", "pointer")


def test_a_bare_label_has_no_pointer(show: Show) -> None:
    page = show(Label("Loose"))
    expect(page.locator("label", has_text="Loose")).not_to_have_css("cursor", "pointer")
