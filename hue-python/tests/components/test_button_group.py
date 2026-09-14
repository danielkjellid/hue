from html import unescape

import pytest

from hue.renderer import render_tree
from hue.ui import Button, ButtonGroup
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _group(**kwargs):
    return ButtonGroup(**kwargs).content(
        Button().variant("outline").content("Day"),
        Button().variant("outline").content("Week"),
    )


class TestButtonGroup:
    # variant(): two different things wearing the same clothes
    @pytest.mark.asyncio
    async def test_attached_by_default(self, context_args):
        # Buttons glued together: one seam, not two borders.
        html = await render_tree(_group(), context_args=context_args)
        assert_selector(html, "div.inline-flex")
        assert "[&>*+*]:-ms-px" in unescape(html)
        assert "[&>*:first-child]:rounded-s-md" in unescape(html)

    @pytest.mark.asyncio
    async def test_attached_has_no_track(self, context_args):
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, "div.bg-surface-sunken")

    @pytest.mark.asyncio
    async def test_segmented_is_a_track(self, context_args):
        html = await render_tree(
            _group().variant("segmented"), context_args=context_args
        )
        assert_selector(html, "div.bg-surface-sunken.border-border")
        # The selected option lifts out of the track.
        assert "[&>[aria-pressed=true]]:shadow-segment" in unescape(html)

    @pytest.mark.asyncio
    async def test_segmented_does_not_collapse_borders(self, context_args):
        html = await render_tree(
            _group().variant("segmented"), context_args=context_args
        )
        assert "[&>*+*]:-ms-px" not in unescape(html)

    # size(): only segmented owns its children's height
    @pytest.mark.asyncio
    async def test_segmented_sizes_its_children(self, context_args):
        html = await render_tree(
            _group().variant("segmented").size("lg"), context_args=context_args
        )
        assert "[&>*]:h-9" in unescape(html)

    @pytest.mark.asyncio
    async def test_attached_leaves_child_heights_alone(self, context_args):
        html = await render_tree(_group().size("lg"), context_args=context_args)
        assert "[&>*]:h-9" not in unescape(html)

    # label(): both branches
    @pytest.mark.asyncio
    async def test_label_makes_it_a_named_group(self, context_args):
        html = await render_tree(
            _group().variant("segmented").label("Date range"),
            context_args=context_args,
        )
        assert_attr(html, 'div[role="group"]', "aria-label", "Date range")

    @pytest.mark.asyncio
    async def test_without_a_label_it_is_not_a_group(self, context_args):
        # A group role with no name announces "group" and nothing else.
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, '[role="group"]')
