import pytest

from hue.renderer import render_tree
from hue.ui import Badge, Button, Column, DataTable, Empty
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
        assert_selector(html, "div#invoices")
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

    # selectable(): both branches
    @pytest.mark.asyncio
    async def test_every_row_checkbox_names_its_own_row(self, context_args):
        # Three checkboxes all announcing "Select" gives a screen reader
        # nothing to select by.
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).selectable("invoice"),
            context_args=context_args,
        )
        boxes = select(html, "tbody input[type=checkbox]")
        labels = [box["aria-label"] for box in boxes]
        assert labels == ["Select INV-2050", "Select INV-2048"]

    @pytest.mark.asyncio
    async def test_the_checkboxes_are_real_and_carry_the_selection(self, context_args):
        # A form around the table posts them without any JavaScript at all.
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).selectable("invoice").name("ids"),
            context_args=context_args,
        )
        boxes = select(html, "tbody input[type=checkbox]")
        assert [box["name"] for box in boxes] == ["ids", "ids"]
        assert [box["value"] for box in boxes] == ["INV-2050", "INV-2048"]

    @pytest.mark.asyncio
    async def test_the_header_checkbox_knows_about_all_the_rows(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).selectable("invoice"),
            context_args=context_args,
        )
        # On the frame, so a band above the rows is inside the scope too.
        assert_attr(
            html,
            "div[x-data]",
            "x-data",
            'hueTableSelection(["INV-2050", "INV-2048"])',
        )
        assert_attr(
            html,
            "thead input",
            "x-effect",
            "$el.checked = all; $el.indeterminate = some",
        )

    @pytest.mark.asyncio
    async def test_a_table_nobody_selects_from_has_no_checkboxes(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS), context_args=context_args
        )
        assert_no_selector(html, "input[type=checkbox]")
        assert_no_selector(html, "[x-data]")

    # bulk_actions(): both branches
    @pytest.mark.asyncio
    async def test_what_to_do_with_the_picked_rows_sits_above_them(self, context_args):
        # Inside the table's own Alpine scope, so an expression in an action
        # can read the list of values the checkboxes carry.
        html = await render_tree(
            DataTable()
            .columns(_COLUMNS)
            .rows(_ROWS)
            .selectable("invoice")
            .bulk_actions(Button().content("Delete")),
            context_args=context_args,
        )
        assert_selector(html, "div.bg-accent-subtle button")
        # One Alpine scope on the frame, so the bar above the rows is inside it.
        assert_selector(html, "div[x-data] div.bg-accent-subtle")
        assert_selector(html, "div.bg-accent-subtle + div > div > table")
        assert_attr(html, "div.bg-accent-subtle", "x-show", "selected.length > 0")

    @pytest.mark.asyncio
    async def test_the_count_announces_itself(self, context_args):
        # Controls appearing after a checkbox is ticked are a change a
        # screen reader has no other way of hearing about.
        html = await render_tree(
            DataTable()
            .columns(_COLUMNS)
            .rows(_ROWS)
            .selectable("invoice")
            .bulk_actions(Button().content("Delete")),
            context_args=context_args,
        )
        assert_attr(html, "[role=status]", "x-text", "selected.length + ' selected'")

    @pytest.mark.asyncio
    async def test_no_actions_means_no_bar(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS).selectable("invoice"),
            context_args=context_args,
        )
        assert_no_selector(html, ".bg-accent-subtle")
        assert_no_selector(html, "[role=status]")

    # sort: a header that goes somewhere, and one that does not
    @pytest.mark.asyncio
    async def test_a_sortable_header_is_a_link_not_a_clickable_cell(self, context_args):
        # A th with a click handler is not keyboard-operable; a link is, and
        # it puts the order in the URL where it can be shared.
        html = await render_tree(
            DataTable()
            .columns([Column("amount", "Amount", sort="amount")])
            .rows(_ROWS)
            .sort_href(lambda order: f"?sort={order}"),
            context_args=context_args,
        )
        assert_attr(html, "th a", "href", "?sort=amount")

    @pytest.mark.asyncio
    async def test_a_column_with_no_sort_is_only_its_label(self, context_args):
        html = await render_tree(
            DataTable().columns(_COLUMNS).rows(_ROWS), context_args=context_args
        )
        assert_no_selector(html, "th a")
        assert_no_selector(html, "[aria-sort]")

    @pytest.mark.asyncio
    async def test_only_the_column_the_rows_are_in_says_which_way(self, context_args):
        # ARIA has no way to rank two sorted columns, so there is never more
        # than one.
        html = await render_tree(
            DataTable()
            .columns(
                [
                    Column("invoice", "Invoice", sort="invoice"),
                    Column("amount", "Amount", sort="amount"),
                ]
            )
            .rows(_ROWS)
            .sorted("-amount")
            .sort_href(lambda order: f"?sort={order}"),
            context_args=context_args,
        )
        marked = select(html, "[aria-sort]")
        assert len(marked) == 1
        assert marked[0]["aria-sort"] == "descending"

    @pytest.mark.asyncio
    async def test_the_sorted_column_turns_around_and_the_others_replace_it(
        self, context_args
    ):
        # One column at a time: clicking another column asks for its order
        # instead, not for both.
        html = await render_tree(
            DataTable()
            .columns(
                [
                    Column("invoice", "Invoice", sort="invoice"),
                    Column("amount", "Amount", sort="amount"),
                ]
            )
            .rows(_ROWS)
            .sorted("amount")
            .sort_href(lambda order: order),
            context_args=context_args,
        )
        assert [link["href"] for link in select(html, "th a")] == ["invoice", "-amount"]

    @pytest.mark.asyncio
    async def test_a_sortable_column_needs_somewhere_to_go(self, context_args):
        with pytest.raises(ValueError, match="sort_href"):
            await render_tree(
                DataTable()
                .columns([Column("amount", "Amount", sort="amount")])
                .rows(_ROWS),
                context_args=context_args,
            )

    # x-target: the swap, and the plain navigation it falls back to
    @pytest.mark.asyncio
    async def test_a_table_with_an_id_is_fetched_and_swapped_in_place(
        self, context_args
    ):
        html = await render_tree(
            DataTable()
            .columns([Column("amount", "Amount", sort="amount")])
            .rows(_ROWS)
            .sort_href(lambda order: f"?sort={order}")
            .id("invoices"),
            context_args=context_args,
        )
        # The rows, not the frame: a toolbar above them keeps its caret.
        assert_attr(html, "th a", "x-target", "invoices-rows")

    @pytest.mark.asyncio
    async def test_without_an_id_the_header_is_just_a_link(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("amount", "Amount", sort="amount")])
            .rows(_ROWS)
            .sort_href(lambda order: f"?sort={order}"),
            context_args=context_args,
        )
        assert_no_selector(html, "[x-target]")
