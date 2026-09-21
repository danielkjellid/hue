import pytest

from hue.renderer import render_tree
from hue.ui import Badge, Tab, Tabs
from hue.ui.base import ChainableComponent
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _tabs(current="/settings/account", **props):
    tabs = Tabs().label("Settings").current(current)
    for key, value in props.items():
        getattr(tabs, key)(value)
    return tabs.content(
        Tab().href("/settings/account").content("Account"),
        Tab().href("/settings/team").content("Team"),
    )


class TestTabs:
    @pytest.mark.asyncio
    async def test_it_is_a_named_nav_of_links(self, context_args):
        # Navigation rather than a widget: a tab goes somewhere, so it is
        # a link and the row around it is a nav.
        html = await render_tree(_tabs(), context_args=context_args)
        assert_selector(html, "nav > a", count=2)
        assert_attr(html, "nav", "aria-label", "Settings")
        assert_no_selector(html, '[role="tab"]')

    @pytest.mark.asyncio
    async def test_the_tab_that_leads_here_marks_itself(self, context_args):
        html = await render_tree(_tabs(), context_args=context_args)
        assert_selector(html, "[aria-current=page]", count=1)
        assert_attr(html, "[aria-current=page]", "href", "/settings/account")

    @pytest.mark.asyncio
    async def test_a_section_stays_marked_on_the_pages_inside_it(self, context_args):
        html = await render_tree(
            _tabs(current="/settings/team/erica"), context_args=context_args
        )
        assert_attr(html, "[aria-current=page]", "href", "/settings/team")

    @pytest.mark.asyncio
    async def test_a_tab_can_ask_for_its_own_path_only(self, context_args):
        html = await render_tree(
            Tabs()
            .current("/settings/team")
            .content(
                Tab().href("/settings").exact().content("Settings"),
                Tab().href("/settings/team").content("Team"),
            ),
            context_args=context_args,
        )
        assert_attr(html, "[aria-current=page]", "href", "/settings/team")

    @pytest.mark.asyncio
    async def test_a_tab_on_no_page_marks_nothing(self, context_args):
        html = await render_tree(
            Tabs().content(Tab().href("/settings").content("Settings")),
            context_args=context_args,
        )
        assert_no_selector(html, "[aria-current=page]")

    @pytest.mark.asyncio
    async def test_tabs_built_while_rendering_are_marked_too(self, context_args):
        # Nothing above them knows they exist, which is what the context
        # is for.
        class Sections(ChainableComponent):
            def _render(self, context):
                return (
                    Tab().href("/settings/account").content("Account"),
                    Tab().href("/settings/team").content("Team"),
                )

        html = await render_tree(
            Tabs().current("/settings/team").content(Sections()),
            context_args=context_args,
        )
        assert_attr(html, "[aria-current=page]", "href", "/settings/team")

    # target(): both branches
    @pytest.mark.asyncio
    async def test_a_target_turns_the_navigation_into_a_swap(self, context_args):
        html = await render_tree(_tabs(target="panel"), context_args=context_args)
        # push, so a section is still a place the back button knows.
        assert_attr(html, "nav a", "x-target.push", "panel")

    @pytest.mark.asyncio
    async def test_without_a_target_a_tab_is_just_a_link(self, context_args):
        html = await render_tree(_tabs(), context_args=context_args)
        assert_no_selector(html, "[x-target\\.push]")

    # variant(): both branches
    @pytest.mark.asyncio
    async def test_underline_draws_a_rule_under_the_tab_you_are_on(self, context_args):
        # And under that one only: an after: utility carries a content of
        # its own, so the bar needs turning off for the rest.
        html = await render_tree(_tabs(), context_args=context_args)
        assert_selector(html, "nav.border-b")
        assert_selector(html, "a[class*='after:bg-accent']")
        assert_selector(html, "a[class*='after:content-none']")

    @pytest.mark.asyncio
    async def test_segmented_wears_what_the_segmented_control_wears(self, context_args):
        html = await render_tree(_tabs(variant="segmented"), context_args=context_args)
        assert_selector(html, "nav.bg-surface-sunken")
        assert_selector(html, "a[class*='shadow-segment']")

    # disabled() and badge(): both branches each
    @pytest.mark.asyncio
    async def test_a_section_with_nothing_in_it_is_not_a_link(self, context_args):
        # A link that goes nowhere is one a keyboard still lands on.
        html = await render_tree(
            Tabs().content(
                Tab().href("/settings/account").content("Account"),
                Tab().href("/settings/gone").disabled().content("Gone"),
            ),
            context_args=context_args,
        )
        assert_selector(html, "nav > a", count=1)
        assert_attr(html, "span[aria-disabled]", "aria-disabled", "true")

    @pytest.mark.asyncio
    async def test_a_reachable_tab_says_nothing(self, context_args):
        html = await render_tree(_tabs(), context_args=context_args)
        assert_no_selector(html, "[aria-disabled]")

    @pytest.mark.asyncio
    async def test_a_tab_can_carry_a_badge(self, context_args):
        html = await render_tree(
            Tabs().content(
                Tab().href("/rows").badge(Badge().content("148")).content("Rows")
            ),
            context_args=context_args,
        )
        assert_selector(html, "nav a span")

    @pytest.mark.asyncio
    async def test_a_tab_without_a_badge_carries_nothing_extra(self, context_args):
        html = await render_tree(
            Tabs().content(Tab().href("/rows").content("Rows")),
            context_args=context_args,
        )
        assert_no_selector(html, "nav a span")

    @pytest.mark.asyncio
    async def test_a_tab_outside_a_row_says_so(self, context_args):
        # It has no row to belong to and nothing to tell it how it is
        # drawn, which is worth saying rather than rendering something
        # that looks like a tab and is not one.
        with pytest.raises(ValueError, match="inside Tabs"):
            await render_tree(
                Tab().href("/stray").content("Stray"), context_args=context_args
            )
