import pytest

from hue.js import unsafe
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
    async def test_the_listbox_never_takes_focus_from_the_trigger(self, context_args):
        # The keys are handled on the trigger, so focus moving to the list
        # would leave it open with nothing listening.
        html = await render_tree(_select(), context_args=context_args)
        listbox = select(html, "#plan-listbox")[0]
        assert not listbox.has_attr("tabindex")
        assert listbox.has_attr("x-on:mousedown.prevent")

    @pytest.mark.asyncio
    async def test_the_value_is_submitted_by_a_hidden_field(self, context_args):
        html = await render_tree(_select().value("pro"), context_args=context_args)
        assert_attr(html, 'input[type="hidden"]', "name", "plan")
        assert_attr(html, 'input[type="hidden"]', "value", "pro")
        assert_no_selector(html, "button[name]")

    @pytest.mark.asyncio
    async def test_x_model_binds_the_submitted_field(self, context_args):
        html = await render_tree(
            _select().x_model(unsafe("plan")), context_args=context_args
        )
        assert_attr(html, 'input[type="hidden"]', "x-model", "plan")
        assert_no_selector(html, "button[x-model]")

    @pytest.mark.asyncio
    async def test_the_submitted_field_joins_a_form_outside_it(self, context_args):
        html = await render_tree(_select().form("billing"), context_args=context_args)
        assert_attr(html, 'input[type="hidden"]', "form", "billing")
        assert_no_selector(html, "button[form]")

    @pytest.mark.parametrize(
        ("value", "shown"), [("pro", "Pro"), (None, "Choose a plan")]
    )
    @pytest.mark.asyncio
    async def test_the_chosen_option_is_selected_and_shown(
        self, context_args, value, shown
    ):
        html = await render_tree(_select().value(value), context_args=context_args)
        selected = [o["data-value"] for o in select(html, '[aria-selected="true"]')]
        assert selected == ([value] if value else [])
        assert select(html, "button#plan span span")[0].get_text() == shown

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
        assert select(html, "button#plan span span")[0].get_text() == "Pro"

    @pytest.mark.asyncio
    async def test_required_is_announced_on_the_trigger(self, context_args):
        # A hidden field cannot be required, so the server validates and the
        # trigger says so.
        html = await render_tree(_select().required(), context_args=context_args)
        assert_attr(html, "button#plan", "aria-required", "true")

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

    @pytest.mark.asyncio
    async def test_disabled_disables_the_trigger_and_what_is_submitted(
        self, context_args
    ):
        html = await render_tree(_select().disabled(), context_args=context_args)
        assert_attr(html, "button#plan", "disabled")
        assert_attr(html, 'input[type="hidden"]', "disabled")

    @pytest.mark.asyncio
    async def test_the_trigger_is_as_wide_as_its_longest_option(self, context_args):
        # Each label is drawn hidden in the same cell, so choosing a shorter
        # one does not shrink the trigger.
        html = await render_tree(_select().value("pro"), context_args=context_args)
        hidden = [s.get_text() for s in select(html, "button#plan span.invisible")]
        assert hidden == ["Choose a plan", "Free", "Pro"]

    @pytest.mark.asyncio
    async def test_only_the_longest_labels_are_measured(self, context_args):
        html = await render_tree(
            Select()
            .name("size")
            .content(
                *(SelectOption().value(v).label(v) for v in ["S", "M", "XL", "XXL"])
            ),
            context_args=context_args,
        )
        hidden = [s.get_text() for s in select(html, "button#size span.invisible")]
        assert hidden == ["XXL", "XL", "S"]

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
        # The id comes from Alpine, so two groups with one label stay apart.
        group = select(html, '[role="group"]')[0]
        assert group[":aria-labelledby"] == "$id('hue-select-group')"
        label = group.find(attrs={":id": "$id('hue-select-group')"})
        assert label.get_text(strip=True) == "Paid"


class TestSelectOption:
    async def _option(self, option, context_args):
        return await render_tree(
            Select().name("plan").content(option), context_args=context_args
        )

    @pytest.mark.parametrize(
        ("option", "label"),
        [
            (SelectOption().value("pro").label("Pro"), "Pro"),
            # The label defaults to the value.
            (SelectOption().value("pro"), "pro"),
        ],
    )
    @pytest.mark.asyncio
    async def test_an_option_carries_its_value_and_label(
        self, context_args, option, label
    ):
        html = await self._option(option, context_args)
        assert_attr(html, '[role="option"]', "data-value", "pro")
        assert_attr(html, '[role="option"]', "data-label", label)

    @pytest.mark.asyncio
    async def test_every_distinct_value_gets_its_own_id(self, context_args):
        # Each of these once shared an id with another, and the keys find the
        # active option by its id.
        values = ["a b", "a-b", "日本", "中国", "€"]
        html = await render_tree(
            Select()
            .name("plan")
            .content(*(SelectOption().value(value) for value in values)),
            context_args=context_args,
        )
        ids = [option["id"] for option in select(html, '[role="option"]')]
        assert len(set(ids)) == len(values)

    @pytest.mark.asyncio
    async def test_the_value_is_quoted_for_alpine(self, context_args):
        # A quote in a value must not end the expression it is compared in.
        html = await self._option(SelectOption().value('a"b'), context_args)
        assert_attr(html, '[role="option"]', ":aria-selected", 'chosen("a\\"b")')

    @pytest.mark.asyncio
    async def test_a_disabled_option_says_so(self, context_args):
        html = await self._option(SelectOption().value("pro").disabled(), context_args)
        assert_attr(html, '[role="option"]', "aria-disabled", "true")

    @pytest.mark.asyncio
    async def test_description_and_meta_are_drawn(self, context_args):
        html = await self._option(
            SelectOption().value("pro").description("For teams").meta("$49"),
            context_args,
        )
        text = select(html, '[role="option"]')[0].get_text()
        assert "For teams" in text
        assert "$49" in text

    @pytest.mark.asyncio
    async def test_an_option_outside_a_select_is_refused(self, context_args):
        with pytest.raises(ValueError):
            await render_tree(SelectOption().value("pro"), context_args=context_args)
