import pytest

from hue.renderer import render_tree
from hue.ui import Checkbox
from tests._a11y import (
    assert_attr,
    assert_label_for,
    assert_no_selector,
    assert_selector,
)


class TestCheckbox:
    @pytest.mark.asyncio
    async def test_renders_native_checkbox_input(self, context_args):
        html = await render_tree(
            Checkbox().name("terms").label("Accept"), context_args=context_args
        )
        assert_attr(html, "input", "type", "checkbox")
        assert_attr(html, "input", "name", "terms")
        assert "Accept" in html

    @pytest.mark.asyncio
    async def test_requires_name(self, context_args):
        with pytest.raises(ValueError, match="requires a name"):
            await render_tree(Checkbox().label("No name"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_label_associated_with_input(self, context_args):
        html = await render_tree(
            Checkbox().name("subscribe").label("Subscribe"), context_args=context_args
        )
        assert_label_for(html, "subscribe")

    # checked() / required() — present vs absent
    @pytest.mark.asyncio
    async def test_checked_and_required(self, context_args):
        html = await render_tree(
            Checkbox().name("a").label("A").checked().required(),
            context_args=context_args,
        )
        assert_attr(html, "input", "checked")
        assert_attr(html, "input", "required")
        # Required fields show a destructive asterisk beside the label.
        assert_selector(html, "span.text-destructive")

    @pytest.mark.asyncio
    async def test_unchecked_and_optional_by_default(self, context_args):
        html = await render_tree(
            Checkbox().name("a").label("A"), context_args=context_args
        )
        assert_no_selector(html, "input[checked]")
        assert_no_selector(html, "input[required]")
        assert_no_selector(html, "span.text-destructive")

    # disabled() — both branches
    @pytest.mark.asyncio
    async def test_disabled(self, context_args):
        html = await render_tree(
            Checkbox().name("d").label("D").disabled(), context_args=context_args
        )
        assert_attr(html, "input", "disabled")
        assert_selector(html, "label.cursor-not-allowed")

    @pytest.mark.asyncio
    async def test_enabled_by_default(self, context_args):
        html = await render_tree(
            Checkbox().name("d").label("D"), context_args=context_args
        )
        assert_no_selector(html, "input[disabled]")
        assert_selector(html, "label.cursor-pointer")

    @pytest.mark.asyncio
    async def test_indeterminate_sets_property_via_alpine(self, context_args):
        # The indeterminate DOM property has no HTML attribute, so it is set on
        # init via Alpine.
        html = await render_tree(
            Checkbox().name("all").label("All").indeterminate(),
            context_args=context_args,
        )
        assert_attr(html, "input", "x-init", "$el.indeterminate = true")

    @pytest.mark.asyncio
    async def test_help_text_describes_input(self, context_args):
        html = await render_tree(
            Checkbox().name("opt").label("Opt").help_text("Optional setting"),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-describedby", "opt-description")
        assert_selector(html, "#opt-description")
        assert "Optional setting" in html

    @pytest.mark.asyncio
    async def test_error_text_marks_invalid(self, context_args):
        html = await render_tree(
            Checkbox().name("c").label("C").error_text("This is required"),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-invalid", "true")
        assert_attr(html, "input", "aria-describedby", "c-error")
        assert_selector(html, '[role="alert"]#c-error')
        assert "This is required" in html

    @pytest.mark.asyncio
    async def test_valid_with_no_description_by_default(self, context_args):
        html = await render_tree(
            Checkbox().name("c").label("C"), context_args=context_args
        )
        assert_no_selector(html, "input[aria-invalid]")
        assert_no_selector(html, "input[aria-describedby]")
        assert_no_selector(html, '[role="alert"]')

    @pytest.mark.asyncio
    async def test_renders_check_and_dash_icons(self, context_args):
        html = await render_tree(
            Checkbox().name("x").label("X"), context_args=context_args
        )
        # The check shows only when checked and not indeterminate; the dash shows
        # on the mixed state — so the dash always wins when both are set.
        assert "peer-[:checked:not(:indeterminate)]:block" in html
        assert "peer-indeterminate:block" in html
        assert_selector(html, "svg path")

    @pytest.mark.asyncio
    async def test_forwards_x_model_to_input(self, context_args):
        html = await render_tree(
            Checkbox().name("v").label("V").x_model("form.v"),
            context_args=context_args,
        )
        assert_attr(html, "input", "x-model", "form.v")

    @pytest.mark.asyncio
    async def test_text_column_omitted_when_no_label_or_text(self, context_args):
        # With no label/help/error, only the box renders — no text column.
        html = await render_tree(Checkbox().name("bare"), context_args=context_args)
        assert_selector(html, "input[type='checkbox']")
        assert_no_selector(html, "div.flex-col")
