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
    async def test_default_shape_is_text(self, context_args):
        html = await render_tree(Skeleton(), context_args=context_args)
        assert_selector(html, "div.h-3\\.5.w-full")

    @pytest.mark.asyncio
    async def test_circle_shape_is_square_and_round(self, context_args):
        html = await render_tree(Skeleton().shape("circle"), context_args=context_args)
        assert_selector(html, "div.h-9.w-9.rounded-full")

    # The box has to match what is loading, or the page jumps on arrival. Each
    # axis replaces the shape's own rather than layering over it, since two
    # width utilities resolve by stylesheet order and not by intent.
    @pytest.mark.asyncio
    async def test_width_replaces_the_shape_width(self, context_args):
        html = await render_tree(
            Skeleton().shape("rect").width("w-1/2"), context_args=context_args
        )
        assert_selector(html, "div.w-1\\/2")
        assert_no_selector(html, "div.w-full")

    @pytest.mark.asyncio
    async def test_height_replaces_the_shape_height(self, context_args):
        html = await render_tree(
            Skeleton().shape("card").height("h-20"), context_args=context_args
        )
        assert_selector(html, "div.h-20")
        assert_no_selector(html, "div.h-32")

    @pytest.mark.asyncio
    async def test_both_axes_on_a_circle(self, context_args):
        html = await render_tree(
            Skeleton().shape("circle").width("w-16").height("h-16"),
            context_args=context_args,
        )
        assert_selector(html, "div.h-16.w-16")
        assert_no_selector(html, "div.h-9")

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

    # lines() is text-only: three circles on top of each other stand in for
    # nothing, and silently ignoring the call would hide the mistake.
    @pytest.mark.parametrize("shape", ["circle", "rect", "card"])
    @pytest.mark.asyncio
    async def test_lines_is_rejected_for_shapes_that_are_single_things(
        self, shape, context_args
    ):
        with pytest.raises(ValueError, match="does not apply"):
            await render_tree(
                Skeleton().shape(shape).lines(3), context_args=context_args
            )

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
