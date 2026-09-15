import pytest

from hue.renderer import render_tree
from hue.ui import Textarea
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestTextarea:
    @pytest.mark.asyncio
    async def test_renders_a_labelled_textarea(self, context_args):
        html = await render_tree(
            Textarea("bio").label("About you"), context_args=context_args
        )
        assert_attr(html, "label", "for", "bio")
        assert_selector(html, "textarea#bio")

    @pytest.mark.asyncio
    async def test_the_value_is_not_padded_onto_its_own_line(self, context_args):
        # A textarea keeps every character between its tags, so a newline the
        # renderer added for readability would come back as part of the value.
        html = await render_tree(
            Textarea("bio").value("Northwind"), context_args=context_args
        )
        assert ">Northwind</textarea>" in html

    # max_length(): both branches
    @pytest.mark.asyncio
    async def test_the_limit_is_counted_not_enforced(self, context_args):
        # No maxlength attribute: an input that stops accepting characters
        # reads as a broken keyboard rather than as a limit.
        html = await render_tree(
            Textarea("bio").label("About you").max_length(280),
            context_args=context_args,
        )
        assert_no_selector(html, "textarea[maxlength]")
        assert "count + ' / 280'" in html
        assert_attr(html, "textarea", ":aria-invalid")

    @pytest.mark.asyncio
    async def test_no_counter_without_a_limit(self, context_args):
        html = await render_tree(
            Textarea("bio").label("About you"), context_args=context_args
        )
        assert_no_selector(html, "span.tabular-nums")
        assert_no_selector(html, "[x-data]")

    # autosize(): both branches
    @pytest.mark.asyncio
    async def test_autosize_measures_on_load_as_well_as_on_input(self, context_args):
        # Server-rendered text is already there, so waiting for a keystroke
        # would leave the box the wrong height until one arrives.
        html = await render_tree(
            Textarea("bio").autosize().value("two\nlines"), context_args=context_args
        )
        assert_selector(html, "textarea[x-init]")
        assert "scrollHeight" in html

    @pytest.mark.asyncio
    async def test_fixed_height_by_default(self, context_args):
        html = await render_tree(Textarea("bio"), context_args=context_args)
        assert_no_selector(html, "textarea[x-init]")

    # A server-side error wins over the counter, which would otherwise clear
    # the invalid state the moment the text got short enough.
    @pytest.mark.asyncio
    async def test_a_server_error_is_not_overwritten_by_the_counter(self, context_args):
        html = await render_tree(
            Textarea("bio").max_length(280).error("Too vague."),
            context_args=context_args,
        )
        assert_attr(html, "textarea", "aria-invalid", "true")
        assert_no_selector(html, "textarea[\\:aria-invalid]")
