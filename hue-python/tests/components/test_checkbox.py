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
        # No asterisk: the native required attribute announces it, and the
        # guide does not mark a choice row the way it marks a field label.
        assert_no_selector(html, "span.text-danger-text")

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
    async def test_the_description_describes_rather_than_names(self, context_args):
        # Wrapping the control in a label makes every word inside it part of
        # the name, so without this a screen reader reads the whole sentence
        # before getting to "checkbox".
        html = await render_tree(
            Checkbox().name("opt").label("Opt").description("Optional setting"),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-labelledby", "opt-label")
        assert_attr(html, "input", "aria-describedby", "opt-description")
        assert_selector(html, "#opt-label")
        assert_selector(html, "#opt-description")

    @pytest.mark.asyncio
    async def test_a_choice_has_no_field_hint(self, context_args):
        # It says its extra line with description(), beside the box, rather
        # than under the whole row where a field puts its hint.
        assert not hasattr(Checkbox(), "hint")

    @pytest.mark.asyncio
    async def test_error_marks_invalid(self, context_args):
        html = await render_tree(
            Checkbox().name("c").label("C").error("This is required"),
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
    async def test_the_dash_wins_over_the_tick(self, context_args):
        html = await render_tree(
            Checkbox().name("x").label("X"), context_args=context_args
        )
        # Both marks are drawn by the box itself, so the tick has to exclude
        # the mixed state rather than rely on which rule Tailwind emits last.
        assert "checked:not-indeterminate:before:content-['']" in html
        assert "indeterminate:before:content-['']" in html
        assert_no_selector(html, "svg")

    @pytest.mark.asyncio
    async def test_forwards_x_model_to_input(self, context_args):
        html = await render_tree(
            Checkbox().name("v").label("V").x_model("form.v"),
            context_args=context_args,
        )
        assert_attr(html, "input", "x-model", "form.v")

    @pytest.mark.asyncio
    async def test_text_column_omitted_when_no_label_or_text(self, context_args):
        # With no label/hint/error, only the box renders — no text column.
        html = await render_tree(Checkbox().name("bare"), context_args=context_args)
        assert_selector(html, "input[type='checkbox']")
        assert_no_selector(html, "span.flex-col")

    @pytest.mark.asyncio
    async def test_constructor_name(self, context_args):
        html = await render_tree(Checkbox().name("terms"), context_args=context_args)
        assert_attr(html, "input", "name", "terms")

    @pytest.mark.asyncio
    async def test_checked_false_omits_attribute(self, context_args):
        # checked="false" would still check the box.
        html = await render_tree(
            Checkbox().name("a").checked(False), context_args=context_args
        )
        assert_no_selector(html, "input[checked]")

    @pytest.mark.asyncio
    async def test_the_whole_row_is_the_hit_area(self, context_args):
        # The label wraps the control, so the text is part of the target
        # rather than something to aim past on the way to an 18px box.
        html = await render_tree(
            Checkbox().name("a").label("Accept"), context_args=context_args
        )
        assert_selector(html, "label > input[type='checkbox']")

    @pytest.mark.asyncio
    async def test_class_applies_to_root(self, context_args):
        html = await render_tree(
            Checkbox().name("a").class_("mt-4"), context_args=context_args
        )
        assert_selector(html, "div.flex.flex-col.mt-4")

    # variant(): both branches
    @pytest.mark.asyncio
    async def test_a_card_reacts_to_its_own_control(self, context_args):
        # The fill follows :checked through :has, so nothing has to be
        # mirrored in Alpine to keep the surface in step with the box.
        html = await render_tree(
            Checkbox().name("plan").label("Pro").card(),
            context_args=context_args,
        )
        assert_selector(html, "label.has-\\[\\:checked\\]\\:bg-accent-subtle")

    @pytest.mark.asyncio
    async def test_inline_by_default(self, context_args):
        html = await render_tree(
            Checkbox().name("plan").label("Pro"), context_args=context_args
        )
        assert_no_selector(html, "label.p-4")

    # description(): both branches
    @pytest.mark.asyncio
    async def test_a_description_sits_under_the_label(self, context_args):
        html = await render_tree(
            Checkbox()
            .name("plan")
            .label("Pro")
            .description("Everything in Free, plus SSO."),
            context_args=context_args,
        )
        assert_selector(html, "span.text-fg-muted")
        assert "Everything in Free, plus SSO." in html

    @pytest.mark.asyncio
    async def test_no_description_by_default(self, context_args):
        html = await render_tree(
            Checkbox().name("plan").label("Pro"), context_args=context_args
        )
        assert_no_selector(html, "span.text-fg-muted")
