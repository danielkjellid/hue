import pytest

from hue.renderer import render_tree
from hue.ui import Disclosure
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestDisclosure:
    @pytest.mark.asyncio
    async def test_the_trigger_is_a_button_inside_a_heading(self, context_args):
        # Not a link: it goes nowhere, and a link that toggles something tells
        # a screen reader the wrong thing about what pressing it does.
        html = await render_tree(
            Disclosure().title("General").content("Fields"),
            context_args=context_args,
        )
        assert_selector(html, "h3 > button[type=button]")
        assert_no_selector(html, "a")

    @pytest.mark.asyncio
    async def test_the_trigger_says_what_it_controls(self, context_args):
        html = await render_tree(
            Disclosure().title("General").content("Fields"),
            context_args=context_args,
        )
        assert_attr(html, "button", ":aria-expanded", "open")
        assert_attr(html, "button", ":aria-controls", "$id('hue-disclosure-panel')")
        assert_attr(html, "button", "x-on:click", "open = !open")

    @pytest.mark.asyncio
    async def test_the_panel_is_named_by_its_heading(self, context_args):
        html = await render_tree(
            Disclosure().title("General").content("Fields"),
            context_args=context_args,
        )
        assert_attr(
            html,
            '[role="region"]',
            ":aria-labelledby",
            "$id('hue-disclosure-title')",
        )

    @pytest.mark.asyncio
    async def test_it_answers_to_nothing_else_on_the_page(self, context_args):
        # Its own scope, which is the whole difference from an accordion.
        html = await render_tree(
            Disclosure().title("General").content("Fields"),
            context_args=context_args,
        )
        assert_attr(html, "[x-data]", "x-data", "{ open: false }")

    # open(): both branches
    @pytest.mark.asyncio
    async def test_it_can_start_open(self, context_args):
        html = await render_tree(
            Disclosure().title("General").open().content("Fields"),
            context_args=context_args,
        )
        assert_attr(html, "[x-data]", "x-data", "{ open: true }")

    @pytest.mark.asyncio
    async def test_it_starts_closed(self, context_args):
        html = await render_tree(
            Disclosure().title("General").content("Fields"),
            context_args=context_args,
        )
        assert_attr(html, "[x-data]", "x-data", "{ open: false }")
