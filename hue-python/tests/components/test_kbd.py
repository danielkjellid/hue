import pytest

from hue.renderer import render_tree
from hue.ui import Kbd
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestKbd:
    @pytest.mark.asyncio
    async def test_renders_a_real_kbd_element_per_key(self, context_args):
        # Real <kbd>, so assistive tech announces the semantics.
        html = await render_tree(Kbd("mod", "K"), context_args=context_args)
        assert_selector(html, "kbd", count=2)

    @pytest.mark.asyncio
    async def test_a_plain_key_renders_verbatim(self, context_args):
        html = await render_tree(Kbd("K"), context_args=context_args)
        assert_selector(html, "kbd", count=1)
        assert ">K<" in html

    @pytest.mark.asyncio
    async def test_keys_can_be_set_after_construction(self, context_args):
        html = await render_tree(Kbd().keys("esc"), context_args=context_args)
        assert "Esc" in html

    @pytest.mark.asyncio
    async def test_wrapper_carries_caller_classes(self, context_args):
        # Even a single key is wrapped, so class_() has one predictable home.
        html = await render_tree(Kbd("K").class_("ml-2"), context_args=context_args)
        assert_selector(html, "span.ml-2 > kbd")

    # Glyph keys: a spoken name alongside, because a screen reader would
    # otherwise read the Unicode name of the glyph.
    @pytest.mark.asyncio
    async def test_glyph_key_carries_a_spoken_name(self, context_args):
        html = await render_tree(Kbd("shift"), context_args=context_args)
        assert_selector(html, "kbd > span.sr-only")
        assert_attr(html, "kbd > span[aria-hidden]", "aria-hidden", "true")
        assert "Shift" in html
        assert "⇧" in html

    @pytest.mark.asyncio
    async def test_word_key_needs_no_spoken_name(self, context_args):
        # "Esc" already reads as a word, so a second announcement is noise.
        html = await render_tree(Kbd("esc"), context_args=context_args)
        assert_no_selector(html, "kbd > span.sr-only")

    @pytest.mark.asyncio
    async def test_unknown_key_needs_no_spoken_name(self, context_args):
        html = await render_tree(Kbd("F5"), context_args=context_args)
        assert_no_selector(html, "kbd > span.sr-only")
        assert "F5" in html

    # mod: only the browser knows which key it is, so the server renders the
    # Apple glyph and Alpine corrects both the glyph and the spoken name.
    @pytest.mark.asyncio
    async def test_mod_resolves_in_the_browser(self, context_args):
        html = await render_tree(Kbd("mod"), context_args=context_args)
        kbd = select(html, "kbd")[0]
        assert "navigator.platform" in kbd["x-data"]
        assert "⌘" in html and "Ctrl" in html
        assert "Command" in html and "Control" in html

    @pytest.mark.asyncio
    async def test_other_keys_need_no_javascript(self, context_args):
        html = await render_tree(Kbd("shift", "K"), context_args=context_args)
        assert_no_selector(html, "kbd[x-data]")
