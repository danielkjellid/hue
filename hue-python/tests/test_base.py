"""Tests for the shared ChainableComponent modifiers.

These live here (not per component) because every component inherits them — they
are exercised once, using Button as a concrete vehicle.
"""

import pytest
from htmy import Renderer

from hue.exceptions import MissingHueContextError
from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Button


class TestChainableComponent:
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

    def test_content_sets_children(self):
        btn = Button().content("a", "b")
        assert btn._children == ("a", "b")

    def test_aria_modifiers(self):
        btn = (
            Button()
            .aria_label("close")
            .aria_hidden("true")
            .aria_expanded("false")
            .aria_controls("panel-1")
            .aria_busy("true")
            .aria_keyshortcuts("Escape")
            .role("dialog")
        )
        attrs = btn._get_base_html_attrs()
        assert attrs["aria_label"] == "close"
        assert attrs["aria_hidden"] == "true"
        assert attrs["aria_expanded"] == "false"
        assert attrs["aria_controls"] == "panel-1"
        assert attrs["aria_busy"] == "true"
        assert attrs["aria_keyshortcuts"] == "Escape"
        assert attrs["role"] == "dialog"

    @pytest.mark.asyncio
    async def test_data_is_a_data_attribute(self, context_args):
        html = await render_tree(
            Button().data("filter-label", "Status").content("Hi"),
            context_args=context_args,
        )
        assert 'data-filter-label="Status"' in html

    def test_base_html_attrs_omits_none(self):
        btn = Button().id("my-id")
        assert btn._get_base_html_attrs() == {"id": "my-id"}

    @pytest.mark.asyncio
    async def test_render_without_hue_context_raises(self):
        with pytest.raises(MissingHueContextError):
            await Renderer().render(Button().content("Hi"))


class TestAlpinePluginModifiers:
    """x-trap and x-anchor build their modifiers into the attribute name."""

    def test_trap_without_modifiers(self):
        attrs = Button().x_trap(unsafe("open"))._get_base_html_attrs()
        assert attrs == {"x-trap": "open"}

    def test_trap_with_modifiers_keeps_alpine_order(self):
        attrs = (
            Button()
            .x_trap(unsafe("open"), noscroll=True, inert=True)
            ._get_base_html_attrs()
        )
        assert attrs == {"x-trap.inert.noscroll": "open"}

    def test_trap_omits_modifiers_left_off(self):
        attrs = Button().x_trap(unsafe("open"), noreturn=True)._get_base_html_attrs()
        assert attrs == {"x-trap.noreturn": "open"}

    def test_anchor_without_placement_or_offset(self):
        attrs = Button().x_anchor(unsafe("$refs.trigger"))._get_base_html_attrs()
        assert attrs == {"x-anchor": "$refs.trigger"}

    def test_anchor_with_placement(self):
        attrs = (
            Button()
            .x_anchor(unsafe("$refs.trigger"), "bottom-start")
            ._get_base_html_attrs()
        )
        assert attrs == {"x-anchor.bottom-start": "$refs.trigger"}

    def test_anchor_with_placement_and_offset(self):
        attrs = (
            Button()
            .x_anchor(unsafe("$refs.trigger"), "top-end", offset=6)
            ._get_base_html_attrs()
        )
        assert attrs == {"x-anchor.top-end.offset.6": "$refs.trigger"}

    def test_anchor_offset_without_placement(self):
        attrs = (
            Button().x_anchor(unsafe("$refs.trigger"), offset=0)._get_base_html_attrs()
        )
        assert attrs == {"x-anchor.offset.0": "$refs.trigger"}

    @pytest.mark.asyncio
    async def test_modifiers_survive_rendering(self, context_args):
        html = await render_tree(
            Button()
            .x_trap(unsafe("open"), inert=True)
            .x_anchor(unsafe("$refs.t"), "bottom"),
            context_args=context_args,
        )
        assert 'x-trap.inert="open"' in html
        assert 'x-anchor.bottom="$refs.t"' in html
