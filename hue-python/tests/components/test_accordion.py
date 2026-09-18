import pytest

from hue.renderer import render_tree
from hue.ui import Accordion, AccordionItem
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _accordion(*items, **props):
    accordion = Accordion()
    for key, value in props.items():
        getattr(accordion, key)(value)
    return accordion.content(
        *(
            items
            or (
                AccordionItem().title("First").open().content("One"),
                AccordionItem().title("Second").content("Two"),
            )
        )
    )


class TestAccordion:
    @pytest.mark.asyncio
    async def test_a_trigger_is_a_button_inside_a_heading(self, context_args):
        # The heading is what lets a screen reader jump between sections; the
        # button is what makes it operable.
        html = await render_tree(_accordion(), context_args=context_args)
        assert_selector(html, "h3 > button[type=button]")

    @pytest.mark.asyncio
    async def test_the_trigger_says_what_it_controls(self, context_args):
        html = await render_tree(_accordion(), context_args=context_args)
        assert_attr(html, "button", ":aria-expanded", "shown(0)")
        assert_attr(html, "button", ":aria-controls", "$id('hue-accordion-panel')")

    @pytest.mark.asyncio
    async def test_the_panel_is_named_by_the_heading_that_opens_it(self, context_args):
        html = await render_tree(_accordion(), context_args=context_args)
        assert_attr(
            html, '[role="region"]', ":aria-labelledby", "$id('hue-accordion-trigger')"
        )
        assert_attr(html, '[role="region"]', "x-show", "shown(0)")

    @pytest.mark.asyncio
    async def test_ids_are_minted_per_item(self, context_args):
        # Two sections in one accordion must not point at each other's panels.
        html = await render_tree(_accordion(), context_args=context_args)
        assert_selector(html, "[x-id]", count=2)

    # heading(): both branches
    @pytest.mark.asyncio
    async def test_the_heading_level_can_be_set(self, context_args):
        html = await render_tree(
            _accordion(AccordionItem().title("Only").heading("h2")),
            context_args=context_args,
        )
        assert_selector(html, "h2 > button")
        assert_no_selector(html, "h3")

    # open(): both branches, and what mode does with them
    @pytest.mark.asyncio
    async def test_the_sections_that_start_open_are_the_ones_that_asked(
        self, context_args
    ):
        html = await render_tree(
            _accordion(
                AccordionItem().title("First").content("One"),
                AccordionItem().title("Second").open().content("Two"),
            ),
            context_args=context_args,
        )
        assert "open: [1]" in str(html)

    @pytest.mark.asyncio
    async def test_nothing_is_open_by_default(self, context_args):
        html = await render_tree(
            _accordion(AccordionItem().title("First").content("One")),
            context_args=context_args,
        )
        assert "open: []" in str(html)

    @pytest.mark.asyncio
    async def test_one_at_a_time_keeps_one_however_many_asked(self, context_args):
        html = await render_tree(
            _accordion(
                AccordionItem().title("First").open().content("One"),
                AccordionItem().title("Second").open().content("Two"),
            ),
            context_args=context_args,
        )
        assert "open: [0]" in str(html)
        assert "single: true" in str(html)

    @pytest.mark.asyncio
    async def test_multiple_keeps_them_all(self, context_args):
        html = await render_tree(
            _accordion(
                AccordionItem().title("First").open().content("One"),
                AccordionItem().title("Second").open().content("Two"),
                multiple=True,
            ),
            context_args=context_args,
        )
        assert "open: [0, 1]" in str(html)
        assert "single: false" in str(html)

    @pytest.mark.asyncio
    async def test_it_is_as_wide_as_its_column(self, context_args):
        # Not as wide as whichever panel is open, or opening one moves the
        # whole accordion.
        html = await render_tree(_accordion(), context_args=context_args)
        assert_selector(html, "div.w-full.border-t")

    # variant(): both branches
    @pytest.mark.asyncio
    async def test_plain_is_a_stack_of_rules(self, context_args):
        html = await render_tree(_accordion(), context_args=context_args)
        assert_selector(html, "div.border-t.border-border")

    @pytest.mark.asyncio
    async def test_boxed_is_a_stack_of_cards(self, context_args):
        html = await render_tree(_accordion(variant="boxed"), context_args=context_args)
        assert_selector(html, "div.flex.flex-col.gap-2")
