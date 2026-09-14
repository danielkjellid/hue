import pytest

from hue.renderer import render_tree
from hue.ui import Skeleton
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestSkeleton:
    @pytest.mark.asyncio
    async def test_is_hidden_from_assistive_tech(self, context_args):
        # Placeholders are decoration; narrating a dozen empty boxes is noise.
        # aria-busy belongs on the region they stand in for.
        html = await render_tree(Skeleton(), context_args=context_args)
        assert_attr(html, "div", "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_shimmers(self, context_args):
        html = await render_tree(Skeleton(), context_args=context_args)
        assert_selector(html, "div.animate-shimmer")

    @pytest.mark.asyncio
    async def test_is_visible_against_the_canvas(self, context_args):
        # The guide's sunken-to-active pair is gray-50 sweeping to gray-100, a
        # 3% difference against white - invisible on the surface a skeleton
        # most often sits on.
        html = await render_tree(Skeleton(), context_args=context_args)
        assert_selector(html, "div.from-surface-active")
        assert_no_selector(html, "div.from-surface-sunken")

    # shape(): default vs an explicit shape, each carrying its own box
    @pytest.mark.asyncio
    async def test_default_shape_is_a_line(self, context_args):
        html = await render_tree(Skeleton(), context_args=context_args)
        assert_selector(html, "div.h-3.w-full")

    @pytest.mark.asyncio
    async def test_circle_shape_is_square_and_round(self, context_args):
        html = await render_tree(Skeleton().shape("circle"), context_args=context_args)
        assert_selector(html, "div.size-9.rounded-full")

    @pytest.mark.asyncio
    async def test_size_can_be_overridden_to_match_real_content(self, context_args):
        # The box has to match what is loading, or the page jumps on arrival.
        html = await render_tree(
            Skeleton().shape("circle").class_("size-16"), context_args=context_args
        )
        assert_selector(html, "div.size-16")

    # lines(): both branches
    @pytest.mark.asyncio
    async def test_single_bar_by_default(self, context_args):
        html = await render_tree(Skeleton(), context_args=context_args)
        assert_selector(html, "div", count=1)
        assert_no_selector(html, "div > div")

    @pytest.mark.asyncio
    async def test_several_lines_stack_with_a_short_last_one(self, context_args):
        # A paragraph does not end flush with the margin.
        html = await render_tree(
            Skeleton().shape("text").lines(3), context_args=context_args
        )
        assert_selector(html, "div.flex.flex-col > div", count=3)
        # The bars are percentage-width, which resolves to nothing against a
        # wrapper sized by its own content, so the stack collapsed in a flex row.
        assert_selector(html, "div.w-full.flex-col")
        assert_selector(html, "div > div.w-\\[62\\%\\]", count=1)

    @pytest.mark.asyncio
    async def test_one_line_does_not_get_the_short_width(self, context_args):
        html = await render_tree(
            Skeleton().shape("text").lines(1), context_args=context_args
        )
        assert_no_selector(html, "div.w-\\[62\\%\\]")

    @pytest.mark.asyncio
    async def test_only_the_wrapper_is_hidden_once(self, context_args):
        html = await render_tree(Skeleton().lines(2), context_args=context_args)
        assert_selector(html, "[aria-hidden]", count=1)
