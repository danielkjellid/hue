import pytest

from hue.renderer import render_tree
from hue.ui import Label, Text
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestText:
    @pytest.mark.asyncio
    async def test_it_is_a_paragraph_unless_told_otherwise(self, context_args):
        paragraph = await render_tree(Text("Hello"), context_args=context_args)
        heading = await render_tree(
            Text("Heading").tag("h1").variant("title-3"), context_args=context_args
        )
        assert_selector(paragraph, "p")
        assert_selector(heading, "h1")

    @pytest.mark.asyncio
    async def test_destructive_wins_over_muted(self, context_args):
        html = await render_tree(
            Text("Error").destructive().muted(), context_args=context_args
        )
        assert_selector(html, "p.text-danger-text")
        assert_no_selector(html, "p.text-fg-muted")


class TestLabel:
    @pytest.mark.asyncio
    async def test_it_labels_the_control_it_names(self, context_args):
        html = await render_tree(
            Label("Name").html_for("name-input"), context_args=context_args
        )
        assert_attr(html, "label", "for", "name-input")

    @pytest.mark.asyncio
    async def test_the_required_marker_is_hidden_from_assistive_tech(
        self, context_args
    ):
        # The control's own required attribute announces it.
        html = await render_tree(Label("Email").required(), context_args=context_args)
        assert_attr(html, "label span:last-child", "aria-hidden", "true")
        assert "*" in html

    @pytest.mark.asyncio
    async def test_hidden_label_is_screen_reader_only(self, context_args):
        html = await render_tree(
            Label("Hidden").hidden_label(), context_args=context_args
        )
        assert_selector(html, "label.sr-only")
