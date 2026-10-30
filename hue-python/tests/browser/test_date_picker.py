from datetime import date

from playwright.sync_api import expect

from hue.ui import DatePicker
from tests.browser.conftest import Show


def _picker(day: date) -> DatePicker:
    return DatePicker().name("day").label("Day").value(day)


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
