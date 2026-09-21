import pytest

from hue.renderer import render_tree
from hue.ui import Badge
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestBadge:
    @pytest.mark.asyncio
    async def test_renders_its_label_in_a_span(self, context_args):
        html = await render_tree(Badge().content("Active"), context_args=context_args)
        assert_selector(html, "span")
        assert "Active" in html

    # variant(): default vs an explicit tone
    @pytest.mark.asyncio
    async def test_default_variant_is_neutral(self, context_args):
        html = await render_tree(Badge().content("Draft"), context_args=context_args)
        assert_selector(html, "span.bg-surface-sunken")

    @pytest.mark.asyncio
    async def test_status_variant_uses_its_own_tone(self, context_args):
        html = await render_tree(
            Badge().variant("danger").content("Failed"), context_args=context_args
        )
        assert_selector(html, "span.bg-danger-subtle")
        assert_selector(html, "span.text-danger-text")

    # dot(): both branches
    @pytest.mark.asyncio
    async def test_dot_is_decorative_and_takes_the_label_colour(self, context_args):
        # The dot repeats what the label already says, so it must not be
        # announced - and it inherits currentColor rather than carrying a
        # per-variant rule of its own.
        html = await render_tree(
            Badge().variant("success").dot().content("Live"),
            context_args=context_args,
        )
        assert_selector(html, "span > span.rounded-full.bg-current")
        assert_attr(html, "span > span.bg-current", "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_no_dot_by_default(self, context_args):
        html = await render_tree(Badge().content("Live"), context_args=context_args)
        assert_no_selector(html, "span > span.bg-current")

    # shape(): a pill widens its own padding, so the size's must not apply
    @pytest.mark.asyncio
    async def test_default_shape_is_rounded(self, context_args):
        html = await render_tree(Badge().content("Draft"), context_args=context_args)
        assert_selector(html, "span.rounded-sm")
        assert_selector(html, "span.px-\\[7px\\]")

    @pytest.mark.asyncio
    async def test_a_pill_overrides_the_size_padding(self, context_args):
        html = await render_tree(
            Badge().pill().content("Draft"), context_args=context_args
        )
        assert_selector(html, "span.rounded-full")
        assert_no_selector(html, "span.rounded-sm")
        assert_selector(html, "span.px-\\[9px\\]")
        assert_no_selector(html, "span.px-\\[7px\\]")

    # size(): both branches
    @pytest.mark.asyncio
    async def test_default_size_is_md(self, context_args):
        html = await render_tree(Badge().content("Draft"), context_args=context_args)
        assert_selector(html, "span.h-5.text-xs")

    @pytest.mark.asyncio
    async def test_large_size(self, context_args):
        html = await render_tree(
            Badge().size("lg").content("Draft"), context_args=context_args
        )
        assert_selector(html, "span.h-6.text-sm")

    # numeric(): both branches
    @pytest.mark.asyncio
    async def test_numeric_lines_figures_up(self, context_args):
        html = await render_tree(
            Badge().numeric().content("128"), context_args=context_args
        )
        assert_selector(html, "span.tabular-nums")

    @pytest.mark.asyncio
    async def test_not_numeric_by_default(self, context_args):
        html = await render_tree(Badge().content("128"), context_args=context_args)
        assert_no_selector(html, "span.tabular-nums")
