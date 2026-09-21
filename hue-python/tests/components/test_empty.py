import pytest

from hue.renderer import render_tree
from hue.ui import Empty
from tests._a11y import assert_no_selector, assert_selector


class TestEmpty:
    @pytest.mark.asyncio
    async def test_renders_title_and_description(self, context_args):
        html = await render_tree(
            Empty().title("No invoices yet").description("They appear here."),
            context_args=context_args,
        )
        assert "No invoices yet" in html
        assert "They appear here." in html

    @pytest.mark.asyncio
    async def test_description_is_measured_in_characters(self, context_args):
        # A description running the full width of a table is not centred copy.
        html = await render_tree(
            Empty().description("Try clearing the filter."),
            context_args=context_args,
        )
        assert_selector(html, "p.max-w-\\[42ch\\]")

    # icon(): the variant's own, one of your own, or none at all
    @pytest.mark.asyncio
    async def test_every_variant_brings_its_own_icon(self, context_args):
        # The variant tints the icon chip and nothing else, so without an
        # icon there is nothing for it to be: variant("danger") would render
        # exactly what neutral does.
        neutral = await render_tree(Empty().title("Nothing"), context_args=context_args)
        danger = await render_tree(
            Empty().variant("danger").title("Could not load"),
            context_args=context_args,
        )
        assert "inbox" in neutral
        assert_selector(neutral, "span.bg-surface-sunken")
        assert "circle-x" in danger
        assert_selector(danger, "span.bg-danger-subtle")

    @pytest.mark.asyncio
    async def test_an_icon_of_your_own_replaces_it(self, context_args):
        html = await render_tree(
            Empty().icon("!").title("Nothing"), context_args=context_args
        )
        assert_selector(html, "span.size-12")
        assert "inbox" not in html

    @pytest.mark.asyncio
    async def test_none_means_no_icon(self, context_args):
        html = await render_tree(
            Empty().icon(None).title("Nothing"), context_args=context_args
        )
        assert_no_selector(html, "span.size-12")
        assert "inbox" not in html

    @pytest.mark.asyncio
    async def test_actions_are_optional(self, context_args):
        with_actions = await render_tree(
            Empty().title("Nothing").actions("retry"), context_args=context_args
        )
        assert_selector(with_actions, "div.mt-4")

        without = await render_tree(Empty().title("Nothing"), context_args=context_args)
        assert_no_selector(without, "div.mt-4")

    @pytest.mark.asyncio
    async def test_title_is_optional(self, context_args):
        html = await render_tree(
            Empty().description("Only a description."), context_args=context_args
        )
        assert_no_selector(html, "div.font-bold")

    # title(heading=...): both branches
    @pytest.mark.asyncio
    async def test_title_is_not_a_heading_by_default(self, context_args):
        # Inside a table cell a heading would land wrongly in the outline.
        html = await render_tree(Empty().title("Nothing"), context_args=context_args)
        assert_no_selector(html, "h1, h2, h3, h4, h5, h6")

    @pytest.mark.asyncio
    async def test_title_can_be_promoted_to_a_heading(self, context_args):
        html = await render_tree(
            Empty().title("Nothing here yet", heading="h2"),
            context_args=context_args,
        )
        assert_selector(html, "h2")

    # compact(): both branches
    @pytest.mark.asyncio
    async def test_roomy_by_default(self, context_args):
        html = await render_tree(Empty().title("Nothing"), context_args=context_args)
        assert_selector(html, "div.py-12")

    @pytest.mark.asyncio
    async def test_compact_shrinks_the_icon_with_the_padding(self, context_args):
        # An empty state inside a table is short on room in both directions.
        html = await render_tree(
            Empty().compact().title("Nothing"), context_args=context_args
        )
        assert_selector(html, "span.size-9")
        assert_no_selector(html, "span.size-12")

    @pytest.mark.asyncio
    async def test_compact(self, context_args):
        html = await render_tree(
            Empty().compact().title("Nothing"), context_args=context_args
        )
        assert_selector(html, "div.py-8")
        assert_no_selector(html, "div.py-12")
