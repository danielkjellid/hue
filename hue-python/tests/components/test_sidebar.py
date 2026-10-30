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
    SidebarSection,
    SidebarSpacer,
)
from hue.ui.base import ChainableComponent
from tests._a11y import assert_attr, assert_no_selector, assert_selector, select


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
    async def test_the_body_is_a_named_navigation(self, context_args):
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_attr(html, "nav", "aria-label", "Main")
        assert_selector(html, "nav hr")
        html = await render_tree(
            SidebarBody().label("Settings"), context_args=context_args
        )
        assert_attr(html, "nav", "aria-label", "Settings")

    @pytest.mark.asyncio
    async def test_an_item_is_a_link_with_a_destination_and_a_button_without(
        self, context_args
    ):
        # Middle-click and "open in a new tab" work; a div with a router push
        # breaks both.
        html = await render_tree(_sidebar(), context_args=context_args)
        assert_selector(html, 'a[href="/events"]')
        html = await render_tree(
            Sidebar().content(SidebarItem().content("Search")),
            context_args=context_args,
        )
        assert_selector(html, "button[type=button]")
        assert_no_selector(html, "a")


class TestCurrentPage:
    """
    The sidebar offers the page it is on; an item marks itself against it.
    """

    @pytest.mark.parametrize(
        ("current", "marked"),
        [
            ("/events", ["/events"]),
            # The row you followed to get here should not go dark when you
            # arrive, and the root, which everything is under, lights only
            # on itself.
            ("/events/2050", ["/events"]),
            ("/", ["/"]),
            # Whether a URL ends in a slash is a routing convention.
            ("/events/", ["/events"]),
            ("/events-archive", []),
            (None, []),
        ],
    )
    @pytest.mark.asyncio
    async def test_an_item_marks_itself_against_the_page(
        self, context_args, current, marked
    ):
        html = await render_tree(_sidebar(current=current), context_args=context_args)
        assert [item["href"] for item in select(html, "[aria-current]")] == marked
        assert_no_selector(html, '[aria-current]:not([aria-current="page"])')

    @pytest.mark.asyncio
    async def test_a_row_with_rows_beneath_it_can_ask_for_its_own_path_only(
        self, context_args
    ):
        # Two rows marked as the page you are on is one too many.
        html = await render_tree(
            Sidebar()
            .current("/settings/billing")
            .content(
                SidebarBody().content(
                    SidebarSection().content(
                        SidebarItem().href("/settings").exact().content("Settings"),
                        SidebarItem().href("/settings/billing").content("Billing"),
                    )
                )
            ),
            context_args=context_args,
        )
        marked = select(html, "[aria-current=page]")
        assert len(marked) == 1
        assert marked[0]["href"] == "/settings/billing"

    @pytest.mark.asyncio
    async def test_items_built_while_rendering_are_marked_too(self, context_args):
        # Walking the children from above could not reach these: they do
        # not exist until the component holding them renders.
        class Workspace(ChainableComponent):
            category = None

            def _render(self, context):
                return SidebarSection().content(
                    SidebarItem().href("/").content("Home"),
                    SidebarItem().href("/events").content("Events"),
                )

        html = await render_tree(
            Sidebar().current("/events").content(SidebarBody().content(Workspace())),
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
