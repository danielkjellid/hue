import pytest

from hue.renderer import render_tree
from hue.ui import SegmentedControl, SegmentedOption
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


def _control(**kwargs):
    return SegmentedControl(**kwargs).content(
        SegmentedOption().value("day").content("Day"),
        SegmentedOption().value("week").content("Week"),
    )


class TestSegmentedControl:
    @pytest.mark.asyncio
    async def test_is_a_named_group_of_buttons(self, context_args):
        # The label is what tells a screen reader what is being chosen.
        html = await render_tree(
            _control().label("Date range"), context_args=context_args
        )
        assert_attr(html, 'div[role="group"]', "aria-label", "Date range")
        assert_selector(html, 'button[type="button"]', count=2)

    # value(): marks one option, and only that one
    @pytest.mark.asyncio
    async def test_marks_the_matching_option(self, context_args):
        html = await render_tree(
            _control().label("Range").value("week"), context_args=context_args
        )
        pressed = [b for b in select(html, "button") if b.get("aria-pressed") == "true"]
        assert len(pressed) == 1
        assert pressed[0].get_text(strip=True) == "Week"

    @pytest.mark.asyncio
    async def test_unmatched_options_say_so(self, context_args):
        html = await render_tree(
            _control().label("Range").value("week"), context_args=context_args
        )
        assert_selector(html, 'button[aria-pressed="false"]', count=1)

    @pytest.mark.asyncio
    async def test_without_a_value_selection_is_left_to_the_browser(self, context_args):
        # ThemeSwitcher binds aria-pressed with Alpine, because which theme is
        # on is only known client-side. A static value would fight it.
        html = await render_tree(_control().label("Range"), context_args=context_args)
        assert_no_selector(html, "button[aria-pressed]")

    # size(): the control owns it, since the options are its own
    @pytest.mark.asyncio
    async def test_default_size(self, context_args):
        html = await render_tree(_control().label("R"), context_args=context_args)
        assert_selector(html, "button.h-7")

    @pytest.mark.asyncio
    async def test_explicit_size_reaches_the_options(self, context_args):
        html = await render_tree(
            _control().label("R").size("lg"), context_args=context_args
        )
        assert_selector(html, "button.h-9", count=2)


class TestSegmentedOption:
    @pytest.mark.asyncio
    async def test_icon_only_option_takes_a_label(self, context_args):
        html = await render_tree(
            SegmentedControl()
            .label("View")
            .value("list")
            .content(SegmentedOption().value("list").label("List view").content("=")),
            context_args=context_args,
        )
        assert_attr(html, "button", "aria-label", "List view")

    @pytest.mark.asyncio
    async def test_option_with_visible_text_needs_no_label(self, context_args):
        html = await render_tree(
            _control().label("Range").value("day"), context_args=context_args
        )
        assert_no_selector(html, "button[aria-label]")

    @pytest.mark.asyncio
    async def test_icon_only_option_is_square_and_named(self, context_args):
        html = await render_tree(
            SegmentedControl()
            .label("View")
            .value("list")
            .content(SegmentedOption().value("list").icon_only("List view")),
            context_args=context_args,
        )
        assert_attr(html, "button", "aria-label", "List view")
        assert_selector(html, "button.w-7")
        # Square means no horizontal padding fighting the fixed width.
        assert_no_selector(html, "button.px-2\\.5")

    @pytest.mark.asyncio
    async def test_text_option_keeps_its_padding(self, context_args):
        html = await render_tree(
            _control().label("Range").value("day"), context_args=context_args
        )
        assert_selector(html, "button.px-2\\.5")
        assert_no_selector(html, "button.w-7")
