from datetime import date

import pytest
from playwright.sync_api import Page, expect

from hue.ui import DatePicker
from tests.browser.conftest import Show


def _picker(*days: date) -> DatePicker:
    return DatePicker().name("day").label("Day").value(*days)


def test_keys_back_to_back_move_from_the_right_cell(show: Show) -> None:
    page = show(_picker(date(2026, 10, 14)))
    cell = page.locator('td[data-date="2026-10-14"]')
    cell.focus()
    # In one task, so the second key arrives before focus has moved.
    cell.evaluate(
        """el => {
            for (const _ of [1, 2]) {
                el.dispatchEvent(
                    new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true })
                );
            }
        }"""
    )
    expect(page.locator('td[data-date="2026-10-16"]')).to_be_focused()


def test_paging_onto_a_blank_cell_keeps_focus_in_the_grid(show: Show) -> None:
    # The 31st's cell is blank in April, which ends on the 30th.
    page = show(_picker(date(2026, 3, 31)))
    page.locator('td[data-date="2026-03-31"]').focus()
    page.evaluate(
        """() => {
            window.dropped = false;
            document.addEventListener("focusout", (event) => {
                if (!event.relatedTarget) window.dropped = true;
            });
        }"""
    )
    page.keyboard.press("PageDown")
    expect(page.locator('td[data-date="2026-04-30"]')).to_be_focused()
    assert not page.evaluate("window.dropped")


def test_tab_lands_on_the_focused_day_only(show: Show) -> None:
    page = show(_picker(date(2026, 4, 30)))
    page.get_by_role("button", name="Next month").focus()
    page.keyboard.press("Tab")
    expect(page.locator('td[data-date="2026-04-30"]')).to_be_focused()


def test_keys_still_work_after_clicking_a_blank_cell(show: Show) -> None:
    page = show(_picker(date(2026, 4, 30)))
    # Past the 30th, on the last row.
    page.locator("td:not([data-date])").last.click()
    page.keyboard.press("ArrowLeft")
    expect(page.locator('td[data-date="2026-04-29"]')).to_be_focused()


def _sent(page: Page) -> list[str]:
    return page.evaluate(
        "[...document.querySelectorAll('input[type=hidden][name=day]')]"
        ".map(input => input.value)"
    )


def test_enter_picks_the_focused_day(show: Show) -> None:
    page = show(_picker(date(2026, 10, 14)))
    page.locator('td[data-date="2026-10-14"]').focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Enter")
    expect(page.locator('td[data-date="2026-10-15"]')).to_have_attribute(
        "aria-selected", "true"
    )
    assert _sent(page) == ["2026-10-15"]


def test_space_adds_the_focused_day_to_several(show: Show) -> None:
    page = show(_picker(date(2026, 10, 6)).mode("multiple"))
    page.locator('td[data-date="2026-10-06"]').focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press(" ")
    expect(page.locator('td[data-date="2026-10-07"]')).to_have_attribute(
        "aria-selected", "true"
    )
    assert _sent(page) == ["2026-10-06", "2026-10-07"]


def test_enter_starts_and_ends_a_range(show: Show) -> None:
    # A committed range, so the next Enter starts a new one.
    page = show(_picker(date(2026, 10, 12), date(2026, 10, 16)).mode("range"))
    page.locator('td[data-date="2026-10-12"]').focus()
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Enter")
    expect(page.locator('td[data-date="2026-10-14"]')).to_have_attribute(
        "aria-selected", "true"
    )
    assert _sent(page) == ["2026-10-12", "2026-10-14"]


@pytest.mark.parametrize(
    "picker",
    [
        _picker(date(2026, 10, 14)),
        _picker(date(2026, 10, 14)).mode("multiple"),
        _picker(date(2026, 10, 14), date(2026, 10, 16)).mode("range"),
    ],
    ids=["single", "multiple", "range"],
)
@pytest.mark.parametrize("key", ["Enter", " "], ids=["enter", "space"])
def test_enter_and_space_on_a_blank_cell_pick_nothing(
    show: Show, picker: DatePicker, key: str
) -> None:
    page = show(picker)
    page.locator('td[data-date="2026-10-14"]').focus()
    # The focused day moves on to the 15th, which nothing has picked.
    page.keyboard.press("ArrowRight")
    expect(page.locator('td[data-date="2026-10-15"]')).to_be_focused()
    before = _sent(page)
    page.locator("td:not([data-date])").last.click()
    page.keyboard.press(key)
    # The arrows still work from there, and show the key was handled.
    page.keyboard.press("ArrowLeft")
    expect(page.locator('td[data-date="2026-10-14"]')).to_be_focused()
    assert _sent(page) == before


def test_enter_before_focus_follows_paging_picks_the_new_day(show: Show) -> None:
    # The 31st's cell is blank in April, so for a tick focus is on a blank.
    page = show(_picker(date(2026, 3, 31)))
    cell = page.locator('td[data-date="2026-03-31"]')
    cell.focus()
    cell.evaluate(
        """el => new Promise(done => {
            const press = (key) => el.dispatchEvent(
                new KeyboardEvent("keydown", { key, bubbles: true })
            );
            press("PageDown");
            // Ahead of the tick that moves focus, and after the redraw.
            setTimeout(() => { press("Enter"); done(); });
        })"""
    )
    expect(page.locator('td[data-date="2026-04-30"]')).to_be_focused()
    assert _sent(page) == ["2026-04-30"]
