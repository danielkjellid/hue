import re
from datetime import date, datetime

import pytest

from hue.formats import Formats
from hue.js import ajax
from hue.renderer import render_tree
from hue.ui import Calendar, Event
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

_OCTOBER = date(2026, 10, 1)


def _calendar(*events: Event) -> Calendar:
    return Calendar().month(_OCTOBER).events(events)


async def _html(component, context_args) -> str:
    return await render_tree(component, context_args=context_args)


class TestGrid:
    @pytest.mark.asyncio
    async def test_the_caption_names_the_month(self, context_args):
        html = await _html(_calendar(), context_args)
        assert select(html, "table caption")[0].get_text().strip() == "October 2026"

    @pytest.mark.asyncio
    async def test_the_header_starts_on_monday_unless_told_otherwise(
        self, context_args
    ):
        monday = await _html(_calendar(), context_args)
        sunday = await _html(_calendar().week_start("sunday"), context_args)
        assert [th.get_text() for th in select(monday, "th")][:2] == ["Mon", "Tue"]
        assert [th.get_text() for th in select(sunday, "th")][:2] == ["Sun", "Mon"]
        # The first cell follows the header.
        assert_attr(monday, "tbody time", "datetime", "2026-09-28")
        assert_attr(sunday, "tbody time", "datetime", "2026-09-27")

    @pytest.mark.asyncio
    async def test_a_column_header_carries_its_full_name(self, context_args):
        html = await _html(_calendar(), context_args)
        assert_attr(html, "th", "scope", "col")
        assert_attr(html, "th", "abbr", "Monday")

    @pytest.mark.asyncio
    async def test_the_names_come_from_formats(self, context_args):
        formats = Formats(
            month_names=tuple(f"m{n}" for n in range(1, 13)),
            day_names=("mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lø", "sø"),
            day_abbreviations=("ma", "ti", "on", "to", "fr", "lø", "sø"),
        )
        html = await _html(_calendar(), {**context_args, "formats": formats})
        assert select(html, "caption")[0].get_text().strip() == "m10 2026"
        assert_attr(html, "th", "abbr", "mandag")
        assert select(html, "th")[0].get_text() == "ma"

    @pytest.mark.asyncio
    async def test_a_day_outside_the_month_says_which_month_it_is_in(
        self, context_args
    ):
        html = await _html(_calendar(), context_args)
        outside = select(html, 'td:has(time[datetime="2026-09-30"])')[0]
        inside = select(html, 'td:has(time[datetime="2026-10-01"])')[0]
        assert "text-fg-subtle" in outside["class"]
        assert outside.select_one("time .sr-only").get_text() == " September"
        assert "text-fg-subtle" not in inside["class"]
        assert inside.select_one("time .sr-only") is None

    @pytest.mark.asyncio
    async def test_today_is_marked_only_when_told(self, context_args):
        told = await _html(_calendar().today(date(2026, 10, 14)), context_args)
        assert_attr(told, '[aria-current="date"] time', "datetime", "2026-10-14")
        assert_selector(told, '[aria-current="date"]', count=1)
        untold = await _html(_calendar(), context_args)
        assert_no_selector(untold, '[aria-current="date"]')

    @pytest.mark.asyncio
    async def test_a_month_is_required(self, context_args):
        with pytest.raises(ValueError, match="month"):
            await _html(Calendar(), context_args)


class TestEvents:
    @pytest.mark.asyncio
    async def test_an_event_with_an_href_is_a_link_and_one_without_is_text(
        self, context_args
    ):
        html = await _html(
            _calendar(
                Event("Linked", date(2026, 10, 14), href="/events/1/"),
                Event("Plain", date(2026, 10, 14)),
            ),
            context_args,
        )
        assert select(html, 'li a[href="/events/1/"]')[0].get_text() == "Linked"
        assert select(html, "li span.truncate")[1].get_text() == "Plain"
        assert_selector(html, "li a", count=1)

    @pytest.mark.asyncio
    async def test_a_timed_event_leads_with_its_time_and_an_all_day_one_does_not(
        self, context_args
    ):
        html = await _html(
            _calendar(
                Event("Standup", datetime(2026, 10, 14, 9, 30)),
                Event("Release", date(2026, 10, 14)),
            ),
            context_args,
        )
        items = select(html, "li")
        assert items[0].get_text().strip() == "Release"
        assert items[0].select_one("time") is None
        assert_attr(html, "li time", "datetime", "2026-10-14T09:30")
        assert select(html, "li time")[0].get_text() == "09:30"

    @pytest.mark.asyncio
    async def test_a_bar_across_days_is_squared_off_where_it_continues(
        self, context_args
    ):
        html = await _html(
            _calendar(
                Event("Offsite", date(2026, 10, 19), date(2026, 10, 21)),
                Event("Release", date(2026, 10, 29)),
            ),
            context_args,
        )
        chips = [li.select_one("span") for li in select(html, "li")]
        first, middle, last, release = (chip["class"] for chip in chips)
        assert "rounded-s-none" not in first and "rounded-e-none" in first
        assert "rounded-s-none" in middle and "rounded-e-none" in middle
        assert "rounded-s-none" in last and "rounded-e-none" not in last
        assert "rounded-s-none" not in release and "rounded-e-none" not in release
        assert_selector(html, "li .sr-only", count=3)
        assert chips[3].select_one(".sr-only") is None

    @pytest.mark.asyncio
    async def test_a_tone_colours_the_chip_and_neutral_is_the_default(
        self, context_args
    ):
        html = await _html(
            _calendar(
                Event("Quiet", date(2026, 10, 14)),
                Event("Loud", date(2026, 10, 14), variant="danger"),
            ),
            context_args,
        )
        quiet, loud = (li.select_one("span")["class"] for li in select(html, "li"))
        assert "bg-surface-sunken" in quiet
        assert "bg-danger-subtle" in loud and "text-danger-text" in loud

    @pytest.mark.asyncio
    async def test_a_day_with_nothing_on_it_has_no_list(self, context_args):
        html = await _html(_calendar(Event("One", date(2026, 10, 14))), context_args)
        assert_selector(html, "td ul", count=1)
        assert select(html, 'td:has(time[datetime="2026-10-15"]) ul') == []


class TestNavigation:
    @pytest.mark.asyncio
    async def test_without_an_href_there_are_no_month_links(self, context_args):
        html = await _html(_calendar().today(date(2026, 10, 14)), context_args)
        assert_no_selector(html, "nav")

    @pytest.mark.asyncio
    async def test_with_one_the_months_either_side_are_plain_links(self, context_args):
        html = await _html(
            _calendar().href(lambda month: f"/?month={month:%Y-%m}"), context_args
        )
        assert_attr(
            html, 'nav a[aria-label="Previous month"]', "href", "/?month=2026-09"
        )
        assert_attr(html, 'nav a[aria-label="Next month"]', "href", "/?month=2026-11")
        assert_no_selector(html, "nav a[id]")
        assert_no_selector(html, "[x-target\\.push]")
        # Today's link needs a today to point at.
        assert_no_selector(html, 'nav a[id$="today"]')
        assert "Today" not in select(html, "nav")[0].get_text()

    @pytest.mark.asyncio
    async def test_with_an_id_the_links_swap_the_calendar_and_carry_ids(
        self, context_args
    ):
        html = await _html(
            _calendar()
            .id("bookings")
            .today(date(2026, 10, 14))
            .href(lambda month: f"/?month={month:%Y-%m}"),
            context_args,
        )
        assert_attr(html, "#bookings-previous", "x-target.push", "bookings")
        assert_attr(html, "#bookings-next", "x-target.push", "bookings")
        assert_attr(html, "#bookings-today", "href", "/?month=2026-10")
        assert select(html, "#bookings-today")[0].get_text() == "Today"

    @pytest.mark.asyncio
    async def test_the_steps_stop_at_the_ends_of_time(self, context_args):
        html = await _html(
            Calendar().month(date(2, 1, 1)).href(lambda month: "/"), context_args
        )
        assert_no_selector(html, 'nav a[aria-label="Previous month"]')
        assert_selector(html, 'nav a[aria-label="Next month"]')


class TestDayAction:
    @pytest.mark.asyncio
    async def test_a_day_action_makes_every_number_a_button_with_a_slot(
        self, context_args
    ):
        html = await _html(
            _calendar()
            .id("bookings")
            ._day_action(
                "New booking",
                lambda day: ajax(f"/bookings/day/?day={day}", target="bookings-day"),
            ),
            context_args,
        )
        button = select(
            html, 'td button[aria-label="New booking, Wednesday 14 October 2026"]'
        )[0]
        assert button["type"] == "button"
        assert button.select_one("time").get_text() == "14"
        assert button["x-on:click"] == (
            '$ajax("/bookings/day/?day=2026-10-14", '
            '{"method": "get", "target": "bookings-day", "sync": true})'
        )
        assert_selector(html, "#bookings > #bookings-day", count=1)
        assert_no_selector(html, "td span time")

    @pytest.mark.asyncio
    async def test_without_one_the_numbers_are_text_and_there_is_no_slot(
        self, context_args
    ):
        html = await _html(_calendar().id("bookings"), context_args)
        assert_no_selector(html, "td button")
        assert_no_selector(html, "#bookings-day")
        assert_selector(html, "td span time")

    @pytest.mark.asyncio
    async def test_a_day_action_needs_an_id(self, context_args):
        with pytest.raises(ValueError, match="id"):
            await _html(
                _calendar()._day_action("Open", lambda day: ajax("/", target="x")),
                context_args,
            )


@pytest.mark.asyncio
async def test_two_calendars_on_one_page_share_no_ids(context_args):
    def one(key: str) -> Calendar:
        return (
            _calendar(Event("Shared", date(2026, 10, 14), href="#"))
            .id(key)
            .today(date(2026, 10, 14))
            .href(lambda month: f"/?{key}={month:%Y-%m}")
            ._day_action("Open", lambda day: ajax(f"/{key}/", target=f"{key}-day"))
        )

    html = await _html(one("first"), context_args) + await _html(
        one("second"), context_args
    )
    ids = re.findall(r' id="([^"]+)"', html)
    assert len(ids) == len(set(ids)) == 10
