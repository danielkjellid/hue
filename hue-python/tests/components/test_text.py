import pytest
from htmy import html as htmy_html

from hue.renderer import render_tree
from hue.ui import Label, Text
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestText:
    @pytest.mark.asyncio
    async def test_render_default_body(self, context_args):
        html = await render_tree(Text("Hello"), context_args=context_args)
        assert_selector(html, "p")
        assert "Hello" in html
        assert "text-sm leading-6" in html  # body variant

    @pytest.mark.asyncio
    async def test_render_title_variant(self, context_args):
        html = await render_tree(
            Text("Title").variant("title-1"), context_args=context_args
        )
        assert "text-5xl font-bold" in html

    @pytest.mark.asyncio
    async def test_render_custom_tag(self, context_args):
        html = await render_tree(
            Text("Heading").tag(htmy_html.h1).variant("title-3"),
            context_args=context_args,
        )
        assert_selector(html, "h1")

    # muted() conditional — both branches
    @pytest.mark.asyncio
    async def test_muted(self, context_args):
        html = await render_tree(Text("Muted").muted(), context_args=context_args)
        assert "text-surface-500" in html

    @pytest.mark.asyncio
    async def test_not_muted(self, context_args):
        html = await render_tree(Text("Plain"), context_args=context_args)
        assert "text-surface-500" not in html

    @pytest.mark.asyncio
    async def test_destructive(self, context_args):
        html = await render_tree(Text("Error").destructive(), context_args=context_args)
        assert "text-destructive" in html


class TestLabel:
    @pytest.mark.asyncio
    async def test_render_default(self, context_args):
        html = await render_tree(Label("Email"), context_args=context_args)
        assert_selector(html, "label")
        assert "Email" in html

    # required() conditional — both branches
    @pytest.mark.asyncio
    async def test_required_shows_marker(self, context_args):
        html = await render_tree(Label("Email").required(), context_args=context_args)
        assert "*" in html

    @pytest.mark.asyncio
    async def test_not_required_hides_marker(self, context_args):
        html = await render_tree(Label("Email"), context_args=context_args)
        assert "*" not in html

    @pytest.mark.asyncio
    async def test_html_for_associates_control(self, context_args):
        html = await render_tree(
            Label("Name").html_for("name-input"), context_args=context_args
        )
        assert_attr(html, "label", "for", "name-input")

    # hidden_label() conditional — both branches
    @pytest.mark.asyncio
    async def test_hidden_label_is_screen_reader_only(self, context_args):
        html = await render_tree(
            Label("Hidden").hidden_label(), context_args=context_args
        )
        assert_selector(html, "label.sr-only")

    @pytest.mark.asyncio
    async def test_visible_label_is_not_sr_only(self, context_args):
        html = await render_tree(Label("Visible"), context_args=context_args)
        assert_no_selector(html, "label.sr-only")
