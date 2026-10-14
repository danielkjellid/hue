from datetime import date, datetime

import pytest

from hue.formats import Formats
from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import DateInput
from tests._a11y import (
    assert_attr,
    assert_label_for,
    assert_no_selector,
    assert_selector,
    select,
    soup,
)

TRIGGER = 'button[aria-controls="starts-picker"]'


def _input():
    return DateInput().name("starts").label("Starts")


class TestField:
    @pytest.mark.asyncio
    async def test_the_field_is_a_patterned_text_input(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        assert_label_for(html, "starts")
        assert_attr(html, "input#starts", "type", "text")
        assert_attr(html, "input#starts", "pattern", r"\d{4}-\d{2}-\d{2}")
        assert_attr(html, "input#starts", "placeholder", "YYYY-MM-DD")
        assert_attr(html, "input#starts", "x-ref", "input")

    @pytest.mark.asyncio
    async def test_base_attrs_and_describedby_land_on_the_input(self, context_args):
        html = await render_tree(
            _input().hint("When it begins").error("Pick a day").x_model(unsafe("day")),
            context_args=context_args,
        )
        assert_attr(html, "input#starts", "x-model", "day")
        assert_attr(
            html, "input#starts", "aria-describedby", "starts-hint starts-error"
        )

    # value(): a date, an ISO string, the empty string, none, and a datetime
    @pytest.mark.asyncio
    async def test_value_from_a_date(self, context_args):
        html = await render_tree(
            _input().value(date(2026, 10, 14)), context_args=context_args
        )
        assert_attr(html, "input#starts", "value", "2026-10-14")

    @pytest.mark.asyncio
    async def test_value_from_a_string(self, context_args):
        html = await render_tree(
            _input().value("2026-10-14"), context_args=context_args
        )
        assert_attr(html, "input#starts", "value", "2026-10-14")

    @pytest.mark.asyncio
    async def test_empty_value_is_kept(self, context_args):
        html = await render_tree(_input().value(""), context_args=context_args)
        assert_attr(html, "input#starts", "value", "")

    @pytest.mark.asyncio
    async def test_no_value_sets_no_attribute(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        assert_no_selector(html, "input#starts[value]")

    def test_a_datetime_is_refused(self):
        with pytest.raises(ValueError, match="holds a day"):
            _input().value(datetime(2026, 10, 14, 9, 30))


class TestTrigger:
    @pytest.mark.asyncio
    async def test_the_button_opens_the_dialog(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        assert_attr(html, TRIGGER, "aria-label", "Choose date")
        assert_attr(html, TRIGGER, "aria-haspopup", "dialog")
        assert_attr(html, TRIGGER, "x-bind:aria-expanded", "open")
        assert_attr(html, TRIGGER, "x-on:click", "toggle()")
        assert_no_selector(html, f"{TRIGGER}[disabled]")
        assert_no_selector(html, f"{TRIGGER}[tabindex]")
        assert_attr(html, f"{TRIGGER} svg", "aria-hidden", "true")

    # disabled() and readonly(): inert, against the live default
    @pytest.mark.asyncio
    @pytest.mark.parametrize("inert", [_input().disabled(), _input().readonly()])
    async def test_inert_means_no_picker(self, context_args, inert):
        html = await render_tree(inert, context_args=context_args)
        assert_selector(html, 'button[aria-label="Choose date"][disabled]')
        assert_no_selector(html, "[x-on\\:click]")
        assert_no_selector(html, '[role="dialog"]')
        assert_no_selector(html, "[x-data]")
        assert_no_selector(html, "[x-ref=shell]")

    @pytest.mark.asyncio
    async def test_live_has_the_picker(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        assert_selector(html, '[role="dialog"]#starts-picker')
        assert_no_selector(html, "[x-data][x-ref]")
        assert_attr(html, "[x-data] > div", "x-ref", "shell")


class TestPanel:
    @pytest.mark.asyncio
    async def test_the_panel_is_a_named_non_modal_dialog(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        panel = "#starts-picker"
        assert_attr(html, panel, "role", "dialog")
        assert_attr(html, panel, "aria-label", "Choose date")
        assert_attr(html, panel, "tabindex", "-1")
        assert_attr(html, panel, "x-show", "open")
        assert_attr(html, panel, "x-anchor.bottom-start.offset.6", "$refs.shell")
        assert_attr(html, panel, "x-on:keydown", "key($event)")
        assert_no_selector(html, f"{panel}[aria-modal]")

    @pytest.mark.asyncio
    async def test_the_root_owns_escape_focusout_and_click_outside(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        root = "[x-data]"
        assert_attr(html, root, "x-on:keydown.escape")
        assert "close()" in select(html, root)[0]["x-on:keydown.escape"]
        assert_attr(html, root, "x-on:focusout", "leave($event)")
        assert_attr(html, root, "x-on:click.outside", "dismiss()")
        assert_no_selector(html, "[x-on\\:keydown\\.escape\\.window]")

    @pytest.mark.asyncio
    async def test_the_grid_is_named_by_the_live_month_heading(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        assert_attr(html, "h2#starts-picker-month", "aria-live", "polite")
        assert_attr(html, "h2#starts-picker-month", "x-text", "heading")
        assert_attr(html, "table", "role", "grid")
        assert_attr(html, "table", "aria-labelledby", "starts-picker-month")
        assert_attr(html, 'button[aria-label="Previous month"]', "@click", "page(-1)")
        assert_attr(html, 'button[aria-label="Next month"]', "@click", "page(1)")

    @pytest.mark.asyncio
    async def test_a_day_is_a_roving_tabindex_button(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        day = "tbody template template td button"
        assert_attr(html, day, "x-bind:tabindex", "cell.iso === focused ? 0 : -1")
        assert_attr(html, day, "x-bind:data-date", "cell.iso")
        assert_attr(html, day, "x-bind:aria-label", "cell.label")
        assert_attr(html, day, "x-bind:aria-current", "cell.today ? 'date' : null")
        assert_attr(html, day, "x-show", "!cell.outside")
        assert_attr(html, day, "x-on:click", "pick(cell.iso)")
        assert_attr(html, "tbody template template td", "x-bind:aria-selected")

    # week_start(): the header order and the index handed to Alpine
    @pytest.mark.asyncio
    async def test_the_week_starts_on_monday(self, context_args):
        html = await render_tree(_input(), context_args=context_args)
        assert [th.text for th in select(html, "th")][:2] == ["Mon", "Tue"]
        assert select(html, "[x-data]")[0]["x-data"].startswith("hueDateInput(0, ")

    @pytest.mark.asyncio
    async def test_the_week_starts_on_sunday(self, context_args):
        html = await render_tree(
            _input().week_start("sunday"), context_args=context_args
        )
        assert [th.text for th in select(html, "th")][:2] == ["Sun", "Mon"]
        assert select(html, "[x-data]")[0]["x-data"].startswith("hueDateInput(6, ")

    @pytest.mark.asyncio
    async def test_the_names_come_from_formats(self, context_args):
        formats = Formats(
            month_names=tuple(f"m{n}" for n in range(12)),
            day_names=tuple(f"d{n}" for n in range(7)),
            day_abbreviations=tuple(f"a{n}" for n in range(7)),
        )
        html = await render_tree(
            _input(), context_args={**context_args, "formats": formats}
        )
        assert_attr(html, "th", "abbr", "d0")
        assert '"m0", "m1"' in select(html, "[x-data]")[0]["x-data"]
        assert '"d0", "d1"' in select(html, "[x-data]")[0]["x-data"]


class TestTwoOnAPage:
    @pytest.mark.asyncio
    async def test_no_id_appears_twice(self, context_args):
        html = await render_tree(
            _input(),
            DateInput().name("ends").label("Ends"),
            context_args=context_args,
        )
        ids = [el["id"] for el in soup(html).select("[id]")]
        assert len(ids) == len(set(ids))
        assert_attr(html, 'button[aria-controls="ends-picker"]', "aria-label")
        assert_selector(html, '[role="dialog"]', count=2)
