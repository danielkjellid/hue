import pytest

from hue.renderer import render_tree
from hue.ui import Badge
from tests._a11y import assert_attr, select


class TestBadge:
    @pytest.mark.asyncio
    async def test_the_dot_is_decorative(self, context_args):
        # The dot repeats what the label already says, so it must not be
        # announced.
        html = await render_tree(
            Badge().variant("success").dot().content("Live"),
            context_args=context_args,
        )
        assert select(html, "span")[0].get_text(strip=True) == "Live"
        assert_attr(html, "span > span", "aria-hidden", "true")
