import pytest

from hue.renderer import render_tree
from hue.ui import Button, Stack, Text
from tests._a11y import assert_selector


class TestComposition:
    @pytest.mark.asyncio
    async def test_button_with_nested_stack_and_text(self, context_args):
        """The target DX: readable nesting via .content()."""
        html = await render_tree(
            Button()
            .variant("outline")
            .type("button")
            .content(
                Stack()
                .direction("horizontal")
                .spacing("xs")
                .align_items("items-center")
                .content(Text("Sign in")),
            ),
            context_args=context_args,
        )
        assert_selector(html, "button .flex-row")  # horizontal stack inside the button
        assert "Sign in" in html
