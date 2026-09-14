import pytest

from hue.renderer import render_tree
from hue.ui import Callout
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestCallout:
    @pytest.mark.asyncio
    async def test_renders_body_content(self, context_args):
        html = await render_tree(
            Callout().content("Something happened."), context_args=context_args
        )
        assert_selector(html, "div.max-w-prose")
        assert "Something happened." in html

    # variant(): default vs an explicit variant
    @pytest.mark.asyncio
    async def test_default_variant_is_gray(self, context_args):
        html = await render_tree(Callout().content("Note"), context_args=context_args)
        assert_selector(html, "div.border-surface-200")
        assert_selector(html, "svg title:-soup-contains('circle-info')")

    @pytest.mark.asyncio
    async def test_error_variant_styles_and_icon(self, context_args):
        html = await render_tree(
            Callout().variant("error").content("Boom"), context_args=context_args
        )
        assert_selector(html, "div.border-wg-red")
        assert "bg-wg-red-50" in html
        # Meaning must not rest on colour alone, so each variant has its own icon.
        assert_selector(html, "svg title:-soup-contains('circle-x')")

    @pytest.mark.asyncio
    async def test_icon_is_decorative(self, context_args):
        html = await render_tree(Callout().content("Note"), context_args=context_args)
        assert_attr(html, "svg", "aria-hidden", "true")

    # title() render_if: both branches
    @pytest.mark.asyncio
    async def test_title_renders_when_set(self, context_args):
        html = await render_tree(
            Callout().title("Heads up").content("Body"), context_args=context_args
        )
        assert_selector(html, "p.font-medium")
        assert "Heads up" in html

    @pytest.mark.asyncio
    async def test_title_absent_when_unset(self, context_args):
        html = await render_tree(Callout().content("Body"), context_args=context_args)
        assert_no_selector(html, "p.font-medium")

    @pytest.mark.asyncio
    async def test_base_modifiers_apply_to_root(self, context_args):
        html = await render_tree(
            Callout().id("note").aria_label("Notice").class_("mt-4").content("Body"),
            context_args=context_args,
        )
        assert_attr(html, "div", "id", "note")
        assert_attr(html, "div", "aria-label", "Notice")
        assert_selector(html, "div#note.mt-4")
