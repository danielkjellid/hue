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
    @pytest.mark.parametrize(
        ("keys", "text"),
        [
            (("K",), "K"),
            (("f5",), "F5"),
            # A capital G alone would read as Shift+G, which "g" does not match.
            (("g",), "g"),
            (("shift", "g"), "G"),
        ],
    )
    async def test_the_last_key_reads_as_written(self, context_args, keys, text):
        html = await render_tree(Kbd(*keys), context_args=context_args)
        assert select(html, "kbd")[-1].get_text() == text

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
    @pytest.mark.parametrize("key", ["esc", "f5"])
    async def test_word_key_needs_no_spoken_name(self, context_args, key):
        # "Esc" already reads as a word, so a second announcement is noise.
        html = await render_tree(Kbd(key), context_args=context_args)
        assert_no_selector(html, "kbd > span.sr-only")

    # mod: only the browser knows which key it is, so the server renders the
    # Apple glyph and Alpine corrects both the glyph and the spoken name.
    @pytest.mark.asyncio
    async def test_mod_resolves_in_the_browser(self, context_args):
        html = await render_tree(Kbd("mod"), context_args=context_args)
        # The same answer the shortcuts are matched by.
        assert "$store.shortcuts?.apple" in html
        assert "⌘" in html and "Ctrl" in html
        assert "Command" in html and "Control" in html

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("key", "glyph", "word"),
        [("ctrl", "⌃", "Ctrl"), ("alt", "⌥", "Alt"), ("shift", "⇧", "Shift")],
    )
    async def test_modifiers_are_words_away_from_apple(
        self, context_args, key, glyph, word
    ):
        html = await render_tree(Kbd(key), context_args=context_args)
        assert_attr(
            html,
            "kbd > span[aria-hidden]",
            ":data-glyph",
            f"($store.shortcuts?.apple ?? true) ? '{glyph}' : '{word}'",
        )
