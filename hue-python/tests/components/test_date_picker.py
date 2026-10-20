import json
from collections import Counter
from datetime import date, datetime

import pytest

from hue.formats import Formats
from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import DatePicker, Stack
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _picker():
    return DatePicker().name("due").label("Due date")


def _config(html: str) -> dict:
    """
    What the root hands date-picker.js.
    """
    source = select(html, '[role="group"]')[0]["x-data"]
    assert source.startswith("hueDatePicker(")
    return json.loads(source.removeprefix("hueDatePicker(").removesuffix(")"))


class TestDatePicker:
    @pytest.mark.asyncio
    async def test_a_named_group_holding_a_grid_of_six_weeks(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        assert_attr(html, '[role="group"]', "aria-label", "Due date")
        assert_selector(html, 'table[role="grid"]', count=1)
        assert_attr(html, 'table[role="grid"]', ":aria-label", "title(0)")
        assert_selector(html, "tbody td[x-bind]", count=42)
        # Monday first, abbreviated, with the whole name for a screen reader.
        assert_attr(html, "th", "abbr", "Monday")
        assert_attr(html, "th", "scope", "col")
        assert select(html, "th")[0].text == "Mon"

    @pytest.mark.asyncio
    async def test_a_missing_label_raises(self, context_args):
        with pytest.raises(ValueError, match="label"):
            await render_tree(DatePicker().name("due"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_week_start_turns_the_header(self, context_args):
        html = await render_tree(
            _picker().week_start("sunday"), context_args=context_args
        )
        assert [th["abbr"] for th in select(html, "th")][:2] == ["Sunday", "Monday"]
        assert _config(html)["weekStart"] == 6

    @pytest.mark.asyncio
    async def test_names_come_from_formats(self, context_args):
        names = Formats(
            month_names=tuple(f"m{n}" for n in range(1, 13)),
            day_names=tuple(f"d{n}" for n in range(1, 8)),
            day_abbreviations=tuple(f"a{n}" for n in range(1, 8)),
        )
        context_args["formats"] = names
        html = await render_tree(_picker(), context_args=context_args)
        assert select(html, "th")[0].text == "a1"
        assert select(html, "[data-item]")[0].text.strip() == "m1"
        config = _config(html)
        assert config["monthNames"][9] == "m10"
        assert config["dayNames"][0] == "d1"

    # value(): ISO strings, sorted, bounded by the mode

    @pytest.mark.asyncio
    async def test_the_value_is_handed_over_as_sorted_iso_days(self, context_args):
        picker = _picker().mode("multiple").value(date(2026, 10, 9), date(2026, 1, 2))
        html = await render_tree(picker, context_args=context_args)
        assert _config(html)["value"] == ["2026-01-02", "2026-10-09"]

    @pytest.mark.asyncio
    async def test_no_value_is_an_empty_list(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        config = _config(html)
        assert config["value"] == []
        assert config["min"] is None
        assert config["max"] is None

    @pytest.mark.asyncio
    async def test_a_range_takes_two_days_and_a_single_one(self, context_args):
        two = (date(2026, 10, 9), date(2026, 10, 2))
        html = await render_tree(
            _picker().mode("range").value(*two), context_args=context_args
        )
        assert _config(html)["value"] == ["2026-10-02", "2026-10-09"]
        with pytest.raises(ValueError, match="single"):
            await render_tree(_picker().value(*two), context_args=context_args)

    def test_a_datetime_is_refused(self):
        with pytest.raises(ValueError, match="days"):
            _picker().value(datetime(2026, 10, 9, 12, 0))

    def test_no_months_is_refused(self):
        with pytest.raises(ValueError, match="at least one"):
            _picker().months(0)

    @pytest.mark.asyncio
    async def test_unavailable_takes_dates_and_weekdays(self, context_args):
        picker = (
            _picker()
            .min(date(2026, 10, 1))
            .max(date(2026, 12, 31))
            .unavailable("saturday", date(2026, 12, 25), "sunday")
            .markers(date(2026, 10, 5), label="has bookings")
        )
        config = _config(await render_tree(picker, context_args=context_args))
        assert config["min"] == "2026-10-01"
        assert config["max"] == "2026-12-31"
        assert config["unavailable"] == ["2026-12-25"]
        assert config["closed"] == [5, 6]
        assert config["markers"] == ["2026-10-05"]
        assert config["markerLabel"] == "has bookings"

    # mode(): several days are a multiselectable grid

    @pytest.mark.asyncio
    async def test_single_is_not_multiselectable(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        assert_no_selector(html, "[aria-multiselectable]")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mode", ["range", "multiple"])
    async def test_range_and_multiple_are_multiselectable(self, context_args, mode):
        html = await render_tree(_picker().mode(mode), context_args=context_args)
        assert_attr(html, "table", "aria-multiselectable", "true")

    # months(): Previous on the first caption, Next on the last

    @pytest.mark.asyncio
    async def test_one_month_has_both_steps(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        assert_selector(html, 'button[aria-label="Previous month"]', count=1)
        assert_selector(html, 'button[aria-label="Next month"]', count=1)

    @pytest.mark.asyncio
    async def test_two_months_split_the_steps(self, context_args):
        html = await render_tree(_picker().months(2), context_args=context_args)
        grids = select(html, 'table[role="grid"]')
        assert len(grids) == 2
        months = [grid.parent for grid in grids]
        assert months[0].select('button[aria-label="Previous month"]')
        assert not months[0].select('button[aria-label="Next month"]')
        assert months[1].select('button[aria-label="Next month"]')
        assert not months[1].select('button[aria-label="Previous month"]')
        # Only the first title jumps, so it is the only one that is a button.
        assert len(select(html, '[x-ref="daysTitle"]')) == 1

    # Submission: one hidden field per day, under the name

    @pytest.mark.asyncio
    async def test_each_day_is_submitted_under_the_name(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        assert_attr(html, "template", "x-for", "day in value")
        field = 'template input[type="hidden"]'
        assert_attr(html, field, "name", "due")
        assert_attr(html, field, ":value", "day")
        assert_no_selector(html, f"{field}[disabled]")

    @pytest.mark.asyncio
    async def test_disabled_submits_nothing_and_steps_are_disabled(self, context_args):
        html = await render_tree(_picker().disabled(), context_args=context_args)
        assert_selector(html, 'template input[type="hidden"][disabled]')
        assert_selector(html, 'button[aria-label="Previous month"][disabled]')
        assert_selector(html, '[x-ref="daysTitle"][disabled]')
        assert _config(html)["disabled"] is True

    @pytest.mark.asyncio
    async def test_form_goes_on_the_submitted_fields(self, context_args):
        html = await render_tree(_picker().form("booking"), context_args=context_args)
        assert_attr(html, 'template input[type="hidden"]', "form", "booking")
        assert_no_selector(html, '[role="group"][form]')

    # x_model: binds the list of days

    @pytest.mark.asyncio
    async def test_x_model_binds_the_value(self, context_args):
        html = await render_tree(
            _picker().x_model(unsafe("days")), context_args=context_args
        )
        assert_attr(html, '[role="group"]', "x-model", "days")
        assert_attr(html, '[role="group"]', "x-modelable", "value")

    @pytest.mark.asyncio
    async def test_without_x_model_nothing_is_modelable(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        assert_no_selector(html, "[x-modelable]")

    # required() and error()

    @pytest.mark.asyncio
    async def test_required_marks_the_grid(self, context_args):
        html = await render_tree(_picker().required(), context_args=context_args)
        assert_attr(html, "table", "aria-required", "true")

    @pytest.mark.asyncio
    async def test_not_required_says_nothing(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        assert_no_selector(html, "[aria-required]")

    @pytest.mark.asyncio
    async def test_an_error_is_shown_and_describes_the_group(self, context_args):
        html = await render_tree(
            _picker().error("Pick a weekday."), context_args=context_args
        )
        assert_attr(html, '[role="group"]', "aria-invalid", "true")
        assert_attr(html, '[role="group"]', "aria-describedby", "due-error")
        assert_attr(html, "#due-error", "role", "alert")

    @pytest.mark.asyncio
    async def test_no_error_no_description(self, context_args):
        html = await render_tree(_picker(), context_args=context_args)
        assert_no_selector(html, "[aria-invalid]")
        assert_no_selector(html, "[aria-describedby]")

    @pytest.mark.asyncio
    async def test_two_on_one_page_share_no_id(self, context_args):
        page = Stack().content(
            _picker().error("Wrong."),
            DatePicker().name("other").label("Other").error("Wrong."),
        )
        html = await render_tree(page, context_args=context_args)
        ids = Counter(tag["id"] for tag in select(html, "[id]"))
        assert ids and all(count == 1 for count in ids.values())
