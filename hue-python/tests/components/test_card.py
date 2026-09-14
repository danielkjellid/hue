import pytest

from hue.renderer import render_tree
from hue.ui import Card, CardBody, CardFooter, CardHeader, CardMedia
from tests._a11y import assert_attr, assert_no_selector, assert_selector


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

    # href() / interactive(): the whole surface becomes one real control
    @pytest.mark.asyncio
    async def test_href_renders_a_real_anchor(self, context_args):
        # A real link, so middle-click and "open in new tab" still work.
        html = await render_tree(
            Card().href("/invoices/2050"), context_args=context_args
        )
        assert_attr(html, "a", "href", "/invoices/2050")
        assert "focus-visible:ring-2" in html

    @pytest.mark.asyncio
    async def test_interactive_renders_a_real_button(self, context_args):
        html = await render_tree(Card().interactive(), context_args=context_args)
        assert_attr(html, "button", "type", "button")
        assert "focus-visible:ring-2" in html

    @pytest.mark.asyncio
    async def test_a_static_card_gets_no_focus_ring(self, context_args):
        html = await render_tree(Card(), context_args=context_args)
        assert "focus-visible:ring-2" not in html

    @pytest.mark.asyncio
    async def test_href_wins_over_interactive(self, context_args):
        # Navigating and acting are the same affordance; one element, not two.
        html = await render_tree(
            Card().href("/x").interactive(), context_args=context_args
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
        assert_selector(html, "div.\\[\\&_img\\]\\:w-full")
        assert_selector(html, "div.\\[\\&_img\\]\\:h-auto")
        assert "aspect-" not in html
