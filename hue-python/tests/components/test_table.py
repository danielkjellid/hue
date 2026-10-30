import pytest
from htmy.html import div as html_div

from hue.renderer import render_tree
from hue.ui import (
    Empty,
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableColumnGroup,
    TableFooter,
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
                TableCaption().content("Users"),
                TableHeader().content(TableRow().content(TableHead().content("Name"))),
                TableBody().content(TableRow().content(TableCell().content("Ada"))),
            ),
            context_args=context_args,
        )
        assert_selector(html, "table > caption + thead + tbody")
        assert_attr(html, "th", "scope", "col")
        # Only the band the table is in scrolls, not the shell: a popover
        # opened from the toolbar has to be able to leave the frame.
        assert "overflow" not in select(html, "div")[0]["class"]
        assert_selector(html, "div.overflow-x-auto > table")

    @pytest.mark.asyncio
    async def test_column_groups_give_a_colgroup_header_its_columns(self, context_args):
        # The W3C multi-level headers pattern: scope="colgroup" names a
        # colgroup, so each group heading has one to stand over.
        html = await render_tree(
            Table().content(
                TableColumnGroup(),
                TableColumnGroup().span(2),
                TableHeader().content(
                    TableRow().content(
                        TableCell(),
                        TableHead().scope("colgroup").colspan(2).content("Mars"),
                    ),
                ),
            ),
            context_args=context_args,
        )
        groups = select(html, "table > colgroup")
        assert [group.get("span") for group in groups] == [None, "2"]
        assert select(html, "table > *")[2].name == "thead"
        assert_attr(html, "th", "scope", "colgroup")

    # True is an int to Python and would render span="true".
    @pytest.mark.parametrize("span", [0, -1, True, 1.5])
    def test_a_span_covers_at_least_one_column(self, span):
        for spanned in (
            lambda: TableColumnGroup().span(span),
            lambda: TableHead().colspan(span),
            lambda: TableCell().colspan(span),
            lambda: TableBody().title("October", colspan=span),
        ):
            with pytest.raises(ValueError, match="at least one"):
                spanned()

    @pytest.mark.asyncio
    async def test_no_part_writes_an_empty_class(self, context_args):
        html = await render_tree(
            Table().content(
                TableCaption().content("Planets"),
                TableColumnGroup(),
                TableHeader().content(TableRow().content(TableHead().content("A"))),
                TableBody().content(TableRow().content(TableCell().content("1"))),
                TableFooter().content(TableRow().content(TableCell().content("1"))),
            ),
            context_args=context_args,
        )
        assert 'class=""' not in html

    @pytest.mark.asyncio
    async def test_the_id_names_the_frame_and_the_label_the_table(self, context_args):
        # A request aims at the id: swap only the table and an empty state
        # sitting under it would still be there afterwards.
        html = await render_tree(
            Table().id("users").aria_label("Users"), context_args=context_args
        )
        assert_selector(html, "div#users > div#users-rows > div > table")
        assert_no_selector(html, "table#users")
        assert_attr(html, "table", "aria-label", "Users")

    @pytest.mark.asyncio
    async def test_the_band_along_the_bottom_is_replaced_with_the_rows(
        self, context_args
    ):
        # It says which page of how many, so a response that changes the
        # rows has to change it too.
        html = await render_tree(
            Table().id("users").under(html_div("1 of 3")), context_args=context_args
        )
        assert_selector(html, "div#users-rows > div.overflow-x-auto + div")
        assert "1 of 3" in str(select(html, "#users-rows")[0])

    @pytest.mark.asyncio
    async def test_the_footer_stays_inside_the_frame(self, context_args):
        # Which is where an empty state belongs: a full-width message is not
        # a cell, and a header with nothing under it is still a table.
        html = await render_tree(
            Table().footer(Empty().title("No invoices")), context_args=context_args
        )
        assert_selector(html, "div.overflow-x-auto + div")
        assert "No invoices" in html

    @pytest.mark.asyncio
    async def test_a_form_is_an_empty_element_the_checkboxes_name(self, context_args):
        html = await render_tree(
            Table().id("invoices").form("/archive/").content(TableBody()),
            context_args=context_args,
        )
        assert_attr(html, "form#invoices-act", "action", "/archive/")
        assert_attr(html, "form#invoices-act", "method", "post")

    @pytest.mark.asyncio
    async def test_the_toolbar_sits_in_the_frame_above_the_rows(self, context_args):
        html = await render_tree(
            Table()
            .id("invoices")
            .toolbar(html_div("Search", id="bar"))
            .content(TableBody()),
            context_args=context_args,
        )
        frame = select(html, "#invoices")[0]
        assert frame.select_one("#bar") is not None
        assert frame.select_one("#invoices-rows #bar") is None

    @pytest.mark.asyncio
    async def test_only_a_selected_row_carries_the_state(self, context_args):
        selected = await render_tree(TableRow().selected(), context_args=context_args)
        plain = await render_tree(TableRow(), context_args=context_args)
        assert_attr(selected, "tr", "aria-selected", "true")
        assert_no_selector(plain, "[aria-selected]")

    @pytest.mark.asyncio
    async def test_the_band_rounds_the_corners_it_reaches(self, context_args):
        # The band is the only thing that clips, so a header background
        # would bleed past the frame's corner unless the band rounds too.
        alone = await render_tree(Table(), context_args=context_args)
        between = await render_tree(
            Table().toolbar(html_div("Search")).under(html_div("1 of 3")),
            context_args=context_args,
        )
        band = "div.overflow-x-auto"
        assert select(alone, band)[0]["class"] == [
            "overflow-x-auto",
            "rounded-t-[11px]",
            "rounded-b-[11px]",
        ]
        assert select(between, band)[0]["class"] == ["overflow-x-auto"]


class TestTableSections:
    """A body with a title is a section of the table."""

    @pytest.mark.asyncio
    async def test_a_title_names_the_rows_under_it(self, context_args):
        html = await render_tree(
            TableBody()
            .title("October 2026", colspan=3)
            .content(TableRow().content(TableCell().content("Sat 24 Oct"))),
            context_args=context_args,
        )
        [title] = select(html, "tbody > tr:first-child > th")
        assert title.get("scope") == "rowgroup"
        assert title.get("colspan") == "3"
        assert title.get_text() == "October 2026"

    def test_a_blank_title_is_refused(self):
        with pytest.raises(ValueError, match="needs a title"):
            TableBody().title(" ", colspan=3)
