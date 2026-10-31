import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import (
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    Dialog,
)
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestCard:
    # href() / interactive(): the title is the one real control, and its
    # overlay stretches it across the card, so the card itself stays a plain
    # container that can still hold buttons of its own.
    @pytest.mark.asyncio
    async def test_href_puts_a_real_anchor_in_the_title(self, context_args):
        # A real link, so middle-click and "open in new tab" still work.
        html = await render_tree(
            Card().href("/invoices/2050").content(CardHeader().title("INV-2050")),
            context_args=context_args,
        )
        assert_attr(html, "div.relative > div a", "href", "/invoices/2050")
        assert select(html, "a")[0].get_text(strip=True) == "INV-2050"
        assert_selector(html, "a.after\\:absolute.after\\:inset-0")

    @pytest.mark.asyncio
    async def test_interactive_puts_a_real_button_in_the_title(self, context_args):
        html = await render_tree(
            Card().interactive().content(CardHeader().title("Pro plan")),
            context_args=context_args,
        )
        assert_attr(html, "button", "type", "button")
        assert select(html, "button")[0].get_text(strip=True) == "Pro plan"

    @pytest.mark.asyncio
    async def test_a_linked_card_can_hold_its_own_buttons(self, context_args):
        # Siblings rather than nested: the footer button sits beside the
        # link instead of inside it.
        html = await render_tree(
            Card()
            .href("/x")
            .content(
                CardHeader().title("Report"),
                CardFooter().content(Button().content("Delete")),
            ),
            context_args=context_args,
        )
        assert_no_selector(html, "a button")
        assert_no_selector(html, "button a")
        assert_selector(html, "button", count=1)

    # Naming and activation belong to the control, since that is what a
    # screen reader names and what a click lands on. Everything else
    # describes the card as a whole and stays on it.
    @pytest.mark.parametrize(
        ("card", "control", "attr", "value"),
        [
            (
                Card().href("/x").aria_label("Open report"),
                "a",
                "aria-label",
                "Open report",
            ),
            (
                Card().interactive().x_on("click", unsafe("picked = true")),
                "button",
                "@click",
                "picked = true",
            ),
            # Alpine AJAX fires its events on the element that made the request.
            (
                Card().href("/x").ajax_success(unsafe("done = true")),
                "a",
                "@ajax:success",
                "done = true",
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_naming_and_activation_land_on_the_control(
        self, context_args, card, control, attr, value
    ):
        html = await render_tree(
            card.content(CardHeader().title("Report")), context_args=context_args
        )
        assert_attr(html, control, attr, value)
        assert not select(html, "div.relative")[0].has_attr(attr)

    @pytest.mark.asyncio
    async def test_a_dialog_trigger_is_wired_to_the_control(self, context_args):
        html = await render_tree(
            Dialog()
            .title("Upgrade")
            .trigger(Card().interactive().content(CardHeader().title("Pro plan"))),
            context_args=context_args,
        )
        assert_attr(html, "button[data-card-link]", "aria-haspopup", "dialog")
        assert_attr(html, "button[data-card-link]", "x-on:click", "open = true")
        assert_attr(html, "button[data-card-link]", "x-bind:aria-expanded", "open")
        # The mark the dialog finds its trigger by, to give focus back to.
        assert_attr(html, "button[data-card-link]", "data-hue-trigger")
        assert_no_selector(html, "div[data-hue-trigger]")

    @pytest.mark.asyncio
    async def test_container_attributes_stay_on_the_card(self, context_args):
        html = await render_tree(
            Card()
            .href("/x")
            .id("report")
            .x_data({"open": True})
            .x_show(unsafe("open"))
            .content(CardHeader().title("Report")),
            context_args=context_args,
        )
        card = select(html, "div.relative")[0]
        assert card.get("id") == "report"
        assert card.get("x-show") == "open"
        assert card.has_attr("x-data")
        anchor = select(html, "a")[0]
        assert not {"id", "x-show", "x-data"} & set(anchor.attrs)

    @pytest.mark.asyncio
    async def test_a_static_card_inside_a_linked_one_stays_static(self, context_args):
        html = await render_tree(
            Card()
            .href("/x")
            .content(
                CardHeader().title("Outer"),
                CardBody().content(Card().content(CardHeader().title("Inner"))),
            ),
            context_args=context_args,
        )
        assert_selector(html, "a", count=1)

    @pytest.mark.asyncio
    async def test_only_the_cards_own_header_becomes_the_link(self, context_args):
        # One link per card, or the card's attributes would land on two
        # controls: a duplicated id and every handler run twice.
        html = await render_tree(
            Card()
            .href("/x")
            .aria_label("Open report")
            .content(
                CardHeader().title("Report"),
                CardHeader().title("Second"),
                CardBody().content(CardHeader().title("Nested")),
            ),
            context_args=context_args,
        )
        assert_selector(html, "a", count=1)
        assert select(html, "a")[0].get_text(strip=True) == "Report"

    @pytest.mark.parametrize(
        "body",
        [
            # Only a header placed directly in the card can become its link.
            CardBody().content(CardHeader().title("Report")),
            # The title is the link's text; without one there is nothing to
            # name it or to click.
            CardBody().content("Hi"),
        ],
    )
    @pytest.mark.asyncio
    async def test_a_linked_card_needs_a_title_of_its_own(self, context_args, body):
        with pytest.raises(ValueError, match="CardHeader"):
            await render_tree(
                Card().href("/x").content(body), context_args=context_args
            )

    @pytest.mark.asyncio
    async def test_href_wins_over_interactive(self, context_args):
        # Navigating and acting are the same affordance; one element, not two.
        html = await render_tree(
            Card().href("/x").interactive().content(CardHeader().title("Report")),
            context_args=context_args,
        )
        assert_selector(html, "a")
        assert_no_selector(html, "button")
