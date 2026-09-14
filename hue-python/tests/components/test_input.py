import pytest

from hue.renderer import render_tree
from hue.ui import EmailInput, NumberInput, PasswordInput, TextInput
from tests._a11y import (
    assert_attr,
    assert_label_for,
    assert_no_selector,
    assert_selector,
)


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
        assert_no_selector(html, "input[disabled]")

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


class TestInputStates:
    @pytest.mark.asyncio
    async def test_constructor_name(self, context_args):
        html = await render_tree(TextInput("username"), context_args=context_args)
        assert_attr(html, "input", "name", "username")

    @pytest.mark.asyncio
    async def test_requires_name(self, context_args):
        with pytest.raises(ValueError, match="requires a name"):
            await render_tree(TextInput().label("No name"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_disabled_and_required_are_native(self, context_args):
        # aria-* alone would leave the field editable and skip browser validation.
        html = await render_tree(
            TextInput("f").disabled().required(), context_args=context_args
        )
        assert_attr(html, "input", "disabled")
        assert_attr(html, "input", "required")

    @pytest.mark.asyncio
    async def test_enabled_and_optional_by_default(self, context_args):
        html = await render_tree(TextInput("f"), context_args=context_args)
        assert_no_selector(html, "input[disabled]")
        assert_no_selector(html, "input[required]")
        assert_no_selector(html, "input[aria-invalid]")
        assert_no_selector(html, "input[aria-describedby]")

    @pytest.mark.asyncio
    async def test_length_constraints_use_html_attribute_names(self, context_args):
        html = await render_tree(
            TextInput("f").min_length(2).max_length(8), context_args=context_args
        )
        assert_attr(html, "input", "minlength", "2")
        assert_attr(html, "input", "maxlength", "8")

    @pytest.mark.asyncio
    async def test_hint_describes_input(self, context_args):
        html = await render_tree(
            TextInput("f").hint("Some help"), context_args=context_args
        )
        assert_attr(html, "input", "aria-describedby", "f-hint")
        assert_selector(html, "#f-hint")
        assert "Some help" in html

    @pytest.mark.asyncio
    async def test_error_marks_invalid_and_describes_the_input(self, context_args):
        # Described rather than pointed at with aria-errormessage, whose
        # screen-reader support is still patchy.
        html = await render_tree(
            TextInput("f").error("Too short"), context_args=context_args
        )
        assert_attr(html, "input", "aria-invalid", "true")
        assert_no_selector(html, "[aria-errormessage]")
        assert_attr(html, "input", "aria-describedby", "f-error")
        assert_selector(html, '[role="alert"]#f-error')

    @pytest.mark.asyncio
    async def test_an_error_replaces_the_hint(self, context_args):
        # Two lines of supporting text under one control is one more than
        # anybody reads.
        html = await render_tree(
            TextInput("f").hint("Some help").error("Too short"),
            context_args=context_args,
        )
        assert "Some help" not in html
        assert_attr(html, "input", "aria-describedby", "f-hint f-error")

    @pytest.mark.asyncio
    async def test_caller_describedby_is_merged(self, context_args):
        html = await render_tree(
            TextInput("f").hint("Help").aria_describedby("external"),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-describedby", "f-hint external")

    @pytest.mark.asyncio
    async def test_class_applies_to_input(self, context_args):
        html = await render_tree(
            TextInput("f").class_("custom"), context_args=context_args
        )
        assert_selector(html, "input.custom")

    # hidden_label() conditional: both branches
    @pytest.mark.asyncio
    async def test_hidden_label_is_screen_reader_only(self, context_args):
        html = await render_tree(
            TextInput("f").label("F").hidden_label(), context_args=context_args
        )
        assert_selector(html, "label.sr-only")

    @pytest.mark.asyncio
    async def test_label_visible_by_default(self, context_args):
        html = await render_tree(TextInput("f").label("F"), context_args=context_args)
        assert_no_selector(html, "label.sr-only")
