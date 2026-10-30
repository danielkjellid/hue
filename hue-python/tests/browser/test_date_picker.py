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
