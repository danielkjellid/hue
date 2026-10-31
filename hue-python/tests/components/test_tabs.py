import pytest

from hue import html as hue_html
from hue.renderer import render_tree
from hue.ui import Tab, Tabs
from hue.ui.base import ChainableComponent
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


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

    @pytest.mark.parametrize(
        ("current", "first", "marked"),
        [
            ("/settings/team", Tab().href("/settings/account"), "/settings/team"),
            # A section stays marked on the pages inside it.
            ("/settings/team/erica", Tab().href("/settings/account"), "/settings/team"),
            # Unless the tab asks for its own path only.
            ("/settings/team", Tab().href("/settings").exact(), "/settings/team"),
            (None, Tab().href("/settings/account"), None),
        ],
        ids=["here", "inside", "exact", "nowhere"],
    )
    @pytest.mark.asyncio
    async def test_the_tab_that_leads_here_marks_itself(
        self, context_args, current, first, marked
    ):
        tabs = Tabs() if current is None else Tabs().current(current)
        html = await render_tree(
            tabs.content(
                first.content("First"), Tab().href("/settings/team").content("Team")
            ),
            context_args=context_args,
        )
        if marked is None:
            assert_no_selector(html, "[aria-current]")
        else:
            assert_selector(html, "[aria-current=page]", count=1)
            assert_attr(html, "[aria-current=page]", "href", marked)

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

    @pytest.mark.asyncio
    async def test_a_target_turns_the_navigation_into_a_swap(self, context_args):
        html = await render_tree(
            _tabs(target="panel", id="settings-tabs"), context_args=context_args
        )
        # push, so a section is still a place the back button knows. The
        # tab you are on replaces, so following it again adds no entry.
        assert_attr(html, 'nav a[href="/settings/team"]', "x-target.push", "panel")
        assert_attr(html, "nav a[aria-current]", "x-target.replace", "panel")
        assert_no_selector(html, "nav a[aria-current][x-target\\.push]")
        # The row sits outside the panel and refreshes itself from the
        # response, so the mark moves to the tab you land on.
        assert_attr(html, "nav#settings-tabs", "x-sync")

    @pytest.mark.asyncio
    async def test_a_focused_tab_scrolls_fully_into_the_row(self, context_args):
        # The row scrolls sideways, and Chrome leaves a half-hidden tab
        # half hidden when it takes focus.
        html = await render_tree(_tabs(), context_args=context_args)
        assert "scrollIntoView" in select(html, "nav")[0]["x-on:focusin"]

    @pytest.mark.asyncio
    async def test_each_tab_takes_an_id_from_the_row(self, context_args):
        # A swap replaces the row, and the id is how focus finds the tab it
        # was on. Two rows on one page keep theirs apart.
        html = await render_tree(
            hue_html.div(
                _tabs(target="panel", id="one"),
                _tabs(target="panel", id="two"),
                Tabs().id("three").content(Tab().href("/x").id("mine")),
            ),
            context_args=context_args,
        )
        ids = [a["id"] for a in select(html, "nav a")]
        assert ids == ["one-tab-0", "one-tab-1", "two-tab-0", "two-tab-1", "mine"]

    @pytest.mark.asyncio
    async def test_a_target_without_an_id_of_its_own_is_refused(self, context_args):
        with pytest.raises(ValueError, match="id"):
            await render_tree(_tabs(target="panel"), context_args=context_args)

    @pytest.mark.asyncio
    async def test_a_section_with_nothing_in_it_is_not_a_link(self, context_args):
        # No href, so the keyboard skips it; the role is what lets a screen
        # reader announce aria-disabled at all, which it ignores on a span.
        html = await render_tree(
            Tabs().content(
                Tab().href("/settings/account").content("Account"),
                Tab().href("/settings/gone").disabled().content("Gone"),
            ),
            context_args=context_args,
        )
        assert_selector(html, "nav > a[href]", count=1)
        assert_attr(html, 'a[role="link"]:not([href])', "aria-disabled", "true")

    @pytest.mark.asyncio
    async def test_a_tab_outside_a_row_says_so(self, context_args):
        # It has no row to belong to and nothing to tell it how it is
        # drawn, which is worth saying rather than rendering something
        # that looks like a tab and is not one.
        with pytest.raises(ValueError, match="inside Tabs"):
            await render_tree(
                Tab().href("/stray").content("Stray"), context_args=context_args
            )
