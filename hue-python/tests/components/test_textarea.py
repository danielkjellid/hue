import pytest

from hue.renderer import render_tree
from hue.ui import Textarea
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestTextarea:
    @pytest.mark.asyncio
    async def test_renders_a_labelled_textarea(self, context_args):
        html = await render_tree(
            Textarea().name("bio").label("About you"), context_args=context_args
        )
        assert_attr(html, "label", "for", "bio")
        assert_selector(html, "textarea#bio")

    @pytest.mark.parametrize(
        ("value", "rendered"),
        [
            # A newline the renderer added for readability would come back as
            # part of the value: a textarea keeps every character.
            ("Northwind", ">\nNorthwind</textarea>"),
            # The parser drops one newline straight after the opening tag, so
            # the one written first is the one it drops.
            ("\nNorthwind", ">\n\nNorthwind</textarea>"),
        ],
    )
    @pytest.mark.asyncio
    async def test_the_value_comes_back_as_it_went_in(
        self, context_args, value, rendered
    ):
        html = await render_tree(
            Textarea().name("bio").value(value), context_args=context_args
        )
        assert rendered in html

    @pytest.mark.asyncio
    async def test_the_limit_is_counted_not_enforced(self, context_args):
        # No maxlength: an input that stops accepting characters reads as a
        # broken keyboard. "12 / 10" read aloud does not say which number is
        # the limit, so the visible count is hidden and a sentence describes
        # the control.
        html = await render_tree(
            Textarea().name("bio").label("About you").max_length(10).value("Hi"),
            context_args=context_args,
        )
        assert_no_selector(html, "textarea[maxlength]")
        assert_attr(html, "textarea", ":aria-invalid")
        assert_attr(html, "span.tabular-nums", "aria-hidden", "true")
        assert_attr(html, "textarea", "aria-describedby", "bio-count")
        assert_attr(html, "#bio-count", "aria-live", "polite")

    @pytest.mark.parametrize(
        ("value", "sentence"),
        [
            ("Hi", "You have 8 characters remaining"),
            ("a" * 11, "You have 1 character too many"),
        ],
    )
    @pytest.mark.asyncio
    async def test_the_count_says_how_far_from_the_limit(
        self, context_args, value, sentence
    ):
        html = await render_tree(
            Textarea().name("bio").label("About you").max_length(10).value(value),
            context_args=context_args,
        )
        assert sentence in html

    @pytest.mark.asyncio
    async def test_no_description_without_a_limit(self, context_args):
        html = await render_tree(
            Textarea().name("bio").label("About you"), context_args=context_args
        )
        assert_no_selector(html, "textarea[aria-describedby]")

    @pytest.mark.asyncio
    async def test_autosize_measures_on_load_as_well_as_on_input(self, context_args):
        # Server-rendered text is already there, so waiting for a keystroke
        # would leave the box the wrong height until one arrives.
        html = await render_tree(
            Textarea().name("bio").autosize().value("two\nlines"),
            context_args=context_args,
        )
        assert_selector(html, "textarea[x-init]")
        assert "scrollHeight" in html

    @pytest.mark.asyncio
    async def test_a_server_error_is_not_overwritten_by_the_counter(self, context_args):
        # Otherwise the invalid state clears the moment the text got short
        # enough.
        html = await render_tree(
            Textarea().name("bio").max_length(280).error("Too vague."),
            context_args=context_args,
        )
        assert_attr(html, "textarea", "aria-invalid", "true")
        assert_no_selector(html, "textarea[\\:aria-invalid]")
