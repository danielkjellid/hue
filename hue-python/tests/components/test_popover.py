import pytest

from hue.renderer import render_tree
from hue.ui import Button, Popover
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _popover():
    return (
        Popover()
        .title("Share Route planner")
        .trigger(Button().variant("outline").content("Share project"))
    )


class TestPopover:
    @pytest.mark.asyncio
    async def test_the_trigger_toggles_it_and_says_so(self, context_args):
        html = await render_tree(_popover(), context_args=context_args)
        assert_attr(html, "button", "@click", "open = !open")
        assert_attr(html, "button", "aria-haspopup", "dialog")
        assert_attr(html, "button", ":aria-expanded", "open")
        assert_attr(html, "button", ":aria-controls", "$id('hue-popover')")

    @pytest.mark.asyncio
    async def test_it_is_not_modal(self, context_args):
        # The page behind stays live, so a form in a popover is a form on the
        # page: nothing is trapped and nothing is made inert.
        html = await render_tree(_popover(), context_args=context_args)
        assert_selector(html, '[role="dialog"]')
        assert_no_selector(html, "[x-trap]")

    @pytest.mark.asyncio
    async def test_escape_closes_it_and_hands_focus_back(self, context_args):
        # A click outside must not, because focus is wherever that click went.
        html = await render_tree(_popover(), context_args=context_args)
        assert_attr(html, "[x-data]", "x-on:keydown.escape.window", "if (open) close()")
        assert_attr(html, "[x-data]", "x-on:click.outside", "open = false")

    @pytest.mark.asyncio
    async def test_it_hangs_off_the_trigger(self, context_args):
        html = await render_tree(
            _popover().placement("top-end"), context_args=context_args
        )
        assert_attr(
            html, '[role="dialog"]', "x-anchor.top-end.offset.6", "$refs.trigger"
        )

    # title(): both branches
    @pytest.mark.asyncio
    async def test_the_title_names_the_panel(self, context_args):
        html = await render_tree(_popover(), context_args=context_args)
        assert_attr(
            html, '[role="dialog"]', ":aria-labelledby", "$id('hue-popover-title')"
        )

    @pytest.mark.asyncio
    async def test_without_a_title_there_is_nothing_to_point_at(self, context_args):
        html = await render_tree(
            Popover().trigger(Button().content("Share")), context_args=context_args
        )
        assert_no_selector(html, "[\\:aria-labelledby]")

    # label(): both branches
    @pytest.mark.asyncio
    async def test_a_label_names_a_panel_with_no_title(self, context_args):
        html = await render_tree(
            Popover().label("Columns").trigger(Button().content("Columns")),
            context_args=context_args,
        )
        assert_attr(html, '[role="dialog"]', "aria-label", "Columns")

    @pytest.mark.asyncio
    async def test_a_title_names_the_panel_instead_of_a_label(self, context_args):
        # Two names for one panel, and a screen reader picks whichever one
        # wins; the visible one should.
        html = await render_tree(
            _popover().label("Something else"), context_args=context_args
        )
        assert_no_selector(html, '[role="dialog"][aria-label]')

    # description(): both branches
    @pytest.mark.asyncio
    async def test_the_description_sits_under_the_title(self, context_args):
        html = await render_tree(
            _popover().description("Anyone with the link can view."),
            context_args=context_args,
        )
        assert_selector(html, '[role="dialog"] p.text-fg-muted')

    @pytest.mark.asyncio
    async def test_no_description_by_default(self, context_args):
        html = await render_tree(_popover(), context_args=context_args)
        assert_no_selector(html, '[role="dialog"] p')

    # content(): both branches
    @pytest.mark.asyncio
    async def test_content_follows_the_copy(self, context_args):
        html = await render_tree(
            _popover().content(Button().content("Copy")), context_args=context_args
        )
        assert_selector(html, '[role="dialog"] div.mt-3\\.5')

    @pytest.mark.asyncio
    async def test_nothing_is_rendered_for_absent_content(self, context_args):
        html = await render_tree(_popover(), context_args=context_args)
        assert_no_selector(html, "div.mt-3\\.5")
