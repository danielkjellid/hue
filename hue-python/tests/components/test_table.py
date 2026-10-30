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
        assert all(group.get("class") is None for group in groups)

    @pytest.mark.parametrize("span", [0, -1])
    def test_a_column_group_covers_at_least_one_column(self, span):
        with pytest.raises(ValueError, match="at least one"):
            TableColumnGroup().span(span)

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
        assert_attr(html, "table", "aria-label", "Users")
        assert_selector(html, "table.custom-class")

    @pytest.mark.asyncio
    async def test_the_id_names_the_frame_rather_than_the_table(self, context_args):
        # Which is what a request has to aim at: swap only the table and an
        # empty state sitting under it would still be there afterwards.
        html = await render_tree(Table().id("users"), context_args=context_args)
        assert_attr(html, "div#users > div#users-rows > div > table", "class")
        assert_no_selector(html, "table#users")

    @pytest.mark.asyncio
    async def test_only_the_band_the_table_is_in_scrolls(self, context_args):
        # Not the shell: a popover opened from the toolbar has to be able to
        # leave the frame, and overflow on the shell would cut it off.
        html = await render_tree(Table(), context_args=context_args)
        assert "overflow" not in select(html, "div")[0]["class"]
        assert_selector(html, "div.overflow-x-auto > table")

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
        # The table is in a band of its own, the footer in the next one.
        assert_selector(html, "div > div > table")
        assert_selector(html, "div.overflow-x-auto + div")
        assert "No invoices" in html

    # TableRow selected(): both branches
    # form(): both branches
    @pytest.mark.asyncio
    async def test_a_form_is_an_empty_element_the_checkboxes_name(self, context_args):
        html = await render_tree(
            Table().id("invoices").form("/archive/").content(TableBody()),
            context_args=context_args,
        )
        assert_attr(html, "form#invoices-act", "action", "/archive/")
        assert_attr(html, "form#invoices-act", "method", "post")

    @pytest.mark.asyncio
    async def test_no_form_by_default(self, context_args):
        html = await render_tree(
            Table().id("invoices").content(TableBody()), context_args=context_args
        )
        assert_no_selector(html, "form")

    # toolbar(): both branches
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
    async def test_no_toolbar_by_default(self, context_args):
        html = await render_tree(
            Table().id("invoices").content(TableBody()), context_args=context_args
        )
        assert [child.get("id") for child in select(html, "#invoices > *")] == [
            "invoices-rows"
        ]

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

    @pytest.mark.asyncio
    async def test_no_title_row_by_default(self, context_args):
        html = await render_tree(
            TableBody().content(TableRow().content(TableCell().content("x"))),
            context_args=context_args,
        )
        assert_no_selector(html, "th")

    def test_a_blank_title_is_refused(self):
        with pytest.raises(ValueError, match="needs a title"):
            TableBody().title(" ", colspan=3)
