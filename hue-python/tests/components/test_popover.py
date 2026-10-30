import pytest

from hue.renderer import render_tree
from hue.ui import Button, DropdownMenu, Popover
from hue.ui.molecules import _overlay
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


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
        assert_attr(html, "button", "x-on:click", "open = !open")
        assert_attr(html, "button", "aria-haspopup", "dialog")
        assert_attr(html, "button", "x-bind:aria-expanded", "open")
        assert_attr(html, "button", "x-bind:aria-controls", "$id('hue-popover')")

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
        # Stopped, so a dialog the popover sits in stays open.
        html = await render_tree(_popover(), context_args=context_args)
        assert_attr(
            html,
            "[x-data]",
            "x-on:keydown.escape",
            "if (open) { $event.stopPropagation(); close() }",
        )
        assert_attr(html, '[role="dialog"]', "tabindex", "-1")
        assert_attr(html, "[x-data]", "x-on:click.outside", "open = false")

    @pytest.mark.asyncio
    async def test_focus_leaving_it_closes_it(self, context_args):
        # Left open, the panel would cover whatever took focus next.
        html = await render_tree(_popover(), context_args=context_args)
        handler = select(html, "[x-data]")[0]["x-on:focusout"]
        assert "!$el.contains($event.relatedTarget)" in handler
        assert "open = false" in handler
        # Focus leaving the document has no relatedTarget either.
        assert "!document.hasFocus()" in handler

    @pytest.mark.asyncio
    async def test_it_hangs_off_the_trigger(self, context_args):
        html = await render_tree(
            _popover().placement("top-end"), context_args=context_args
        )
        assert_attr(
            html, '[role="dialog"]', "x-anchor.fixed.top-end.offset.6", _overlay.TRIGGER
        )

    @pytest.mark.asyncio
    async def test_without_a_trigger_it_finds_none_in_its_content(self, context_args):
        # The first trigger inside it would be the nested menu's, and focus
        # would go back to a button that never opened this popover.
        popover = (
            Popover()
            .label("Filters")
            .content(DropdownMenu().label("Sort").trigger(Button().content("Sort")))
        )
        html = await render_tree(popover, context_args=context_args)
        assert_attr(
            html, '[role="dialog"]', "x-anchor.fixed.bottom-start.offset.6", "null"
        )
        assert "querySelector" not in select(html, "span[x-data]")[0]["x-data"]

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
            Popover().label("Share").trigger(Button().content("Share")),
            context_args=context_args,
        )
        assert_no_selector(html, "[\\:aria-labelledby]")

    @pytest.mark.asyncio
    async def test_a_popover_with_no_name_is_refused(self, context_args):
        with pytest.raises(ValueError, match="needs an accessible name"):
            await render_tree(
                Popover().trigger(Button().content("Share")),
                context_args=context_args,
            )

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
