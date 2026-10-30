"""Tests for the shared ChainableComponent modifiers.

These live here (not per component) because every component inherits them — they
are exercised once, using Button as a concrete vehicle.
"""

import re

import pytest
from htmy import Renderer

from hue import ui
from hue.exceptions import MissingHueContextError
from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import Button, TextInput
from hue.ui.base import Awaited


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
            .aria_labelledby("title-1")
            .aria_busy("true")
            .aria_keyshortcuts("Escape")
            .role("dialog")
        )
        attrs = btn._get_base_html_attrs()
        assert attrs["aria_label"] == "close"
        assert attrs["aria_hidden"] == "true"
        assert attrs["aria_expanded"] == "false"
        assert attrs["aria_controls"] == "panel-1"
        assert attrs["aria_labelledby"] == "title-1"
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

    def test_attribute_name_that_breaks_out_raises(self):
        with pytest.raises(ValueError, match="may only hold"):
            Button().data('a" onmouseover="alert(1)', "v")

    def test_attribute_name_with_underscore_raises(self):
        with pytest.raises(ValueError, match="hyphen"):
            Button().x_on("my_event", unsafe("go()"))

    def test_dotted_and_namespaced_event_names_pass(self):
        attrs = (
            Button()
            .x_on("keydown.escape.window", unsafe("close()"))
            .x_on("ajax:success", unsafe("done()"))
            ._get_base_html_attrs()
        )
        assert "@keydown.escape.window" in attrs
        assert "@ajax:success" in attrs

    def test_base_html_attrs_omits_none(self):
        btn = Button().id("my-id")
        assert btn._get_base_html_attrs() == {"id": "my-id"}

    @pytest.mark.asyncio
    async def test_render_without_hue_context_raises(self):
        with pytest.raises(MissingHueContextError):
            await Renderer().render(Button().content("Hi"))


class TestFormElementMixin:
    """
    The form attribute, which reaches the element a form submits: the button
    itself here, and the input inside a control's field.
    """

    @pytest.mark.asyncio
    async def test_a_button_can_belong_to_a_form_it_is_not_in(self, context_args):
        html = await render_tree(
            Button().type("submit").form("invoices").content("Archive"),
            context_args=context_args,
        )
        assert 'form="invoices"' in html

    @pytest.mark.asyncio
    async def test_it_lands_on_a_controls_own_element(self, context_args):
        html = await render_tree(
            TextInput().name("q").label("Search").form("invoices"),
            context_args=context_args,
        )
        assert re.search(r'<input[^>]*form="invoices"', html)


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


@pytest.mark.asyncio
async def test_awaited_renders_what_its_coroutine_returns(context_args):
    async def draw(context):
        return Button().content("Drawn")

    html = await render_tree(Awaited(draw), context_args=context_args)
    assert "Drawn" in html
    assert "<button" in html


# A component whose root holds hue's own Alpine scope: x_data() on it would
# replace that scope or be dropped, either way without a word.
_OWNS_A_SCOPE = {
    "Accordion": lambda: ui.Accordion.example(),
    "BarChart": lambda: ui.BarChart.example(),
    "Command": lambda: ui.Command.example(),
    "DatePicker": lambda: ui.DatePicker.example(),
    "Dialog": lambda: ui.Dialog.example(),
    "Disclosure": lambda: ui.Disclosure.example(),
    "Drawer": lambda: ui.Drawer.example(),
    "DropdownMenu": lambda: ui.DropdownMenu.example(),
    "checkable MenuItem": lambda: ui.MenuItem().content("Wrap").checkable(),
    "Popover": lambda: ui.Popover.example(),
    "PieChart": lambda: ui.PieChart.example(),
    "ScatterChart": lambda: ui.ScatterChart.example(),
    "SegmentedControl": lambda: ui.SegmentedControl.example(),
    "TableOfContents": lambda: ui.TableOfContents.example(),
    "Toast": lambda: ui.Toast.example(),
    "ToastRegion": lambda: ui.ToastRegion(),
    "Tooltip": lambda: ui.Tooltip.example(),
}


@pytest.mark.asyncio
@pytest.mark.parametrize("make", _OWNS_A_SCOPE.values(), ids=_OWNS_A_SCOPE.keys())
async def test_x_data_raises_on_a_component_with_a_scope_of_its_own(make, context_args):
    with pytest.raises(ValueError, match="around it, or inside it"):
        await render_tree(make().x_data("{ mine: 1 }"), context_args=context_args)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make",
    [
        lambda: ui.MenuItem().content("Wrap"),
        lambda: ui.SegmentedControl()
        .label("Range")
        .content(ui.SegmentedOption().value("week").content("Week")),
    ],
    ids=["plain MenuItem", "SegmentedControl without a value"],
)
async def test_x_data_is_kept_where_the_component_has_no_scope_of_its_own(
    make, context_args
):
    html = await render_tree(make().x_data("{ mine: 1 }"), context_args=context_args)
    assert 'x-data="{ mine: 1 }"' in html
