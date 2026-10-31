import json

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

    @pytest.mark.asyncio
    async def test_marks_the_matching_option(self, context_args):
        html = await render_tree(
            _control().label("Range").value("week"), context_args=context_args
        )
        pressed = [b for b in select(html, "button") if b.get("aria-pressed") == "true"]
        assert len(pressed) == 1
        assert pressed[0].get_text(strip=True) == "Week"
        assert_selector(html, 'button[aria-pressed="false"]', count=1)

    @pytest.mark.asyncio
    async def test_without_a_value_selection_is_left_to_the_browser(self, context_args):
        # ThemeSwitcher binds aria-pressed with Alpine, because which theme is
        # on is only known client-side. A static value would fight it.
        html = await render_tree(_control().label("Range"), context_args=context_args)
        assert_no_selector(html, "button[aria-pressed]")
        assert_no_selector(html, "div[x-data]")
        assert_no_selector(html, "button[\\@click]")

    @pytest.mark.asyncio
    async def test_an_empty_value_still_gets_an_alpine_root(self, context_args):
        # An "All" option is commonly valued "", which is falsy but still a
        # value, so its click bindings need state to act on.
        html = await render_tree(
            SegmentedControl()
            .label("Status")
            .value("")
            .content(
                SegmentedOption().value("").content("All"),
                SegmentedOption().value("open").content("Open"),
            ),
            context_args=context_args,
        )
        assert_attr(html, 'div[role="group"]', "x-data", '{ selected: "" }')
        assert_selector(html, "button[\\@click]", count=2)

    @pytest.mark.asyncio
    async def test_values_are_quoted_as_json(self, context_args):
        # repr writes a Python literal, which only happens to read as
        # JavaScript; JSON is the quoting every expression in hue uses.
        value = 'it\'s "new"'
        html = await render_tree(
            SegmentedControl()
            .label("Status")
            .value(value)
            .content(SegmentedOption().value(value).content("New")),
            context_args=context_args,
        )
        quoted = json.dumps(value)
        assert_attr(html, 'div[role="group"]', "x-data", f"{{ selected: {quoted} }}")
        assert_attr(html, "button", "@click", f"selected = {quoted}")
        assert_attr(html, "button", ":aria-pressed", f"selected === {quoted}")


class TestSegmentedOption:
    @pytest.mark.asyncio
    async def test_icon_only_option_is_named(self, context_args):
        html = await render_tree(
            SegmentedControl()
            .label("View")
            .value("list")
            .content(
                SegmentedOption().value("list").label("List view").content("="),
                SegmentedOption().value("grid").icon_only("Grid view"),
            ),
            context_args=context_args,
        )
        names = [b["aria-label"] for b in select(html, "button")]
        assert names == ["List view", "Grid view"]
