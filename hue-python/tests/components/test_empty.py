import re

import pytest

from hue.assets import icons_path
from hue.renderer import render_tree
from hue.ui import Empty
from tests._a11y import assert_no_selector, assert_selector


def _drawing(name: str) -> str:
    # The icon's first path, which is what tells one icon from another.
    match = re.search(r' d="([^"]+)"', (icons_path() / f"{name}.svg").read_text())
    assert match is not None
    return match.group(1)


class TestEmpty:
    @pytest.mark.asyncio
    async def test_renders_title_and_description(self, context_args):
        html = await render_tree(
            Empty().title("No invoices yet").description("They appear here."),
            context_args=context_args,
        )
        assert "No invoices yet" in html
        assert "They appear here." in html

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("variant", "icon"), [("neutral", "inbox"), ("danger", "circle-x")]
    )
    async def test_every_variant_brings_its_own_icon(self, context_args, variant, icon):
        # The variant tints the icon chip and nothing else, so without an
        # icon there is nothing for it to be.
        html = await render_tree(
            Empty().variant(variant).title("Nothing"), context_args=context_args
        )
        assert _drawing(icon) in html

    @pytest.mark.asyncio
    @pytest.mark.parametrize("icon", ["!", None])
    async def test_an_icon_of_your_own_or_none_replaces_it(self, context_args, icon):
        html = await render_tree(
            Empty().icon(icon).title("Nothing"), context_args=context_args
        )
        assert _drawing("inbox") not in html

    @pytest.mark.asyncio
    async def test_title_is_not_a_heading_by_default(self, context_args):
        # Inside a table cell a heading would land wrongly in the outline.
        html = await render_tree(Empty().title("Nothing"), context_args=context_args)
        assert_no_selector(html, "h1, h2, h3, h4, h5, h6")

    @pytest.mark.asyncio
    async def test_title_can_be_promoted_to_a_heading(self, context_args):
        html = await render_tree(
            Empty().title("Nothing here yet", heading="h2"),
            context_args=context_args,
        )
        assert_selector(html, "h2")
