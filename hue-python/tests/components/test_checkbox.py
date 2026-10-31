import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Checkbox
from tests._a11y import (
    assert_attr,
    assert_label_for,
    assert_no_selector,
    assert_selector,
    select,
)


class TestCheckbox:
    @pytest.mark.asyncio
    async def test_a_native_checkbox_inside_its_label(self, context_args):
        # The label wraps the control, so the text is part of the target
        # rather than something to aim past on the way to an 18px box.
        html = await render_tree(
            Checkbox().name("terms").label("Accept").x_model(unsafe("form.terms")),
            context_args=context_args,
        )
        assert_selector(html, "label > input[type='checkbox']")
        assert_attr(html, "input", "name", "terms")
        assert_attr(html, "input", "x-model", "form.terms")
        assert_label_for(html, "terms")
        assert_attr(html, "input", "aria-labelledby", "terms-label")

    @pytest.mark.asyncio
    async def test_requires_name(self, context_args):
        with pytest.raises(ValueError, match="requires a name"):
            await render_tree(Checkbox().label("No name"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_boxes_sharing_a_name_are_told_apart_by_value(self, context_args):
        # One id between them, and the label of the second toggles the first.
        html = await render_tree(
            Checkbox().name("tags").value("north america").label("NA"),
            context_args=context_args,
        )
        assert_label_for(html, "tags-north%20america")
        assert_attr(html, "input", "aria-labelledby", "tags-north%20america-label")

    @pytest.mark.asyncio
    async def test_values_that_differ_only_in_spacing_get_ids_of_their_own(
        self, context_args
    ):
        ids = set()
        for value in ("north america", "north-america", "a b", "a  b"):
            html = await render_tree(
                Checkbox().name("tags").value(value).label(value),
                context_args=context_args,
            )
            ids.add(select(html, "input")[0]["id"])
        assert len(ids) == 4

    @pytest.mark.asyncio
    async def test_an_explicit_id_wins_over_the_value(self, context_args):
        html = await render_tree(
            Checkbox().name("tags").value("a").label("A").id("own"),
            context_args=context_args,
        )
        assert_label_for(html, "own")

    @pytest.mark.asyncio
    async def test_checked_required_and_disabled_reach_the_input(self, context_args):
        html = await render_tree(
            Checkbox().name("a").label("A").checked().required().disabled(),
            context_args=context_args,
        )
        assert_attr(html, "input", "checked")
        assert_attr(html, "input", "required")
        assert_attr(html, "input", "disabled")

    @pytest.mark.asyncio
    async def test_checked_false_omits_attribute(self, context_args):
        # checked="false" would still check the box.
        html = await render_tree(
            Checkbox().name("a").checked(False), context_args=context_args
        )
        assert_no_selector(html, "input[checked]")

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
    async def test_the_dash_wins_over_the_tick(self, context_args):
        html = await render_tree(
            Checkbox().name("x").label("X"), context_args=context_args
        )
        # Both marks are drawn by the box itself, so the tick has to exclude
        # the mixed state rather than rely on which rule Tailwind emits last.
        assert "checked:not-indeterminate:before:content-['']" in html
        assert "indeterminate:before:content-['']" in html

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
    async def test_a_hidden_label_moves_onto_the_control(self, context_args):
        # Nothing on the page left to point at, so the name goes on the box,
        # and the id goes too: a column of these would otherwise share one.
        html = await render_tree(
            Checkbox().name("selected").label("Select INV-2050").hidden_label(),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-label", "Select INV-2050")
        assert_no_selector(html, "label")
        assert_no_selector(html, "input[id]")

    @pytest.mark.asyncio
    async def test_a_hidden_label_keeps_an_id_it_was_given(self, context_args):
        html = await render_tree(
            Checkbox().name("selected").label("Select all").hidden_label().id("all"),
            context_args=context_args,
        )
        assert_attr(html, "input", "id", "all")

    @pytest.mark.asyncio
    async def test_a_hidden_label_keeps_a_labelledby_it_was_given(self, context_args):
        # The box names itself "Select" and borrows the rest from its row.
        html = await render_tree(
            Checkbox()
            .name("selected")
            .label("Select")
            .hidden_label()
            .id("r1-select")
            .aria_labelledby("r1-select r1-name"),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-labelledby", "r1-select r1-name")

    @pytest.mark.asyncio
    async def test_a_visible_label_is_joined_by_a_labelledby_it_was_given(
        self, context_args
    ):
        html = await render_tree(
            Checkbox().name("terms").label("I accept").aria_labelledby("policy"),
            context_args=context_args,
        )
        assert_attr(html, "input", "aria-labelledby", "terms-label policy")
