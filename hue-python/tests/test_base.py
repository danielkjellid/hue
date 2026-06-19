"""Tests for the shared ChainableComponent modifiers.

These live here (not per component) because every component inherits them — they
are exercised once, using Button as a concrete vehicle.
"""

import pytest
from htmy import Renderer

from hue.exceptions import MissingHueContextError
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
            .role("dialog")
        )
        attrs = btn._get_base_html_attrs()
        assert attrs["aria_label"] == "close"
        assert attrs["aria_hidden"] == "true"
        assert attrs["aria_expanded"] == "false"
        assert attrs["aria_controls"] == "panel-1"
        assert attrs["role"] == "dialog"

    def test_base_html_attrs_omits_none(self):
        btn = Button().id("my-id")
        assert btn._get_base_html_attrs() == {"id": "my-id"}

    @pytest.mark.asyncio
    async def test_render_without_hue_context_raises(self):
        with pytest.raises(MissingHueContextError):
            await Renderer().render(Button().content("Hi"))
