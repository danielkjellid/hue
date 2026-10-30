import pytest
from playwright.sync_api import Locator, Page, expect

from hue.ui import Select, SelectOption, TextInput
from hue.ui.atoms.icon import HueIcon
from tests.browser._fields import contrast, css, still, token
from tests.browser.conftest import Show


def _fruit() -> Select:
    return (
        Select()
        .name("fruit")
        .label("Fruit")
        .content(
            SelectOption().value("apple").label("Apple").icon(HueIcon("eye")),
            SelectOption().value("banana").label("Banana"),
            SelectOption().value("bravo").label("Bravo"),
        )
    )


def test_option_icon_is_small_and_leaves_the_label_its_room(show: Show) -> None:
    page = show(_fruit(), width=320)
    page.get_by_role("combobox", name="Fruit").click()
    option = page.get_by_role("option", name="Apple")
    icon = option.locator("svg").bounding_box()
    assert icon is not None
    assert (icon["width"], icon["height"]) == (16, 16)
    label = option.get_by_text("Apple")
    assert label.evaluate("el => el.scrollWidth <= el.clientWidth")


def test_focus_leaving_closes_the_list(show: Show) -> None:
    page = show(_fruit(), TextInput().name("other").label("Other"))
    page.get_by_role("combobox", name="Fruit").click()
    expect(page.get_by_role("listbox")).to_be_visible()
    page.get_by_label("Other").focus()
    expect(page.get_by_role("listbox")).to_be_hidden()


def test_fast_typing_from_closed_keeps_letters_in_order(show: Show) -> None:
    page = show(_fruit())
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.type("br")
    page.keyboard.press("Enter")
    expect(page.locator("input[name=fruit]")).to_have_value("bravo")


def test_open_invalid_select_stays_red_with_a_solid_ring(show: Show) -> None:
    page = still(show(_fruit().error("Pick one")))
    trigger = page.get_by_role("combobox", name="Fruit")
    trigger.click()
    expect(trigger).to_have_attribute("aria-expanded", "true")
    expect(trigger).to_have_css("border-top-color", token(page, "danger"))
    shadow = css(trigger, "boxShadow")
    assert f"{token(page, 'danger')} 0px 0px 0px 2px" in shadow
    assert token(page, "accent-subtle") not in shadow


def test_open_valid_select_keeps_its_accent_halo(show: Show) -> None:
    page = still(show(_fruit()))
    trigger = page.get_by_role("combobox", name="Fruit")
    trigger.click()
    expect(trigger).to_have_css("border-top-color", token(page, "accent"))
    ring = f"{token(page, 'accent-subtle')} 0px 0px 0px 3px"
    assert ring in css(trigger, "boxShadow")


def test_escape_closes_without_choosing(show: Show) -> None:
    page = show(_fruit())
    trigger = page.get_by_role("combobox", name="Fruit")
    trigger.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("listbox")).to_be_visible()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Escape")
    expect(page.get_by_role("listbox")).to_be_hidden()
    expect(page.locator("input[name=fruit]")).to_have_value("")
    expect(trigger).to_be_focused()


def test_enter_chooses_the_active_option_and_closes(show: Show) -> None:
    page = show(_fruit())
    page.get_by_role("combobox", name="Fruit").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("listbox")).to_be_visible()
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    expect(page.get_by_role("listbox")).to_be_hidden()
    expect(page.locator("input[name=fruit]")).to_have_value("banana")


def test_reopening_while_the_list_fades_out_raises_nothing(show: Show) -> None:
    page = show(_fruit())
    trigger = page.get_by_role("combobox", name="Fruit")
    trigger.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("listbox")).to_be_visible()
    # Reopened once the fade out has begun and before Alpine's next tick,
    # which cuts the fade short. The fixture fails the test on the console
    # error an unhandled rejection from that would log.
    trigger.evaluate(
        """async el => {
            const press = (key) => el.dispatchEvent(
                new KeyboardEvent("keydown", { key, bubbles: true })
            );
            press("Escape");
            await Promise.resolve();
            press("Enter");
        }"""
    )
    expect(page.get_by_role("listbox")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("listbox")).to_be_hidden()


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


def test_only_a_cancelled_transition_rejection_is_handled(show: Show) -> None:
    page = show(_fruit())
    assert page.evaluate(_RECORD_REJECTION, "cancelled") is True
    assert page.evaluate(_RECORD_REJECTION, "real") is False


def _tiers() -> Select:
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


def _active(page: Page) -> Locator:
    return page.locator("[role=option][data-active]")


def test_home_end_paging_skip_disabled_options(show: Show) -> None:
    page = show(_tiers())
    page.get_by_role("combobox", name="Plan").focus()
    page.keyboard.press("End")
    expect(_active(page)).to_have_attribute("data-value", "max")
    page.keyboard.press("Home")
    expect(_active(page)).to_have_attribute("data-value", "free")
    page.keyboard.press("ArrowDown")
    expect(_active(page)).to_have_attribute("data-value", "pro")
    page.keyboard.press("PageDown")
    expect(_active(page)).to_have_attribute("data-value", "max")
    page.keyboard.press("PageUp")
    expect(_active(page)).to_have_attribute("data-value", "free")
    page.keyboard.press("Enter")
    expect(page.locator("input[name=plan]")).to_have_value("free")


def test_typeahead_moves_to_the_match_and_tab_chooses_it(show: Show) -> None:
    page = show(_tiers())
    page.get_by_role("combobox", name="Plan").focus()
    page.keyboard.press("Enter")
    page.keyboard.type("ma")
    expect(_active(page)).to_have_attribute("data-value", "max")
    page.keyboard.press("Tab")
    expect(page.locator("input[name=plan]")).to_have_value("max")


def _plans() -> Select:
    return (
        Select()
        .name("plan")
        .label("Plan")
        .value("free")
        .content(
            SelectOption().value("free").label("Free").meta("$0"),
            SelectOption()
            .value("pro")
            .label("Pro")
            .description("For growing teams")
            .meta("$12"),
        )
    )


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_option_text_is_legible_active_or_selected(show: Show, theme: str) -> None:
    page = still(show(_plans(), theme=theme))
    page.get_by_role("combobox", name="Plan").focus()
    page.keyboard.press("Enter")
    # Free is selected; Pro becomes the active one.
    page.keyboard.press("ArrowDown")
    expect(page.get_by_role("option", name="Pro")).to_have_attribute(
        "data-active", "true"
    )
    listbox = page.get_by_role("listbox")
    for text in ["$0", "$12", "For growing teams"]:
        assert contrast(listbox.get_by_text(text)) >= 4.5, text
