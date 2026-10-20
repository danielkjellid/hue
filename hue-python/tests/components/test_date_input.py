import json
from collections import Counter
from datetime import date, datetime

import pytest

from hue.formats import Formats
from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import DateInput, Stack
from tests._a11y import (
    assert_attr,
    assert_label_for,
    assert_no_selector,
    assert_selector,
    select,
)

_ROOT = '[x-data^="hueDateInput("]'


def _field():
    return DateInput().name("starts").label("Start date")


def config(html: str) -> dict:
    """
    What the root hands date-input.js. Shared with the DateTimeInput and
    TimeInput tests.
    """
    source = select(html, _ROOT)[0]["x-data"]
    return json.loads(source.removeprefix("hueDateInput(").removesuffix(")"))


class TestDateInput:
    @pytest.mark.asyncio
    async def test_a_labelled_text_field_opening_a_named_dialog(self, context_args):
        html = await render_tree(_field(), context_args=context_args)
        assert_label_for(html, "starts")
        # The text is for people; the value is submitted in hidden fields.
        assert not select(html, "input#starts")[0].has_attr("name")
        assert_attr(html, 'template input[type="hidden"]', "name", "starts")
        assert_attr(html, "[aria-haspopup]", "aria-haspopup", "dialog")
        assert_attr(html, "[aria-haspopup]", "aria-controls", "starts-picker")
        assert_attr(html, "[aria-haspopup]", "aria-label", "Choose date")
        assert_attr(html, '#starts-picker[role="dialog"]', "aria-label", "Start date")
        # Anchored fixed, so a Dialog's hidden overflow cannot clip it.
        assert_attr(html, "#starts-picker", "x-anchor.fixed.bottom-start.offset.6")
        assert_selector(html, 'table[role="grid"]', count=1)

    @pytest.mark.asyncio
    async def test_the_value_is_iso_and_written_with_formats(self, context_args):
        context_args["formats"] = Formats(date="%d.%m.%Y")
        html = await render_tree(
            _field().value(date(2026, 10, 20)), context_args=context_args
        )
        assert config(html)["committed"] == ["2026-10-20"]
        assert_attr(html, "input#starts", "value", "20.10.2026")
        assert_attr(html, "input#starts", "placeholder", "DD.MM.YYYY")
        assert config(html)["formats"]["date"] == "%d.%m.%Y"

    @pytest.mark.asyncio
    async def test_a_format_it_cannot_read_back_is_refused(self, context_args):
        context_args["formats"] = Formats(date="%d/%m/%y")
        with pytest.raises(ValueError, match="DateInput cannot read %y back"):
            await render_tree(_field(), context_args=context_args)

    @pytest.mark.asyncio
    async def test_names_are_written_from_formats_and_handed_to_the_script(
        self, context_args
    ):
        abbreviations = tuple(f"m{i}." for i in range(1, 13))
        context_args["formats"] = Formats(
            date="%e %b %Y", month_abbreviations=abbreviations
        )
        html = await render_tree(
            _field().value(date(2026, 7, 5)), context_args=context_args
        )
        # strftime would write Jul, in the process locale.
        assert_attr(html, "input#starts", "value", " 5 m7. 2026")
        assert_attr(html, "input#starts", "placeholder", "D Mon YYYY")
        assert config(html)["monthAbbreviations"] == list(abbreviations)

    @pytest.mark.asyncio
    async def test_no_value_is_empty(self, context_args):
        html = await render_tree(_field(), context_args=context_args)
        assert config(html)["committed"] == []
        assert not select(html, "input#starts")[0].has_attr("value")
        assert_attr(html, "input#starts", "placeholder", "YYYY-MM-DD")

    @pytest.mark.asyncio
    async def test_a_range_keeps_both_ends_even_on_one_day(self, context_args):
        field = _field().mode("range").value(date(2026, 10, 9), date(2026, 10, 9))
        html = await render_tree(field, context_args=context_args)
        assert config(html)["committed"] == ["2026-10-09", "2026-10-09"]
        assert_attr(html, "input#starts", "value", "2026-10-09 \N{EN DASH} 2026-10-09")

    @pytest.mark.asyncio
    async def test_a_range_of_one_end_is_refused(self, context_args):
        field = _field().mode("range").value(date(2026, 10, 9))
        with pytest.raises(ValueError, match="both of its ends"):
            await render_tree(field, context_args=context_args)

    def test_a_datetime_is_refused(self):
        with pytest.raises(ValueError, match="Pass a date"):
            _field().value(datetime(2026, 10, 9, 12))

    # mode(): a range has two months, a footer, and presets when asked

    @pytest.mark.asyncio
    async def test_a_range_shows_two_months_and_apply(self, context_args):
        html = await render_tree(_field().mode("range"), context_args=context_args)
        assert_selector(html, 'table[role="grid"]', count=2)
        assert config(html)["months"] == 2
        assert [b.text.strip() for b in select(html, "#starts-picker button")][-2:] == [
            "Cancel",
            "Apply",
        ]

    @pytest.mark.asyncio
    async def test_a_single_field_has_no_footer(self, context_args):
        html = await render_tree(_field(), context_args=context_args)
        assert_no_selector(html, '#starts-picker [aria-live="polite"]')
        assert "Apply" not in html

    @pytest.mark.asyncio
    async def test_presets_when_asked(self, context_args):
        field = _field().mode("range", presets=True)
        html = await render_tree(field, context_args=context_args)
        presets = select(html, '[role="group"][aria-label="Presets"] button')
        assert [b.text.strip() for b in presets][:2] == ["Today", "Yesterday"]
        assert presets[2]["x-bind"] == "preset(2)"

    @pytest.mark.asyncio
    async def test_no_presets_unless_asked(self, context_args):
        html = await render_tree(_field().mode("range"), context_args=context_args)
        assert_no_selector(html, '[aria-label="Presets"]')

    def test_presets_belong_to_a_range(self):
        with pytest.raises(ValueError, match="range"):
            _field().mode("single", presets=True)

    @pytest.mark.asyncio
    async def test_multiple_lists_its_days_as_chips(self, context_args):
        field = _field().mode("multiple").required()
        html = await render_tree(field, context_args=context_args)
        assert_attr(html, 'ul[aria-label="Start date"]', "x-show", "committed.length")
        assert_attr(html, "ul li button", ":aria-label", "removeLabel(day)")
        # The text empties once a day is added, so required is said, not enforced.
        assert_attr(html, "input#starts", "aria-required", "true")
        assert not select(html, "input#starts")[0].has_attr("required")

    @pytest.mark.asyncio
    async def test_a_single_field_has_no_chips_and_is_required_natively(
        self, context_args
    ):
        html = await render_tree(_field().required(), context_args=context_args)
        assert_no_selector(html, "ul")
        assert_attr(html, "input#starts", "required")

    # Inert: disabled and readonly have no popover

    @pytest.mark.asyncio
    async def test_disabled_has_no_popover_and_submits_nothing(self, context_args):
        html = await render_tree(_field().disabled(), context_args=context_args)
        assert_no_selector(html, '[role="dialog"]')
        assert_attr(html, "button[aria-label='Choose date']", "disabled")
        assert_no_selector(html, "[aria-haspopup]")
        assert_attr(html, 'template input[type="hidden"]', "disabled")
        assert config(html)["inert"] is True

    @pytest.mark.asyncio
    async def test_readonly_has_no_popover_but_submits(self, context_args):
        html = await render_tree(_field().readonly(), context_args=context_args)
        assert_no_selector(html, '[role="dialog"]')
        assert_attr(html, "input#starts", "readonly")
        assert not select(html, 'template input[type="hidden"]')[0].has_attr("disabled")

    @pytest.mark.asyncio
    async def test_enabled_opens_and_submits(self, context_args):
        html = await render_tree(_field(), context_args=context_args)
        assert_selector(html, '[role="dialog"]')
        assert not select(html, 'template input[type="hidden"]')[0].has_attr("disabled")
        assert config(html)["inert"] is False

    # The error: one element for the server's and a typed one

    @pytest.mark.asyncio
    async def test_a_server_error_is_shown_in_the_typed_errors_place(
        self, context_args
    ):
        html = await render_tree(
            _field().hint("Any weekday").error("Too late"), context_args=context_args
        )
        alert = select(html, '#starts-error[role="alert"]')[0]
        assert alert.select_one("[x-text]").text == "Too late"
        assert alert.select_one('[x-text="error"]')
        assert_attr(html, "input#starts", "aria-invalid", "true")
        assert_attr(html, "input#starts", "aria-describedby", "starts-error")
        assert config(html)["error"] == "Too late"
        assert select(html, "#starts-hint")[0].parent["x-show"] == "!error"

    @pytest.mark.asyncio
    async def test_no_error_waits_hidden_and_the_hint_describes(self, context_args):
        field = _field().hint("Any weekday")
        html = await render_tree(field, context_args=context_args)
        assert select(html, "#starts-error")[0].parent.has_attr("x-cloak")
        assert not select(html, "input#starts")[0].has_attr("aria-invalid")
        assert_attr(html, "input#starts", "aria-describedby", "starts-hint")
        assert_attr(
            html,
            "input#starts",
            ":aria-describedby",
            'error ? "starts-error" : "starts-hint"',
        )
        assert config(html)["error"] is None

    @pytest.mark.asyncio
    async def test_a_horizontal_hint_stays_by_the_label(self, context_args):
        field = _field().hint("Any weekday").horizontal()
        html = await render_tree(field, context_args=context_args)
        assert_selector(html, "#starts-hint", count=1)
        assert not select(html, f"{_ROOT} #starts-hint")

    # Binding, forms, and two on a page

    @pytest.mark.asyncio
    async def test_x_model_binds_the_iso_list(self, context_args):
        html = await render_tree(
            _field().x_model(unsafe("days")), context_args=context_args
        )
        assert_attr(html, _ROOT, "x-modelable", "committed")
        assert_attr(html, _ROOT, "x-model", "days")
        assert_attr(html, "input#starts", "x-model", "text")

    @pytest.mark.asyncio
    async def test_without_x_model_nothing_is_modelable(self, context_args):
        html = await render_tree(_field(), context_args=context_args)
        assert not select(html, _ROOT)[0].has_attr("x-modelable")

    @pytest.mark.asyncio
    async def test_form_goes_on_the_submitted_fields(self, context_args):
        html = await render_tree(_field().form("booking"), context_args=context_args)
        assert_attr(html, 'template input[type="hidden"]', "form", "booking")
        assert not select(html, "input#starts")[0].has_attr("form")

    @pytest.mark.asyncio
    async def test_two_on_one_page_share_no_id(self, context_args):
        page = Stack().content(
            _field(), DateInput().name("ends").label("End date").mode("range")
        )
        html = await render_tree(page, context_args=context_args)
        ids = Counter(tag["id"] for tag in select(html, "[id]"))
        assert ids and max(ids.values()) == 1

    @pytest.mark.asyncio
    async def test_week_start_reaches_the_grid(self, context_args):
        html = await render_tree(
            _field().week_start("sunday"), context_args=context_args
        )
        assert select(html, "th")[0]["abbr"] == "Sunday"
        assert config(html)["weekStart"] == 6

    @pytest.mark.asyncio
    async def test_refusals_reach_the_grid(self, context_args):
        field = (
            _field()
            .min(date(2026, 10, 1))
            .max(date(2026, 10, 31))
            .unavailable("sunday", date(2026, 10, 14))
        )
        html = await render_tree(field, context_args=context_args)
        data = config(html)
        assert (data["min"], data["max"]) == ("2026-10-01", "2026-10-31")
        assert (data["unavailable"], data["closed"]) == (["2026-10-14"], [6])
