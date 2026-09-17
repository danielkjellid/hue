import pytest

from hue.renderer import render_tree
from hue.ui import Button, Drawer
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _drawer():
    return (
        Drawer()
        .title("Filters")
        .description("3 filters applied")
        .trigger(Button().variant("outline").content("Open filters"))
    )


class TestDrawer:
    @pytest.mark.asyncio
    async def test_the_trigger_opens_it_and_says_so(self, context_args):
        html = await render_tree(_drawer(), context_args=context_args)
        assert_attr(html, "button[aria-haspopup]", "@click", "open = true")
        assert_attr(html, "button[aria-haspopup]", ":aria-expanded", "open")

    @pytest.mark.asyncio
    async def test_it_is_a_modal_aside_named_by_its_title(self, context_args):
        html = await render_tree(_drawer(), context_args=context_args)
        assert_selector(html, 'aside[role="dialog"]')
        assert_attr(html, "aside", "aria-modal", "true")
        assert_attr(html, "aside", ":aria-labelledby")

    @pytest.mark.asyncio
    async def test_focus_is_trapped_and_the_page_behind_is_inert(self, context_args):
        html = await render_tree(_drawer(), context_args=context_args)
        assert_attr(html, "aside", "x-trap.inert.noscroll", "open")

    # side(): the sheet is the shared base, the edges are what md adds
    @pytest.mark.asyncio
    async def test_a_side_drawer_is_a_sheet_until_md(self, context_args):
        # A 420px panel on a 375px screen is a dialog with a worse animation.
        html = await render_tree(_drawer(), context_args=context_args)
        assert_selector(html, "aside.animate-sheet-in.md\\:animate-drawer-end")
        assert_selector(html, "div.md\\:justify-end")

    @pytest.mark.asyncio
    async def test_the_other_edge_arrives_from_the_other_side(self, context_args):
        html = await render_tree(_drawer().side("start"), context_args=context_args)
        assert_selector(html, "aside.md\\:animate-drawer-start")

    @pytest.mark.asyncio
    async def test_a_bottom_drawer_stays_a_sheet_at_every_width(self, context_args):
        html = await render_tree(_drawer().side("bottom"), context_args=context_args)
        assert_no_selector(html, "aside[class*='md:']")
        # And keeps its grabber, where a side drawer loses it at md.
        assert_selector(html, "aside > div.bg-border-strong")
        assert_no_selector(html, "div.bg-border-strong.md\\:hidden")

    # dismissible(): both branches
    @pytest.mark.asyncio
    async def test_dismissible_by_default(self, context_args):
        html = await render_tree(_drawer(), context_args=context_args)
        assert_selector(html, 'button[aria-label="Close"]')
        assert_selector(html, "[x-on\\:click\\.self]")

    @pytest.mark.asyncio
    async def test_undismissible_keeps_escape(self, context_args):
        html = await render_tree(
            _drawer().dismissible(False), context_args=context_args
        )
        assert_no_selector(html, 'button[aria-label="Close"]')
        assert_no_selector(html, "[x-on\\:click\\.self]")
        assert_attr(html, "[x-data]", "x-on:keydown.escape.window", "close()")

    # open(): both branches
    @pytest.mark.asyncio
    async def test_it_starts_closed(self, context_args):
        html = await render_tree(_drawer(), context_args=context_args)
        assert "open: false" in str(html)

    @pytest.mark.asyncio
    async def test_the_server_can_start_it_open(self, context_args):
        html = await render_tree(_drawer().open(), context_args=context_args)
        assert "open: true" in str(html)

    # size(): only a side drawer has a width
    @pytest.mark.asyncio
    async def test_a_side_drawer_takes_its_width_from_the_size(self, context_args):
        html = await render_tree(_drawer().size("lg"), context_args=context_args)
        assert_selector(html, "aside[class*='md:w-[min(560px']")

    @pytest.mark.asyncio
    async def test_a_bottom_sheet_is_the_width_of_the_screen(self, context_args):
        html = await render_tree(
            _drawer().side("bottom").size("lg"), context_args=context_args
        )
        assert_no_selector(html, "aside[class*='560px']")
