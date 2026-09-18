import pytest

from hue.renderer import render_tree
from hue.ui import Pagination
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


class TestPagination:
    @pytest.mark.asyncio
    async def test_it_is_a_named_nav_beside_the_count(self, context_args):
        # "Page 3 of 7" without "148 records" leaves nobody able to tell
        # whether their filter did anything.
        html = await render_tree(
            Pagination().page(3).total_pages(15).total_records(148),
            context_args=context_args,
        )
        assert_attr(html, "nav", "aria-label", "Pagination")
        assert "Showing" in str(html)
        assert "21\u201330" in str(html)
        assert "148" in str(html)

    @pytest.mark.asyncio
    async def test_the_page_you_are_on_is_marked(self, context_args):
        html = await render_tree(
            Pagination().page(3).total_pages(15).total_records(148),
            context_args=context_args,
        )
        assert_attr(html, '[aria-current="page"]', "aria-current", "page")
        assert select(html, '[aria-current="page"]')[0].get_text().strip() == "3"

    @pytest.mark.asyncio
    async def test_the_window_keeps_the_ends_reachable(self, context_args):
        # First and last always, the rest folded, so a jump to the end is one
        # press rather than a scroll through fifteen numbers.
        html = await render_tree(
            Pagination().page(8).total_pages(15).total_records(148),
            context_args=context_args,
        )
        numbers = [item.get_text().strip() for item in select(html, "nav button")]
        # The arrows carry their icon's title, so the numbers are what is left.
        numbers = [text for text in numbers if text.isdigit()]
        assert numbers[0] == "1"
        assert numbers[-1] == "15"
        assert "7" in numbers and "9" in numbers
        assert_selector(html, 'span[aria-hidden="true"]', count=2)

    @pytest.mark.asyncio
    async def test_a_step_with_nowhere_to_go_stays_and_says_so(self, context_args):
        # Announced but not activatable: a control that disappears at the ends
        # teaches nobody where the ends are.
        html = await render_tree(
            Pagination().page(1).total_pages(15).total_records(148),
            context_args=context_args,
        )
        assert_attr(html, '[aria-label="Previous page"]', "aria-disabled", "true")
        assert_no_selector(html, 'button[aria-label="Previous page"]')
        assert_selector(html, 'button[aria-label="Next page"]')

    # href(): both branches
    @pytest.mark.asyncio
    async def test_with_a_destination_the_steps_are_links(self, context_args):
        html = await render_tree(
            Pagination().page(3).total_pages(15).href(lambda p: f"?page={p}"),
            context_args=context_args,
        )
        assert_selector(html, 'nav a[href="?page=4"]')
        assert_no_selector(html, "nav button")

    @pytest.mark.asyncio
    async def test_without_one_they_are_buttons(self, context_args):
        html = await render_tree(
            Pagination().page(3).total_pages(15), context_args=context_args
        )
        assert_selector(html, "nav button")
        assert_no_selector(html, "nav a")

    # The one-page case
    @pytest.mark.asyncio
    async def test_one_page_keeps_the_control_and_makes_it_inert(self, context_args):
        # A row that vanishes when a filter narrows the list to one page
        # reads as something breaking.
        html = await render_tree(
            Pagination().page(1).total_pages(1).total_records(10),
            context_args=context_args,
        )
        assert_attr(html, "nav", "aria-label", "Pagination, single page")
        assert_no_selector(html, "nav button")
        assert_no_selector(html, "nav a")
        assert_selector(html, 'nav [aria-disabled="true"]', count=2)
        assert_selector(html, 'nav [aria-current="page"]')

    # cursor(): the other way to page
    @pytest.mark.asyncio
    async def test_a_cursor_knows_only_which_ways_it_can_go(self, context_args):
        html = await render_tree(
            Pagination().total_records(2481).cursor(previous=False, next=True),
            context_args=context_args,
        )
        steps = select(html, "nav button")
        assert [step.get_text().strip() for step in steps] == ["Previous", "Next"]
        assert steps[0].has_attr("disabled")
        assert not steps[1].has_attr("disabled")
        assert_no_selector(html, '[aria-current="page"]')

    @pytest.mark.asyncio
    async def test_rows_per_page_names_itself_once(self, context_args):
        # The select carries the name; the words beside it are the same
        # words, marked as decoration so they are not read twice.
        html = await render_tree(
            Pagination()
            .total_records(2481)
            .page_size(25)
            .page_sizes([10, 25, 50])
            .cursor(previous=False, next=True),
            context_args=context_args,
        )
        assert_selector(html, "select")
        assert_selector(html, "option[selected]")
        # One name, from the select's own label; the words beside it are
        # marked as decoration rather than announced a second time.
        assert_selector(html, 'label[for="page_size"]')
        assert_attr(html, 'span[aria-hidden="true"]', "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_a_cursor_counts_rather_than_ranges(self, context_args):
        # There is no page number to take a range from.
        html = await render_tree(
            Pagination().total_records(2481).cursor(previous=True, next=True),
            context_args=context_args,
        )
        assert "2,481 records" in str(html)
        assert "Showing" not in str(html)

    @pytest.mark.asyncio
    async def test_the_count_is_optional(self, context_args):
        html = await render_tree(
            Pagination().page(2).total_pages(4), context_args=context_args
        )
        assert "Showing" not in str(html)
        assert_selector(html, "nav")

    # page_size() changes what the range says
    @pytest.mark.asyncio
    async def test_the_page_size_sets_the_range(self, context_args):
        html = await render_tree(
            Pagination().page(2).total_pages(5).total_records(96).page_size(25),
            context_args=context_args,
        )
        assert "26\u201350" in str(html)
