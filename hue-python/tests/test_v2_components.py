import pytest

from hue.context import HueContextArgs
from hue.renderer import render_tree
from hue.ui.v2 import (
    Button,
    EmailInput,
    Label,
    NumberInput,
    PasswordInput,
    Spacer,
    Stack,
    TextInput,
    Text,
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
        from htmy import html as htmy_html

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
        # Required by default → asterisk
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
            Spacer("lg"),
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
