import pytest

from hue.renderer import render_tree
from hue.ui import Stack
from tests._a11y import assert_selector


class TestStack:
    # direction() conditional — both branches
    @pytest.mark.asyncio
    async def test_default_is_vertical(self, context_args):
        html = await render_tree(Stack().content("A", "B"), context_args=context_args)
        assert_selector(html, "div.flex-col")
        assert "A" in html
        assert "B" in html

    @pytest.mark.asyncio
    async def test_horizontal(self, context_args):
        html = await render_tree(
            Stack().direction("horizontal").content("X"), context_args=context_args
        )
        assert_selector(html, "div.flex-row")

    @pytest.mark.asyncio
    async def test_spacing(self, context_args):
        html = await render_tree(
            Stack().spacing("lg").content("Child"), context_args=context_args
        )
        assert "space-y-8" in html  # lg vertical spacing

    @pytest.mark.asyncio
    async def test_align_and_justify(self, context_args):
        html = await render_tree(
            Stack()
            .align_items("items-center")
            .justify_content("justify-center")
            .content("C"),
            context_args=context_args,
        )
        assert "items-center" in html
        assert "justify-center" in html
