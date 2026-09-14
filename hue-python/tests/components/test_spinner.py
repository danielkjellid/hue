import pytest

from hue.renderer import render_tree
from hue.ui import Spinner
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestSpinner:
    # label(): both branches. The live region has to sit on whatever carries
    # the text, so the two shapes differ in more than one class.
    @pytest.mark.asyncio
    async def test_unlabelled_spinner_announces_itself(self, context_args):
        html = await render_tree(Spinner(), context_args=context_args)
        assert_attr(html, 'span[role="status"]', "aria-label", "Loading")
        assert_selector(html, "span.animate-spinner")

    @pytest.mark.asyncio
    async def test_labelled_spinner_announces_the_label(self, context_args):
        html = await render_tree(
            Spinner().label("Loading payments"), context_args=context_args
        )
        assert_selector(html, 'span[role="status"] > span.animate-spinner')
        assert "Loading payments" in html
        # The label says what is happening, so the ring is decoration.
        assert_attr(html, "span.animate-spinner", "aria-hidden", "true")
        assert_no_selector(html, "span[aria-label]")

    @pytest.mark.asyncio
    async def test_only_one_live_region(self, context_args):
        # Two nested status regions would announce the same thing twice.
        html = await render_tree(Spinner().label("Saving"), context_args=context_args)
        assert_selector(html, '[role="status"]', count=1)

    # size(): drives both the ring and the label scale
    @pytest.mark.asyncio
    async def test_default_size_is_md(self, context_args):
        html = await render_tree(Spinner(), context_args=context_args)
        assert_selector(html, "span.size-5")

    @pytest.mark.asyncio
    async def test_large_size_thickens_the_ring(self, context_args):
        html = await render_tree(Spinner().size("lg"), context_args=context_args)
        assert_selector(html, "span.size-8")
        assert_selector(html, "span.border-\\[3px\\]")

    # muted(): both branches
    @pytest.mark.asyncio
    async def test_accent_by_default(self, context_args):
        html = await render_tree(Spinner(), context_args=context_args)
        assert_selector(html, "span.text-accent")

    @pytest.mark.asyncio
    async def test_muted(self, context_args):
        html = await render_tree(Spinner().muted(), context_args=context_args)
        assert_selector(html, "span.text-fg-subtle")
        assert_no_selector(html, "span.text-accent")
