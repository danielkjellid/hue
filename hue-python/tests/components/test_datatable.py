import pytest

from hue.renderer import render_tree
from hue.ui import Column, DataTable, Text
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestDataTable:
    """The data-driven DataTable component."""

    @pytest.mark.asyncio
    async def test_renders_header_and_rows(self, context_args):
        html = await render_tree(
            DataTable()
            .columns(
                [
                    Column("Name", accessor="name"),
                    Column("Email", accessor="email"),
                ]
            )
            .data(
                [
                    {"name": "Ada", "email": "ada@example.com"},
                    {"name": "Alan", "email": "alan@example.com"},
                ]
            ),
            context_args=context_args,
        )
        assert "Name" in html
        assert "Email" in html
        assert "Ada" in html
        assert "alan@example.com" in html
        assert_selector(html, "th", count=2)
        assert_selector(html, "td", count=4)

    @pytest.mark.asyncio
    async def test_dotted_accessor_resolves_nested(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("City", accessor="address.city")])
            .data([{"address": {"city": "London"}}]),
            context_args=context_args,
        )
        assert "London" in html

    @pytest.mark.asyncio
    async def test_callable_accessor(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("Full", accessor=lambda r: f"{r['first']} {r['last']}")])
            .data([{"first": "Ada", "last": "Lovelace"}]),
            context_args=context_args,
        )
        assert "Ada Lovelace" in html

    @pytest.mark.asyncio
    async def test_custom_cell_render_function(self, context_args):
        html = await render_tree(
            DataTable()
            .columns(
                [
                    Column(
                        "Name", accessor="name", cell=lambda r: Text(r["name"].upper())
                    )
                ]
            )
            .data([{"name": "ada"}]),
            context_args=context_args,
        )
        assert "ADA" in html

    # Empty-state conditional — both branches
    @pytest.mark.asyncio
    async def test_populated_has_no_empty_state(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("Name", accessor="name")])
            .data([{"name": "Ada"}]),
            context_args=context_args,
        )
        assert "No results." not in html

    @pytest.mark.asyncio
    async def test_empty_data_shows_accessible_empty_state(self, context_args):
        html = await render_tree(
            DataTable()
            .columns(
                [Column("Name", accessor="name"), Column("Email", accessor="email")]
            )
            .data([]),
            context_args=context_args,
        )
        assert "No results." in html
        assert_attr(html, '[role="status"]', "role", "status")
        assert_attr(html, "td", "colspan", "2")

    @pytest.mark.asyncio
    async def test_caption_renders(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("Name", accessor="name")])
            .data([{"name": "Ada"}])
            .caption("Registered users"),
            context_args=context_args,
        )
        assert_selector(html, "caption")
        assert "Registered users" in html

    @pytest.mark.asyncio
    async def test_id_and_class_apply_to_table(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("Name", accessor="name")])
            .data([{"name": "Ada"}])
            .id("users-table")
            .class_("custom-class"),
            context_args=context_args,
        )
        assert_attr(html, "table", "id", "users-table")
        assert_selector(html, "table.custom-class")

    @pytest.mark.asyncio
    async def test_caption_is_first_child_of_table(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("Name", accessor="name")])
            .data([{"name": "Ada"}])
            .caption("Users"),
            context_args=context_args,
        )
        table = select(html, "table")[0]
        first_child = next(c for c in table.children if c.name)
        assert first_child.name == "caption"

    @pytest.mark.asyncio
    async def test_empty_state_keeps_cell_semantics(self, context_args):
        html = await render_tree(
            DataTable().columns([Column("Name", accessor="name")]).data([]),
            context_args=context_args,
        )
        # role="status" on the td itself would replace its cell role.
        assert_no_selector(html, 'td[role="status"]')
        assert_selector(html, 'td [role="status"]')

    def test_column_needs_accessor_or_cell(self):
        with pytest.raises(ValueError, match="accessor or a cell"):
            Column("Name")

    @pytest.mark.asyncio
    async def test_cell_only_column(self, context_args):
        html = await render_tree(
            DataTable()
            .columns([Column("Actions", cell=lambda r: Text("Edit"))])
            .data([{"id": 1}]),
            context_args=context_args,
        )
        assert "Edit" in html

    @pytest.mark.asyncio
    async def test_missing_key_reports_accessor(self, context_args):
        with pytest.raises(ValueError, match="'city' is not a key"):
            await render_tree(
                DataTable()
                .columns([Column("City", accessor="address.city")])
                .data([{"address": {}}]),
                context_args=context_args,
            )
