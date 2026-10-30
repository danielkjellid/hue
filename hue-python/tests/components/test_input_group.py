import pytest

from hue.renderer import render_tree
from hue.ui import PasswordInput, TextInput
from hue.ui.atoms.icon import HueIcon
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestAttachedSegments:
    @pytest.mark.asyncio
    async def test_prefix_and_suffix_sit_on_the_matching_sides(self, context_args):
        html = await render_tree(
            TextInput().name("rate").label("Rate").prefix("$").suffix("/mo"),
            context_args=context_args,
        )
        assert html.index("$") < html.index("<input") < html.index("/mo")

    @pytest.mark.asyncio
    async def test_the_leading_icon_is_decorative(self, context_args):
        # The label names the control; an announced icon would name it twice.
        html = await render_tree(
            TextInput().name("q").label("Search").leading_icon(HueIcon("search")),
            context_args=context_args,
        )
        assert_attr(html, 'span[aria-hidden="true"]', "aria-hidden", "true")


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
