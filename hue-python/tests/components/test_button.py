import pytest

from hue.renderer import render_tree
from hue.ui import Button
from tests._a11y import assert_attr, assert_selector


class TestButton:
    def test_defaults(self):
        btn = Button()
        assert btn._get_prop("variant", "primary") == "primary"
        assert btn._get_prop("size", "md") == "md"
        assert btn._get_prop("shape", "rounded") == "rounded"
        assert btn._get_prop("fluid", True) is True
        assert btn._get_prop("type", "button") == "button"

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
        assert_attr(html, "button", "tabindex", "0")

    # disabled() conditional — both branches
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
    async def test_render_submit_type(self, context_args):
        html = await render_tree(
            Button().type("submit").content("Send"), context_args=context_args
        )
        assert_attr(html, "button", "type", "submit")

    @pytest.mark.asyncio
    async def test_render_aria_label(self, context_args):
        html = await render_tree(
            Button().aria_label("Close dialog").content("X"), context_args=context_args
        )
        assert_attr(html, "button", "aria-label", "Close dialog")

    @pytest.mark.asyncio
    async def test_render_with_id_and_class(self, context_args):
        html = await render_tree(
            Button().id("btn-1").class_("extra").content("OK"),
            context_args=context_args,
        )
        assert_attr(html, "button", "id", "btn-1")
        assert_selector(html, "button.extra")
