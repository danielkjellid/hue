import re

import pytest

from hue.renderer import render_tree
from hue.ui import Accordion, AccordionItem, Disclosure
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


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
        assert_attr(html, "button", ":aria-expanded", "hueOpen")
        assert_attr(html, "button", ":aria-controls", "$id('hue-disclosure-panel')")
        assert_attr(html, "button", "x-on:click", "hueOpen = !hueOpen")

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
        # One scope of its own, holding the only state there is: no index, no
        # neighbours, nothing to coordinate. That is the whole difference
        # from an accordion.
        html = await render_tree(
            Disclosure().title("General").content("Fields"),
            context_args=context_args,
        )
        assert_selector(html, "[x-data]", count=1)
        assert_attr(html, "[x-data]", "x-id")

    # closed(): both branches
    @pytest.mark.asyncio
    async def test_it_starts_open(self, context_args):
        # A section of a form is there to be filled in, so the fields are
        # what the page shows first.
        html = await render_tree(
            Disclosure().title("General").content("Fields"),
            context_args=context_args,
        )
        assert select(html, "[x-data]")[0]["x-data"].startswith("{ hueOpen: true,")

    @pytest.mark.asyncio
    async def test_it_can_start_folded_away(self, context_args):
        html = await render_tree(
            Disclosure().title("General").closed().content("Fields"),
            context_args=context_args,
        )
        assert select(html, "[x-data]")[0]["x-data"].startswith("{ hueOpen: false,")


def _top_level_keys(x_data: str) -> list[str]:
    """
    The keys of an x-data object literal: what is left at its top level once
    every nested bracket and string is taken out.
    """
    body = x_data.strip()[1:-1]
    body = re.sub(r"'[^']*'", "''", body)
    while re.search(r"[({[][^(){}[\]]*[)}\]]", body):
        body = re.sub(r"[({[][^(){}[\]]*[)}\]]", "", body)
    return re.findall(r"(?:^|,)\s*(\w+)\s*[:(]?", body)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "component",
    [
        Disclosure().title("General").content("Fields"),
        Accordion().content(AccordionItem().title("One").open().content("Fields")),
    ],
    ids=["disclosure", "accordion"],
)
async def test_every_key_in_its_state_is_hue_prefixed(component, context_args):
    # The section holds the caller's markup, so an unprefixed key would shadow
    # a name of theirs in there, such as a form's own submitting flag.
    html = await render_tree(component, context_args=context_args)
    keys = _top_level_keys(select(html, "[x-data]")[0]["x-data"])
    assert keys
    assert [key for key in keys if not key.startswith("hue")] == []
