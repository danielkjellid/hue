import pytest

from hue.renderer import render_tree
from hue.ui import Item
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestItem:
    @pytest.mark.asyncio
    async def test_renders_title_and_description(self, context_args):
        html = await render_tree(
            Item().title("Ada Lovelace").description("ada@example.com"),
            context_args=context_args,
        )
        assert "Ada Lovelace" in html
        assert "ada@example.com" in html

    @pytest.mark.asyncio
    async def test_text_truncates_rather_than_wrapping(self, context_args):
        # One row growing to two lines shifts everything below it, which is
        # what makes a long list feel unruly.
        html = await render_tree(
            Item().title("A very long name indeed").description("and a subtitle"),
            context_args=context_args,
        )
        assert_selector(html, "span.truncate", count=2)

    # Each slot is optional and has to be absent cleanly.
    @pytest.mark.asyncio
    async def test_media_and_actions_flank_the_text(self, context_args):
        html = await render_tree(
            Item().title("Ada").media("AL").actions("menu"),
            context_args=context_args,
        )
        assert_selector(html, "span.flex-none", count=2)
        assert "AL" in html
        assert "menu" in html

    @pytest.mark.asyncio
    async def test_no_media_or_actions_by_default(self, context_args):
        html = await render_tree(Item().title("Ada"), context_args=context_args)
        assert_no_selector(html, "span.flex-none")

    @pytest.mark.asyncio
    async def test_description_is_optional(self, context_args):
        html = await render_tree(Item().title("Ada"), context_args=context_args)
        assert_no_selector(html, "span.text-fg-muted")

    # variant(): both branches
    @pytest.mark.asyncio
    async def test_plain_by_default(self, context_args):
        html = await render_tree(Item().title("Ada"), context_args=context_args)
        assert_selector(html, "div.border-transparent")

    @pytest.mark.asyncio
    async def test_bordered(self, context_args):
        html = await render_tree(
            Item().variant("bordered").title("Ada"), context_args=context_args
        )
        assert_selector(html, "div.border-border.bg-surface")

    # href() / interactive(): a real control, or a plain container
    @pytest.mark.asyncio
    async def test_static_by_default(self, context_args):
        html = await render_tree(Item().title("Ada"), context_args=context_args)
        assert_selector(html, "div")
        assert_no_selector(html, "a")
        assert_no_selector(html, "button")
        assert "focus-visible:ring-2" not in html

    @pytest.mark.asyncio
    async def test_href_renders_a_real_link(self, context_args):
        html = await render_tree(
            Item().href("/people/ada").title("Ada"), context_args=context_args
        )
        assert_attr(html, "a", "href", "/people/ada")
        assert "focus-visible:ring-2" in html

    @pytest.mark.asyncio
    async def test_interactive_renders_a_real_button(self, context_args):
        html = await render_tree(
            Item().interactive().title("Ada"), context_args=context_args
        )
        assert_attr(html, "button", "type", "button")

    # selected(): both branches
    @pytest.mark.asyncio
    async def test_selected(self, context_args):
        html = await render_tree(
            Item().selected().title("Ada"), context_args=context_args
        )
        assert_attr(html, "div", "aria-selected", "true")
        assert_selector(html, "div.bg-accent-subtle")

    @pytest.mark.asyncio
    async def test_not_selected_omits_the_attribute(self, context_args):
        html = await render_tree(Item().title("Ada"), context_args=context_args)
        assert_no_selector(html, "[aria-selected]")

    # disabled(): both branches, and the right mechanism per element
    @pytest.mark.asyncio
    async def test_disabled_button_uses_the_native_attribute(self, context_args):
        html = await render_tree(
            Item().interactive().disabled().title("Ada"), context_args=context_args
        )
        assert_attr(html, "button", "disabled")

    @pytest.mark.asyncio
    async def test_disabled_container_says_so_in_aria(self, context_args):
        # A div has no disabled attribute to set, so the state has to be
        # announced rather than merely dimmed.
        html = await render_tree(
            Item().disabled().title("Ada"), context_args=context_args
        )
        assert_attr(html, "div", "aria-disabled", "true")
        assert_selector(html, "div.opacity-55")

    @pytest.mark.asyncio
    async def test_enabled_by_default(self, context_args):
        html = await render_tree(
            Item().interactive().title("Ada"), context_args=context_args
        )
        assert_no_selector(html, "[disabled]")
        assert_no_selector(html, "[aria-disabled]")

    @pytest.mark.asyncio
    async def test_disabled_row_loses_its_hover_affordance(self, context_args):
        html = await render_tree(
            Item().interactive().disabled().title("Ada"), context_args=context_args
        )
        assert "hover:bg-surface-hover" not in html
