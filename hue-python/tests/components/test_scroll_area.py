import pytest

from hue.renderer import render_tree
from hue.ui import ScrollArea
from tests._a11y import assert_attr, assert_no_selector, assert_selector


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

    @pytest.mark.asyncio
    async def test_it_refuses_to_render_without_a_label(self, context_args):
        with pytest.raises(ValueError, match="label"):
            await render_tree(ScrollArea().content("Oslo"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_the_scroll_stays_inside_it(self, context_args):
        # Scrolling a list to its end should not carry on into the page
        # behind it, which is what overscroll-contain stops.
        html = await render_tree(
            ScrollArea().label("Time zones").content("Oslo"),
            context_args=context_args,
        )
        assert_selector(html, "div.overflow-auto.overscroll-contain.scrollbar-thin")

    @pytest.mark.asyncio
    async def test_max_height_is_where_it_starts_scrolling(self, context_args):
        html = await render_tree(
            ScrollArea().label("Time zones").max_height("max-h-64").content("Oslo"),
            context_args=context_args,
        )
        assert_selector(html, "div.max-h-64")

    # fade(): both branches
    @pytest.mark.asyncio
    async def test_a_faded_edge_knows_which_way_there_is_more(self, context_args):
        html = await render_tree(
            ScrollArea().label("Release notes").fade().content("4.2.0"),
            context_args=context_args,
        )
        assert_selector(html, "div.scroll-fade")
        assert_attr(html, "div", "x-data", "hueScrollArea()")
        assert_attr(html, "div", ":data-scroll-above", "above || null")
        assert_attr(html, "div", ":data-scroll-below", "below || null")

    @pytest.mark.asyncio
    async def test_without_the_fade_there_is_nothing_to_watch(self, context_args):
        html = await render_tree(
            ScrollArea().label("Release notes").content("4.2.0"),
            context_args=context_args,
        )
        assert_no_selector(html, ".scroll-fade")
        assert_no_selector(html, "[x-data]")
