from datetime import time

import pytest

from hue.formats import Formats
from hue.renderer import render_tree
from hue.ui import TimeInput
from tests._a11y import assert_attr, assert_no_selector, select
from tests.components.test_date_input import config


def _field():
    return TimeInput().name("reminder").label("Reminder")


class TestTimeInput:
    @pytest.mark.asyncio
    async def test_a_list_of_times_named_by_the_field(self, context_args):
        html = await render_tree(_field(), context_args=context_args)
        assert_attr(html, "[aria-haspopup]", "aria-label", "Choose time")
        assert_no_selector(html, 'table[role="grid"]')
        listbox = '[role="dialog"] > [role="listbox"]'
        assert_attr(html, listbox, "aria-label", "Reminder")
        assert len(select(html, '[role="option"]')) == 96
        assert config(html)["committed"] == []

    @pytest.mark.asyncio
    async def test_midnight_is_a_value(self, context_args):
        html = await render_tree(_field().value(time(0, 0)), context_args=context_args)
        assert config(html)["committed"] == ["00:00"]
        assert_attr(html, "input#reminder", "value", "00:00")

    @pytest.mark.asyncio
    async def test_a_twelve_hour_format_writes_the_list(self, context_args):
        context_args["formats"] = Formats(time="%I:%M %p")
        html = await render_tree(
            _field().value(time(14, 30)), context_args=context_args
        )
        option = select(html, '[data-time="14:30"]')[0]
        assert option.text.strip() == "02:30 PM"
        assert_attr(html, "input#reminder", "value", "02:30 PM")
        assert_attr(html, "input#reminder", "placeholder", "hh:mm AM")
        # Submitted the same either way.
        assert config(html)["committed"] == ["14:30"]
