import re

import pytest

from hue.renderer import render_tree
from hue.ui import Progress, ProgressRing
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _bar() -> Progress:
    # A bare bar, named but drawing no label row.
    return Progress().label("Upload").hidden_label()


class TestProgress:
    @pytest.mark.parametrize(
        ("value", "now", "text"),
        [
            (64, "64", "64%"),
            (0, "0", "0%"),
            (0.5, "0.5", "0%"),
            (100, "100", "100%"),
            # Clamped to the track.
            (150, "100", "100%"),
        ],
    )
    @pytest.mark.asyncio
    async def test_reports_its_position(self, context_args, value, now, text):
        html = await render_tree(_bar().value(value), context_args=context_args)
        assert_attr(html, '[role="progressbar"]', "aria-valuenow", now)
        assert_attr(html, '[role="progressbar"]', "aria-valuemin", "0")
        assert_attr(html, '[role="progressbar"]', "aria-valuemax", "100")
        assert_attr(html, '[role="progressbar"]', "aria-valuetext", text)
        assert f"width:{min(value, 100)}%" in html

    # aria-valuenow="0" would announce "0 percent", which reads as stalled
    # rather than unknown. A bar with no value is the same as not knowing, and
    # indeterminate wins over a stale value so it needn't be unset first.
    @pytest.mark.parametrize(
        "bar",
        [_bar().indeterminate(), _bar().value(64).indeterminate(), _bar()],
        ids=["indeterminate", "over-a-value", "no-value"],
    )
    @pytest.mark.asyncio
    async def test_indeterminate_omits_the_position(self, context_args, bar):
        html = await render_tree(bar, context_args=context_args)
        assert_no_selector(html, "[aria-valuenow]")
        assert_no_selector(html, "[aria-valuetext]")
        assert_selector(html, "div.animate-progress")

    @pytest.mark.asyncio
    async def test_reduced_motion_fills_the_track_rather_than_stopping_at_40(
        self, context_args
    ):
        # The global reduced-motion rule ends the sweep after one pass, which
        # would leave a still 40% fill that reads as 40% done.
        html = await render_tree(_bar().indeterminate(), context_args=context_args)
        assert_selector(html, "div.motion-reduce\\:w-full")

    @pytest.mark.asyncio
    async def test_nan_is_refused_rather_than_reported_complete(self, context_args):
        with pytest.raises(ValueError, match="NaN"):
            await render_tree(_bar().value(float("nan")), context_args=context_args)

    @pytest.mark.asyncio
    async def test_label_is_shown_and_names_the_bar(self, context_args):
        html = await render_tree(
            Progress().value(64).label("  Uploading archive.zip  "),
            context_args=context_args,
        )
        assert "Uploading archive.zip" in html
        assert_attr(html, '[role="progressbar"]', "aria-label", "Uploading archive.zip")
        assert select(html, "span.tabular-nums")[0].text == "64%"

    @pytest.mark.asyncio
    async def test_only_a_full_bar_claims_100(self, context_args):
        html = await render_tree(
            Progress().value(99.99999).label("Upload"), context_args=context_args
        )
        assert select(html, "span.tabular-nums")[0].text == "99%"
        # A screen reader rounds aria-valuenow itself, so it is told the
        # readout's text too.
        assert_attr(html, '[role="progressbar"]', "aria-valuenow", "99.99999")
        assert_attr(html, '[role="progressbar"]', "aria-valuetext", "99%")

    @pytest.mark.asyncio
    async def test_a_hidden_label_leaves_just_the_named_track(self, context_args):
        html = await render_tree(
            _bar().value(64).class_("w-40"),
            context_args=context_args,
        )
        assert_no_selector(html, "span.tabular-nums")
        assert_attr(html, '[role="progressbar"]', "aria-label", "Upload")
        # With no wrapper to carry them, the caller's classes go on the track.
        assert_selector(html, '[role="progressbar"].w-40')

    @pytest.mark.parametrize("label", [None, "", "   "])
    @pytest.mark.asyncio
    async def test_a_bar_with_no_name_is_refused(self, context_args, label):
        bar = Progress().value(64)
        if label is not None:
            bar.label(label)
        with pytest.raises(ValueError, match="label"):
            await render_tree(bar, context_args=context_args)

    @pytest.mark.asyncio
    async def test_indeterminate_label_shows_no_percentage(self, context_args):
        html = await render_tree(
            Progress().indeterminate().label("Exporting"), context_args=context_args
        )
        assert "Exporting" in html
        assert_no_selector(html, "span.tabular-nums")


class TestProgressRing:
    # A circle says nothing on its own, so the percentage is always stated.
    @pytest.mark.parametrize(
        ("label", "name"),
        [
            (None, "28 percent complete"),
            ("Storage used", "Storage used, 28 percent complete"),
            ("", "28 percent complete"),
            ("   ", "28 percent complete"),
        ],
    )
    @pytest.mark.asyncio
    async def test_is_named_by_its_percentage(self, context_args, label, name):
        ring = ProgressRing().value(28)
        if label is not None:
            ring.label(label)
        html = await render_tree(ring, context_args=context_args)
        assert_attr(html, 'svg[role="img"]', "aria-label", name)

    @pytest.mark.asyncio
    async def test_the_arc_matches_the_value(self, context_args):
        empty = await render_tree(ProgressRing().value(0), context_args=context_args)
        full = await render_tree(ProgressRing().value(100), context_args=context_args)
        # A full ring has no gap left; an empty one is all gap.
        assert 'stroke-dashoffset="0.00"' in full
        assert 'stroke-dashoffset="131.95"' in empty

    @pytest.mark.asyncio
    async def test_short_of_full_leaves_a_gap_the_caps_cannot_close(self, context_args):
        html = await render_tree(ProgressRing().value(99.9), context_args=context_args)
        offset = float(re.search(r'stroke-dashoffset="([\d.]+)"', html)[1])
        # 5px of round caps plus a gap that still shows.
        assert offset > 5 + 2

    @pytest.mark.asyncio
    async def test_nan_is_refused_rather_than_reported_complete(self, context_args):
        with pytest.raises(ValueError, match="NaN"):
            await render_tree(
                ProgressRing().value(float("nan")), context_args=context_args
            )

    @pytest.mark.parametrize(("value", "shown"), [(99.99999, "99"), (100, "100")])
    @pytest.mark.asyncio
    async def test_only_a_full_ring_claims_100(self, context_args, value, shown):
        html = await render_tree(
            ProgressRing().value(value).show_value(), context_args=context_args
        )
        # The svg already announces it, so the printed figure is decorative.
        assert select(html, 'span[aria-hidden="true"]')[0].text == f"{shown}%"
        assert_attr(html, 'svg[role="img"]', "aria-label", f"{shown} percent complete")
