import pytest

from hue.renderer import render_tree
from hue.ui import Progress, ProgressRing
from tests._a11y import assert_attr, assert_no_selector, assert_selector


class TestProgress:
    @pytest.mark.asyncio
    async def test_reports_its_position(self, context_args):
        html = await render_tree(Progress().value(64), context_args=context_args)
        assert_attr(html, '[role="progressbar"]', "aria-valuenow", "64")
        assert_attr(html, '[role="progressbar"]', "aria-valuemin", "0")
        assert_attr(html, '[role="progressbar"]', "aria-valuemax", "100")
        assert "width:64%" in html

    # value(): determinate and indeterminate differ in more than styling
    @pytest.mark.asyncio
    async def test_indeterminate_omits_the_position(self, context_args):
        # aria-valuenow="0" would announce "0 percent", which reads as stalled
        # rather than unknown.
        html = await render_tree(Progress(), context_args=context_args)
        assert_no_selector(html, "[aria-valuenow]")
        assert_selector(html, "div.animate-progress")

    @pytest.mark.asyncio
    async def test_determinate_does_not_animate_the_sweep(self, context_args):
        html = await render_tree(Progress().value(40), context_args=context_args)
        assert_no_selector(html, "div.animate-progress")

    @pytest.mark.asyncio
    async def test_value_is_clamped_to_the_track(self, context_args):
        html = await render_tree(Progress().value(140), context_args=context_args)
        assert_attr(html, '[role="progressbar"]', "aria-valuenow", "100")
        assert "width:100%" in html

    # label(): both branches
    @pytest.mark.asyncio
    async def test_label_is_shown_and_names_the_bar(self, context_args):
        html = await render_tree(
            Progress().value(64).label("Uploading archive.zip"),
            context_args=context_args,
        )
        assert "Uploading archive.zip" in html
        assert_attr(html, '[role="progressbar"]', "aria-label", "Uploading archive.zip")
        # The percentage is shown alongside, on shared figure widths.
        assert_selector(html, "span.tabular-nums")
        assert "64%" in html

    @pytest.mark.asyncio
    async def test_unlabelled_bar_is_just_the_track(self, context_args):
        html = await render_tree(Progress().value(64), context_args=context_args)
        assert_no_selector(html, "span.tabular-nums")

    @pytest.mark.asyncio
    async def test_indeterminate_label_shows_no_percentage(self, context_args):
        html = await render_tree(
            Progress().label("Exporting"), context_args=context_args
        )
        assert "Exporting" in html
        assert_no_selector(html, "span.tabular-nums")

    # variant() and size()
    @pytest.mark.asyncio
    async def test_default_variant_and_size(self, context_args):
        html = await render_tree(Progress().value(10), context_args=context_args)
        assert_selector(html, "div.bg-accent")
        assert_selector(html, "div.h-1\\.5")

    @pytest.mark.asyncio
    async def test_explicit_variant_and_size(self, context_args):
        html = await render_tree(
            Progress().value(10).variant("danger").size("lg"),
            context_args=context_args,
        )
        assert_selector(html, "div.bg-danger")
        assert_selector(html, "div.h-2\\.5")


class TestProgressRing:
    @pytest.mark.asyncio
    async def test_states_the_percentage_because_a_circle_says_nothing(
        self, context_args
    ):
        html = await render_tree(ProgressRing().value(28), context_args=context_args)
        assert_attr(html, 'svg[role="img"]', "aria-label", "28 percent complete")

    @pytest.mark.asyncio
    async def test_label_is_folded_into_the_announcement(self, context_args):
        html = await render_tree(
            ProgressRing().value(28).label("Storage used"), context_args=context_args
        )
        assert_attr(
            html, 'svg[role="img"]', "aria-label", "Storage used, 28 percent complete"
        )

    @pytest.mark.asyncio
    async def test_the_arc_matches_the_value(self, context_args):
        empty = await render_tree(ProgressRing().value(0), context_args=context_args)
        full = await render_tree(ProgressRing().value(100), context_args=context_args)
        # A full ring has no gap left; an empty one is all gap.
        assert 'stroke-dashoffset="0.00"' in full
        assert 'stroke-dashoffset="131.95"' in empty

    @pytest.mark.asyncio
    async def test_variant_colours_the_arc_with_a_literal_class(self, context_args):
        html = await render_tree(
            ProgressRing().value(50).variant("success"), context_args=context_args
        )
        assert "stroke-success" in html
