import pytest

from hue.renderer import render_tree
from hue.ui import ThemeSwitcher
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestThemeSwitcher:
    @pytest.mark.asyncio
    async def test_renders_three_options_in_a_labelled_group(self, context_args):
        html = await render_tree(ThemeSwitcher(), context_args=context_args)
        # "system" has to be selectable, so three buttons, never a binary toggle.
        assert_selector(html, 'div[role="group"] button', count=3)
        assert_attr(html, 'div[role="group"]', "aria-label", "Color theme")

    @pytest.mark.asyncio
    async def test_each_option_selects_its_theme_and_tracks_pressed(self, context_args):
        html = await render_tree(ThemeSwitcher(), context_args=context_args)
        for choice in ("light", "dark", "system"):
            assert_selector(html, f"button[\\@click*=\"select('{choice}')\"]")
            assert_selector(html, f"button[\\:aria-pressed*=\"choice === '{choice}'\"]")

    @pytest.mark.asyncio
    async def test_buttons_do_not_submit_surrounding_forms(self, context_args):
        html = await render_tree(ThemeSwitcher(), context_args=context_args)
        assert_selector(html, 'button[type="button"]', count=3)

    # labelled(): icon-only names the theme it selects; labelled lets the visible
    # text do it, so an aria-label would only contradict what is on screen.
    @pytest.mark.asyncio
    async def test_icons_alone_label_every_button(self, context_args):
        html = await render_tree(ThemeSwitcher(), context_args=context_args)
        assert_attr(html, "button", "aria-label", "Light theme")
        assert_selector(html, 'button[aria-label="Match system"]')
        assert "Light</button>" not in html

    @pytest.mark.asyncio
    async def test_labelled_shows_text_and_drops_the_aria_label(self, context_args):
        html = await render_tree(ThemeSwitcher().labelled(), context_args=context_args)
        assert_no_selector(html, "button[aria-label]")
        for text in ("Light", "Dark", "System"):
            assert text in html

    @pytest.mark.asyncio
    async def test_icons_are_decorative(self, context_args):
        html = await render_tree(ThemeSwitcher(), context_args=context_args)
        assert_selector(html, 'svg[aria-hidden="true"]', count=3)

    @pytest.mark.asyncio
    async def test_caller_can_relabel_the_group(self, context_args):
        html = await render_tree(
            ThemeSwitcher().aria_label("Fargetema"), context_args=context_args
        )
        assert_attr(html, 'div[role="group"]', "aria-label", "Fargetema")
