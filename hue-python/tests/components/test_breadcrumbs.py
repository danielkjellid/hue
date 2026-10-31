import pytest

from hue.renderer import render_tree
from hue.ui import Breadcrumbs
from hue.ui.molecules.breadcrumbs import Crumb
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select

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
    async def test_a_named_nav_around_an_ordered_list(self, context_args):
        # Ordered, because the steps are a hierarchy rather than a set.
        html = await render_tree(Breadcrumbs().items(_TRAIL), context_args=context_args)
        assert_attr(html, "nav", "aria-label", "Breadcrumb")
        assert_selector(html, "nav > ol > li", count=4)
        # The page you are on is not a link: making it one teaches people that
        # breadcrumbs do nothing.
        assert_selector(html, '[aria-current="page"]')
        assert_no_selector(html, 'a[aria-current="page"]')
        assert_selector(html, "nav a", count=3)

    @pytest.mark.parametrize(
        ("trail", "limit", "folds"),
        [
            (_TRAIL, 3, True),
            (_TRAIL, 4, False),
            # The root and the last two always show, so a trail of two has no
            # middle to fold, however low the limit.
            (_TRAIL[::3], 1, False),
        ],
    )
    @pytest.mark.asyncio
    async def test_a_long_trail_folds_in_the_middle(
        self, context_args, trail, limit, folds
    ):
        html = await render_tree(
            Breadcrumbs().items(trail).collapse_after(limit),
            context_args=context_args,
        )
        # Where you started, where you are, and the step back between them.
        buttons = select(html, "button")
        assert [b["aria-label"] for b in buttons] == (
            ["Show 1 hidden level"] if folds else []
        )
        assert_selector(html, "nav > ol > li", count=min(len(trail), 4))

    @pytest.mark.asyncio
    async def test_the_hidden_steps_are_links_in_a_panel(self, context_args):
        # A list of links is navigation: role="menu" would announce them as
        # commands and change what the arrow keys are expected to do.
        html = await render_tree(
            Breadcrumbs().items(_TRAIL).collapse_after(3), context_args=context_args
        )
        assert_selector(html, '[role="dialog"] ul > li > a[href="/billing"]')
        assert_no_selector(html, '[role="menu"]')
        assert_attr(html, '[role="dialog"]', "aria-label", "Hidden level")
        assert_attr(html, '[role="dialog"]', "x-show", "open")
        # A fragment link stays on the page, under a panel left open.
        assert_attr(html, '[role="dialog"] a', "x-on:click", "close()")
