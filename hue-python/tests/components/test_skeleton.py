import pytest

from hue.renderer import render_tree
from hue.ui import Skeleton
from tests._a11y import assert_attr, assert_selector


class TestSkeleton:
    @pytest.mark.asyncio
    async def test_decorative_and_animated(self, context_args):
        """A skeleton is decorative (aria-hidden) and pulses, with motion-reduce."""
        html = await render_tree(Skeleton(), context_args=context_args)
        assert_attr(html, "div", "aria-hidden", "true")
        assert "animate-pulse" in html
        assert "motion-reduce:animate-none" in html

    @pytest.mark.asyncio
    async def test_line_shape(self, context_args):
        html = await render_tree(Skeleton().shape("line"), context_args=context_args)
        assert "rounded-md" in html and "h-4" in html

    @pytest.mark.asyncio
    async def test_circle_shape(self, context_args):
        html = await render_tree(Skeleton().shape("circle"), context_args=context_args)
        assert "rounded-full" in html and "size-10" in html

    @pytest.mark.asyncio
    async def test_rect_shape(self, context_args):
        html = await render_tree(Skeleton().shape("rect"), context_args=context_args)
        assert "rounded-lg" in html and "h-24" in html

    @pytest.mark.asyncio
    async def test_dimension_overrides(self, context_args):
        html = await render_tree(
            Skeleton().width("w-32").height("h-8").rounded("rounded-xl"),
            context_args=context_args,
        )
        assert "w-32" in html and "h-8" in html and "rounded-xl" in html
        # The default line width/height are replaced, not appended.
        assert "w-full" not in html and "h-4" not in html

    @pytest.mark.asyncio
    async def test_single_line_renders_one_bar(self, context_args):
        """lines == 1: a single bar, no stacking wrapper."""
        html = await render_tree(Skeleton().lines(1), context_args=context_args)
        assert_selector(html, "div", count=1)

    @pytest.mark.asyncio
    async def test_multiple_lines_stack_and_taper(self, context_args):
        """lines > 1: a column of bars whose last line is shortened."""
        html = await render_tree(Skeleton().lines(3), context_args=context_args)
        assert "flex flex-col gap-2" in html
        # Three bars inside the stacking wrapper.
        assert_selector(html, "div.flex.flex-col.gap-2 > div", count=3)
        # The last line is tapered to read as the end of a paragraph.
        assert "w-3/4" in html

    @pytest.mark.asyncio
    async def test_multiple_lines_honour_class_and_width(self, context_args):
        """
        The stacking branch respects the shared modifiers too.

        It builds its own wrapper class list, so .class_() and .width() have to
        be threaded through explicitly — they were previously dropped here while
        the single-shape branch honoured them.
        """
        html = await render_tree(
            Skeleton().lines(2).width("w-32").class_("mt-4"),
            context_args=context_args,
        )
        assert_selector(html, "div.flex.flex-col.mt-4.w-32")
        # width sizes the paragraph block; the bars fill it.
        assert_selector(html, "div.flex.flex-col > div.w-full", count=1)

    @pytest.mark.asyncio
    async def test_single_line_honours_class(self, context_args):
        html = await render_tree(Skeleton().class_("mt-4"), context_args=context_args)
        assert_selector(html, "div.animate-pulse.mt-4")

    @pytest.mark.asyncio
    async def test_unknown_shape_falls_back_to_a_line(self, context_args):
        """Shape is a typed Literal, but an untyped caller gets a shape, not a crash."""
        html = await render_tree(
            Skeleton().shape("blob"),  # type: ignore[arg-type]
            context_args=context_args,
        )
        assert "h-4" in html and "rounded-md" in html
