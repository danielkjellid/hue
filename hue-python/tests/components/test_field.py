import pytest

from hue.renderer import render_tree
from hue.ui import Field
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestField:
    @pytest.mark.asyncio
    async def test_the_label_points_at_the_control(self, context_args):
        # Without this the label is decorative text and clicking it does
        # nothing, whatever it looks like.
        html = await render_tree(
            Field().label("Region").html_for("region"), context_args=context_args
        )
        assert_attr(html, "label", "for", "region")

    # hint() and error(): both branches, and the error wins
    @pytest.mark.asyncio
    async def test_the_hint_is_identified_for_the_control(self, context_args):
        html = await render_tree(
            Field().label("Region").html_for("region").hint("Where data lives."),
            context_args=context_args,
        )
        assert_selector(html, "#region-hint")

    @pytest.mark.asyncio
    async def test_no_hint_by_default(self, context_args):
        html = await render_tree(
            Field().label("Region").html_for("region"), context_args=context_args
        )
        assert_no_selector(html, "#region-hint")

    @pytest.mark.asyncio
    async def test_the_error_is_announced(self, context_args):
        # It usually appears after a submit the user has already made, so
        # nothing would prompt a screen reader to revisit it.
        html = await render_tree(
            Field().label("Region").html_for("region").error("Pick one."),
            context_args=context_args,
        )
        assert_selector(html, '[role="alert"]#region-error')

    @pytest.mark.asyncio
    async def test_an_error_replaces_the_hint(self, context_args):
        html = await render_tree(
            Field()
            .label("Region")
            .html_for("region")
            .hint("Where data lives.")
            .error("Pick one."),
            context_args=context_args,
        )
        assert_no_selector(html, "#region-hint")
        assert_selector(html, "#region-error")

    # layout(): both branches
    @pytest.mark.asyncio
    async def test_stacked_by_default(self, context_args):
        html = await render_tree(
            Field().label("Region").hint("Where data lives."),
            context_args=context_args,
        )
        assert_selector(html, "div.flex-col")
        assert_no_selector(html, "div.flex-row")

    @pytest.mark.asyncio
    async def test_horizontal_moves_the_hint_into_the_label_column(self, context_args):
        # Under a 180px column the hint reads as part of the question; left
        # under the control it would sit in the next row's space.
        html = await render_tree(
            Field()
            .label("Region")
            .html_for("region")
            .hint("Where data lives.")
            .layout("horizontal")
            .content("a control"),
            context_args=context_args,
        )
        assert_selector(html, "div.flex-row")
        assert_selector(html, "div.w-\\[180px\\] > #region-hint")

    # A horizontal row centres only when both columns are one line.
    @pytest.mark.asyncio
    async def test_a_single_line_row_is_centred(self, context_args):
        # One line against one box: top-aligning them leaves the label sitting
        # above the middle of the control it names.
        html = await render_tree(
            Field()
            .label("Region")
            .html_for("region")
            .layout("horizontal")
            .content("a control"),
            context_args=context_args,
        )
        assert_selector(html, "div.flex-row.items-center")

    @pytest.mark.asyncio
    async def test_a_hint_puts_the_row_back_on_its_top_edge(self, context_args):
        # Centred, the label would drift down past the control as the column
        # under it grows.
        html = await render_tree(
            Field()
            .label("Region")
            .html_for("region")
            .hint("Where data lives.")
            .layout("horizontal"),
            context_args=context_args,
        )
        assert_selector(html, "div.flex-row.items-start")

    @pytest.mark.asyncio
    async def test_an_error_does_the_same_from_the_other_side(self, context_args):
        html = await render_tree(
            Field()
            .label("Region")
            .html_for("region")
            .error("Pick one.")
            .layout("horizontal")
            .content("a control"),
            context_args=context_args,
        )
        assert_selector(html, "div.flex-row.items-start")

    # trailing(): both branches
    @pytest.mark.asyncio
    async def test_trailing_sits_at_the_end_of_the_label_row(self, context_args):
        html = await render_tree(
            Field().label("Display name").trailing("Optional"),
            context_args=context_args,
        )
        assert_selector(html, "span.text-fg-subtle")
        assert "Optional" in html

    @pytest.mark.asyncio
    async def test_nothing_trailing_by_default(self, context_args):
        html = await render_tree(
            Field().label("Display name"), context_args=context_args
        )
        assert_no_selector(html, "span.text-fg-subtle")

    # An unlabelled field still has to lay out whatever is inside it.
    @pytest.mark.asyncio
    async def test_no_header_without_a_label(self, context_args):
        html = await render_tree(
            Field().content("a control"), context_args=context_args
        )
        assert "a control" in html
        assert_no_selector(html, "label")


class TestHiddenLabel:
    @pytest.mark.asyncio
    async def test_a_hidden_label_leaves_no_row_above_the_control(self, context_args):
        # sr-only takes it out of the flow, so a header holding only that is
        # a gap above the control and nothing else - which is what pushed a
        # bare select out of line with the buttons beside it.
        html = await render_tree(
            Field().label("Rows per page").hidden_label().content("control"),
            context_args=context_args,
        )
        assert_selector(html, "label.sr-only")
        assert_no_selector(html, "div.items-baseline")

    @pytest.mark.asyncio
    async def test_a_visible_label_keeps_its_row(self, context_args):
        html = await render_tree(
            Field().label("Rows per page").content("control"),
            context_args=context_args,
        )
        assert_selector(html, "div.items-baseline label")
