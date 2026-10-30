import pytest

from hue.renderer import render_tree
from hue.ui import Button, Kbd, Tooltip
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


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
        assert_attr(html, "[x-data]", "x-on:focusin", "shown = true")
        assert_attr(html, "[x-data]", "x-on:mouseenter")

    @pytest.mark.asyncio
    async def test_escape_dismisses_it_wherever_focus_is(self, context_args):
        # One opened by hover sits over what the user is reading while focus
        # is elsewhere, so the key is heard on the window (WCAG 1.4.13).
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_attr(
            html,
            "[x-data]",
            "x-on:keydown.escape.window",
            "clearTimeout($el._t); shown = false",
        )

    @pytest.mark.asyncio
    async def test_it_waits_before_opening(self, context_args):
        # A pointer crossing a toolbar would otherwise trail bubbles behind it.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert "shown = true, 400)" in html

    @pytest.mark.parametrize(
        ("placement", "ltr", "rtl"),
        [
            ("top", "top", "top"),
            ("bottom", "bottom", "bottom"),
            ("start", "left", "right"),
            ("end", "right", "left"),
        ],
    )
    @pytest.mark.asyncio
    async def test_each_placement_puts_the_bubble_somewhere_else(
        self, context_args, placement, ltr, rtl
    ):
        # noflip: the arrow is drawn for one side only. Start and end swap
        # sides with the direction, which only the browser knows.
        html = await render_tree(
            _tooltip().placement(placement), context_args=context_args
        )
        bound = select(html, '[role="tooltip"]')[0]["x-bind"]
        when_rtl, when_ltr = bound.split(" : ")
        assert f'"x-anchor.fixed.noflip.{rtl}.offset.6"' in when_rtl
        assert f'"x-anchor.fixed.noflip.{ltr}.offset.6"' in when_ltr

    @pytest.mark.parametrize(
        ("placement", "bridge"),
        [
            ("top", "before:top-full"),
            ("bottom", "before:bottom-full"),
            ("start", "before:start-full"),
            ("end", "before:end-full"),
        ],
    )
    @pytest.mark.asyncio
    async def test_the_gap_to_the_trigger_is_bridged(
        self, context_args, placement, bridge
    ):
        # Without it the pointer leaves the wrapper on its way into the bubble,
        # which closes before it can be hovered (WCAG 1.4.13).
        html = await render_tree(
            _tooltip().placement(placement), context_args=context_args
        )
        assert_selector(html, f'[role="tooltip"][class~="{bridge}"]')

    @pytest.mark.asyncio
    async def test_the_arrow_is_decorative(self, context_args):
        # It is a triangle made of borders; there is nothing to announce.
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_attr(html, '[role="tooltip"] span', "aria-hidden", "true")

    # keys(): both branches
    @pytest.mark.asyncio
    async def test_the_keys_sit_after_the_label(self, context_args):
        # A Kbd, which renders real kbd elements and gives each modifier a
        # spoken name - a glyph alone is announced by its Unicode name.
        html = await render_tree(
            _tooltip().keys(Kbd("mod", "K")), context_args=context_args
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
    async def test_no_keys_by_default(self, context_args):
        html = await render_tree(_tooltip(), context_args=context_args)
        assert_no_selector(html, "kbd")
