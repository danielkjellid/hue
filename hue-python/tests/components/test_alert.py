import pytest

from hue.renderer import render_tree
from hue.ui import Alert
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestAlert:
    @pytest.mark.asyncio
    async def test_renders_a_title_and_description(self, context_args):
        html = await render_tree(
            Alert().title("Payment failed").description("The card was declined."),
            context_args=context_args,
        )
        assert "Payment failed" in html
        assert "The card was declined." in html

    @pytest.mark.parametrize(
        ("variant", "fill"),
        [
            ("neutral", "bg-surface-sunken"),
            ("info", "bg-info-subtle"),
            ("success", "bg-success-subtle"),
            ("warning", "bg-warning-subtle"),
            ("danger", "bg-danger-subtle"),
        ],
    )
    @pytest.mark.asyncio
    async def test_each_variant_has_its_own_tone(self, context_args, variant, fill):
        html = await render_tree(
            Alert().variant(variant).title("T"), context_args=context_args
        )
        assert_selector(html, f"div.{fill}")

    @pytest.mark.asyncio
    async def test_the_icon_is_decorative(self, context_args):
        # The words say what the alert is; an announced icon would say it
        # twice, and "circle x" is not what it means anyway.
        html = await render_tree(
            Alert().variant("danger").title("T"), context_args=context_args
        )
        assert_attr(html, 'span[aria-hidden="true"]', "aria-hidden", "true")

    @pytest.mark.asyncio
    async def test_an_icon_of_your_own_replaces_it(self, context_args):
        html = await render_tree(
            Alert().variant("info").icon("!").title("T"), context_args=context_args
        )
        assert_no_selector(html, "svg")

    # live(): both branches
    @pytest.mark.asyncio
    async def test_it_is_not_a_live_region_by_default(self, context_args):
        # One on the page at load is read in order like any other text; a live
        # region would have it said a second time.
        html = await render_tree(Alert().title("T"), context_args=context_args)
        assert_no_selector(html, '[role="alert"]')

    @pytest.mark.asyncio
    async def test_live_announces_it(self, context_args):
        html = await render_tree(Alert().title("T").live(), context_args=context_args)
        assert_selector(html, '[role="alert"]')

    # dismissible(): both branches
    @pytest.mark.asyncio
    async def test_dismissible_adds_a_named_close(self, context_args):
        html = await render_tree(
            Alert().title("T").dismissible(), context_args=context_args
        )
        assert_attr(html, "button", "aria-label", "Dismiss")
        assert_selector(html, "[x-data] [x-on\\:click]")

    @pytest.mark.asyncio
    async def test_not_dismissible_by_default(self, context_args):
        html = await render_tree(Alert().title("T"), context_args=context_args)
        assert_no_selector(html, "button")
        assert_no_selector(html, "[x-data]")

    # banner(): both branches
    @pytest.mark.asyncio
    async def test_a_banner_runs_edge_to_edge(self, context_args):
        html = await render_tree(Alert().title("T").banner(), context_args=context_args)
        assert_selector(html, "div.rounded-none")

    @pytest.mark.asyncio
    async def test_boxed_by_default(self, context_args):
        html = await render_tree(Alert().title("T"), context_args=context_args)
        assert_selector(html, "div.rounded-md")

    # actions(): both branches
    @pytest.mark.asyncio
    async def test_actions_take_the_alerts_own_tone(self, context_args):
        # A near-black ghost label surrounded by tinted copy, and an opaque
        # grey hover patch on a coloured fill, are both wrong here.
        html = await render_tree(
            Alert().variant("danger").title("T").actions("retry"),
            context_args=context_args,
        )
        assert_selector(html, "div.mt-3")
        assert "text-current" in html

    @pytest.mark.asyncio
    async def test_no_actions_by_default(self, context_args):
        html = await render_tree(Alert().title("T"), context_args=context_args)
        assert_no_selector(html, "div.mt-3")
