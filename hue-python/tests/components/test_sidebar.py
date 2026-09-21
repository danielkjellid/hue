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
from hue.ui.base import ChainableComponent
from tests._a11y import (
    assert_attr,
    assert_no_selector,
    assert_selector,
    select,
)


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
    async def test_the_icon_sits_half_a_step_down(self, context_args):
        # Where a glyph's optical centre sits against a line of text rather
        # than against the box around it.
        html = await render_tree(
            SidebarItem().href("/").icon("icon").content("Home"),
            context_args=context_args,
        )
        assert_selector(html, "span.mt-0\\.5")

    @pytest.mark.asyncio
    async def test_hovering_a_row_shows(self, context_args):
        # The sidebar's ground is canvas-subtle, which is the same colour as
        # surface-hover in light mode, so the hover has to be a step further.
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_selector(html, "a[class*='hover:bg-surface-active']")

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
        # The bar and nothing else: filling the row is what hover does, and
        # a row that looks hovered when the pointer is elsewhere says nothing.
        assert_selector(html, '[aria-current="page"] span.bg-accent')
        assert_no_selector(html, '[aria-current="page"].bg-surface-active')

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
        assert_no_selector(html, "span.bg-accent")

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


class TestCurrentPage:
    """
    The sidebar offers the page it is on; an item marks itself against it.
    """

    @pytest.mark.asyncio
    async def test_an_item_marks_itself_against_the_page(self, context_args):
        html = await render_tree(
            Sidebar()
            .current("/events")
            .content(
                SidebarBody().content(
                    SidebarSection().content(
                        SidebarItem().href("/").content("Home"),
                        SidebarItem().href("/events").content("Events"),
                    )
                )
            ),
            context_args=context_args,
        )
        marked = select(html, "[aria-current=page]")
        assert len(marked) == 1
        assert marked[0]["href"] == "/events"

    @pytest.mark.asyncio
    async def test_items_built_while_rendering_are_marked_too(self, context_args):
        # Walking the children from above could not reach these: they do
        # not exist until the component holding them renders.
        class Nav(ChainableComponent):
            category = None

            def _render(self, context):
                return SidebarSection().content(
                    SidebarItem().href("/").content("Home"),
                    SidebarItem().href("/events").content("Events"),
                )

        html = await render_tree(
            Sidebar().current("/events").content(SidebarBody().content(Nav())),
            context_args=context_args,
        )
        marked = select(html, "[aria-current=page]")
        assert len(marked) == 1
        assert marked[0]["href"] == "/events"

    @pytest.mark.asyncio
    async def test_an_item_can_still_say_so_itself(self, context_args):
        # For a row that stands for several paths, which no href matches.
        html = await render_tree(
            Sidebar()
            .current("/events/2048")
            .content(SidebarItem().href("/events").current().content("Events")),
            context_args=context_args,
        )
        assert_selector(html, "[aria-current=page]")

    @pytest.mark.asyncio
    async def test_a_sidebar_that_names_no_page_marks_nothing(self, context_args):
        html = await render_tree(
            Sidebar().content(SidebarItem().href("/events").content("Events")),
            context_args=context_args,
        )
        assert_no_selector(html, "[aria-current]")
