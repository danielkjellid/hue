import pytest

from hue.js import unsafe
from hue.renderer import render_tree
from hue.ui import (
    Button,
    Card,
    CardBody,
    CardFooter,
    CardHeader,
    CardMedia,
    Dialog,
)
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestCard:
    @pytest.mark.asyncio
    async def test_renders_a_plain_container_by_default(self, context_args):
        html = await render_tree(
            Card().content(CardBody().content("Hi")), context_args=context_args
        )
        assert_selector(html, "div.rounded-lg")
        assert_no_selector(html, "a")
        assert_no_selector(html, "button")

    # variant(): flat on the canvas by default; elevation is for things that
    # genuinely float.
    @pytest.mark.asyncio
    async def test_default_variant_is_bordered(self, context_args):
        html = await render_tree(Card(), context_args=context_args)
        assert_selector(html, "div.border-border")
        assert_no_selector(html, "div.shadow-raised")

    @pytest.mark.asyncio
    async def test_raised_variant_swaps_the_border_for_a_shadow(self, context_args):
        html = await render_tree(Card().variant("raised"), context_args=context_args)
        assert_selector(html, "div.shadow-raised")
        assert_selector(html, "div.border-transparent")

    @pytest.mark.asyncio
    async def test_flat_variant(self, context_args):
        html = await render_tree(Card().variant("flat"), context_args=context_args)
        assert_selector(html, "div.bg-surface-sunken")

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
    @pytest.mark.asyncio
    async def test_a_label_lands_on_the_control(self, context_args):
        html = await render_tree(
            Card()
            .href("/x")
            .aria_label("Open report")
            .content(CardHeader().title("Report")),
            context_args=context_args,
        )
        assert_attr(html, "a", "aria-label", "Open report")
        assert_no_selector(html, "div[aria-label]")

    @pytest.mark.asyncio
    async def test_a_click_handler_lands_on_the_control(self, context_args):
        html = await render_tree(
            Card()
            .interactive()
            .x_on("click", unsafe("picked = true"))
            .content(CardHeader().title("Pro plan")),
            context_args=context_args,
        )
        assert_attr(html, "button", "@click", "picked = true")
        assert_no_selector(html, "div[\\@click]")

    @pytest.mark.asyncio
    async def test_a_dialog_trigger_is_wired_to_the_control(self, context_args):
        html = await render_tree(
            Dialog()
            .title("Upgrade")
            .trigger(Card().interactive().content(CardHeader().title("Pro plan"))),
            context_args=context_args,
        )
        assert_attr(html, "button[data-card-link]", "aria-haspopup", "dialog")
        assert_attr(html, "button[data-card-link]", "@click")
        assert_attr(html, "button[data-card-link]", ":aria-expanded")

    @pytest.mark.asyncio
    async def test_an_ajax_listener_lands_on_the_control(self, context_args):
        # Alpine AJAX fires its events on the element that made the request.
        html = await render_tree(
            Card()
            .href("/x")
            .ajax_success("done = true")
            .content(CardHeader().title("Report")),
            context_args=context_args,
        )
        assert_attr(html, "a", "@ajax:success", "done = true")

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
    async def test_a_linked_card_gets_a_focus_ring(self, context_args):
        html = await render_tree(
            Card().href("/x").content(CardHeader().title("Report")),
            context_args=context_args,
        )
        assert "focus-visible]:ring-2" in html

    @pytest.mark.asyncio
    async def test_a_static_card_gets_no_link_or_focus_ring(self, context_args):
        html = await render_tree(
            Card().content(CardHeader().title("Report")), context_args=context_args
        )
        assert "ring-2" not in html
        assert_no_selector(html, "div.relative")
        assert_no_selector(html, "a")

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

    @pytest.mark.asyncio
    async def test_a_header_wrapped_in_another_element_does_not_count(
        self, context_args
    ):
        # Only a header placed directly in the card can become its link.
        with pytest.raises(ValueError, match="CardHeader"):
            await render_tree(
                Card()
                .href("/x")
                .content(CardBody().content(CardHeader().title("Report"))),
                context_args=context_args,
            )

    @pytest.mark.asyncio
    async def test_a_linked_card_needs_a_title(self, context_args):
        # The title is the link's text; without one there is nothing to name
        # it or to click.
        with pytest.raises(ValueError, match="CardHeader"):
            await render_tree(
                Card().href("/x").content(CardBody().content("Hi")),
                context_args=context_args,
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


class TestCardSlots:
    @pytest.mark.asyncio
    async def test_header_renders_title_and_description(self, context_args):
        html = await render_tree(
            CardHeader().title("Monthly revenue").description("Last 30 days"),
            context_args=context_args,
        )
        assert "Monthly revenue" in html
        assert "Last 30 days" in html

    # Both header fields are optional, and each has to be absent cleanly.
    @pytest.mark.asyncio
    async def test_header_without_a_description(self, context_args):
        html = await render_tree(
            CardHeader().title("Monthly revenue"), context_args=context_args
        )
        assert_no_selector(html, "div.text-fg-muted")

    @pytest.mark.asyncio
    async def test_header_without_a_title(self, context_args):
        html = await render_tree(
            CardHeader().description("Last 30 days"), context_args=context_args
        )
        assert_no_selector(html, "div.font-bold")

    @pytest.mark.asyncio
    async def test_header_puts_children_opposite_the_title(self, context_args):
        html = await render_tree(
            CardHeader().title("Revenue").content("badge"), context_args=context_args
        )
        assert_selector(html, "div.justify-between")
        assert "badge" in html

    @pytest.mark.asyncio
    async def test_body_pads_itself_only_when_it_stands_alone(self, context_args):
        # Under a header its top spacing comes from the header's own padding.
        html = await render_tree(CardBody().content("Text"), context_args=context_args)
        assert_selector(html, "div.pt-0.first\\:pt-5")

    @pytest.mark.asyncio
    async def test_footer_is_a_tinted_strip(self, context_args):
        html = await render_tree(
            CardFooter().content("Save"), context_args=context_args
        )
        assert_selector(html, "div.border-t.bg-surface-sunken")

    @pytest.mark.asyncio
    async def test_media_locks_width_and_leaves_height_alone(self, context_args):
        # The image keeps its own aspect ratio rather than being cropped into
        # a fixed one.
        html = await render_tree(CardMedia(), context_args=context_args)
        assert_selector(html, "div.aspect-video")
        assert_selector(html, "div.\\[\\&_img\\]\\:object-cover")
