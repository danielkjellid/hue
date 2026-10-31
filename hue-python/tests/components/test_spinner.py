import pytest

from hue.renderer import render_tree
from hue.ui import Spinner
from tests._a11y import assert_attr, assert_no_selector, select


class TestSpinner:
    # The live region has to sit on whatever carries the text.
    @pytest.mark.asyncio
    async def test_unlabelled_spinner_announces_itself(self, context_args):
        # A live region reads its text and ignores an aria-label.
        html = await render_tree(Spinner(), context_args=context_args)
        assert select(html, '[role="status"] .sr-only')[0].text == "Loading"
        assert_attr(html, "span.animate-spinner", "aria-hidden", "true")
        assert_no_selector(html, "span[aria-label]")

    @pytest.mark.asyncio
    async def test_a_hidden_label_is_only_announced(self, context_args):
        html = await render_tree(
            Spinner().label("Saving", visible=False), context_args=context_args
        )
        assert select(html, '[role="status"] .sr-only')[0].text == "Saving"

    @pytest.mark.asyncio
    async def test_labelled_spinner_announces_the_label(self, context_args):
        html = await render_tree(
            Spinner().label("Loading payments"), context_args=context_args
        )
        # Two nested status regions would announce the same thing twice.
        status = select(html, '[role="status"]')
        assert len(status) == 1
        assert status[0].get_text(strip=True) == "Loading payments"
        assert_no_selector(html, ".sr-only")
        # The label says what is happening, so the ring is decoration.
        assert_attr(html, "span.animate-spinner", "aria-hidden", "true")
        assert_no_selector(html, "span[aria-label]")
