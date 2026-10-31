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
        html = await render_tree(Skeleton().lines(2), context_args=context_args)
        assert_selector(html, "[aria-hidden]", count=1)

    # The box has to match what is loading, or the page jumps on arrival. Each
    # axis replaces the shape's own rather than layering over it, since two
    # width utilities resolve by stylesheet order and not by intent.
    @pytest.mark.parametrize(
        ("skeleton", "kept", "replaced"),
        [
            (Skeleton().shape("rect").width("w-1/2"), "w-1\\/2", "w-full"),
            (Skeleton().shape("card").height("h-20"), "h-20", "h-32"),
            (
                Skeleton().shape("circle").width("w-16").height("h-16"),
                "h-16.w-16",
                "h-9",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_a_size_replaces_the_shapes_own(
        self, context_args, skeleton, kept, replaced
    ):
        html = await render_tree(skeleton, context_args=context_args)
        assert_selector(html, f"div.{kept}")
        assert_no_selector(html, f"div.{replaced}")

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
