import pytest

from hue.renderer import render_tree
from hue.ui import TableOfContents
from tests._a11y import assert_attr, assert_selector, select


class TestTableOfContents:
    @pytest.mark.asyncio
    async def test_it_is_told_where_to_read_rather_than_what_is_there(
        self, context_args
    ):
        # The entries come from the page itself, so there is no list here to
        # fall out of step with the headings it names.
        html = await render_tree(
            TableOfContents().of("#article", headings="h2, h3, h4"),
            context_args=context_args,
        )
        assert_attr(
            html,
            "nav",
            "x-data",
            'hueToc({"of": "#article", "headings": "h2, h3, h4"})',
        )

    @pytest.mark.asyncio
    async def test_it_reads_the_main_element_and_two_levels_by_default(
        self, context_args
    ):
        # h1 is the page's own title rather than a section of it, and a
        # fourth level is more shape than a list down a side can carry.
        html = await render_tree(TableOfContents(), context_args=context_args)
        assert_attr(
            html, "nav", "x-data", 'hueToc({"of": "main", "headings": "h2, h3"})'
        )

    @pytest.mark.asyncio
    async def test_the_navigation_is_named_by_its_own_title(self, context_args):
        html = await render_tree(
            TableOfContents().title("Contents"), context_args=context_args
        )
        assert_attr(html, "nav", ":aria-labelledby", "$id('hue-toc-title')")
        assert "Contents" in html

    @pytest.mark.asyncio
    async def test_the_title_says_on_this_page_unless_it_is_told_otherwise(
        self, context_args
    ):
        html = await render_tree(TableOfContents(), context_args=context_args)
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
        assert (
            "aria-[current=location]:font-semibold"
            in select(html, "template a")[0]["class"]
        )

    @pytest.mark.asyncio
    async def test_the_list_starts_empty_and_hidden(self, context_args):
        # Nothing has been read yet. Without x-cloak a page that turns out
        # to have no headings would show a title over an empty list first.
        html = await render_tree(TableOfContents(), context_args=context_args)
        assert_selector(html, "ol[x-ref=list]")
        assert select(html, "ol")[0].find_all("li") == []
        assert_attr(html, "nav", "x-cloak")

    @pytest.mark.asyncio
    async def test_the_rail_is_not_announced(self, context_args):
        # It says the same thing the list already says, in a way a screen
        # reader cannot use.
        html = await render_tree(TableOfContents(), context_args=context_args)
        assert_attr(html, "svg[x-ref=rail]", "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_the_rail_carries_no_geometry_of_its_own(self, context_args):
        # Every number in it is measured from the rows once they exist, so
        # there is nothing here to disagree with where they landed.
        html = await render_tree(TableOfContents(), context_args=context_args)
        rail = select(html, "svg[x-ref=rail]")[0]
        assert "width" not in rail.attrs
        assert [path.get("d") for path in rail.find_all("path")] == [None, None]

    @pytest.mark.asyncio
    async def test_a_page_can_keep_a_heading_out_of_its_own_contents(
        self, context_args
    ):
        # headings is a selector rather than a list of levels, so leaving a
        # section out needs nothing here that is not already there.
        html = await render_tree(
            TableOfContents().of("main", headings="h2:not([data-toc-skip]), h3"),
            context_args=context_args,
        )
        assert "h2:not([data-toc-skip]), h3" in select(html, "nav")[0]["x-data"]
