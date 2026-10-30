import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Radio, RadioGroup
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _group():
    return (
        RadioGroup("region")
        .legend("Region")
        .content(
            Radio().value("eu").label("Europe"),
            Radio().value("us").label("North America"),
        )
    )


class TestRadioGroup:
    @pytest.mark.asyncio
    async def test_the_question_is_announced_with_each_option(self, context_args):
        # A fieldset and legend, so "Region, Europe" rather than "Europe" on
        # its own with the question left behind somewhere above.
        html = await render_tree(_group(), context_args=context_args)
        assert_selector(html, "fieldset > legend")
        assert "Region" in html

    @pytest.mark.asyncio
    async def test_the_group_owns_the_name(self, context_args):
        # Options are exclusive only because they share one name.
        html = await render_tree(_group(), context_args=context_args)
        assert_selector(html, 'input[type="radio"][name="region"]', count=2)

    @pytest.mark.asyncio
    async def test_a_form_the_group_is_outside_reaches_every_option(self, context_args):
        # The radios are what the form submits; a form attribute on the
        # fieldset alone would tie only the fieldset to it.
        html = await render_tree(_group().form("settings"), context_args=context_args)
        assert_selector(html, 'input[type=radio][form="settings"]', count=2)
        assert_no_selector(html, "fieldset[form]")

    @pytest.mark.asyncio
    async def test_the_named_option_starts_checked(self, context_args):
        html = await render_tree(_group().value("us"), context_args=context_args)
        assert_attr(html, 'input[value="us"]', "checked")
        assert_no_selector(html, 'input[value="eu"][checked]')

    @pytest.mark.asyncio
    async def test_disabled_reaches_the_inputs(self, context_args):
        html = await render_tree(_group().disabled(), context_args=context_args)
        assert_selector(html, "input[disabled]", count=2)
        html = await render_tree(
            RadioGroup("r")
            .legend("R")
            .content(
                Radio().value("a").label("A"),
                Radio().value("b").label("B").disabled(),
            ),
            context_args=context_args,
        )
        assert_selector(html, "input[disabled]", count=1)

    @pytest.mark.asyncio
    async def test_an_error_is_announced_and_describes_the_group(self, context_args):
        html = await render_tree(
            _group().error("Pick a region."), context_args=context_args
        )
        # A radiogroup, where ARIA 1.2 supports aria-invalid; a group does not.
        assert_attr(html, "fieldset", "role", "radiogroup")
        assert_attr(html, "fieldset", "aria-invalid", "true")
        assert_attr(html, "fieldset", "aria-describedby", "region-error")
        assert_selector(html, '[role="alert"]#region-error')

    @pytest.mark.asyncio
    async def test_valid_by_default(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, "[aria-invalid]")

    @pytest.mark.asyncio
    async def test_the_description_follows_an_id_set_on_the_group(self, context_args):
        # Built from the name, the hint's id would not be the one pointed at.
        html = await render_tree(
            _group().id("billing").hint("Where you pay tax."),
            context_args=context_args,
        )
        assert_attr(html, "fieldset", "aria-describedby", "billing-hint")
        assert_selector(html, "#billing-hint")

    @pytest.mark.asyncio
    async def test_a_description_of_the_callers_own_is_added(self, context_args):
        html = await render_tree(
            _group().hint("Where you pay tax.").aria_describedby("extra"),
            context_args=context_args,
        )
        assert_attr(html, "fieldset", "aria-describedby", "region-hint extra")

    @pytest.mark.asyncio
    async def test_x_model_binds_the_options(self, context_args):
        # Alpine ignores x-model on a fieldset, which holds no value.
        html = await render_tree(
            _group().x_model(unsafe("region")), context_args=context_args
        )
        assert_selector(html, 'input[type="radio"][x-model="region"]', count=2)
        assert_no_selector(html, "fieldset[x-model]")

    @pytest.mark.asyncio
    async def test_required_is_marked_on_the_options_and_the_legend(self, context_args):
        # A fieldset has no required attribute; one marked radio makes the
        # whole name required. The legend carries the same visible mark a
        # field's label does - the attribute alone showed nothing at all.
        html = await render_tree(_group().required(), context_args=context_args)
        assert_selector(html, "input[required]", count=2)
        assert_no_selector(html, "fieldset[required]")
        assert_selector(html, 'legend > span[aria-hidden="true"]')


class TestRadio:
    @pytest.mark.asyncio
    async def test_an_option_is_known_by_its_name_and_value(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_selector(html, 'input#region-eu[type="radio"]')
        assert_selector(html, 'label[for="region-eu"]')

    @pytest.mark.asyncio
    async def test_an_option_given_an_id_keeps_it(self, context_args):
        html = await render_tree(
            RadioGroup()
            .name("region")
            .content(Radio().value("eu").label("Europe").id("a-eu")),
            context_args=context_args,
        )
        assert_selector(html, 'input#a-eu[type="radio"]')
        assert_selector(html, 'label[for="a-eu"]')
        assert_attr(html, "input", "aria-labelledby", "a-eu-label")
        assert_no_selector(html, "#region-eu")

    @pytest.mark.asyncio
    async def test_options_take_their_ids_from_the_group(self, context_args):
        # So two groups sharing a name stay apart once one is given an id.
        html = await render_tree(
            RadioGroup("r").id("billing").content(Radio().value("a").label("A")),
            context_args=context_args,
        )
        assert_attr(html, "input", "id", "billing-a")

    @pytest.mark.asyncio
    async def test_an_option_is_named_by_its_label_alone(self, context_args):
        # The label wraps the control, so without this the description becomes
        # part of the option's name and is read out before "radio button".
        html = await render_tree(
            RadioGroup("r")
            .legend("Plan")
            .content(Radio().value("a").label("Solo").description("One seat.")),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-labelledby", "r-a-label")
        assert_attr(html, "input", "aria-describedby", "r-a-description")

    @pytest.mark.asyncio
    async def test_values_that_differ_only_in_spacing_get_ids_of_their_own(
        self, context_args
    ):
        # Folding whitespace into a hyphen gave these one id between them,
        # so the second label toggled the first; and an aria-labelledby
        # built from "r-north america" would name two ids.
        values = ("north america", "north-america", "a b", "a  b")
        html = await render_tree(
            RadioGroup("r").content(*(Radio().value(v).label(v) for v in values)),
            context_args=context_args,
        )
        inputs = select(html, "input[type=radio]")
        assert len({tag["id"] for tag in inputs}) == len(values)
        assert inputs[0]["aria-labelledby"] == "r-north%20america-label"

    @pytest.mark.asyncio
    async def test_a_callers_describedby_survives(self, context_args):
        html = await render_tree(
            RadioGroup("r").content(
                Radio().value("a").label("A").aria_describedby("note"),
                Radio()
                .value("b")
                .label("B")
                .description("Second.")
                .aria_describedby("note"),
            ),
            context_args=context_args,
        )
        assert_attr(html, "input#r-a", "aria-describedby", "note")
        assert_attr(html, "input#r-b", "aria-describedby", "r-b-description note")
