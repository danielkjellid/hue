from typing import get_args

import pytest

from hue.renderer import render_tree
from hue.ui import Button, ButtonGroup
from hue.ui.atoms.button import ButtonVariant
from hue.ui.molecules.button_group import _SUPPORTED_VARIANTS
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _group():
    return ButtonGroup().content(
        Button().variant("outline").content("Export"),
        Button().variant("outline").content("Schedule"),
    )


class TestButtonGroup:
    def test_every_supported_variant_is_a_real_one(self):
        # A renamed Button variant would otherwise leave a dead string in the
        # allowlist, quietly rejecting the variant it used to name. ButtonVariant
        # is a PEP 695 alias, so the Literal is behind __value__.
        assert _SUPPORTED_VARIANTS <= set(get_args(ButtonVariant.__value__))

    # A group is made of its buttons' borders, so a variant without a box has
    # nothing to join and would render as loose text.
    @pytest.mark.parametrize(
        ("variant", "joins"),
        [
            ("outline", True),
            ("danger-outline", True),
            ("ghost", False),
            ("link", False),
        ],
    )
    @pytest.mark.asyncio
    async def test_joins_only_buttons_with_a_box(self, variant, joins, context_args):
        group = ButtonGroup().content(Button().variant(variant).content("Day"))
        if joins:
            assert_selector(
                await render_tree(group, context_args=context_args), "button"
            )
        else:
            with pytest.raises(ValueError, match="cannot join"):
                await render_tree(group, context_args=context_args)

    @pytest.mark.asyncio
    async def test_a_label_makes_it_a_named_group(self, context_args):
        html = await render_tree(
            _group().label("Export options"), context_args=context_args
        )
        assert_attr(html, 'div[role="group"]', "aria-label", "Export options")

    @pytest.mark.asyncio
    async def test_without_a_label_it_is_not_a_group(self, context_args):
        # A group role with no name announces "group" and nothing else.
        html = await render_tree(_group(), context_args=context_args)
        assert_no_selector(html, '[role="group"]')
