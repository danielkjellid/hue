import pytest

from hue.renderer import render_tree
from hue.ui import Button, PasswordInput, TextInput
from hue.ui.atoms.icon import HueIcon
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestAttachedSegments:
    # Grouped or not: the input gives up its own frame only when there is a
    # group to own one.
    @pytest.mark.asyncio
    async def test_a_plain_input_keeps_its_own_frame(self, context_args):
        html = await render_tree(
            TextInput().name("url").label("URL"), context_args=context_args
        )
        assert_selector(html, "input.shadow-field")
        assert_no_selector(html, "input.bg-transparent")

    @pytest.mark.asyncio
    async def test_the_group_takes_the_frame_over(self, context_args):
        # A square segment inside a rounded box pokes past the corner, so the
        # border and the fill have to belong to the outer element.
        html = await render_tree(
            TextInput().name("url").label("URL").prefix("hue.app/"),
            context_args=context_args,
        )
        assert_selector(html, "div.focus-within\\:border-accent")
        assert_selector(html, "input.bg-transparent.border-none")
        assert_no_selector(html, "input.shadow-field")

    @pytest.mark.asyncio
    async def test_prefix_and_suffix_sit_on_the_matching_sides(self, context_args):
        html = await render_tree(
            TextInput().name("rate").label("Rate").prefix("$").suffix("/mo"),
            context_args=context_args,
        )
        assert_selector(html, "span.rounded-s-\\[7px\\]")
        assert_selector(html, "span.rounded-e-\\[7px\\]")
        assert "$" in html
        assert "/mo" in html

    @pytest.mark.asyncio
    async def test_the_leading_icon_is_decorative(self, context_args):
        # The label names the control; an announced icon would name it twice.
        html = await render_tree(
            TextInput().name("q").label("Search").leading_icon(HueIcon("search")),
            context_args=context_args,
        )
        assert_attr(html, 'span[aria-hidden="true"]', "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_a_labelled_action_is_a_segment_of_the_control(self, context_args):
        # Flush with the end, the outer edges coming from the group: a button
        # with a radius of its own puts square corners on the group's round
        # ones.
        html = await render_tree(
            TextInput()
            .name("key")
            .label("API key")
            .action(Button().variant("outline").content("Copy")),
            context_args=context_args,
        )
        assert_selector(html, "div.flex.w-full > button")
        assert_selector(html, "div[class*='rounded-e-[7px]']")

    @pytest.mark.asyncio
    async def test_an_icon_action_floats_inside_the_field(self, context_args):
        # It acts on what is in the input, where a labelled button is a
        # second thing to press beside it.
        html = await render_tree(
            TextInput()
            .name("q")
            .label("Search")
            .action(Button().variant("ghost").icon_only("Clear")),
            context_args=context_args,
        )
        assert_selector(html, "div.flex.w-full > span.pe-1 > button")


class TestRevealablePassword:
    # revealable(): both branches
    @pytest.mark.asyncio
    async def test_the_toggle_keeps_one_name(self, context_args):
        # A control renamed to "Hide password" is announced as a different
        # control each time it is pressed; aria-pressed says the state instead.
        html = await render_tree(
            PasswordInput().name("pw").label("Password").revealable(),
            context_args=context_args,
        )
        assert_attr(html, "button", "aria-label", "Show password")
        assert_attr(html, "button", "aria-pressed", "false")
        assert_attr(html, "button", ":aria-pressed", "shown")

    @pytest.mark.asyncio
    async def test_the_type_is_bound_so_it_can_change(self, context_args):
        html = await render_tree(
            PasswordInput().name("pw").label("Password").revealable(),
            context_args=context_args,
        )
        assert_attr(html, "input", ":type", "shown ? 'text' : 'password'")
        # The scope has to wrap both: declared on the input it would reach
        # only the input, leaving every expression on the toggle - which is
        # its sibling - reading a name that is not there.
        assert_selector(html, "[x-data] input")
        assert_selector(html, "[x-data] button")
        assert_no_selector(html, "input[x-data]")

    @pytest.mark.asyncio
    async def test_no_toggle_by_default(self, context_args):
        html = await render_tree(
            PasswordInput().name("pw").label("Password"), context_args=context_args
        )
        assert_no_selector(html, "button")
        assert_attr(html, "input", "type", "password")
