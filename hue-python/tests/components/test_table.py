import pytest

from hue.renderer import render_tree
from hue.ui import (
    Empty,
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
)
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


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

    # compact(): both branches
    @pytest.mark.asyncio
    async def test_compact_sets_the_padding_for_every_cell_at_once(self, context_args):
        # On the table rather than on the cells, so one class sets the rhythm
        # and no two cells can disagree.
        comfortable = await render_tree(Table(), context_args=context_args)
        compact = await render_tree(Table().compact(), context_args=context_args)
        assert "[&_td]:py-[11px]" in select(comfortable, "table")[0]["class"]
        assert "[&_td]:py-[7px]" in select(compact, "table")[0]["class"]

    @pytest.mark.asyncio
    async def test_the_footer_stays_inside_the_frame(self, context_args):
        # Which is where an empty state belongs: a full-width message is not
        # a cell, and a header with nothing under it is still a table.
        html = await render_tree(
            Table().footer(Empty().title("No invoices")), context_args=context_args
        )
        assert_selector(html, "div > table + div")
        assert "No invoices" in html

    # TableRow selected(): both branches
    @pytest.mark.asyncio
    async def test_a_selected_row_is_marked_for_the_screen_reader_too(
        self, context_args
    ):
        html = await render_tree(TableRow().selected(), context_args=context_args)
        assert_attr(html, "tr", "aria-selected", "true")

    @pytest.mark.asyncio
    async def test_an_unselected_row_carries_no_state(self, context_args):
        html = await render_tree(TableRow(), context_args=context_args)
        assert_no_selector(html, "[aria-selected]")

    # align(): the end of a column, and the start of one
    @pytest.mark.asyncio
    async def test_ending_a_cell_lines_its_digits_up_as_well(self, context_args):
        html = await render_tree(
            TableCell().align("end").content("2190.00"), context_args=context_args
        )
        assert_selector(html, "td.text-end.tabular-nums")

    @pytest.mark.asyncio
    async def test_a_text_cell_starts_and_keeps_proportional_figures(
        self, context_args
    ):
        html = await render_tree(
            TableCell().content("Contoso"), context_args=context_args
        )
        assert_selector(html, "td.text-start")
        assert_no_selector(html, ".tabular-nums")
