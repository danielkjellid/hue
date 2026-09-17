import pytest

from hue.renderer import render_tree
from hue.ui import Button, Kbd, Tooltip
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _tooltip():
    return (
        Tooltip()
        .content("Rename")
        .trigger(Button().variant("ghost").icon_only("Rename"))
    )


class TestTooltip:
    @pytest.mark.asyncio
    async def test_the_bubble_describes_the_control_not_the_wrapper(self, context_args):
        # On the span around the control it describes nothing: a screen reader
        # reads a description from the element it is focused on.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_attr(html, "button", ":aria-describedby", "$id('hue-tooltip')")
        assert_no_selector(html, "span[aria-describedby]")

    @pytest.mark.asyncio
    async def test_the_id_is_minted_rather_than_fixed(self, context_args):
        # Two tooltips on a page would otherwise point at the same bubble.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_attr(html, '[role="tooltip"]', ":id", "$id('hue-tooltip')")
        assert_attr(html, "[x-id]", "x-id", "['hue-tooltip']")

    @pytest.mark.asyncio
    async def test_it_opens_on_focus_as_well_as_hover(self, context_args):
        # A keyboard never hovers, so hover alone hides it from half the users.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_attr(html, "[x-data]", "x-on:focusin", "open = true")
        assert_attr(html, "[x-data]", "x-on:mouseenter")

    @pytest.mark.asyncio
    async def test_escape_dismisses_it(self, context_args):
        # One sitting over what the user is trying to read needs a way out.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_attr(html, "[x-data]", "x-on:keydown.escape", "open = false")

    @pytest.mark.asyncio
    async def test_it_waits_before_opening(self, context_args):
        # A pointer crossing a toolbar would otherwise trail bubbles behind it.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert "open = true, 400)" in html

    @pytest.mark.parametrize(
        ("placement", "position"),
        [
            ("top", "bottom-full"),
            ("bottom", "top-full"),
            ("start", "right-full"),
            ("end", "left-full"),
        ],
    )
    @pytest.mark.asyncio
    async def test_each_placement_puts_the_bubble_somewhere_else(
        self, context_args, placement, position
    ):
        html = await render_tree(
            _tooltip().placement(placement), context_args=context_args
        )
        assert_selector(html, f'[role="tooltip"].{position}')

    @pytest.mark.asyncio
    async def test_the_arrow_is_decorative(self, context_args):
        # It is a triangle made of borders; there is nothing to announce.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_attr(html, '[role="tooltip"] span', "aria-hidden", "true")

    # shortcut(): both branches
    @pytest.mark.asyncio
    async def test_a_shortcut_sits_after_the_label(self, context_args):
        # A Kbd, which renders real kbd elements and gives each modifier a
        # spoken name - a glyph alone is announced by its Unicode name.
        html = await render_tree(
            _tooltip().shortcut(Kbd("mod", "K")), context_args=context_args
        )
        assert_selector(html, '[role="tooltip"] kbd')

    @pytest.mark.asyncio
    async def test_the_bubble_answers_to_the_theme(self, context_args):
        # Inverted in light, lifted in dark - and the arrow has to follow the
        # bubble, or it points back at it in a different colour.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_selector(html, '[role="tooltip"].bg-surface-inverse')
        assert_selector(html, "span.border-t-surface-inverse")

    @pytest.mark.asyncio
    async def test_no_shortcut_by_default(self, context_args):
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_no_selector(html, "kbd")
