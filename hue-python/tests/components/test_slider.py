import pytest

from hue.renderer import render_tree
from hue.ui import Slider
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _slider():
    return Slider().name("seats").label("Team seats").min(1).max(50).value(12)


class TestSlider:
    @pytest.mark.asyncio
    async def test_renders_a_labelled_range_input(self, context_args):
        # A native range, so the arrow keys, Home and End all come free.
        html = await render_tree(_slider(), context_args=context_args)
        assert_attr(html, "label", "for", "seats")
        assert_attr(html, "input", "type", "range")
        assert_attr(html, "input", "min", "1")
        assert_attr(html, "input", "max", "50")

    @pytest.mark.asyncio
    async def test_the_fill_is_a_fraction_of_the_range(self, context_args):
        # The track's fill is a gradient stop, because a range input has
        # nowhere to put a second element.
        html = await render_tree(_slider(), context_args=context_args)
        assert_attr(html, "input", ":style")
        assert "--slider-fill" in html
        # Measured from the low end, over the span, not over the max.
        assert "(value - 1) / 49" in html

    # show_value(): both branches
    @pytest.mark.asyncio
    async def test_the_readout_is_right_before_alpine_runs(self, context_args):
        # Bound as well as rendered: an x-text alone leaves an empty box until
        # the page hydrates.
        html = await render_tree(_slider(), context_args=context_args)
        assert_selector(html, "span.tabular-nums")
        assert ">12<" in html

    @pytest.mark.asyncio
    async def test_the_readout_can_be_turned_off(self, context_args):
        html = await render_tree(_slider().show_value(False), context_args=context_args)
        assert_no_selector(html, "span.tabular-nums")

    @pytest.mark.asyncio
    async def test_prefix_and_suffix_wrap_the_number(self, context_args):
        html = await render_tree(
            _slider().prefix("$").suffix("/mo"), context_args=context_args
        )
        assert ">$12/mo<" in html
        assert "'$' + value + '/mo'" in html

    # ticks(): both branches
    @pytest.mark.asyncio
    async def test_ticks_spread_across_the_track(self, context_args):
        html = await render_tree(
            _slider().ticks("1", "25", "50"), context_args=context_args
        )
        assert_selector(html, "div.text-2xs > span", count=3)

    @pytest.mark.asyncio
    async def test_no_ticks_by_default(self, context_args):
        html = await render_tree(_slider(), context_args=context_args)
        assert_no_selector(html, "div.text-2xs")

    @pytest.mark.asyncio
    async def test_the_state_covers_the_track_and_the_readout(self, context_args):
        # They are in different columns of the field, so the scope has to be
        # the field itself.
        html = await render_tree(_slider(), context_args=context_args)
        assert_selector(html, "[x-data] input[type='range']")
        assert_selector(html, "[x-data] span[x-text]")
