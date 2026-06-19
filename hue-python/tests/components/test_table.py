import pytest

from hue.renderer import render_tree
from hue.ui import (
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
)
from tests._a11y import assert_attr, assert_selector


class TestTable:
    """The compositional Table primitives."""

    @pytest.mark.asyncio
    async def test_render_full_table(self, context_args):
        html = await render_tree(
            Table().content(
                TableHeader().content(
                    TableRow().content(
                        TableHead().content("Name"),
                        TableHead().content("Email"),
                    ),
                ),
                TableBody().content(
                    TableRow().content(
                        TableCell().content("Ada"),
                        TableCell().content("ada@example.com"),
                    ),
                ),
            ),
            context_args=context_args,
        )
        assert_selector(html, ".overflow-x-auto table")  # scrollable wrapper
        assert_selector(html, "thead")
        assert_selector(html, "tbody")
        assert "Ada" in html
        assert "ada@example.com" in html

    # TableHead scope() conditional — default vs override
    @pytest.mark.asyncio
    async def test_head_default_scope_is_col(self, context_args):
        html = await render_tree(TableHead().content("Name"), context_args=context_args)
        assert_attr(html, "th", "scope", "col")

    @pytest.mark.asyncio
    async def test_head_scope_override(self, context_args):
        html = await render_tree(
            TableHead().scope("row").content("Total"), context_args=context_args
        )
        assert_attr(html, "th", "scope", "row")

    @pytest.mark.asyncio
    async def test_cell_colspan_and_align(self, context_args):
        html = await render_tree(
            TableCell().colspan(3).align("center").content("Spanning"),
            context_args=context_args,
        )
        assert_attr(html, "td", "colspan", "3")
        assert "text-center" in html

    @pytest.mark.asyncio
    async def test_caption_renders(self, context_args):
        html = await render_tree(
            TableCaption().content("A list of users."), context_args=context_args
        )
        assert_selector(html, "caption")
        assert "A list of users." in html

    @pytest.mark.asyncio
    async def test_base_modifiers_apply_to_table(self, context_args):
        html = await render_tree(
            Table().id("users").class_("custom-class").aria_label("Users"),
            context_args=context_args,
        )
        assert_attr(html, "table", "id", "users")
        assert_attr(html, "table", "aria-label", "Users")
        assert_selector(html, "table.custom-class")
