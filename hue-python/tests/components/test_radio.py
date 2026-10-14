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

    # value(): both branches
    # form(): both branches
    @pytest.mark.asyncio
    async def test_a_form_the_group_is_outside_reaches_every_option(self, context_args):
        # The radios are what the form submits; a form attribute on the
        # fieldset alone would tie only the fieldset to it.
        html = await render_tree(_group().form("settings"), context_args=context_args)
        assert_selector(html, 'input[type=radio][form="settings"]', count=2)
        assert_no_selector(html, "fieldset[form]")

    @pytest.mark.asyncio
    async def test_options_belong_to_no_other_form_by_default(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, "input[form]")

    @pytest.mark.asyncio
    async def test_the_named_option_starts_checked(self, context_args):
        html = await render_tree(_group().value("us"), context_args=context_args)
        assert_attr(html, 'input[value="us"]', "checked")
        assert_no_selector(html, 'input[value="eu"][checked]')

    @pytest.mark.asyncio
    async def test_nothing_checked_by_default(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, "input[checked]")

    # disabled(): the group's answer reaches every option
    @pytest.mark.asyncio
    async def test_disabling_the_group_disables_the_options(self, context_args):
        html = await render_tree(_group().disabled(), context_args=context_args)
        assert_selector(html, "input[disabled]", count=2)

    @pytest.mark.asyncio
    async def test_an_option_can_be_disabled_on_its_own(self, context_args):
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

    # variant(): both branches, and it reaches the options
    @pytest.mark.asyncio
    async def test_cards_react_to_their_own_control(self, context_args):
        html = await render_tree(_group().card(), context_args=context_args)
        assert_selector(html, "label.has-\\[\\:checked\\]\\:bg-accent-subtle", count=2)

    @pytest.mark.asyncio
    async def test_inline_by_default(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, "label.p-4")

    # error(): both branches
    @pytest.mark.asyncio
    async def test_an_error_is_announced_and_describes_the_group(self, context_args):
        html = await render_tree(
            _group().error("Pick a region."), context_args=context_args
        )
        assert_attr(html, "fieldset", "aria-invalid", "true")
        assert_attr(html, "fieldset", "aria-describedby", "region-error")
        assert_selector(html, '[role="alert"]#region-error')

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
    async def test_valid_by_default(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, "[aria-invalid]")

    # legend(): both branches
    @pytest.mark.asyncio
    async def test_no_legend_renders_no_empty_one(self, context_args):
        html = await render_tree(
            RadioGroup("r").content(Radio().value("a").label("A")),
            context_args=context_args,
        )
        assert_no_selector(html, "legend")


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
        assert_no_selector(html, "#region-eu")

    @pytest.mark.asyncio
    async def test_a_description_sits_under_the_label(self, context_args):
        html = await render_tree(
            RadioGroup("r")
            .legend("R")
            .content(Radio().value("a").label("A").description("The first one.")),
            context_args=context_args,
        )
        assert_selector(html, "span.text-fg-muted")

    @pytest.mark.asyncio
    async def test_the_whole_row_is_the_hit_area(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_selector(html, 'label > input[type="radio"]', count=2)

    @pytest.mark.asyncio
    async def test_required_is_marked_on_the_options(self, context_args):
        # A fieldset has no required attribute; one marked radio makes the
        # whole name required.
        html = await render_tree(
            RadioGroup("r")
            .legend("R")
            .required()
            .content(Radio().value("a").label("A"), Radio().value("b").label("B")),
            context_args=context_args,
        )
        assert_selector(html, "input[required]", count=2)
        assert_no_selector(html, "fieldset[required]")

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
    async def test_an_id_holds_no_whitespace(self, context_args):
        # An aria-labelledby built from "r-north america" would name two ids.
        html = await render_tree(
            RadioGroup("r").content(Radio().value("north america").label("NA")),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-labelledby", "r-north%20america-label")

    @pytest.mark.asyncio
    async def test_values_that_differ_only_in_spacing_get_ids_of_their_own(
        self, context_args
    ):
        # Folding whitespace into a hyphen gave these one id between them,
        # so the second label toggled the first.
        values = ("north america", "north-america", "a b", "a  b")
        html = await render_tree(
            RadioGroup("r").content(*(Radio().value(v).label(v) for v in values)),
            context_args=context_args,
        )
        ids = {tag["id"] for tag in select(html, "input[type=radio]")}
        assert len(ids) == len(values)

    @pytest.mark.asyncio
    async def test_a_callers_describedby_survives_without_a_description(
        self, context_args
    ):
        html = await render_tree(
            RadioGroup("r").content(
                Radio().value("a").label("A").aria_describedby("note")
            ),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-describedby", "note")

    @pytest.mark.asyncio
    async def test_a_callers_describedby_joins_the_description(self, context_args):
        html = await render_tree(
            RadioGroup("r").content(
                Radio()
                .value("a")
                .label("A")
                .description("First.")
                .aria_describedby("note")
            ),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-describedby", "r-a-description note")

    @pytest.mark.asyncio
    async def test_options_take_their_ids_from_the_group(self, context_args):
        # So two groups sharing a name stay apart once one is given an id.
        html = await render_tree(
            RadioGroup("r").id("billing").content(Radio().value("a").label("A")),
            context_args=context_args,
        )
        assert_attr(html, "input", "id", "billing-a")

    @pytest.mark.asyncio
    async def test_an_option_keeps_an_id_of_its_own(self, context_args):
        html = await render_tree(
            RadioGroup("r").content(Radio().value("a").label("A").id("own")),
            context_args=context_args,
        )
        assert_attr(html, "input", "id", "own")
        assert_attr(html, "input", "aria-labelledby", "own-label")

    @pytest.mark.asyncio
    async def test_the_group_keeps_a_hint(self, context_args):
        # Group-level, unlike an option's description: it is about the
        # question, not about one of the answers.
        html = await render_tree(
            RadioGroup("r")
            .legend("Plan")
            .hint("Change any time.")
            .content(Radio().value("a").label("Solo")),
            context_args=context_args,
        )
        assert_attr(html, "fieldset", "aria-describedby", "r-hint")

    # required(): both branches, visible as well as announced
    @pytest.mark.asyncio
    async def test_a_required_group_is_marked_on_its_legend(self, context_args):
        # The legend is the group's label, so it carries the same mark a
        # field's label does - the attribute alone showed nothing at all.
        html = await render_tree(_group().required(), context_args=context_args)
        assert_selector(html, 'legend > span[aria-hidden="true"]')

    @pytest.mark.asyncio
    async def test_an_optional_group_is_not_marked(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, 'legend > span[aria-hidden="true"]')

    @pytest.mark.asyncio
    async def test_the_legend_carries_the_gap_the_fieldset_cannot(self, context_args):
        # A legend is not a flex item of its fieldset, so the gap that spaces
        # every other child never reaches it and the first option sits flush
        # against the question.
        html = await render_tree(_group(), context_args=context_args)
        assert_selector(html, "legend.mb-1\\.5")
