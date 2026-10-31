import pytest

from hue.renderer import render_tree
from hue.ui import ThemeSwitcher
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestThemeSwitcher:
    @pytest.mark.asyncio
    async def test_three_pressable_buttons_in_a_labelled_group(self, context_args):
        # "system" has to be selectable, so three buttons, never a binary
        # toggle, and none of them submits a form around it.
        html = await render_tree(ThemeSwitcher(), context_args=context_args)
        assert_attr(html, 'div[role="group"]', "aria-label", "Color theme")
        assert_selector(html, 'div[role="group"] button[type="button"]', count=3)
        for choice in ("light", "dark", "system"):
            assert_selector(html, f"button[\\@click*=\"select('{choice}')\"]")
            assert_selector(html, f"button[\\:aria-pressed*=\"choice === '{choice}'\"]")

    # labelled(): icon-only names the theme it selects; labelled lets the visible
    # text do it, so an aria-label would only contradict what is on screen.
    @pytest.mark.asyncio
    async def test_icons_alone_label_every_button(self, context_args):
        html = await render_tree(ThemeSwitcher(), context_args=context_args)
        assert_attr(html, "button", "aria-label", "Light theme")
        assert_selector(html, 'button[aria-label="Match system"]')

    @pytest.mark.asyncio
    async def test_labelled_shows_text_and_drops_the_aria_label(self, context_args):
        html = await render_tree(ThemeSwitcher().labelled(), context_args=context_args)
        assert_no_selector(html, "button[aria-label]")
        for text in ("Light", "Dark", "System"):
            assert text in html

    @pytest.mark.asyncio
    async def test_caller_can_relabel_the_group(self, context_args):
        html = await render_tree(
            ThemeSwitcher().aria_label("Fargetema"), context_args=context_args
        )
        assert_attr(html, 'div[role="group"]', "aria-label", "Fargetema")
