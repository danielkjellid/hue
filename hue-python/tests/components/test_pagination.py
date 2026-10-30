import pytest

from hue import html as hue_html
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

    # A page past either end lands on the nearest real one
    @pytest.mark.asyncio
    async def test_a_page_before_the_first_is_the_first(self, context_args):
        html = await render_tree(
            Pagination().page(0).total_pages(7).total_records(148),
            context_args=context_args,
        )
        assert "1\u201310" in str(html)
        assert select(html, '[aria-current="page"]')[0].get_text().strip() == "1"

    @pytest.mark.asyncio
    async def test_a_page_past_the_last_is_the_last(self, context_args):
        html = await render_tree(
            Pagination()
            .page(20)
            .total_pages(15)
            .total_records(148)
            .href(lambda p: f"?page={p}"),
            context_args=context_args,
        )
        assert "141\u2013148" in str(html)
        assert select(html, '[aria-current="page"]')[0].get_text().strip() == "15"
        assert_selector(html, 'nav a[href="?page=14"][aria-label="Previous page"]')

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

    @pytest.mark.asyncio
    async def test_no_records_is_said_as_such(self, context_args):
        html = await render_tree(
            Pagination().page(1).total_pages(1).total_records(0),
            context_args=context_args,
        )
        assert "No records" in html
        assert "Showing" not in html

    # target(): both branches
    @pytest.mark.asyncio
    async def test_a_target_swaps_the_page_in_and_remembers_it(self, context_args):
        html = await render_tree(
            Pagination()
            .page(3)
            .total_pages(15)
            .href(lambda p: f"?page={p}")
            .target("invoices-rows")
            .id("invoices-pages"),
            context_args=context_args,
        )
        assert_attr(html, 'nav a[href="?page=4"]', "x-target.push", "invoices-rows")
        # The page you are on replaces: Enter on it, where focus lands once
        # a step is spent, would otherwise add the same page again.
        assert_attr(html, 'nav a[href="?page=3"]', "x-target.replace", "invoices-rows")
        assert_no_selector(html, 'nav a[href="?page=3"][x-target\\.push]')
        # It sits outside the rows and refreshes itself from the response,
        # so the mark moves to the page you land on.
        assert_attr(html, "#invoices-pages", "x-sync")

    @pytest.mark.asyncio
    async def test_its_links_take_ids_from_its_own(self, context_args):
        # A swap replaces the links, and the id is how focus finds the one it
        # was on. A step spent by the swap hands focus to the page it led to.
        def pages(own_id):
            return (
                Pagination()
                .page(3)
                .total_pages(15)
                .href(lambda p: f"?page={p}")
                .target("rows")
                .id(own_id)
            )

        html = await render_tree(
            hue_html.div(pages("a"), pages("b")), context_args=context_args
        )
        ids = [link["id"] for link in select(html, "nav a")]
        assert len(ids) == len(set(ids))
        assert_attr(html, "#a-next", "href", "?page=4")
        assert_attr(html, "#a-next", "data-hue-refocus", "a-page-4")
        assert_attr(html, "#b-previous", "data-hue-refocus", "b-page-2")
        assert_attr(html, "#b-page-15", "href", "?page=15")

    @pytest.mark.asyncio
    async def test_without_an_id_its_links_have_none(self, context_args):
        html = await render_tree(
            Pagination().page(3).total_pages(15).href(lambda p: f"?page={p}"),
            context_args=context_args,
        )
        assert_no_selector(html, "nav a[id]")
        assert_no_selector(html, "[data-hue-refocus]")

    @pytest.mark.asyncio
    async def test_a_target_without_an_id_of_its_own_is_refused(self, context_args):
        with pytest.raises(ValueError, match="id"):
            await render_tree(
                Pagination().page(3).total_pages(15).target("invoices-rows"),
                context_args=context_args,
            )

    @pytest.mark.asyncio
    async def test_without_a_target_a_step_is_a_navigation(self, context_args):
        html = await render_tree(
            Pagination().page(3).total_pages(15).href(lambda p: f"?page={p}"),
            context_args=context_args,
        )
        assert_no_selector(html, "[x-target\\.push]")
        assert_no_selector(html, "[x-sync]")

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
            .id("results")
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
        assert_selector(html, 'label[for="results-page-size"]')
        assert_attr(html, 'span[aria-hidden="true"]', "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_rows_per_page_shows_beside_numbered_steps_too(self, context_args):
        html = await render_tree(
            Pagination().id("results").page(2).total_pages(5).page_sizes([10, 25]),
            context_args=context_args,
        )
        assert_selector(html, "select")

    @pytest.mark.asyncio
    async def test_rows_per_page_without_an_id_raises(self, context_args):
        # Without an id the select would fall back to a bare page_size id,
        # and a second pagination on the page would claim the same one.
        with pytest.raises(ValueError, match="page_sizes"):
            await render_tree(
                Pagination().page(2).total_pages(5).page_sizes([10, 25]),
                context_args=context_args,
            )

    @pytest.mark.asyncio
    async def test_without_page_sizes_there_is_no_select(self, context_args):
        html = await render_tree(
            Pagination().page(2).total_pages(5), context_args=context_args
        )
        assert_no_selector(html, "select")

    @pytest.mark.asyncio
    async def test_the_select_takes_its_id_from_the_pagination(self, context_args):
        # One pagination above a table and one below must not share an id,
        # or the second label points at the first select.
        html = await render_tree(
            Pagination().id("top").page(2).total_pages(5).page_sizes([10, 25]),
            context_args=context_args,
        )
        assert_selector(html, 'select[id="top-page-size"]')
        assert_selector(html, 'label[for="top-page-size"]')

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
