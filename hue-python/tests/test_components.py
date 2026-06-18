import pytest
from htmy import Renderer
from htmy import html as htmy_html

from hue.context import HueContextArgs
from hue.exceptions import MissingHueContextError
from hue.renderer import render_tree
from hue.ui import (
    Button,
    Column,
    DataTable,
    EmailInput,
    Label,
    NumberInput,
    PasswordInput,
    Spacer,
    Stack,
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
    Text,
    TextInput,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _MockRequest:
    pass


def _context_args() -> HueContextArgs[_MockRequest]:
    return HueContextArgs(request=_MockRequest(), csrf_token="tok")


# ---------------------------------------------------------------------------
# ChainableComponent base tests
# ---------------------------------------------------------------------------


class TestChainableComponent:
    """Tests for the shared modifiers on ChainableComponent."""

    def test_class_returns_self(self):
        btn = Button()
        assert btn.class_("foo") is btn

    def test_id_returns_self(self):
        btn = Button()
        assert btn.id("bar") is btn

    def test_content_returns_self(self):
        btn = Button()
        assert btn.content("child") is btn

    def test_class_accumulates(self):
        btn = Button().class_("a").class_("b")
        assert "a" in btn._get_prop("class_")
        assert "b" in btn._get_prop("class_")

    def test_aria_modifiers(self):
        btn = (
            Button()
            .aria_label("close")
            .aria_hidden("true")
            .aria_expanded("false")
            .aria_controls("panel-1")
            .role("dialog")
        )
        attrs = btn._get_base_html_attrs()
        assert attrs["aria_label"] == "close"
        assert attrs["aria_hidden"] == "true"
        assert attrs["aria_expanded"] == "false"
        assert attrs["aria_controls"] == "panel-1"
        assert attrs["role"] == "dialog"

    def test_base_html_attrs_omits_none(self):
        btn = Button().id("my-id")
        attrs = btn._get_base_html_attrs()
        assert attrs == {"id": "my-id"}

    def test_content_sets_children(self):
        btn = Button().content("a", "b")
        assert btn._children == ("a", "b")

    @pytest.mark.asyncio
    async def test_render_without_hue_context_raises(self):
        with pytest.raises(MissingHueContextError):
            await Renderer().render(Button().content("Hi"))


# ---------------------------------------------------------------------------
# Button tests
# ---------------------------------------------------------------------------


class TestButton:
    """Tests for the Button chainable component."""

    def test_defaults(self):
        btn = Button()
        assert btn._get_prop("variant", "primary") == "primary"
        assert btn._get_prop("size", "md") == "md"
        assert btn._get_prop("shape", "rounded") == "rounded"
        assert btn._get_prop("fluid", True) is True
        assert btn._get_prop("type", "button") == "button"

    def test_chaining(self):
        btn = (
            Button()
            .variant("outline")
            .size("lg")
            .shape("pill")
            .fluid(False)
            .type("submit")
            .disabled(True)
        )
        assert btn._get_prop("variant") == "outline"
        assert btn._get_prop("size") == "lg"
        assert btn._get_prop("shape") == "pill"
        assert btn._get_prop("fluid") is False
        assert btn._get_prop("type") == "submit"
        assert btn._get_prop("disabled") is True

    @pytest.mark.asyncio
    async def test_render_basic(self):
        html = await render_tree(
            Button().content("Click"),
            context_args=_context_args(),
        )
        assert "<button" in html
        assert "Click" in html
        assert 'type="button"' in html

    @pytest.mark.asyncio
    async def test_render_variant_classes(self):
        html = await render_tree(
            Button().variant("outline").content("Go"),
            context_args=_context_args(),
        )
        assert "border" in html
        assert "Go" in html

    @pytest.mark.asyncio
    async def test_render_disabled(self):
        html = await render_tree(
            Button().disabled().content("No"),
            context_args=_context_args(),
        )
        assert "disabled" in html

    @pytest.mark.asyncio
    async def test_render_with_id_and_class(self):
        html = await render_tree(
            Button().id("btn-1").class_("extra").content("OK"),
            context_args=_context_args(),
        )
        assert 'id="btn-1"' in html
        assert "extra" in html

    @pytest.mark.asyncio
    async def test_render_submit_type(self):
        html = await render_tree(
            Button().type("submit").content("Send"),
            context_args=_context_args(),
        )
        assert 'type="submit"' in html

    @pytest.mark.asyncio
    async def test_render_aria_label(self):
        html = await render_tree(
            Button().aria_label("Close dialog").content("X"),
            context_args=_context_args(),
        )
        assert 'aria-label="Close dialog"' in html

    @pytest.mark.asyncio
    async def test_chaining_order_independence(self):
        """Props should be the same regardless of chaining order."""
        btn_a = Button().variant("secondary").size("sm").disabled()
        btn_b = Button().disabled().size("sm").variant("secondary")
        assert btn_a._props == btn_b._props


# ---------------------------------------------------------------------------
# Text tests
# ---------------------------------------------------------------------------


class TestText:
    @pytest.mark.asyncio
    async def test_render_default(self):
        html = await render_tree(
            Text("Hello"),
            context_args=_context_args(),
        )
        assert "<p" in html
        assert "Hello" in html
        assert "text-sm leading-6" in html  # body variant

    @pytest.mark.asyncio
    async def test_render_title_variant(self):
        html = await render_tree(
            Text("Title").variant("title-1"),
            context_args=_context_args(),
        )
        assert "text-5xl font-bold" in html

    @pytest.mark.asyncio
    async def test_render_with_tag(self):
        result = await render_tree(
            Text("Heading").tag(htmy_html.h1).variant("title-3"),
            context_args=_context_args(),
        )
        assert "<h1" in result
        assert "</h1>" in result

    @pytest.mark.asyncio
    async def test_render_muted(self):
        html = await render_tree(
            Text("Muted").muted(),
            context_args=_context_args(),
        )
        assert "text-surface-500" in html

    @pytest.mark.asyncio
    async def test_render_destructive(self):
        html = await render_tree(
            Text("Error").destructive(),
            context_args=_context_args(),
        )
        assert "text-destructive" in html

    @pytest.mark.asyncio
    async def test_render_align_center(self):
        html = await render_tree(
            Text("Centered").align("text-center"),
            context_args=_context_args(),
        )
        assert "text-center" in html

    @pytest.mark.asyncio
    async def test_render_with_class(self):
        html = await render_tree(
            Text("Styled").class_("w-full"),
            context_args=_context_args(),
        )
        assert "w-full" in html


# ---------------------------------------------------------------------------
# Label tests
# ---------------------------------------------------------------------------


class TestLabel:
    @pytest.mark.asyncio
    async def test_render_default(self):
        html = await render_tree(
            Label("Email"),
            context_args=_context_args(),
        )
        assert "<label" in html
        assert "Email" in html
        assert "*" not in html

    @pytest.mark.asyncio
    async def test_render_required(self):
        html = await render_tree(
            Label("Email").required(),
            context_args=_context_args(),
        )
        assert "*" in html

    @pytest.mark.asyncio
    async def test_render_not_required(self):
        html = await render_tree(
            Label("Optional").required(False),
            context_args=_context_args(),
        )
        assert "*" not in html

    @pytest.mark.asyncio
    async def test_render_html_for(self):
        html = await render_tree(
            Label("Name").html_for("name-input"),
            context_args=_context_args(),
        )
        assert 'for="name-input"' in html

    @pytest.mark.asyncio
    async def test_render_hidden_label(self):
        html = await render_tree(
            Label("Hidden").hidden_label(),
            context_args=_context_args(),
        )
        assert "sr-only" in html

    @pytest.mark.asyncio
    async def test_render_disabled(self):
        html = await render_tree(
            Label("Disabled").disabled(),
            context_args=_context_args(),
        )
        assert "pointer-events-none" in html


# ---------------------------------------------------------------------------
# Stack tests
# ---------------------------------------------------------------------------


class TestStack:
    @pytest.mark.asyncio
    async def test_render_default_vertical(self):
        html = await render_tree(
            Stack().content("A", "B"),
            context_args=_context_args(),
        )
        assert "<div" in html
        assert "flex-col" in html
        assert "A" in html
        assert "B" in html

    @pytest.mark.asyncio
    async def test_render_horizontal(self):
        html = await render_tree(
            Stack().direction("horizontal").content("X"),
            context_args=_context_args(),
        )
        assert "flex-row" in html

    @pytest.mark.asyncio
    async def test_render_with_spacing(self):
        html = await render_tree(
            Stack().spacing("lg").content("Child"),
            context_args=_context_args(),
        )
        assert "space-y-8" in html  # lg vertical spacing

    @pytest.mark.asyncio
    async def test_render_align_items(self):
        html = await render_tree(
            Stack().align_items("items-center").content("C"),
            context_args=_context_args(),
        )
        assert "items-center" in html

    @pytest.mark.asyncio
    async def test_render_justify_content(self):
        html = await render_tree(
            Stack().justify_content("justify-center").content("C"),
            context_args=_context_args(),
        )
        assert "justify-center" in html


# ---------------------------------------------------------------------------
# Spacer tests
# ---------------------------------------------------------------------------


class TestSpacer:
    @pytest.mark.asyncio
    async def test_render_default(self):
        html = await render_tree(
            Spacer(),
            context_args=_context_args(),
        )
        assert "<div" in html

    @pytest.mark.asyncio
    async def test_render_with_spacing(self):
        html = await render_tree(
            Spacer().spacing("lg"),
            context_args=_context_args(),
        )
        assert "mb-8" in html  # lg bottom margin

    @pytest.mark.asyncio
    async def test_spacing_method(self):
        html = await render_tree(
            Spacer().spacing("xl"),
            context_args=_context_args(),
        )
        assert "mb-16" in html  # xl bottom margin


# ---------------------------------------------------------------------------
# InputV2 tests
# ---------------------------------------------------------------------------


class TestTextInput:
    @pytest.mark.asyncio
    async def test_render_basic(self):
        html = await render_tree(
            TextInput().name("username").label("Username"),
            context_args=_context_args(),
        )
        assert 'type="text"' in html
        assert 'name="username"' in html
        assert "Username" in html

    @pytest.mark.asyncio
    async def test_render_placeholder(self):
        html = await render_tree(
            TextInput().name("name").label("Name").placeholder("Enter name"),
            context_args=_context_args(),
        )
        assert 'placeholder="Enter name"' in html

    @pytest.mark.asyncio
    async def test_render_disabled(self):
        html = await render_tree(
            TextInput().name("f").label("F").disabled(),
            context_args=_context_args(),
        )
        assert "cursor-not-allowed" in html

    @pytest.mark.asyncio
    async def test_id_links_input_and_label(self):
        html = await render_tree(
            TextInput().name("email").label("Email"),
            context_args=_context_args(),
        )
        assert 'id="email"' in html
        assert 'for="email"' in html

    @pytest.mark.asyncio
    async def test_explicit_id_links_input_and_label(self):
        html = await render_tree(
            TextInput().name("email").label("Email").id("custom-id"),
            context_args=_context_args(),
        )
        assert 'id="custom-id"' in html
        assert 'for="custom-id"' in html
        assert 'id="email"' not in html

    @pytest.mark.asyncio
    async def test_forwards_base_attrs_to_input(self):
        html = await render_tree(
            TextInput()
            .name("email")
            .label("Email")
            .role("searchbox")
            .aria_describedby("hint")
            .x_model("form.email"),
            context_args=_context_args(),
        )
        assert 'role="searchbox"' in html
        assert "hint" in html
        assert "x-model" in html


class TestEmailInput:
    @pytest.mark.asyncio
    async def test_render_email_type(self):
        html = await render_tree(
            EmailInput().name("email").label("Email"),
            context_args=_context_args(),
        )
        assert 'type="email"' in html
        assert 'autocomplete="email"' in html


class TestPasswordInput:
    @pytest.mark.asyncio
    async def test_render_password_type(self):
        html = await render_tree(
            PasswordInput().name("pwd").label("Password"),
            context_args=_context_args(),
        )
        assert 'type="password"' in html
        assert 'autocomplete="current-password"' in html


class TestNumberInput:
    @pytest.mark.asyncio
    async def test_render_with_min_max_step(self):
        html = await render_tree(
            NumberInput().name("qty").label("Quantity").min(1).max(100).step(1),
            context_args=_context_args(),
        )
        assert 'type="number"' in html
        assert 'min="1"' in html
        assert 'max="100"' in html
        assert 'step="1"' in html


# ---------------------------------------------------------------------------
# Integration: composing v2 components
# ---------------------------------------------------------------------------


class TestComposition:
    @pytest.mark.asyncio
    async def test_button_with_nested_stack_and_text(self):
        """Demonstrates the target DX: readable nesting via .content()."""
        html = await render_tree(
            Button()
            .variant("outline")
            .type("button")
            .content(
                Stack()
                .direction("horizontal")
                .spacing("xs")
                .align_items("items-center")
                .content(
                    Text("Sign in"),
                )
            ),
            context_args=_context_args(),
        )
        assert "<button" in html
        assert "Sign in" in html
        assert "flex-row" in html  # horizontal stack


# ---------------------------------------------------------------------------
# Table primitive tests
# ---------------------------------------------------------------------------


class TestTable:
    """Tests for the compositional Table primitives."""

    @pytest.mark.asyncio
    async def test_render_full_table(self):
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
            context_args=_context_args(),
        )
        # Wrapped in a horizontally scrollable container.
        assert "overflow-x-auto" in html
        assert "<table" in html
        assert "<thead" in html
        assert "<tbody" in html
        assert "<tr" in html
        assert "<td" in html
        assert "Ada" in html
        assert "ada@example.com" in html

    @pytest.mark.asyncio
    async def test_table_head_default_scope_is_col(self):
        html = await render_tree(
            TableHead().content("Name"),
            context_args=_context_args(),
        )
        assert "<th" in html
        assert 'scope="col"' in html

    @pytest.mark.asyncio
    async def test_table_head_scope_override(self):
        html = await render_tree(
            TableHead().scope("row").content("Total"),
            context_args=_context_args(),
        )
        assert 'scope="row"' in html

    @pytest.mark.asyncio
    async def test_cell_colspan_and_align(self):
        html = await render_tree(
            TableCell().colspan(3).align("center").content("Spanning"),
            context_args=_context_args(),
        )
        assert 'colspan="3"' in html
        assert "text-center" in html

    @pytest.mark.asyncio
    async def test_caption_renders(self):
        html = await render_tree(
            TableCaption().content("A list of users."),
            context_args=_context_args(),
        )
        assert "<caption" in html
        assert "A list of users." in html

    @pytest.mark.asyncio
    async def test_chainable_base_modifiers_apply_to_table(self):
        html = await render_tree(
            Table().id("users").class_("custom-class").aria_label("Users"),
            context_args=_context_args(),
        )
        assert 'id="users"' in html
        assert "custom-class" in html
        assert 'aria-label="Users"' in html


# ---------------------------------------------------------------------------
# DataTable tests
# ---------------------------------------------------------------------------


class TestDataTable:
    """Tests for the data-driven DataTable component."""

    @pytest.mark.asyncio
    async def test_renders_header_and_rows(self):
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
            context_args=_context_args(),
        )
        assert "<table" in html
        assert "Name" in html
        assert "Email" in html
        assert "Ada" in html
        assert "alan@example.com" in html
        # Two header cells + four body cells (trailing space avoids matching
        # <thead>).
        assert html.count("<th ") == 2
        assert html.count("<td ") == 4

    @pytest.mark.asyncio
    async def test_dotted_accessor_resolves_nested(self):
        html = await render_tree(
            DataTable()
            .columns([Column("City", accessor="address.city")])
            .data([{"address": {"city": "London"}}]),
            context_args=_context_args(),
        )
        assert "London" in html

    @pytest.mark.asyncio
    async def test_callable_accessor(self):
        html = await render_tree(
            DataTable()
            .columns([Column("Full", accessor=lambda r: f"{r['first']} {r['last']}")])
            .data([{"first": "Ada", "last": "Lovelace"}]),
            context_args=_context_args(),
        )
        assert "Ada Lovelace" in html

    @pytest.mark.asyncio
    async def test_custom_cell_render_function(self):
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
            context_args=_context_args(),
        )
        assert "ADA" in html

    @pytest.mark.asyncio
    async def test_empty_data_shows_empty_state(self):
        html = await render_tree(
            DataTable()
            .columns(
                [Column("Name", accessor="name"), Column("Email", accessor="email")]
            )
            .data([]),
            context_args=_context_args(),
        )
        assert "No results." in html
        assert 'role="status"' in html
        assert 'colspan="2"' in html

    @pytest.mark.asyncio
    async def test_caption_renders(self):
        html = await render_tree(
            DataTable()
            .columns([Column("Name", accessor="name")])
            .data([{"name": "Ada"}])
            .caption("Registered users"),
            context_args=_context_args(),
        )
        assert "<caption" in html
        assert "Registered users" in html

    @pytest.mark.asyncio
    async def test_id_and_class_apply_to_table(self):
        html = await render_tree(
            DataTable()
            .columns([Column("Name", accessor="name")])
            .data([{"name": "Ada"}])
            .id("users-table")
            .class_("custom-class"),
            context_args=_context_args(),
        )
        assert 'id="users-table"' in html
        assert "custom-class" in html
