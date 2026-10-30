from datetime import date

import pytest
from htmy import html
from playwright.sync_api import Page, expect

from hue.ui import DatePicker
from tests.browser.conftest import Show

_COUNT_SUBMITS = "event.preventDefault(); window.submits = (window.submits || 0) + 1"


def _form(picker: DatePicker) -> html.form:
    return html.form(picker, onsubmit=_COUNT_SUBMITS)


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


def _sent(page: Page) -> list[str]:
    return page.evaluate(
        "[...document.querySelectorAll('input[type=hidden][name=day]')]"
        ".map(input => input.value)"
    )


def test_enter_picks_the_focused_day_without_submitting(show: Show) -> None:
    page = show(_form(_picker(date(2026, 10, 14))))
    page.locator('td[data-date="2026-10-14"]').focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Enter")
    expect(page.locator('td[data-date="2026-10-15"]')).to_have_attribute(
        "aria-selected", "true"
    )
    assert _sent(page) == ["2026-10-15"]
    assert page.evaluate("window.submits") is None


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
    ("picker", "key", "blank"),
    [
        (_picker(date(2026, 10, 14)), "Enter", "first"),
        (_picker(date(2026, 10, 14)).mode("multiple"), " ", "last"),
        (
            _picker(date(2026, 10, 14), date(2026, 10, 16)).mode("range"),
            "Enter",
            "last",
        ),
    ],
    ids=["single", "multiple", "range"],
)
def test_enter_and_space_on_a_blank_cell_pick_nothing(
    show: Show, picker: DatePicker, key: str, blank: str
) -> None:
    page = show(_form(picker))
    page.locator('td[data-date="2026-10-14"]').focus()
    # The focused day moves on to the 15th, which nothing has picked.
    page.keyboard.press("ArrowRight")
    expect(page.locator('td[data-date="2026-10-15"]')).to_be_focused()
    before = _sent(page)
    # October 2026 starts on a Thursday, so a Monday week opens with blanks.
    blanks = page.locator("td:not([data-date])")
    (blanks.first if blank == "first" else blanks.last).click()
    page.keyboard.press(key)
    # The arrows still work from there, and show the key was handled.
    page.keyboard.press("ArrowLeft")
    expect(page.locator('td[data-date="2026-10-14"]')).to_be_focused()
    assert _sent(page) == before
    assert page.evaluate("window.submits") is None


def test_enter_on_a_refused_day_picks_nothing(show: Show) -> None:
    picker = _picker(date(2026, 10, 14)).max(date(2026, 10, 15)).unavailable("saturday")
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
    assert _sent(page) == ["2026-10-14"]


def test_enter_straight_after_a_move_onto_a_refused_day(show: Show) -> None:
    page = show(_picker(date(2026, 10, 14)).unavailable("thursday"))
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
    assert _sent(page) == ["2026-10-14"]


def test_keys_in_one_of_two_pickers_leave_the_other_alone(show: Show) -> None:
    other = DatePicker().name("other").label("Other").value(date(2026, 10, 14))
    page = show(_picker(date(2026, 10, 14)), other)
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
