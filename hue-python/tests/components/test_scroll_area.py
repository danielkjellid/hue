import pytest

from hue.renderer import render_tree
from hue.ui import ScrollArea
from tests._a11y import assert_attr, assert_selector


class TestScrollArea:
    @pytest.mark.asyncio
    async def test_the_keyboard_can_reach_it_and_is_told_what_it_reached(
        self, context_args
    ):
        # WCAG 2.1.1 covers scrolling: without a tab stop there is no way to
        # scroll this with a keyboard, and without a name the stop is one
        # nobody can account for.
        html = await render_tree(
            ScrollArea().label("Time zones").content("Oslo"),
            context_args=context_args,
        )
        assert_attr(html, "div", "tabindex", "0")
        assert_attr(html, "div", "role", "region")
        assert_attr(html, "div", "aria-label", "Time zones")

    @pytest.mark.parametrize("label", [None, "", "  "])
    @pytest.mark.asyncio
    async def test_it_refuses_to_render_without_a_label(self, context_args, label):
        area = ScrollArea().content("Oslo")
        if label is not None:
            area.label(label)
        with pytest.raises(ValueError, match="label"):
            await render_tree(area, context_args=context_args)

    @pytest.mark.asyncio
    async def test_the_scroll_stays_inside_it(self, context_args):
        # Scrolling a list to its end should not carry on into the page
        # behind it, which is what overscroll-contain stops.
        html = await render_tree(
            ScrollArea().label("Time zones").content("Oslo"),
            context_args=context_args,
        )
        assert_selector(html, "div.overflow-auto.overscroll-contain")

    @pytest.mark.asyncio
    async def test_a_faded_edge_knows_which_way_there_is_more(self, context_args):
        html = await render_tree(
            ScrollArea().label("Release notes").fade().content("4.2.0"),
            context_args=context_args,
        )
        assert_attr(html, "div", "x-data", "hueScrollArea()")
        assert_attr(html, "div", ":data-scroll-above", "above || null")
        assert_attr(html, "div", ":data-scroll-below", "below || null")

    # A faded area's x-data is hue's own, so a caller's would replace it or
    # be replaced: both branches.
    @pytest.mark.asyncio
    async def test_a_faded_area_refuses_a_scope_of_its_own(self, context_args):
        area = ScrollArea().label("Release notes").fade().x_data("{n: 1}")
        with pytest.raises(ValueError, match="x_data"):
            await render_tree(area, context_args=context_args)

    @pytest.mark.asyncio
    async def test_an_unfaded_area_keeps_a_callers_scope(self, context_args):
        html = await render_tree(
            ScrollArea().label("Release notes").x_data("{n: 1}").content("4.2.0"),
            context_args=context_args,
        )
        assert_attr(html, "div", "x-data", "{n: 1}")
