import pytest

from hue.renderer import render_tree
from hue.ui import Button, Dialog
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _dialog():
    return (
        Dialog()
        .title("Invite teammates")
        .description("They will get a join link.")
        .trigger(Button().content("Invite"))
    )


class TestDialog:
    @pytest.mark.asyncio
    async def test_the_trigger_opens_it_and_says_so(self, context_args):
        # Without this the dialog renders and nothing can ever show it.
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, "button", "@click", "open = true")
        assert_attr(html, "button", "aria-haspopup", "dialog")
        assert_attr(html, "button", ":aria-expanded", "open")

    @pytest.mark.asyncio
    async def test_it_is_modal_and_named_by_its_title(self, context_args):
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, '[role="dialog"]', "aria-modal", "true")
        assert_attr(html, '[role="dialog"]', ":aria-labelledby")

    @pytest.mark.asyncio
    async def test_focus_is_trapped_and_the_page_behind_is_inert(self, context_args):
        # inert takes the page out of the tab order, noscroll stops it moving
        # under the scrim, and the trap returns focus to whatever opened it.
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, '[role="dialog"]', "x-trap.inert.noscroll", "open")

    # destructive(): both branches
    @pytest.mark.asyncio
    async def test_destructive_is_an_alertdialog_that_reads_its_description(
        self, context_args
    ):
        html = await render_tree(_dialog().destructive(), context_args=context_args)
        assert_selector(html, '[role="alertdialog"]')
        assert_attr(html, '[role="alertdialog"]', ":aria-describedby")

    @pytest.mark.asyncio
    async def test_an_ordinary_dialog_leaves_the_description_to_be_read(
        self, context_args
    ):
        # Announced with the title it would be said before the reader has any
        # use for it; in order, it arrives where it belongs.
        html = await render_tree(_dialog(), context_args=context_args)
        assert_selector(html, '[role="dialog"]')
        assert_no_selector(html, "[\\:aria-describedby]")

    # dismissible(): both branches
    @pytest.mark.asyncio
    async def test_dismissible_by_default(self, context_args):
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, 'button[aria-label="Close"]', "aria-label", "Close")
        assert_selector(html, "[x-on\\:click\\.self]")

    @pytest.mark.asyncio
    async def test_undismissible_keeps_escape(self, context_args):
        # A modal with no way out is a trap, whatever the question was.
        html = await render_tree(
            _dialog().dismissible(False), context_args=context_args
        )
        assert_no_selector(html, 'button[aria-label="Close"]')
        assert_no_selector(html, "[x-on\\:click\\.self]")
        assert_attr(html, "[x-data]", "x-on:keydown.escape.window", "open = false")

    # open(): both branches
    @pytest.mark.asyncio
    async def test_it_starts_closed(self, context_args):
        html = await render_tree(_dialog(), context_args=context_args)
        assert_attr(html, "[x-data]", "x-data", "{ open: false }")

    @pytest.mark.asyncio
    async def test_the_server_can_start_it_open(self, context_args):
        html = await render_tree(_dialog().open(), context_args=context_args)
        assert_attr(html, "[x-data]", "x-data", "{ open: true }")

    @pytest.mark.asyncio
    async def test_the_body_scrolls_rather_than_pushing_the_footer_out(
        self, context_args
    ):
        html = await render_tree(
            _dialog().content("a lot of text").footer("ok"),
            context_args=context_args,
        )
        assert_selector(html, "div.min-h-0.overflow-y-auto")
