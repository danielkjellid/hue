import pytest

from hue.renderer import render_tree
from hue.ui import Radio, RadioGroup
from tests._a11y import assert_attr, assert_no_selector, assert_selector


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
        html = await render_tree(_group().variant("card"), context_args=context_args)
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
