import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Combobox, SelectOption
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _combobox():
    return (
        Combobox()
        .name("country")
        .label("Country")
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
        )
    )


class TestCombobox:
    @pytest.mark.asyncio
    async def test_the_text_field_is_a_combobox_for_a_listbox(self, context_args):
        html = await render_tree(_combobox(), context_args=context_args)
        assert_attr(html, "label", "for", "country")
        field = "input#country"
        assert_attr(html, field, "role", "combobox")
        assert_attr(html, field, "aria-autocomplete", "list")
        assert_attr(html, field, "aria-expanded", "false")
        assert_attr(html, field, "aria-controls", "country-listbox")
        assert_attr(html, field, "autocomplete", "off")
        assert_attr(html, "#country-listbox", "role", "listbox")
        assert_attr(html, "#country-listbox", "aria-label", "Country")
        assert_selector(html, '[role="option"]', count=2)

    @pytest.mark.asyncio
    async def test_the_text_field_is_not_submitted(self, context_args):
        # What is typed is a search; the values go in hidden fields.
        html = await render_tree(_combobox(), context_args=context_args)
        assert_no_selector(html, "input#country[name]")
        assert_attr(html, 'template input[type="hidden"]', "name", "country")

    @pytest.mark.asyncio
    async def test_the_toggle_is_named_and_out_of_the_tab_order(self, context_args):
        html = await render_tree(_combobox(), context_args=context_args)
        toggle = 'button[aria-controls="country-listbox"]'
        assert_attr(html, toggle, "tabindex", "-1")
        assert_attr(html, toggle, "aria-label", "Country")
        assert_attr(html, f"{toggle} svg", "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_nothing_matching_is_announced(self, context_args):
        html = await render_tree(
            _combobox().empty_message("No country matches that."),
            context_args=context_args,
        )
        assert_selector(html, '[role="status"]')
        assert "No country matches that." in html

    # value(): both branches
    @pytest.mark.asyncio
    async def test_a_chosen_value_is_shown_and_selected(self, context_args):
        html = await render_tree(_combobox().value("se"), context_args=context_args)
        assert_attr(html, "input#country", "value", "Sweden")
        assert_attr(html, '[data-value="se"]', "aria-selected", "true")
        assert_attr(html, '[data-value="no"]', "aria-selected", "false")

    @pytest.mark.asyncio
    async def test_without_a_value_the_field_is_empty(self, context_args):
        html = await render_tree(_combobox(), context_args=context_args)
        assert_no_selector(html, "input#country[value]")
        assert_no_selector(html, '[aria-selected="true"]')

    # multiple(): both branches
    @pytest.mark.asyncio
    async def test_multiple_draws_tokens_named_by_what_they_remove(self, context_args):
        html = await render_tree(
            _combobox().multiple().value("no", "se"), context_args=context_args
        )
        assert_attr(html, "#country-listbox", "aria-multiselectable", "true")
        assert_attr(html, "template button", ":aria-label", "`Remove ${item.label}`")
        assert_selector(html, '[aria-selected="true"]', count=2)
        # The field is for adding another, so it does not repeat a label.
        assert_no_selector(html, "input#country[value]")

    @pytest.mark.asyncio
    async def test_the_list_opens_when_the_field_gets_focus(self, context_args):
        html = await render_tree(_combobox(), context_args=context_args)
        assert_attr(html, "input#country", "x-on:focus", "focused()")

    @pytest.mark.asyncio
    async def test_a_multiple_field_has_room_for_tokens(self, context_args):
        # Tokens wrap inside a width of their own instead of widening it.
        html = await render_tree(_combobox().multiple(), context_args=context_args)
        assert_selector(html, ".invisible.w-64")

    @pytest.mark.asyncio
    async def test_a_single_field_is_as_wide_as_its_options(self, context_args):
        html = await render_tree(_combobox(), context_args=context_args)
        assert_no_selector(html, ".invisible.w-64")
        assert [s.get_text(strip=True) for s in select(html, ".invisible")] == [
            "Norway",
            "Sweden",
        ]

    @pytest.mark.asyncio
    async def test_single_has_no_tokens(self, context_args):
        html = await render_tree(_combobox().value("se"), context_args=context_args)
        assert_no_selector(html, "[aria-multiselectable]")
        assert_no_selector(html, "template button")

    @pytest.mark.asyncio
    async def test_several_values_need_multiple(self, context_args):
        with pytest.raises(ValueError):
            await render_tree(_combobox().value("no", "se"), context_args=context_args)

    # x_model(): both branches
    @pytest.mark.asyncio
    async def test_x_model_binds_the_value_not_the_search(self, context_args):
        html = await render_tree(
            _combobox().x_model(unsafe("country")), context_args=context_args
        )
        assert_attr(html, "[x-modelable]", "x-modelable", "value")
        assert_attr(html, "[x-modelable]", "x-model", "country")
        assert_attr(html, "input#country", "x-model", "query")

    @pytest.mark.asyncio
    async def test_a_multiple_binding_holds_the_list(self, context_args):
        html = await render_tree(
            _combobox().multiple().x_model(unsafe("countries")),
            context_args=context_args,
        )
        assert_attr(html, "[x-modelable]", "x-modelable", "values")

    @pytest.mark.asyncio
    async def test_without_a_binding_nothing_is_modelable(self, context_args):
        html = await render_tree(_combobox(), context_args=context_args)
        assert_no_selector(html, "[x-modelable]")

    @pytest.mark.asyncio
    async def test_the_submitted_fields_join_a_form_outside_it(self, context_args):
        html = await render_tree(_combobox().form("billing"), context_args=context_args)
        assert_attr(html, 'template input[type="hidden"]', "form", "billing")
        assert_no_selector(html, "input#country[form]")

    # required(), error() and disabled(): both branches
    @pytest.mark.asyncio
    async def test_required_invalid_and_disabled_reach_the_field(self, context_args):
        html = await render_tree(
            _combobox().required().error("Pick one").disabled(),
            context_args=context_args,
        )
        field = "input#country"
        assert_attr(html, field, "aria-required", "true")
        assert_attr(html, field, "aria-invalid", "true")
        assert_attr(html, field, "aria-describedby", "country-error")
        assert_attr(html, field, "disabled")
        assert_attr(html, 'button[aria-controls="country-listbox"]', "disabled")
        # Neither submitted nor opened by a click on the shell around the field.
        assert_attr(html, 'template input[type="hidden"]', "disabled")
        assert_no_selector(html, '[x-ref="shell"][x-on\\:click]')

    @pytest.mark.asyncio
    async def test_by_default_the_field_is_optional_valid_and_enabled(
        self, context_args
    ):
        html = await render_tree(_combobox(), context_args=context_args)
        assert_no_selector(html, "[aria-required]")
        assert_no_selector(html, "[aria-invalid]")
        assert_no_selector(html, "[disabled]")
        assert_attr(html, '[x-ref="shell"]', "x-on:click")

    @pytest.mark.asyncio
    async def test_a_value_no_option_holds_shows_the_value(self, context_args):
        # Nothing to take a label from, so the value stands in for one.
        html = await render_tree(_combobox().value("dk"), context_args=context_args)
        assert select(html, "input#country")[0]["value"] == "dk"
