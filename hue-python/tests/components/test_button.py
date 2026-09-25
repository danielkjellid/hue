import re

import pytest

from hue.renderer import render_tree
from hue.ui import Button
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestButton:
    @pytest.mark.asyncio
    async def test_render_basic(self, context_args):
        html = await render_tree(Button().content("Click"), context_args=context_args)
        assert_attr(html, "button", "type", "button")
        assert "Click" in html

    @pytest.mark.asyncio
    async def test_a_button_can_submit_a_form_it_is_not_in(self, context_args):
        html = await render_tree(
            Button()
            .type("submit")
            .form("invoices-act")
            .formaction("/archive/")
            .content("Archive"),
            context_args=context_args,
        )
        assert_attr(html, "button", "form", "invoices-act")
        assert_attr(html, "button", "formaction", "/archive/")

    @pytest.mark.asyncio
    async def test_render_submit_type(self, context_args):
        html = await render_tree(
            Button().type("submit").content("Send"), context_args=context_args
        )
        assert_attr(html, "button", "type", "submit")

    @pytest.mark.asyncio
    async def test_focus_visible_styles_present(self, context_args):
        # Keyboard users must get a visible ring; mouse users must not get one
        # on click, which is why it is focus-visible and not focus.
        html = await render_tree(
            Button().content("Tab to me"), context_args=context_args
        )
        assert "focus-visible:ring-2" in html
        assert "focus:ring-2" not in html

    # variant(): each one renders its own fill, and hover moves the background
    # rather than the foreground.
    @pytest.mark.asyncio
    async def test_default_variant_is_primary(self, context_args):
        html = await render_tree(Button().content("Go"), context_args=context_args)
        assert_selector(html, "button.bg-accent")

    @pytest.mark.asyncio
    async def test_outline_variant(self, context_args):
        html = await render_tree(
            Button().variant("outline").content("Go"), context_args=context_args
        )
        assert_selector(html, "button.border-border-input")

    @pytest.mark.parametrize(
        "variant",
        [
            "primary",
            "secondary",
            "outline",
            "ghost",
            "link",
            "danger",
            "danger-outline",
        ],
    )
    @pytest.mark.asyncio
    async def test_exactly_one_border_colour_per_variant(self, variant, context_args):
        # Two border-color utilities on one element resolve by stylesheet order,
        # not by the order they are written, so a shared base border-transparent
        # silently beat the outline variants' colours and left them borderless.
        html = await render_tree(
            Button().variant(variant).content("Go"), context_args=context_args
        )
        classes = select(html, "button")[0]["class"]
        colours = [c for c in classes if re.fullmatch(r"border-(?!\d)[a-z-]+", c)]
        assert len(colours) == 1, f"{variant} has competing borders: {colours}"

    @pytest.mark.asyncio
    async def test_danger_variant_uses_the_on_fill_foreground(self, context_args):
        html = await render_tree(
            Button().variant("danger").content("Delete"), context_args=context_args
        )
        assert_selector(html, "button.bg-danger")
        assert_selector(html, "button.text-danger-fg")

    @pytest.mark.asyncio
    async def test_link_variant_drops_the_control_box(self, context_args):
        # A link button is text in a sentence, so it must not carry a control
        # height or horizontal padding.
        html = await render_tree(
            Button().variant("link").content("Learn more"), context_args=context_args
        )
        assert_selector(html, "button.h-auto")
        assert_no_selector(html, "button.h-control-md")
        assert_selector(html, "button.underline")

    # size(): drives height and type scale together
    @pytest.mark.asyncio
    async def test_default_size_is_md(self, context_args):
        html = await render_tree(Button().content("Go"), context_args=context_args)
        assert_selector(html, "button.h-control-md")
        assert_selector(html, "button.text-base")

    @pytest.mark.asyncio
    async def test_explicit_size(self, context_args):
        html = await render_tree(
            Button().size("lg").content("Go"), context_args=context_args
        )
        assert_selector(html, "button.h-control-lg")
        assert_selector(html, "button.text-md")

    # shape(): both branches
    @pytest.mark.asyncio
    async def test_default_shape_is_rounded(self, context_args):
        html = await render_tree(Button().content("Go"), context_args=context_args)
        assert_selector(html, "button.rounded-md")

    @pytest.mark.asyncio
    async def test_a_pill_rounds_the_ends(self, context_args):
        html = await render_tree(
            Button().pill().content("Go"), context_args=context_args
        )
        assert_selector(html, "button.rounded-full")
        assert_no_selector(html, "button.rounded-md")

    # disabled(): both branches, including an explicit False
    @pytest.mark.asyncio
    async def test_render_disabled(self, context_args):
        html = await render_tree(
            Button().disabled().content("No"), context_args=context_args
        )
        assert_attr(html, "button", "disabled")

    @pytest.mark.asyncio
    async def test_render_not_disabled(self, context_args):
        html = await render_tree(Button().content("Yes"), context_args=context_args)
        assert_selector(html, "button:not([disabled])")

    @pytest.mark.asyncio
    async def test_disabled_false_omits_attribute(self, context_args):
        # Boolean attributes are true by presence; disabled="false" would still
        # disable the button.
        html = await render_tree(
            Button().disabled(False).content("Yes"), context_args=context_args
        )
        assert_no_selector(html, "button[disabled]")

    # fluid(): both branches. Not fluid is the default, so a button in a row of
    # buttons does not have to opt out of filling the row.
    @pytest.mark.asyncio
    async def test_not_fluid_by_default(self, context_args):
        html = await render_tree(Button().content("Go"), context_args=context_args)
        assert_no_selector(html, "button.w-full")

    @pytest.mark.asyncio
    async def test_fluid(self, context_args):
        html = await render_tree(
            Button().fluid().content("Go"), context_args=context_args
        )
        assert_selector(html, "button.w-full")

    # icon_only(): both branches
    @pytest.mark.asyncio
    async def test_icon_only_is_square_and_named(self, context_args):
        html = await render_tree(
            Button().icon_only("Add project").content("+"), context_args=context_args
        )
        assert_attr(html, "button", "aria-label", "Add project")
        assert_selector(html, "button.w-control-md")
        # Square means no horizontal padding fighting the fixed width.
        assert_no_selector(html, "button.px-3\\.5")

    @pytest.mark.asyncio
    async def test_text_button_is_not_square_or_labelled(self, context_args):
        html = await render_tree(Button().content("Go"), context_args=context_args)
        assert_no_selector(html, "button[aria-label]")
        assert_no_selector(html, "button.w-control-md")
        assert_selector(html, "button.px-3\\.5")

    @pytest.mark.asyncio
    async def test_icon_only_ignores_fluid(self, context_args):
        # A square button that also fills the row is a contradiction.
        html = await render_tree(
            Button().icon_only("Add").fluid().content("+"), context_args=context_args
        )
        assert_no_selector(html, "button.w-full")

    # loading(): both branches
    @pytest.mark.asyncio
    async def test_loading_keeps_the_label_and_announces_busy(self, context_args):
        html = await render_tree(
            Button().loading().content("Save"), context_args=context_args
        )
        assert_attr(html, "button", "aria-busy", "true")
        # The label stays rendered so the width and the accessible name hold.
        assert "Save" in html
        assert_selector(html, "button > span.opacity-0")
        # opacity, not visibility: the latter drops it from the a11y tree.
        assert_no_selector(html, "button > span.invisible")
        assert_selector(html, "span.animate-spinner")

    @pytest.mark.asyncio
    async def test_loading_blocks_a_second_submit(self, context_args):
        html = await render_tree(
            Button().loading().content("Save"), context_args=context_args
        )
        assert_attr(html, "button", "disabled")
        # It is disabled to stop a double submit, but must not also read as
        # greyed out - the spinner already explains why it cannot be pressed.
        assert_no_selector(html, "button.disabled\\:opacity-45")

    @pytest.mark.asyncio
    async def test_not_loading(self, context_args):
        html = await render_tree(Button().content("Save"), context_args=context_args)
        assert_no_selector(html, "button[aria-busy]")
        assert_no_selector(html, "span.animate-spinner")
        assert_selector(html, "button.disabled\\:opacity-45")

    @pytest.mark.asyncio
    async def test_loading_spinner_is_decorative(self, context_args):
        html = await render_tree(
            Button().loading().content("Save"), context_args=context_args
        )
        spinner = select(html, "span.animate-spinner")[0]
        assert spinner["aria-hidden"] == "true"
