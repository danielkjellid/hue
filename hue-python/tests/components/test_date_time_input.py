from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from hue.formats import Formats
from hue.renderer import render_tree
from hue.ui import DateTimeInput
from tests._a11y import assert_attr, select
from tests.components.test_date_input import config


def _field():
    return DateTimeInput().name("publish_at").label("Publish at")


class TestDateTimeInput:
    @pytest.mark.asyncio
    async def test_a_grid_beside_a_list_of_times(self, context_args):
        html = await render_tree(_field(), context_args=context_args)
        assert_attr(html, "[aria-haspopup]", "aria-label", "Choose date and time")
        assert len(select(html, 'table[role="grid"]')) == 1
        options = select(html, '[role="listbox"][aria-label="Time"] [role="option"]')
        assert len(options) == 96
        assert (options[1]["data-time"], options[1].text.strip()) == ("00:15", "00:15")
        assert [b.text.strip() for b in select(html, "#publish_at-picker button")][
            -2:
        ] == ["Now", "Done"]

    @pytest.mark.asyncio
    async def test_the_value_is_iso_to_the_minute(self, context_args):
        moment = datetime(2026, 10, 20, 14, 30, 59)
        html = await render_tree(_field().value(moment), context_args=context_args)
        assert config(html)["committed"] == ["2026-10-20T14:30"]
        assert_attr(html, "input#publish_at", "value", "2026-10-20 14:30")
        assert_attr(html, "input#publish_at", "placeholder", "YYYY-MM-DD HH:mm")

    @pytest.mark.asyncio
    async def test_an_aware_value_is_in_the_readers_time(self, context_args):
        oslo = timezone(timedelta(hours=2))
        context_args["formats"] = Formats(localize=lambda m: m.astimezone(oslo))
        moment = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
        html = await render_tree(_field().value(moment), context_args=context_args)
        assert config(html)["committed"] == ["2026-10-20T14:00"]

    @pytest.mark.asyncio
    async def test_a_year_under_1000_is_padded_and_the_offset_dropped(
        self, context_args
    ):
        # glibc's strftime writes year 5 as 5, which fromisoformat refuses.
        moment = datetime(5, 1, 2, 3, 4, tzinfo=UTC)
        html = await render_tree(_field().value(moment), context_args=context_args)
        assert config(html)["committed"] == ["0005-01-02T03:04"]

    @pytest.mark.asyncio
    async def test_seconds_in_the_format_are_refused(self, context_args):
        context_args["formats"] = Formats(datetime="%Y-%m-%d %H:%M:%S")
        with pytest.raises(ValueError, match="DateTimeInput cannot read %S back"):
            await render_tree(_field(), context_args=context_args)

    @pytest.mark.asyncio
    async def test_step_spaces_the_list(self, context_args):
        html = await render_tree(_field().step(30), context_args=context_args)
        assert len(select(html, '[role="option"]')) == 48
        assert config(html)["step"] == 30

    def test_a_step_outside_a_day_is_refused(self):
        with pytest.raises(ValueError, match="between 1 and 720"):
            _field().step(0)

    @pytest.mark.asyncio
    async def test_refusals_reach_the_grid(self, context_args):
        html = await render_tree(
            _field().min(date(2026, 10, 1)), context_args=context_args
        )
        assert config(html)["min"] == "2026-10-01"
