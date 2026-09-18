import pytest

from hue.renderer import render_tree
from hue.ui import TableOfContents
from hue.ui.molecules.table_of_contents import Heading, _rail
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

_HEADINGS = [
    Heading("intro", "Introduction"),
    Heading("concepts", "Core Concepts"),
    Heading("architecture", "Architecture", 3),
    Heading("components", "Components"),
]


class TestTableOfContents:
    @pytest.mark.asyncio
    async def test_every_entry_is_a_link_to_its_section(self, context_args):
        # An in-page anchor rather than a scroll handler: it works before
        # Alpine has started, it can be opened in a new tab, and the browser
        # moves the keyboard through the page along with the view.
        html = await render_tree(
            TableOfContents().items(_HEADINGS), context_args=context_args
        )
        hrefs = [link["href"] for link in select(html, "nav ol li a")]
        assert hrefs == ["#intro", "#concepts", "#architecture", "#components"]

    @pytest.mark.asyncio
    async def test_the_navigation_is_named_by_its_own_title(self, context_args):
        html = await render_tree(
            TableOfContents().items(_HEADINGS).title("Contents"),
            context_args=context_args,
        )
        assert_attr(html, "nav", ":aria-labelledby", "$id('hue-toc-title')")
        assert "Contents" in html

    @pytest.mark.asyncio
    async def test_the_rail_is_not_announced(self, context_args):
        # It says the same thing the list already says, in a way a screen
        # reader cannot use.
        html = await render_tree(
            TableOfContents().items(_HEADINGS), context_args=context_args
        )
        assert_attr(html, "svg.absolute", "aria-hidden", "true")

    # current(): the heading it names, and the fallback when it names none
    @pytest.mark.asyncio
    async def test_the_current_heading_is_marked_as_the_location(self, context_args):
        html = await render_tree(
            TableOfContents().items(_HEADINGS).current("architecture"),
            context_args=context_args,
        )
        marked = select(html, "[aria-current]")
        assert len(marked) == 1
        assert marked[0]["href"] == "#architecture"

    @pytest.mark.asyncio
    async def test_an_unknown_current_falls_back_to_the_first(self, context_args):
        html = await render_tree(
            TableOfContents().items(_HEADINGS).current("nowhere"),
            context_args=context_args,
        )
        assert select(html, "[aria-current]")[0]["href"] == "#intro"

    @pytest.mark.asyncio
    async def test_where_the_reader_is_is_where_the_fill_reaches(self, context_args):
        # The three parts that move are one number: the index into the
        # distances the server measured along the path.
        html = await render_tree(
            TableOfContents().items(_HEADINGS).current("components"),
            context_args=context_args,
        )
        assert_attr(html, "nav", "x-data")
        assert "], 3, [" in select(html, "nav")[0]["x-data"]
        assert_attr(html, "path[stroke-dasharray]", ":stroke-dashoffset")

    # items(): with headings, and without
    @pytest.mark.asyncio
    async def test_an_empty_list_draws_no_rail(self, context_args):
        html = await render_tree(TableOfContents(), context_args=context_args)
        assert_no_selector(html, "svg.absolute")
        assert_selector(html, "ol")

    @pytest.mark.asyncio
    async def test_a_plain_tuple_is_a_heading(self, context_args):
        html = await render_tree(
            TableOfContents().items([("intro", "Introduction", 2)]),
            context_args=context_args,
        )
        assert_attr(html, "a", "href", "#intro")


class TestRail:
    def test_a_nested_heading_moves_the_rail_and_the_label_together(self):
        rail = _rail([2, 3])
        assert rail.xs[1] > rail.xs[0]

    def test_the_shallowest_heading_is_the_top_of_the_rail(self):
        # A page whose headings start at h3 is not a page indented by one.
        assert _rail([3, 4]).xs == _rail([2, 3]).xs

    def test_a_change_of_level_is_longer_than_the_drop_it_covers(self):
        # Which is the whole reason the distances are measured rather than
        # counted: the dot rides the curve, so it has further to travel than
        # it would down a straight line.
        straight = _rail([2, 2])
        bent = _rail([2, 3])
        assert bent.length > straight.length

    def test_the_last_heading_is_the_end_of_the_path(self):
        # The browser divides by this to place the dot, and takes it from the
        # distances rather than being told twice.
        rail = _rail([2, 3, 3, 2])
        assert rail.reach[-1] == pytest.approx(rail.length)
