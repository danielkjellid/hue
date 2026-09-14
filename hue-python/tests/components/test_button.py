import pytest

from hue.renderer import render_tree
from hue.ui import Button
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestButton:
    @pytest.mark.asyncio
    async def test_render_basic(self, context_args):
        html = await render_tree(Button().content("Click"), context_args=context_args)
        assert_attr(html, "button", "type", "button")
        assert "Click" in html

    @pytest.mark.asyncio
    async def test_render_variant_classes(self, context_args):
        html = await render_tree(
            Button().variant("outline").content("Go"), context_args=context_args
        )
        assert_selector(html, "button.border")

    @pytest.mark.asyncio
    async def test_focus_visible_styles_present(self, context_args):
        """Keyboard users must get a visible focus ring."""
        html = await render_tree(
            Button().content("Tab to me"), context_args=context_args
        )
        assert "focus-visible:outline" in html

    # disabled() conditional: both branches, including an explicit False
    @pytest.mark.asyncio
    async def test_render_disabled(self, context_args):
        html = await render_tree(
            Button().disabled().content("No"), context_args=context_args
        )
        assert_attr(html, "button", "disabled")

    @pytest.mark.asyncio
    async def test_render_not_disabled(self, context_args):
        html = await render_tree(Button().content("Yes"), context_args=context_args)
        assert_selector(html, "button:not([disabled])")

    @pytest.mark.asyncio
    async def test_disabled_false_omits_attribute(self, context_args):
        # Boolean attributes are true by presence; disabled="false" would still
        # disable the button.
        html = await render_tree(
            Button().disabled(False).content("Yes"), context_args=context_args
        )
        assert_no_selector(html, "button[disabled]")

    # fluid() conditional: both branches
    @pytest.mark.asyncio
    async def test_fluid_by_default(self, context_args):
        html = await render_tree(Button().content("Go"), context_args=context_args)
        assert_selector(html, "button.w-full")

    @pytest.mark.asyncio
    async def test_not_fluid(self, context_args):
        html = await render_tree(
            Button().fluid(False).content("Go"), context_args=context_args
        )
        assert_selector(html, "button.w-fit")
        assert_no_selector(html, "button.w-full")

    @pytest.mark.asyncio
    async def test_render_submit_type(self, context_args):
        html = await render_tree(
            Button().type("submit").content("Send"), context_args=context_args
        )
        assert_attr(html, "button", "type", "submit")
