import pytest

from hue.renderer import render_tree
from hue.ui import TableOfContents
from tests._a11y import assert_attr, assert_selector, select


class TestTableOfContents:
    @pytest.mark.parametrize(
        ("toc", "config"),
        [
            # h1 is the page's own title rather than a section of it.
            (TableOfContents(), '{"of": "main", "headings": "h2, h3"}'),
            # headings is a selector, so a section can keep itself out.
            (
                TableOfContents().of("#article", headings="h2:not([data-toc-skip])"),
                '{"of": "#article", "headings": "h2:not([data-toc-skip])"}',
            ),
        ],
        ids=["default", "custom"],
    )
    @pytest.mark.asyncio
    async def test_it_is_told_where_to_read_rather_than_what_is_there(
        self, context_args, toc, config
    ):
        # The entries come from the page itself, so there is no list here to
        # fall out of step with the headings it names.
        html = await render_tree(toc, context_args=context_args)
        assert_attr(html, "nav", "x-data", f"hueToc({config})")

    @pytest.mark.asyncio
    async def test_the_navigation_is_named_by_its_own_title(self, context_args):
        html = await render_tree(TableOfContents(), context_args=context_args)
        assert_attr(html, "nav", ":aria-labelledby", "$id('hue-toc-title')")
        assert "On this page" in html

    @pytest.mark.asyncio
    async def test_an_entry_is_a_template_rather_than_markup_in_javascript(
        self, context_args
    ):
        # Tailwind reads the source for its class names and never sees a
        # string put together at runtime, so the row is rendered here and
        # copied there.
        html = await render_tree(TableOfContents(), context_args=context_args)
        assert_selector(html, "template[x-ref=row] li > a > span")

    @pytest.mark.asyncio
    async def test_the_list_starts_empty_and_hidden(self, context_args):
        # Nothing has been read yet. Without x-cloak a page that turns out
        # to have no headings would show a title over an empty list first.
        html = await render_tree(TableOfContents(), context_args=context_args)
        assert select(html, "ol[x-ref=list]")[0].find_all("li") == []
        assert_attr(html, "nav", "x-cloak")
