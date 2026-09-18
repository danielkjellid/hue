import pytest

from hue.renderer import render_tree
from hue.ui import Breadcrumbs
from hue.ui.molecules.breadcrumbs import Crumb
from tests._a11y import assert_attr, assert_no_selector, assert_selector

_TRAIL = [
    Crumb("/", "Home"),
    Crumb("/billing", "Billing"),
    Crumb("/billing/invoices", "Invoices"),
    Crumb(None, "INV-2048"),
]


class TestBreadcrumbs:
    @pytest.mark.asyncio
    async def test_a_plain_pair_is_a_crumb_too(self, context_args):
        # The names are for reading; the pair still unpacks.
        html = await render_tree(
            Breadcrumbs().items([("/", "Home"), (None, "Here")]),
            context_args=context_args,
        )
        assert_selector(html, 'a[href="/"]')
        assert_selector(html, '[aria-current="page"]')

    @pytest.mark.asyncio
    async def test_it_is_a_named_nav_around_an_ordered_list(self, context_args):
        # Ordered, because the steps are a hierarchy rather than a set.
        html = await render_tree(Breadcrumbs().items(_TRAIL), context_args=context_args)
        assert_attr(html, "nav", "aria-label", "Breadcrumb")
        assert_selector(html, "nav > ol > li", count=4)

    @pytest.mark.asyncio
    async def test_the_page_you_are_on_is_not_a_link(self, context_args):
        # Making it one teaches people that breadcrumbs do nothing.
        html = await render_tree(Breadcrumbs().items(_TRAIL), context_args=context_args)
        assert_attr(html, '[aria-current="page"]', "aria-current", "page")
        assert_no_selector(html, 'a[aria-current="page"]')
        assert_selector(html, "nav a", count=3)

    @pytest.mark.asyncio
    async def test_the_separators_are_decoration(self, context_args):
        # "Greater than" read four times is noise.
        html = await render_tree(Breadcrumbs().items(_TRAIL), context_args=context_args)
        assert_selector(html, 'span[aria-hidden="true"] svg', count=3)

    # collapse_after(): both branches
    @pytest.mark.asyncio
    async def test_a_long_trail_folds_in_the_middle(self, context_args):
        html = await render_tree(
            Breadcrumbs().items(_TRAIL).collapse_after(3), context_args=context_args
        )
        # Where you started, where you are, and the step back between them.
        assert_attr(html, "button", "aria-label", "Show 1 hidden level")
        assert_selector(html, "nav > ol > li", count=4)

    @pytest.mark.asyncio
    async def test_a_trail_within_the_limit_is_left_alone(self, context_args):
        html = await render_tree(
            Breadcrumbs().items(_TRAIL).collapse_after(4), context_args=context_args
        )
        assert_no_selector(html, "button")
        assert_selector(html, "nav > ol > li", count=4)

    @pytest.mark.asyncio
    async def test_nothing_folds_without_a_limit(self, context_args):
        html = await render_tree(Breadcrumbs().items(_TRAIL), context_args=context_args)
        assert_no_selector(html, "button")

    @pytest.mark.asyncio
    async def test_the_hidden_steps_are_links_in_a_panel(self, context_args):
        # A list of links is navigation: role="menu" would announce them as
        # commands and change what the arrow keys are expected to do.
        html = await render_tree(
            Breadcrumbs().items(_TRAIL).collapse_after(3), context_args=context_args
        )
        assert_selector(html, '[role="dialog"] ul > li > a[href="/billing"]')
        assert_no_selector(html, '[role="menu"]')

    @pytest.mark.asyncio
    async def test_the_panel_leaves_the_trail_one_line(self, context_args):
        # Expanding in place would push the page around while the reader is
        # looking at it.
        html = await render_tree(
            Breadcrumbs().items(_TRAIL).collapse_after(3), context_args=context_args
        )
        assert_attr(html, '[role="dialog"]', "x-show", "open")
