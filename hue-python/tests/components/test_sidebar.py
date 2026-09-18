import pytest

from hue.renderer import render_tree
from hue.ui import (
    Sidebar,
    SidebarBody,
    SidebarDivider,
    SidebarFooter,
    SidebarHeader,
    SidebarHeading,
    SidebarItem,
    SidebarLabel,
    SidebarSection,
    SidebarSpacer,
)
from tests._a11y import assert_attr, assert_no_selector, assert_selector


def _sidebar(*, current: str | None = "/events"):
    sidebar = Sidebar()
    if current is not None:
        sidebar.current(current)
    return sidebar.content(
        SidebarHeader().content("Northwind"),
        SidebarBody().content(
            SidebarSection().content(
                SidebarItem().href("/").content("Home"),
                SidebarItem().href("/events").content("Events"),
            ),
            SidebarDivider(),
            SidebarHeading().content("Upcoming"),
            SidebarSpacer(),
        ),
        SidebarFooter().content("Erica"),
    )


class TestSidebar:
    @pytest.mark.asyncio
    async def test_the_navigation_is_the_part_that_scrolls(self, context_args):
        # A header and a footer that stay, and one nav between them.
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_selector(html, "nav.overflow-y-auto")
        assert_attr(html, "nav", "aria-label", "Main")
        assert_selector(html, "div.border-b")
        assert_selector(html, "div.border-t")

    @pytest.mark.asyncio
    async def test_an_item_with_a_destination_is_a_real_link(self, context_args):
        # Middle-click and "open in a new tab" work; a div with a router push
        # breaks both.
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_selector(html, 'a[href="/events"]')

    @pytest.mark.asyncio
    async def test_an_item_without_one_is_a_button(self, context_args):
        html = await render_tree(
            Sidebar().content(SidebarItem().content("Search")),
            context_args=context_args,
        )
        assert_selector(html, "button[type=button]")
        assert_no_selector(html, "a")

    # current(): on the sidebar, on the item, and neither
    @pytest.mark.asyncio
    async def test_the_sidebar_marks_the_page_you_are_on(self, context_args):
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_attr(html, '[aria-current="page"]', "href", "/events")
        # Twice: a tint for the eye and a bar in the gutter for the glance.
        assert_selector(html, '[aria-current="page"].bg-accent-subtle')
        assert_selector(html, '[aria-current="page"] span[aria-hidden="true"]')

    @pytest.mark.asyncio
    async def test_an_item_can_say_so_itself(self, context_args):
        # For a row standing for several paths, where matching cannot tell.
        html = await render_tree(
            Sidebar().content(SidebarItem().href("/reports/2026").current()),
            context_args=context_args,
        )
        assert_selector(html, '[aria-current="page"]')

    @pytest.mark.asyncio
    async def test_nothing_is_marked_without_a_current_path(self, context_args):
        html = await render_tree(_sidebar(current=None), context_args=context_args)
        assert_no_selector(html, "[aria-current]")
        assert_no_selector(html, ".bg-accent-subtle")

    @pytest.mark.asyncio
    async def test_a_spacer_pushes_what_follows_to_the_bottom(self, context_args):
        # Which is how a section sits down there without being pinned.
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_selector(html, "div.flex-1.mt-8")

    @pytest.mark.asyncio
    async def test_a_divider_is_a_rule(self, context_args):
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_selector(html, "nav hr")

    @pytest.mark.asyncio
    async def test_a_label_leaves_room_for_what_sits_beside_it(self, context_args):
        html = await render_tree(
            SidebarItem()
            .href("/orders")
            .content(SidebarLabel().content("Orders"), "3"),
            context_args=context_args,
        )
        assert_selector(html, "a > span.truncate")
