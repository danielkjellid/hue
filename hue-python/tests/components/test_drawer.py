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
        assert_attr(html, "button[aria-haspopup]", "x-on:click", "open = true")
        assert_attr(html, "button[aria-haspopup]", "x-bind:aria-expanded", "open")

    @pytest.mark.asyncio
    async def test_it_is_a_modal_aside_named_by_its_title(self, context_args):
        html = await render_tree(_drawer(), context_args=context_args)
        assert_selector(html, 'aside[role="dialog"]')
        assert_attr(html, "aside", "aria-modal", "true")
        assert_attr(html, "aside", ":aria-labelledby")

    @pytest.mark.asyncio
    async def test_without_a_title_the_label_names_it(self, context_args):
        drawer = Drawer().label("Filters").content("Status")
        html = await render_tree(drawer, context_args=context_args)
        assert_attr(html, "aside", "aria-label", "Filters")
        assert_no_selector(html, "[\\:aria-labelledby]")

    @pytest.mark.asyncio
    async def test_a_drawer_with_no_name_is_refused(self, context_args):
        with pytest.raises(ValueError, match="needs an accessible name"):
            await render_tree(Drawer().content("?"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_focus_is_trapped_and_the_page_behind_is_inert(self, context_args):
        html = await render_tree(_drawer(), context_args=context_args)
        assert_attr(html, "aside", "x-trap.inert.noscroll", "open")

    @pytest.mark.asyncio
    async def test_undismissible_keeps_escape(self, context_args):
        html = await render_tree(
            _drawer().dismissible(False), context_args=context_args
        )
        assert_no_selector(html, 'button[aria-label="Close"]')
        assert_no_selector(html, "[x-on\\:click\\.self]")
        # On the overlay and stopped there, so a popover inside closes on
        # its own and a page-wide Escape behind it hears nothing.
        assert_attr(
            html,
            "[x-data]",
            "x-on:keydown.escape",
            "if (open) { $event.stopPropagation(); close() }",
        )
        # The scrim takes a click's focus, so Escape still reaches it after
        # a click on the panel's text or beside it.
        assert_attr(html, "[x-show]", "tabindex", "-1")

    @pytest.mark.asyncio
    async def test_the_server_can_start_it_open(self, context_args):
        html = await render_tree(_drawer().open(), context_args=context_args)
        assert "open: true" in str(html)
