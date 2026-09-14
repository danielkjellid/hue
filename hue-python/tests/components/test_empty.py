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

    # Every slot is optional and has to be absent cleanly.
    @pytest.mark.asyncio
    async def test_icon_is_optional(self, context_args):
        with_icon = await render_tree(
            Empty().icon("!").title("Nothing"), context_args=context_args
        )
        assert_selector(with_icon, "span.size-12")

        without = await render_tree(Empty().title("Nothing"), context_args=context_args)
        assert_no_selector(without, "span.size-12")

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

    # variant(): only the icon chip changes tone
    @pytest.mark.asyncio
    async def test_neutral_by_default(self, context_args):
        html = await render_tree(
            Empty().icon("!").title("Nothing"), context_args=context_args
        )
        assert_selector(html, "span.bg-surface-sunken")

    @pytest.mark.asyncio
    async def test_danger_tints_the_icon(self, context_args):
        html = await render_tree(
            Empty().variant("danger").icon("!").title("Could not load"),
            context_args=context_args,
        )
        assert_selector(html, "span.bg-danger-subtle")
        assert_no_selector(html, "span.bg-surface-sunken")

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
    async def test_compact(self, context_args):
        html = await render_tree(
            Empty().compact().title("Nothing"), context_args=context_args
        )
        assert_selector(html, "div.py-8")
        assert_no_selector(html, "div.py-12")
