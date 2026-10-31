import re

import pytest

from hue.renderer import render_tree
from hue.ui import Button
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestButton:
    @pytest.mark.parametrize(
        ("button", "type_"),
        [(Button(), "button"), (Button().type("submit"), "submit")],
    )
    @pytest.mark.asyncio
    async def test_it_submits_only_when_asked(self, context_args, button, type_):
        # A bare button inside a form would otherwise submit it.
        html = await render_tree(button.content("Go"), context_args=context_args)
        assert_attr(html, "button", "type", type_)

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

    @pytest.mark.parametrize(("value", "disabled"), [(True, True), (False, False)])
    @pytest.mark.asyncio
    async def test_disabled(self, context_args, value, disabled):
        # Boolean attributes are true by presence; disabled="false" would still
        # disable the button.
        html = await render_tree(
            Button().disabled(value).content("Go"), context_args=context_args
        )
        assert bool(select(html, "button[disabled]")) is disabled

    @pytest.mark.asyncio
    async def test_an_icon_only_button_is_named(self, context_args):
        html = await render_tree(
            Button().icon_only("Add project").content("+"), context_args=context_args
        )
        assert_attr(html, "button", "aria-label", "Add project")

    @pytest.mark.asyncio
    async def test_loading_announces_busy_and_blocks_a_second_submit(
        self, context_args
    ):
        html = await render_tree(
            Button().loading().content("Save"), context_args=context_args
        )
        assert_attr(html, "button", "aria-busy", "true")
        assert_attr(html, "button", "disabled")
        # The label stays rendered so the width and the accessible name hold:
        # opacity, not visibility, which drops it from the a11y tree.
        assert "Save" in html
        assert_selector(html, "button > span.opacity-0")
        assert_no_selector(html, "button > span.invisible")
        assert_attr(html, "span.animate-spinner", "aria-hidden", "true")
