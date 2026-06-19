import pytest

from hue.renderer import render_tree
from hue.ui import Spacer
from tests._a11y import assert_selector


class TestSpacer:
    @pytest.mark.asyncio
    async def test_render_default(self, context_args):
        html = await render_tree(Spacer(), context_args=context_args)
        assert_selector(html, "div")

    @pytest.mark.asyncio
    async def test_spacing_lg(self, context_args):
        html = await render_tree(Spacer().spacing("lg"), context_args=context_args)
        assert "mb-8" in html

    @pytest.mark.asyncio
    async def test_spacing_xl(self, context_args):
        html = await render_tree(Spacer().spacing("xl"), context_args=context_args)
        assert "mb-16" in html
