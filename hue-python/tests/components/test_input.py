import pytest

from hue.js import unsafe
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
    async def test_a_named_text_input_with_its_label(self, context_args):
        html = await render_tree(
            TextInput().name("username").label("Username"), context_args=context_args
        )
        assert_attr(html, "input", "type", "text")
        assert_attr(html, "input", "name", "username")
        assert_label_for(html, "username")

    @pytest.mark.asyncio
    async def test_explicit_id_links_input_and_label(self, context_args):
        html = await render_tree(
            TextInput().name("email").label("Email").id("custom-id"),
            context_args=context_args,
        )
        assert_label_for(html, "custom-id")

    @pytest.mark.asyncio
    async def test_forwards_base_attrs_to_input(self, context_args):
        html = await render_tree(
            TextInput()
            .name("email")
            .label("Email")
            .role("searchbox")
            .aria_describedby("hint")
            .x_model(unsafe("form.email")),
            context_args=context_args,
        )
        assert_attr(html, "input", "role", "searchbox")
        assert_attr(html, "input", "aria-describedby", "hint")
        assert "x-model" in html

    @pytest.mark.asyncio
    async def test_requires_name(self, context_args):
        with pytest.raises(ValueError, match="requires a name"):
            await render_tree(TextInput().label("No name"), context_args=context_args)


class TestTypedInputs:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("control", "type_", "autocomplete"),
        [
            (EmailInput, "email", "email"),
            (PasswordInput, "password", "current-password"),
            (NumberInput, "number", None),
        ],
    )
    async def test_type_and_autocomplete(
        self, context_args, control, type_, autocomplete
    ):
        html = await render_tree(control().name("f"), context_args=context_args)
        assert_attr(html, "input", "type", type_)
        if autocomplete:
            assert_attr(html, "input", "autocomplete", autocomplete)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("number", "inputmode"),
        [
            (NumberInput().min(0), "numeric"),
            (NumberInput().min(0).step(5), "numeric"),
            (NumberInput().min(0).step(0.01), "decimal"),
            (NumberInput().min(0).step("any"), "decimal"),
            # Both keypads lack a minus sign, so type=number picks the keyboard.
            (NumberInput(), None),
            (NumberInput().min(-10), None),
            (NumberInput().min(-10).step(0.5), None),
        ],
    )
    async def test_number_inputmode_follows_step(self, context_args, number, inputmode):
        # numeric is a digits-only keypad on iOS, with no decimal separator.
        html = await render_tree(number.name("n"), context_args=context_args)
        if inputmode:
            assert_attr(html, "input", "inputmode", inputmode)
        else:
            assert_no_selector(html, "input[inputmode]")


class TestInputStates:
    @pytest.mark.asyncio
    async def test_disabled_and_required_are_native(self, context_args):
        # aria-* alone would leave the field editable and skip browser validation.
        html = await render_tree(
            TextInput().name("f").disabled().required(), context_args=context_args
        )
        assert_attr(html, "input", "disabled")
        assert_attr(html, "input", "required")

    @pytest.mark.asyncio
    async def test_a_plain_input_is_valid_and_described_by_nothing(self, context_args):
        html = await render_tree(TextInput().name("f"), context_args=context_args)
        assert_no_selector(html, "input[aria-invalid]")
        assert_no_selector(html, "input[aria-describedby]")

    @pytest.mark.asyncio
    async def test_length_constraints_use_html_attribute_names(self, context_args):
        html = await render_tree(
            TextInput().name("f").min_length(2).max_length(8), context_args=context_args
        )
        assert_attr(html, "input", "minlength", "2")
        assert_attr(html, "input", "maxlength", "8")

    @pytest.mark.asyncio
    async def test_hint_describes_input(self, context_args):
        html = await render_tree(
            TextInput().name("f").hint("Some help"), context_args=context_args
        )
        assert_attr(html, "input", "aria-describedby", "f-hint")
        assert_selector(html, "#f-hint")
        assert "Some help" in html

    @pytest.mark.asyncio
    async def test_error_marks_invalid_and_describes_the_input(self, context_args):
        # Described rather than pointed at with aria-errormessage, whose
        # screen-reader support is still patchy.
        html = await render_tree(
            TextInput().name("f").error("Too short"), context_args=context_args
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
            TextInput().name("f").hint("Some help").error("Too short"),
            context_args=context_args,
        )
        assert "Some help" not in html
        assert_attr(html, "input", "aria-describedby", "f-error")

    @pytest.mark.asyncio
    async def test_caller_describedby_is_merged(self, context_args):
        html = await render_tree(
            TextInput().name("f").hint("Help").aria_describedby("external"),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-describedby", "f-hint external")

    @pytest.mark.asyncio
    async def test_hidden_label_is_screen_reader_only(self, context_args):
        html = await render_tree(
            TextInput().name("f").label("F").hidden_label(), context_args=context_args
        )
        assert_selector(html, "label.sr-only")
