import pytest

from hue.renderer import render_tree
from hue.ui import Badge, Column, DataTable, Empty
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

_COLUMNS = [
    Column("invoice", "Invoice"),
    Column("amount", "Amount", align="end"),
]
_ROWS = [
    {"invoice": "INV-2050", "amount": "2190"},
    {"invoice": "INV-2048", "amount": "1200"},
]


class TestDataTable:
    @pytest.mark.asyncio
    async def test_a_column_per_definition_and_a_row_per_record(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS), context_args=context_args
        )
        assert_selector(html, "th", count=2)
        assert_selector(html, "tbody tr", count=2)
        assert "INV-2050" in html

    @pytest.mark.asyncio
    async def test_ending_a_column_lines_its_digits_up(self, context_args):
        # Ending a column and lining its digits up are one decision: the only
        # thing that wants the right edge is a number, and without tabular
        # figures the decimal points drift and the column stops being
        # something you can scan.
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS), context_args=context_args
        )
        amounts = select(html, "td.tabular-nums")
        assert len(amounts) == 2
        assert all("text-end" in cell["class"] for cell in amounts)

    @pytest.mark.asyncio
    async def test_a_value_comes_from_a_key_a_path_or_a_callable(self, context_args):
        html = await render_tree(
            DataTable()
            .columns(
                [
                    Column("customer.city", "City"),
                    Column(lambda row: row["first"] + " " + row["last"], "Name"),
                ]
            )
            .rows([{"customer": {"city": "Oslo"}, "first": "Ada", "last": "Lovelace"}]),
            context_args=context_args,
        )
        assert "Oslo" in html
        assert "Ada Lovelace" in html

    @pytest.mark.asyncio
    async def test_a_key_that_is_not_there_says_which_part_was_missing(
        self, context_args
    ):
        with pytest.raises(ValueError, match="'city'"):
            await render_tree(
                DataTable()
                .columns([Column("customer.city", "City")])
                .rows([{"customer": {}}]),
                context_args=context_args,
            )

    # render(): a column that is a component rather than a value
    @pytest.mark.asyncio
    async def test_a_column_can_render_the_row_instead(self, context_args):
        html = await render_tree(
            DataTable()
            .columns(
                [Column("status", "Status", render=lambda r: Badge().content("X"))]
            )
            .rows([{"status": "paid"}]),
            context_args=context_args,
        )
        assert_selector(html, "td span")
        assert "paid" not in html

    @pytest.mark.asyncio
    async def test_a_value_that_is_not_a_scalar_asks_for_a_render(self, context_args):
        with pytest.raises(ValueError, match="render"):
            await render_tree(
                DataTable().columns([Column("tags", "Tags")]).rows([{"tags": ["a"]}]),
                context_args=context_args,
            )

    # loading(): both branches
    @pytest.mark.asyncio
    async def test_loading_stands_bars_where_the_values_will_be(self, context_args):
        # aria-busy on the table and aria-hidden on the placeholders: the
        # screen reader is told the table is mid-update once, rather than
        # reading out rows of nothing.
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).loading(),
            context_args=context_args,
        )
        assert_attr(html, "table", "aria-busy", "true")
        assert_attr(html, "tbody", "aria-hidden", "true")
        assert "INV-2050" not in html

    @pytest.mark.asyncio
    async def test_loading_keeps_the_table_the_height_it_already_was(
        self, context_args
    ):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).loading(),
            context_args=context_args,
        )
        assert_selector(html, "tbody tr", count=len(_ROWS))

    @pytest.mark.asyncio
    async def test_a_table_that_has_finished_says_so(self, context_args):
        # Not merely the absence of aria-busy: a swap that leaves the table
        # element in place would leave a stale "true" on it for good.
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS), context_args=context_args
        )
        assert_attr(html, "table", "aria-busy", "false")

    # empty(): given, defaulted, and not reached at all
    @pytest.mark.asyncio
    async def test_no_rows_keeps_the_header_and_says_so_underneath(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows([]), context_args=context_args
        )
        assert_selector(html, "th", count=2)
        assert_no_selector(html, "tbody")
        assert "Nothing here yet" in html

    @pytest.mark.asyncio
    async def test_an_empty_state_can_say_why(self, context_args):
        html = await render_tree(
            DataTable()
            .columns(_COLUMNS)
            .rows([])
            .empty(Empty().title("No invoices match")),
            context_args=context_args,
        )
        assert "No invoices match" in html
        assert "Nothing here yet" not in html

    @pytest.mark.asyncio
    async def test_rows_leave_the_empty_state_out(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).empty(Empty().title("None")),
            context_args=context_args,
        )
        assert "None" not in html

    # error(): both branches
    @pytest.mark.asyncio
    async def test_an_error_replaces_the_rows_whatever_else_is_going_on(
        self, context_args
    ):
        html = await render_tree(
            DataTable()
            .columns(_COLUMNS)
            .rows(_ROWS)
            .error(Empty().variant("danger").title("Could not load invoices")),
            context_args=context_args,
        )
        assert "Could not load invoices" in html
        assert "INV-2050" not in html
        assert_no_selector(html, "tbody")

    @pytest.mark.asyncio
    async def test_without_an_error_the_rows_are_the_rows(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS), context_args=context_args
        )
        assert_selector(html, "tbody tr", count=2)

    @pytest.mark.asyncio
    async def test_the_caption_comes_first_and_reads_before_the_table(
        self, context_args
    ):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).caption("Invoices, September"),
            context_args=context_args,
        )
        assert_selector(html, "table > caption:first-child")
        assert "Invoices, September" in html

    @pytest.mark.asyncio
    async def test_compact_tightens_the_rows(self, context_args):
        comfortable = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS), context_args=context_args
        )
        compact = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).compact(),
            context_args=context_args,
        )
        assert "[&_td]:py-[11px]" in select(comfortable, "table")[0]["class"]
        assert "[&_td]:py-[7px]" in select(compact, "table")[0]["class"]

    @pytest.mark.asyncio
    async def test_base_modifiers_land_on_the_table(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).id("invoices").class_("mt-4"),
            context_args=context_args,
        )
        assert_attr(html, "table", "id", "invoices")
        assert_selector(html, "table.mt-4")

    # The placeholder's own alignment: a block ignores text-align
    @pytest.mark.asyncio
    async def test_a_placeholder_stands_on_its_column_s_own_side(self, context_args):
        # Otherwise an ended column fills in from the wrong side and jumps
        # across the moment the rows arrive.
        html = await render_tree(
            DataTable().columns(_COLUMNS).loading(), context_args=context_args
        )
        bars = select(html, "tbody tr:first-child td > div")
        assert "ms-auto" not in bars[0]["class"]
        assert "ms-auto" in bars[1]["class"]

    @pytest.mark.asyncio
    async def test_a_centred_placeholder_is_centred_too(self, context_args):
        html = await render_tree(
            DataTable().columns([Column("note", "Note", align="center")]).loading(),
            context_args=context_args,
        )
        assert_selector(html, "tbody td > div.mx-auto")
