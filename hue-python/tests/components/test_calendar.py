import re
from collections import Counter
from datetime import date, datetime

import pytest

from hue.formats import Formats
from hue.renderer import render_tree
from hue.ui import Button, Calendar, Event
from tests._a11y import assert_attr, assert_no_selector, select

_WEDNESDAY = date(2026, 10, 14)
# The en dash a range is written with.
_DASH = "\u2013"

_REVIEW = Event(
    "Design review",
    datetime(2026, 10, 14, 13),
    datetime(2026, 10, 14, 14, 30),
    id="1",
    location="Room 3B",
    notes="Bring the matrix.",
)
_AUDIT = Event("Contrast audit", datetime(2026, 10, 15, 10), datetime(2026, 10, 15, 12))
_PAIRING = Event("Pairing", datetime(2026, 10, 15, 11), datetime(2026, 10, 15, 12, 30))
_FREEZE = Event("Release freeze", date(2026, 10, 16), date(2026, 10, 17), color=4)
_STANDUP = Event(
    "Standup",
    datetime(2026, 10, 12, 9),
    datetime(2026, 10, 12, 9, 15),
    recurring=True,
    href="/standup/",
)


def _href(day: date, view: str) -> str:
    return f"/cal/{view}/{day}/"


def _calendar(*events: Event) -> Calendar:
    return Calendar().date(_WEDNESDAY).events(events).href(_href)


async def _html(components, context_args) -> str:
    many = components if isinstance(components, tuple) else (components,)
    return await render_tree(*many, context_args=context_args)


def _event(html: str, title: str):
    return next(
        button
        for button in select(html, "button[data-starts]")
        if button["aria-label"].startswith(f"{title},")
    )


class TestFrame:
    @pytest.mark.asyncio
    async def test_the_id_names_the_frame_and_the_links_swap_the_view_inside(
        self, context_args
    ):
        # The status stays outside what is swapped, so its text changes in
        # place and is announced; the view region refreshes from any
        # response that carries it, as a table's rows do.
        html = await _html(_calendar().id("cal"), context_args)
        assert_attr(html, "#cal > p#cal-status", "role", "status")
        assert_attr(html, "#cal-status", "x-sync")
        status = select(html, "#cal-status")[0]
        assert status.get_text() == f"12 {_DASH} 18 October 2026"
        assert_attr(html, "#cal > #cal-view", "x-sync")
        assert_attr(html, "#cal-next", "x-target.push", "cal-view")
        assert_attr(html, "nav[aria-label=View] a", "x-target.push", "cal-view")

    @pytest.mark.asyncio
    async def test_without_an_id_the_links_are_plain_navigation(self, context_args):
        html = await _html(_calendar(), context_args)
        assert_no_selector(html, "[role=status]")
        assert_no_selector(html, "[x-sync]")
        assert_no_selector(html, "[x-target\\.push]")

    @pytest.mark.asyncio
    async def test_a_date_is_required(self, context_args):
        with pytest.raises(ValueError, match="date"):
            await _html(Calendar(), context_args)

    @pytest.mark.parametrize(
        ("view", "title", "before", "after"),
        [
            ("day", "Wednesday 14 October 2026", "2026-10-13", "2026-10-15"),
            ("week", f"12 {_DASH} 18 October 2026", "2026-10-07", "2026-10-21"),
            ("month", "October 2026", "2026-09-14", "2026-11-14"),
            ("year", "2026", "2025-10-14", "2027-10-14"),
            (
                "agenda",
                f"14 October {_DASH} 12 November 2026",
                "2026-09-14",
                "2026-11-13",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_each_view_names_its_range_and_steps_by_it(
        self, context_args, view, title, before, after
    ):
        html = await _html(
            _calendar().view(view).today(date(2026, 10, 20)), context_args
        )
        assert select(html, "h2")[0].get_text() == title
        assert_attr(html, "a[aria-label=Previous]", "href", f"/cal/{view}/{before}/")
        assert_attr(html, "a[aria-label=Next]", "href", f"/cal/{view}/{after}/")
        today = next(a for a in select(html, "nav a") if a.get_text() == "Today")
        assert today["href"] == f"/cal/{view}/2026-10-20/"
        current = select(html, "nav[aria-label=View] [aria-current=page]")[0]
        assert current.get_text() == view.title()

    @pytest.mark.asyncio
    async def test_a_week_title_says_as_much_of_the_start_as_differs(
        self, context_args
    ):
        across_months = await _html(
            Calendar().date(date(2026, 9, 30)).href(_href), context_args
        )
        across_years = await _html(
            Calendar().date(date(2026, 12, 30)).href(_href), context_args
        )
        assert select(across_months, "h2")[0].get_text() == (
            f"28 September {_DASH} 4 October 2026"
        )
        assert select(across_years, "h2")[0].get_text() == (
            f"28 December 2026 {_DASH} 3 January 2027"
        )

    @pytest.mark.asyncio
    async def test_a_week_title_names_the_days_shown(self, context_args):
        seven = await _html(_calendar().id("cal"), context_args)
        five = await _html(_calendar().weekdays().id("cal"), context_args)
        for html, last in ((seven, 18), (five, 16)):
            title = f"12 {_DASH} {last} October 2026"
            assert select(html, "h2")[0].get_text() == title
            assert select(html, "#cal-status")[0].get_text() == title

    @pytest.mark.asyncio
    async def test_without_a_destination_there_is_nothing_to_navigate_with(
        self, context_args
    ):
        html = await _html(Calendar().date(_WEDNESDAY).today(_WEDNESDAY), context_args)
        assert_no_selector(html, "nav")
        assert_no_selector(html, "a")
        assert select(html, "h2")[0].get_text() == f"12 {_DASH} 18 October 2026"

    @pytest.mark.parametrize("view", ["day", "week", "month", "year", "agenda"])
    @pytest.mark.asyncio
    async def test_the_ends_of_the_calendar_render_and_lead_no_further(
        self, context_args, view
    ):
        # A grid reaches into the weeks around its range, so the last pages
        # a date can draw stop a year short of either end.
        for day, step, edge in (
            (date.min, "Previous", "0002-01-01"),
            (date.max, "Next", "9998-12-31"),
        ):
            calendar = _calendar().date(day).view(view).week_start("saturday")
            html = await _html(calendar, context_args)
            assert_no_selector(html, f"a[aria-label={step}]")
            switcher = select(html, "nav[aria-label=View] [aria-current=page]")[0]
            assert switcher["href"] == f"/cal/{view}/{edge}/"

    @pytest.mark.asyncio
    async def test_next_never_leads_past_the_last_page(self, context_args):
        html = await _html(
            _calendar().date(date(9998, 12, 20)).view("agenda"), context_args
        )
        assert_no_selector(html, "a[aria-label=Next]")

    @pytest.mark.asyncio
    async def test_today_is_a_link_only_when_told(self, context_args):
        html = await _html(_calendar(), context_args)
        assert not [a for a in select(html, "nav a") if a.get_text() == "Today"]

    @pytest.mark.asyncio
    async def test_two_calendars_on_one_page_share_no_id(self, context_args):
        mine = _calendar(_REVIEW).id("mine")
        ours = _calendar(_REVIEW).view("month").id("ours")
        html = await _html((mine, ours), context_args)
        ids = re.findall(r'\sid="([^"]+)"', html)
        assert ids
        assert [name for name, count in Counter(ids).items() if count > 1] == []


class TestTimeGrid:
    @pytest.mark.asyncio
    async def test_a_day_header_is_a_link_to_its_day_named_in_full(self, context_args):
        html = await _html(_calendar().today(_WEDNESDAY), context_args)
        heads = select(html, "a[aria-label$='October 2026, today']")
        assert len(heads) == 1
        assert heads[0]["href"] == "/cal/day/2026-10-14/"
        assert heads[0]["aria-current"] == "date"
        thursday = select(html, "a[aria-label='Thursday 15 October 2026']")[0]
        assert "aria-current" not in thursday.attrs

    @pytest.mark.asyncio
    async def test_the_columns_carry_their_date_and_the_weekend_is_tinted(
        self, context_args
    ):
        html = await _html(_calendar(), context_args)
        columns = select(html, "[data-date]")
        assert [column["data-date"] for column in columns][:2] == [
            "2026-10-12",
            "2026-10-13",
        ]
        saturday = select(html, "[data-date='2026-10-17']")[0]
        friday = select(html, "[data-date='2026-10-16']")[0]
        assert "bg-canvas-subtle" in saturday["class"]
        assert "bg-canvas-subtle" not in friday["class"]

    @pytest.mark.asyncio
    async def test_weekdays_leaves_saturday_and_sunday_out(self, context_args):
        seven = await _html(_calendar(), context_args)
        five = await _html(_calendar().weekdays(), context_args)
        assert len(select(seven, "[data-date]")) == 7
        assert [c["data-date"][-2:] for c in select(five, "[data-date]")] == [
            "12",
            "13",
            "14",
            "15",
            "16",
        ]

    @pytest.mark.asyncio
    async def test_a_day_view_is_one_column_around_the_date(self, context_args):
        html = await _html(_calendar(_REVIEW).view("day"), context_args)
        assert [c["data-date"] for c in select(html, "[data-date]")] == ["2026-10-14"]
        assert _event(html, "Design review") is not None

    @pytest.mark.asyncio
    async def test_overlapping_events_sit_side_by_side(self, context_args):
        html = await _html(_calendar(_AUDIT, _PAIRING, _REVIEW), context_args)
        audit = _event(html, "Contrast audit").find_parent("li", class_="absolute")
        pairing = _event(html, "Pairing").find_parent("li", class_="absolute")
        review = _event(html, "Design review").find_parent("li", class_="absolute")
        assert "left: calc(0 / 2 * 100% + 2px)" in audit["style"]
        assert "width: calc(100% / 2 - 4px)" in audit["style"]
        assert "left: calc(1 / 2 * 100% + 2px)" in pairing["style"]
        assert "top: 480px; height: 94px" in audit["style"]
        assert "width: calc(100% / 1 - 4px)" in review["style"]

    @pytest.mark.asyncio
    async def test_an_event_is_named_by_its_title_time_and_day(self, context_args):
        html = await _html(_calendar(_REVIEW, _STANDUP), context_args)
        assert _event(html, "Design review")["aria-label"] == (
            "Design review, Wednesday 14 October 2026, 13:00 to 14:30"
        )
        standup = _event(html, "Standup")
        assert standup["aria-label"].endswith("09:00 to 09:15, repeats")
        assert standup.select_one("svg title").get_text() == "repeat"
        assert _event(html, "Design review").select_one("svg") is None

    @pytest.mark.asyncio
    async def test_the_clock_comes_from_formats(self, context_args):
        html = await _html(
            _calendar(_REVIEW),
            {**context_args, "formats": Formats(time="%I:%M %p")},
        )
        assert "01:00 PM to 02:30 PM" in _event(html, "Design review")["aria-label"]
        assert select(html, "[aria-hidden=true].relative span")[8].get_text() == (
            "09:00 AM"
        )

    @pytest.mark.asyncio
    async def test_a_short_event_is_one_line_and_a_longer_one_two(self, context_args):
        html = await _html(_calendar(_STANDUP, _REVIEW), context_args)
        assert "flex" in _event(html, "Standup")["class"]
        assert [s.get_text() for s in _event(html, "Standup").select("span")][-1] == (
            "09:00"
        )
        assert "block" in _event(html, "Design review")["class"]
        assert f"13:00 {_DASH} 14:30" in _event(html, "Design review").get_text()

    @pytest.mark.asyncio
    async def test_an_event_past_midnight_is_drawn_on_each_day_it_covers(
        self, context_args
    ):
        late = Event("Late", datetime(2026, 10, 14, 23), datetime(2026, 10, 15, 1))
        html = await _html(_calendar(late), context_args)
        boxes = select(html, "li.absolute")
        days = [box.find_parent(attrs={"data-date": True})["data-date"] for box in boxes]
        assert days == ["2026-10-14", "2026-10-15"]
        assert "top: 1104px; height: 46px" in boxes[0]["style"]
        assert "top: 0px; height: 46px" in boxes[1]["style"]
        first, second = (box.select_one("button") for box in boxes)
        assert "rounded-b-none" in first["class"]
        assert "rounded-t-none" not in first["class"]
        assert "rounded-t-none" in second["class"]
        assert "rounded-b-none" not in second["class"]
        name = "Late, Wednesday 14 October 2026, 23:00 to 01:00 Thursday 15 October 2026"
        assert first["aria-label"] == second["aria-label"] == name

    @pytest.mark.asyncio
    async def test_an_event_ending_at_midnight_fills_its_day_and_stops(
        self, context_args
    ):
        late = Event("Late", datetime(2026, 10, 14, 22), datetime(2026, 10, 15))
        html = await _html(_calendar(late), context_args)
        boxes = select(html, "li.absolute")
        assert len(boxes) == 1
        assert "top: 1056px; height: 94px" in boxes[0]["style"]
        assert "rounded-b-none" not in boxes[0].select_one("button")["class"]

    @pytest.mark.asyncio
    async def test_a_day_view_shows_what_began_the_day_before(self, context_args):
        late = Event("Late", datetime(2026, 10, 13, 22), datetime(2026, 10, 14, 2))
        html = await _html(_calendar(late).view("day"), context_args)
        boxes = select(html, "li.absolute")
        assert len(boxes) == 1
        assert "top: 0px; height: 94px" in boxes[0]["style"]

    @pytest.mark.asyncio
    async def test_a_moment_before_midnight_stays_inside_the_grid(self, context_args):
        tiny = Event("Tiny", datetime(2026, 10, 14, 23, 55), datetime(2026, 10, 14, 23, 59))
        html = await _html(_calendar(tiny).view("day"), context_args)
        style = select(html, "li.absolute")[0]["style"]
        top, height = (int(n) for n in re.findall(r"(?:top|height): (\d+)px", style))
        assert top + height <= 24 * 48

    @pytest.mark.asyncio
    async def test_a_multi_day_timed_event_fills_the_days_between(self, context_args):
        conference = Event(
            "Conference", datetime(2026, 10, 11, 9), datetime(2026, 10, 14, 17)
        )
        html = await _html(_calendar(conference), context_args)
        boxes = select(html, "li.absolute")
        days = [box.find_parent(attrs={"data-date": True})["data-date"] for box in boxes]
        assert days == ["2026-10-12", "2026-10-13", "2026-10-14"]
        assert "top: 0px; height: 1150px" in boxes[0]["style"]
        assert "top: 0px; height: 814px" in boxes[2]["style"]

    @pytest.mark.asyncio
    async def test_an_all_day_event_spans_its_columns(self, context_args):
        html = await _html(_calendar(_FREEZE), context_args)
        bar = _event(html, "Release freeze").find_parent("li")
        assert bar["style"] == "grid-column: 5 / 7"
        assert_attr(html, "button[data-all-day]", "data-starts", "2026-10-16")
        assert_attr(html, "button[data-all-day]", "data-ends", "2026-10-17")
        assert "(continues)" not in bar.get_text()

    @pytest.mark.asyncio
    async def test_a_bar_cut_by_the_week_says_it_continues(self, context_args):
        long = Event("Offsite", date(2026, 10, 10), date(2026, 10, 13))
        html = await _html(_calendar(long), context_args)
        button = _event(html, "Offsite")
        assert "rounded-s-none" in button["class"]
        assert "rounded-e-none" not in button["class"]
        assert "(continues)" in button.get_text()

    @pytest.mark.asyncio
    async def test_the_now_line_sits_in_todays_column_only(self, context_args):
        shown = await _html(_calendar().today(_WEDNESDAY), context_args)
        line = select(shown, "[data-date='2026-10-14'] [x-data*=minute]")
        assert len(line) == 1
        assert line[0]["aria-hidden"] == "true"
        assert select(shown, "[x-data*=minute]") == line
        elsewhere = await _html(_calendar().today(date(2026, 11, 2)), context_args)
        assert_no_selector(elsewhere, "[x-data*=minute]")

    @pytest.mark.asyncio
    async def test_the_grid_opens_at_half_past_seven(self, context_args):
        html = await _html(_calendar(), context_args)
        assert_attr(html, ".overflow-y-auto", "x-init", "$el.scrollTop = 360")


class TestMonth:
    @pytest.mark.asyncio
    async def test_a_month_is_a_table_of_six_weeks_with_named_columns(
        self, context_args
    ):
        html = await _html(_calendar().view("month"), context_args)
        assert select(html, "caption")[0].get_text(strip=True) == "October 2026"
        assert_attr(html, "th", "scope", "col")
        assert_attr(html, "th", "abbr", "Monday")
        assert len(select(html, "tbody tr")) == 6
        assert len(select(html, "tbody tr:first-child td")) == 7
        assert_attr(html, "tbody td", "data-date", "2026-09-28")

    @pytest.mark.asyncio
    async def test_the_week_can_start_on_sunday_and_lose_its_weekend(
        self, context_args
    ):
        sunday = await _html(
            _calendar().view("month").week_start("sunday"), context_args
        )
        assert [th.get_text() for th in select(sunday, "th")][:2] == ["Sun", "Mon"]
        assert_attr(sunday, "tbody td", "data-date", "2026-09-27")
        weekdays = await _html(_calendar().view("month").weekdays(), context_args)
        assert [th.get_text() for th in select(weekdays, "th")] == [
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
        ]

    @pytest.mark.asyncio
    async def test_a_day_outside_the_month_is_muted_and_each_number_is_a_link(
        self, context_args
    ):
        html = await _html(_calendar().view("month").today(_WEDNESDAY), context_args)
        outside = select(html, "td[data-date='2026-09-30']")[0]
        inside = select(html, "td[data-date='2026-10-01']")[0]
        assert "text-fg-subtle" in outside["class"]
        assert "text-fg-subtle" not in inside["class"]
        number = inside.select_one("a")
        assert number["href"] == "/cal/day/2026-10-01/"
        assert number["aria-label"] == "Thursday 1 October 2026"
        assert_attr(html, "td[data-date='2026-10-14'] a", "aria-current", "date")

    @pytest.mark.asyncio
    async def test_a_full_day_folds_the_rest_into_more(self, context_args):
        extra = [Event(f"Talk {n}", datetime(2026, 10, 15, 14 + n)) for n in range(3)]
        html = await _html(
            _calendar(_AUDIT, _PAIRING, *extra).view("month"), context_args
        )
        cell = select(html, "td[data-date='2026-10-15']")[0]
        assert len(cell.select(":scope > ul > li")) == 2
        more = cell.select_one("button[aria-label^='+3 more']")
        assert more.get_text(strip=True) == "+3 more"
        panel = more.find_parent(attrs={"x-data": True}).select_one("[role=dialog]")
        assert len(panel.select("button[data-starts]")) == 5

    @pytest.mark.asyncio
    async def test_three_events_fit_without_a_more(self, context_args):
        html = await _html(
            _calendar(_AUDIT, _PAIRING, _REVIEW).view("month"), context_args
        )
        cell = select(html, "td[data-date='2026-10-15']")[0]
        assert len(cell.select(":scope > ul > li")) == 2
        assert cell.select_one("button[aria-label*=more]") is None

    @pytest.mark.asyncio
    async def test_a_timed_item_leads_with_a_dot_and_its_time_and_a_bar_fills(
        self, context_args
    ):
        html = await _html(_calendar(_REVIEW, _FREEZE).view("month"), context_args)
        review = _event(html, "Design review")
        assert "bg-chart-1" in review.select("span")[0]["class"]
        assert review.select("span")[1].get_text() == "13:00"
        freeze = _event(html, "Release freeze")
        assert "bg-chart-4/15" in freeze["class"]
        assert len(select(html, "td[data-date='2026-10-17'] button[data-all-day]")) == 1


class TestYear:
    @pytest.mark.asyncio
    async def test_twelve_months_of_day_links_with_a_dot_where_something_is_on(
        self, context_args
    ):
        html = await _html(_calendar(_FREEZE).view("year"), context_args)
        assert len(select(html, "table")) == 12
        assert [c.get_text(strip=True) for c in select(html, "caption")][:2] == [
            "January",
            "February",
        ]
        busy = select(html, "a[href='/cal/day/2026-10-16/']")[0]
        assert busy["aria-label"] == "Friday 16 October 2026, 1 event"
        assert busy.select_one("span[aria-hidden]") is not None
        quiet = select(html, "a[href='/cal/day/2026-10-15/']")[0]
        assert quiet["aria-label"] == "Thursday 15 October 2026"
        assert quiet.select_one("span[aria-hidden]") is None


class TestAgenda:
    @pytest.mark.asyncio
    async def test_thirty_days_grouped_by_the_days_with_something_on(
        self, context_args
    ):
        html = await _html(_calendar(_REVIEW, _FREEZE).view("agenda"), context_args)
        days = select(html, "section[data-date]")
        assert [d["data-date"] for d in days] == [
            "2026-10-14",
            "2026-10-16",
            "2026-10-17",
        ]
        assert days[0].select_one("a")["href"] == "/cal/day/2026-10-14/"
        assert f"13:00 {_DASH} 14:30" in days[0].get_text()
        assert "Room 3B" in days[0].get_text()
        assert "Day 2 of 2" in days[2].get_text()

    @pytest.mark.asyncio
    async def test_nothing_scheduled_is_an_empty_state(self, context_args):
        html = await _html(_calendar().view("agenda"), context_args)
        assert_no_selector(html, "section")
        assert "Nothing scheduled" in html
        assert "Wednesday 14 October 2026 to Thursday 12 November 2026." in html


class TestEventPopover:
    @pytest.mark.asyncio
    async def test_the_event_opens_a_dialog_named_by_it_anchored_fixed(
        self, context_args
    ):
        html = await _html(_calendar(_REVIEW), context_args)
        root = _event(html, "Design review").find_parent(attrs={"x-data": True})
        panel = root.select_one("[role=dialog]")
        assert panel["aria-label"] == "Design review"
        # Fixed, because the time grid scrolls and would clip the panel.
        assert panel["x-anchor.fixed.bottom-start.offset.6"].startswith("$root")

    @pytest.mark.asyncio
    async def test_the_popover_says_when_where_and_what_else(self, context_args):
        html = await _html(_calendar(_REVIEW, _STANDUP, _FREEZE), context_args)
        review = _event(html, "Design review").find_parent(attrs={"x-data": True})
        rows = [dt.get_text() for dt in review.select("dt")]
        assert rows == ["When", "Location", "Notes"]
        assert f"Wednesday 14 October 2026 · 13:00 {_DASH} 14:30" in review.get_text()
        assert "Bring the matrix." in review.get_text()
        standup = _event(html, "Standup").find_parent(attrs={"x-data": True})
        assert [dt.get_text() for dt in standup.select("dt")] == ["When", "Repeats"]
        freeze = _event(html, "Release freeze").find_parent(attrs={"x-data": True})
        assert f"Friday 16 October 2026 {_DASH} Saturday 17 October 2026 · All day" in (
            freeze.get_text()
        )

    @pytest.mark.asyncio
    async def test_actions_and_the_link_fill_the_foot_and_nothing_else_draws_one(
        self, context_args
    ):
        html = await _html(
            _calendar(_REVIEW, _STANDUP).actions(
                lambda event: [Button().size("sm").content(f"Edit {event.id}")]
            ),
            context_args,
        )
        review = _event(html, "Design review").find_parent(attrs={"x-data": True})
        edit = review.select_one("[role=dialog] button[type=button]")
        assert edit.get_text(strip=True) == "Edit 1"
        standup = _event(html, "Standup").find_parent(attrs={"x-data": True})
        assert standup.select_one("[role=dialog] a")["href"] == "/standup/"
        plain = await _html(_calendar(_REVIEW), context_args)
        assert_no_selector(plain, "[role=dialog] .border-t")
        assert_no_selector(plain, "[role=dialog] a")

    @pytest.mark.asyncio
    async def test_the_event_carries_what_a_script_moves_it_by(self, context_args):
        html = await _html(_calendar(_REVIEW), context_args)
        button = _event(html, "Design review")
        assert button["data-event-id"] == "1"
        assert button["data-starts"] == "2026-10-14T13:00:00"
        assert button["data-ends"] == "2026-10-14T14:30:00"
        assert "data-all-day" not in button.attrs
