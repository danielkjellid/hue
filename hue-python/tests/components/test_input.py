import pytest

from hue.renderer import render_tree
from hue.ui import EmailInput, NumberInput, PasswordInput, TextInput
from tests._a11y import assert_attr, assert_label_for


class TestTextInput:
    @pytest.mark.asyncio
    async def test_render_basic(self, context_args):
        html = await render_tree(
            TextInput().name("username").label("Username"), context_args=context_args
        )
        assert_attr(html, "input", "type", "text")
        assert_attr(html, "input", "name", "username")
        assert "Username" in html

    @pytest.mark.asyncio
    async def test_label_associated_with_input(self, context_args):
        """Accessibility: label's `for` must match the input's id."""
        html = await render_tree(
            TextInput().name("email").label("Email"), context_args=context_args
        )
        assert_label_for(html, "email")

    @pytest.mark.asyncio
    async def test_explicit_id_links_input_and_label(self, context_args):
        html = await render_tree(
            TextInput().name("email").label("Email").id("custom-id"),
            context_args=context_args,
        )
        assert_label_for(html, "custom-id")

    @pytest.mark.asyncio
    async def test_placeholder(self, context_args):
        html = await render_tree(
            TextInput().name("name").label("Name").placeholder("Enter name"),
            context_args=context_args,
        )
        assert_attr(html, "input", "placeholder", "Enter name")

    # disabled() conditional — both branches
    @pytest.mark.asyncio
    async def test_disabled(self, context_args):
        html = await render_tree(
            TextInput().name("f").label("F").disabled(), context_args=context_args
        )
        assert "cursor-not-allowed" in html

    @pytest.mark.asyncio
    async def test_not_disabled(self, context_args):
        html = await render_tree(
            TextInput().name("f").label("F"), context_args=context_args
        )
        assert "cursor-not-allowed" not in html

    @pytest.mark.asyncio
    async def test_forwards_base_attrs_to_input(self, context_args):
        html = await render_tree(
            TextInput()
            .name("email")
            .label("Email")
            .role("searchbox")
            .aria_describedby("hint")
            .x_model("form.email"),
            context_args=context_args,
        )
        assert_attr(html, "input", "role", "searchbox")
        assert_attr(html, "input", "aria-describedby", "hint")
        assert "x-model" in html


class TestTypedInputs:
    @pytest.mark.asyncio
    async def test_email_type_and_autocomplete(self, context_args):
        html = await render_tree(
            EmailInput().name("email").label("Email"), context_args=context_args
        )
        assert_attr(html, "input", "type", "email")
        assert_attr(html, "input", "autocomplete", "email")

    @pytest.mark.asyncio
    async def test_password_type_and_autocomplete(self, context_args):
        html = await render_tree(
            PasswordInput().name("pwd").label("Password"), context_args=context_args
        )
        assert_attr(html, "input", "type", "password")
        assert_attr(html, "input", "autocomplete", "current-password")

    @pytest.mark.asyncio
    async def test_number_min_max_step(self, context_args):
        html = await render_tree(
            NumberInput().name("qty").label("Quantity").min(1).max(100).step(1),
            context_args=context_args,
        )
        assert_attr(html, "input", "type", "number")
        assert_attr(html, "input", "min", "1")
        assert_attr(html, "input", "max", "100")
        assert_attr(html, "input", "step", "1")
