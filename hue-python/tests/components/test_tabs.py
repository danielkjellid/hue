import pytest

from hue.renderer import render_tree
from hue.ui import Badge, Tab, TabList, TabPanel, Tabs
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _tabs(**props):
    tabs = Tabs()
    for key, value in props.items():
        getattr(tabs, key)(value)
    return tabs.content(
        TabList().content(
            Tab().value("overview").label("Overview"),
            Tab().value("activity").label("Activity"),
        ),
        TabPanel().value("overview").content("What happened"),
        TabPanel().value("activity").content("Who did what"),
    )


class TestTabs:
    @pytest.mark.asyncio
    async def test_it_is_a_tablist_of_tabs_and_panels(self, context_args):
        html = await render_tree(_tabs(), context_args=context_args)
        assert_selector(html, '[role="tablist"] > button[role="tab"]', count=2)
        assert_selector(html, '[role="tabpanel"]', count=2)

    @pytest.mark.asyncio
    async def test_each_tab_names_its_panel_and_the_panel_names_it_back(
        self, context_args
    ):
        html = await render_tree(_tabs(), context_args=context_args)
        assert_attr(html, "button", ":aria-controls", "$id('hue-tabpanel', 'overview')")
        assert_attr(
            html, '[role="tabpanel"]', ":aria-labelledby", "$id('hue-tab', 'overview')"
        )

    @pytest.mark.asyncio
    async def test_only_the_selected_tab_is_a_tab_stop(self, context_args):
        # Roving, so Tab moves past the row rather than through it.
        html = await render_tree(_tabs(), context_args=context_args)
        assert_attr(html, "button", ":tabindex", "selected === 'overview' ? 0 : -1")

    @pytest.mark.asyncio
    async def test_the_arrows_walk_the_row_and_the_panel_follows(self, context_args):
        html = await render_tree(_tabs(), context_args=context_args)
        assert_attr(
            html,
            '[role="tablist"]',
            "x-on:keydown.right.prevent",
            "$focus.wrap().next()",
        )
        assert_attr(html, "button", "x-on:focus", "selected = 'overview'")

    @pytest.mark.asyncio
    async def test_the_panel_can_be_reached(self, context_args):
        # A panel of text has nothing else to land on.
        html = await render_tree(_tabs(), context_args=context_args)
        assert_attr(html, '[role="tabpanel"]', "tabindex", "0")

    @pytest.mark.asyncio
    async def test_it_is_as_wide_as_its_column(self, context_args):
        # Or the rule under the row follows whichever panel is showing.
        html = await render_tree(_tabs(), context_args=context_args)
        assert_selector(html, 'div.w-full > [role="tablist"]')

    # value(): given, and falling back to the first tab
    @pytest.mark.asyncio
    async def test_the_named_tab_starts_selected(self, context_args):
        html = await render_tree(_tabs(value="activity"), context_args=context_args)
        assert "selected: 'activity'" in str(html)

    @pytest.mark.asyncio
    async def test_the_first_tab_claims_the_selection_if_nothing_else_has(
        self, context_args
    ):
        # The row cannot see its own tabs any more, so the first one to
        # initialise takes it - which is the first one in the document.
        html = await render_tree(_tabs(), context_args=context_args)
        assert "selected: ''" in str(html)
        assert_attr(html, "button", "x-init", "selected = selected || 'overview'")

    # variant(): both branches
    @pytest.mark.asyncio
    async def test_underline_draws_a_rule_under_the_selected_tab(self, context_args):
        # And under that one only: an after: utility carries a content of its
        # own, so the bar needs turning off for the rest.
        html = await render_tree(_tabs(), context_args=context_args)
        assert_selector(html, '[role="tablist"].border-b')
        assert_selector(html, "button[class*='after:bg-accent']")
        assert_selector(html, "button[class*='after:content-none']")

    @pytest.mark.asyncio
    async def test_segmented_wears_what_the_segmented_control_wears(self, context_args):
        html = await render_tree(_tabs(variant="segmented"), context_args=context_args)
        assert_selector(html, '[role="tablist"].bg-surface-sunken')
        assert_selector(html, "button[class*='aria-selected:shadow-segment']")

    # disabled() and badge(): both branches each
    @pytest.mark.asyncio
    async def test_a_disabled_tab_cannot_be_reached(self, context_args):
        html = await render_tree(
            Tabs().content(
                Tab().value("overview").label("Overview").content("One"),
                Tab().value("gone").label("Gone").disabled().content("Two"),
            ),
            context_args=context_args,
        )
        assert_selector(html, "button[disabled]", count=1)

    @pytest.mark.asyncio
    async def test_an_enabled_tab_says_nothing(self, context_args):
        html = await render_tree(_tabs(), context_args=context_args)
        assert_no_selector(html, "button[disabled]")

    @pytest.mark.asyncio
    async def test_a_tab_can_carry_a_badge(self, context_args):
        html = await render_tree(
            Tabs().content(
                Tab()
                .value("rows")
                .label("Rows")
                .badge(Badge().content("148"))
                .content("Table")
            ),
            context_args=context_args,
        )
        assert_selector(html, 'button[role="tab"] span')

    @pytest.mark.asyncio
    async def test_a_tab_outside_a_row_says_so(self, context_args):
        # It has no row to belong to and no scope to ask whether it is
        # showing, which is worth saying rather than rendering something
        # inert that looks like a tab.
        with pytest.raises(ValueError, match="inside Tabs"):
            await render_tree(
                Tab().value("stray").label("Stray"), context_args=context_args
            )
