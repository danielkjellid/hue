import pytest

from hue.renderer import render_tree
from hue.ui import Select, SelectGroup, SelectOption
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _select():
    return (
        Select()
        .name("plan")
        .label("Plan")
        .placeholder("Choose a plan")
        .content(
            SelectOption().value("free").label("Free"),
            SelectOption().value("pro").label("Pro"),
        )
    )


class TestSelect:
    @pytest.mark.asyncio
    async def test_the_trigger_is_a_combobox_for_a_listbox(self, context_args):
        html = await render_tree(_select(), context_args=context_args)
        assert_attr(html, "label", "for", "plan")
        trigger = "button#plan"
        assert_attr(html, trigger, "type", "button")
        assert_attr(html, trigger, "role", "combobox")
        assert_attr(html, trigger, "aria-haspopup", "listbox")
        assert_attr(html, trigger, "aria-expanded", "false")
        assert_attr(html, trigger, "aria-controls", "plan-listbox")
        assert_attr(html, "#plan-listbox", "role", "listbox")
        assert_attr(html, "#plan-listbox", "aria-label", "Plan")
        assert_selector(html, '[role="option"]', count=2)

    @pytest.mark.asyncio
    async def test_the_value_is_submitted_by_a_hidden_field(self, context_args):
        html = await render_tree(_select().value("pro"), context_args=context_args)
        assert_attr(html, 'input[type="hidden"]', "name", "plan")
        assert_attr(html, 'input[type="hidden"]', "value", "pro")
        assert_no_selector(html, "button[name]")

    @pytest.mark.asyncio
    async def test_x_model_binds_the_submitted_field(self, context_args):
        html = await render_tree(_select().x_model("plan"), context_args=context_args)
        assert_attr(html, 'input[type="hidden"]', "x-model", "plan")
        assert_no_selector(html, "button[x-model]")

    @pytest.mark.asyncio
    async def test_the_submitted_field_joins_a_form_outside_it(self, context_args):
        html = await render_tree(_select().form("billing"), context_args=context_args)
        assert_attr(html, 'input[type="hidden"]', "form", "billing")
        assert_no_selector(html, "button[form]")

    # value(): both branches
    @pytest.mark.asyncio
    async def test_the_chosen_option_is_selected_and_shown(self, context_args):
        html = await render_tree(_select().value("pro"), context_args=context_args)
        assert_attr(html, "#plan-option-pro", "aria-selected", "true")
        assert_attr(html, "#plan-option-free", "aria-selected", "false")
        label = select(html, "button#plan span")[0]
        assert label.get_text() == "Pro"
        assert "text-fg-subtle" not in label["class"]

    @pytest.mark.asyncio
    async def test_without_a_value_the_trigger_shows_the_placeholder(
        self, context_args
    ):
        html = await render_tree(_select(), context_args=context_args)
        assert_no_selector(html, '[aria-selected="true"]')
        label = select(html, "button#plan span")[0]
        assert label.get_text() == "Choose a plan"
        assert "text-fg-subtle" in label["class"]

    @pytest.mark.asyncio
    async def test_a_value_is_found_inside_a_group(self, context_args):
        html = await render_tree(
            Select()
            .name("plan")
            .value("pro")
            .content(
                SelectGroup()
                .label("Paid")
                .content(SelectOption().value("pro").label("Pro"))
            ),
            context_args=context_args,
        )
        assert select(html, "button#plan span")[0].get_text() == "Pro"

    # required(): both branches
    @pytest.mark.asyncio
    async def test_required_is_announced_on_the_trigger(self, context_args):
        # A hidden field cannot be required, so the server validates and the
        # trigger says so.
        html = await render_tree(_select().required(), context_args=context_args)
        assert_attr(html, "button#plan", "aria-required", "true")

    @pytest.mark.asyncio
    async def test_optional_by_default(self, context_args):
        html = await render_tree(_select(), context_args=context_args)
        assert_no_selector(html, "button[aria-required]")

    # error(): both branches
    @pytest.mark.asyncio
    async def test_an_error_marks_the_trigger_invalid(self, context_args):
        html = await render_tree(
            _select().error("Pick a plan"), context_args=context_args
        )
        assert_attr(html, "button#plan", "aria-invalid", "true")
        assert_attr(html, "button#plan", "aria-describedby", "plan-error")

    @pytest.mark.asyncio
    async def test_valid_by_default(self, context_args):
        html = await render_tree(_select(), context_args=context_args)
        assert_no_selector(html, "button[aria-invalid]")

    # disabled(): both branches
    @pytest.mark.asyncio
    async def test_disabled_disables_the_trigger(self, context_args):
        html = await render_tree(_select().disabled(), context_args=context_args)
        assert_attr(html, "button#plan", "disabled")

    @pytest.mark.asyncio
    async def test_enabled_by_default(self, context_args):
        html = await render_tree(_select(), context_args=context_args)
        assert_no_selector(html, "button[disabled]")

    @pytest.mark.asyncio
    async def test_the_chevron_is_decorative(self, context_args):
        html = await render_tree(_select(), context_args=context_args)
        assert_attr(html, "button#plan svg", "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_a_select_needs_a_name(self, context_args):
        with pytest.raises(ValueError):
            await render_tree(Select().label("Plan"), context_args=context_args)


class TestSelectGroup:
    @pytest.mark.asyncio
    async def test_a_group_is_named_by_its_label(self, context_args):
        html = await render_tree(
            Select()
            .name("plan")
            .content(
                SelectGroup()
                .label("Paid")
                .content(SelectOption().value("pro").label("Pro"))
            ),
            context_args=context_args,
        )
        assert_attr(html, '[role="group"]', "aria-labelledby", "plan-group-Paid")
        assert select(html, "#plan-group-Paid")[0].get_text(strip=True) == "Paid"


class TestSelectOption:
    async def _option(self, option, context_args):
        return await render_tree(
            Select().name("plan").content(option), context_args=context_args
        )

    @pytest.mark.asyncio
    async def test_an_option_carries_its_value_and_label(self, context_args):
        html = await self._option(
            SelectOption().value("pro").label("Pro"), context_args
        )
        assert_attr(html, "#plan-option-pro", "data-value", "pro")
        assert_attr(html, "#plan-option-pro", "data-label", "Pro")

    @pytest.mark.asyncio
    async def test_the_label_defaults_to_the_value(self, context_args):
        html = await self._option(SelectOption().value("pro"), context_args)
        assert_attr(html, "#plan-option-pro", "data-label", "pro")

    @pytest.mark.asyncio
    async def test_the_value_is_quoted_for_alpine(self, context_args):
        # A quote in a value must not end the expression it is compared in.
        html = await self._option(SelectOption().value('a"b'), context_args)
        assert_attr(html, '[role="option"]', ":aria-selected", 'value === "a\\"b"')

    # disabled(): both branches
    @pytest.mark.asyncio
    async def test_a_disabled_option_says_so(self, context_args):
        html = await self._option(SelectOption().value("pro").disabled(), context_args)
        assert_attr(html, "#plan-option-pro", "aria-disabled", "true")

    @pytest.mark.asyncio
    async def test_an_option_is_enabled_by_default(self, context_args):
        html = await self._option(SelectOption().value("pro"), context_args)
        assert_no_selector(html, "[aria-disabled]")

    # description() and meta(): both branches
    @pytest.mark.asyncio
    async def test_description_and_meta_are_drawn(self, context_args):
        html = await self._option(
            SelectOption().value("pro").description("For teams").meta("$49"),
            context_args,
        )
        text = select(html, "#plan-option-pro")[0].get_text()
        assert "For teams" in text
        assert "$49" in text

    @pytest.mark.asyncio
    async def test_a_plain_option_is_only_its_label(self, context_args):
        html = await self._option(
            SelectOption().value("pro").label("Pro"), context_args
        )
        assert select(html, "#plan-option-pro")[0].get_text(strip=True) == "Pro"

    @pytest.mark.asyncio
    async def test_an_option_outside_a_select_is_refused(self, context_args):
        with pytest.raises(ValueError):
            await render_tree(SelectOption().value("pro"), context_args=context_args)
