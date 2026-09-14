import pytest

from hue.renderer import render_tree
from hue.ui import Panel
from tests._a11y import assert_no_selector, assert_selector


class TestPanel:
    @pytest.mark.asyncio
    async def test_renders_content_inside_a_bordered_frame(self, context_args):
        html = await render_tree(Panel().content("Specimen"), context_args=context_args)
        assert_selector(html, "div.rounded-lg.border-border")
        assert "Specimen" in html

    # The bar appears only when it has something to say, so a panel used as a
    # plain frame is not topped by an empty strip.
    @pytest.mark.asyncio
    async def test_bar_renders_with_a_label(self, context_args):
        html = await render_tree(
            Panel().label("Variants").content("x"), context_args=context_args
        )
        assert_selector(html, "div.bg-surface-sunken.border-b")
        assert "Variants" in html

    @pytest.mark.asyncio
    async def test_bar_renders_with_only_a_hint(self, context_args):
        html = await render_tree(
            Panel().hint("Never colour alone").content("x"),
            context_args=context_args,
        )
        assert_selector(html, "div.bg-surface-sunken")
        assert "Never colour alone" in html

    @pytest.mark.asyncio
    async def test_no_bar_without_either(self, context_args):
        html = await render_tree(Panel().content("x"), context_args=context_args)
        assert_no_selector(html, "div.bg-surface-sunken")

    @pytest.mark.asyncio
    async def test_label_and_hint_sit_at_opposite_ends(self, context_args):
        html = await render_tree(
            Panel().label("Scale").hint("14px is the default").content("x"),
            context_args=context_args,
        )
        assert_selector(html, "div.justify-between > span", count=2)

    # padding(): three branches, and "none" matters for content that brings
    # its own edges, such as a table.
    @pytest.mark.asyncio
    async def test_default_padding(self, context_args):
        html = await render_tree(Panel().content("x"), context_args=context_args)
        assert_selector(html, "div.p-6")

    @pytest.mark.asyncio
    async def test_small_padding(self, context_args):
        html = await render_tree(
            Panel().padding("sm").content("x"), context_args=context_args
        )
        assert_selector(html, "div.p-4")
        assert_no_selector(html, "div.p-6")

    @pytest.mark.asyncio
    async def test_no_padding(self, context_args):
        html = await render_tree(
            Panel().padding("none").content("x"), context_args=context_args
        )
        assert_selector(html, "div.p-0")
        assert_no_selector(html, "div.p-6")

    # sunken(): both branches
    @pytest.mark.asyncio
    async def test_body_is_not_tinted_by_default(self, context_args):
        html = await render_tree(Panel().content("x"), context_args=context_args)
        assert_no_selector(html, "div.bg-canvas-subtle")

    @pytest.mark.asyncio
    async def test_sunken_body(self, context_args):
        html = await render_tree(
            Panel().sunken().content("x"), context_args=context_args
        )
        assert_selector(html, "div.bg-canvas-subtle")
