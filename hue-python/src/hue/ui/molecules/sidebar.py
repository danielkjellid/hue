from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if, render_when

_LINK = (
    "flex items-center gap-2 rounded-md px-2 py-[7px] font-ui text-base "
    "font-medium no-underline cursor-pointer "
    "[&_svg]:size-4 [&_svg]:flex-none"
)

# The accent is spent here and nowhere else in the sidebar: this is the one
# place in an app where "where am I" has to be answerable at a glance.
_CURRENT = "bg-accent-subtle text-accent-text [&_svg]:text-accent-text"

_IDLE = (
    "text-fg-muted [&_svg]:text-fg-subtle "
    "hover:bg-surface-active hover:text-fg [&:hover_svg]:text-fg-muted"
)


class Sidebar(ChainableComponent):
    """
    The app's own navigation, down the side.

    current() is the path of the page you are on, which is what marks one
    link as where you are. brand() names the app at the top and footer()
    holds whatever belongs at the bottom, usually the account.

        Sidebar().brand("Northwind").current("/billing").content(...)
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .brand("Northwind")
            .current("/billing")
            .content(
                SidebarGroup()
                .label("Workspace")
                .content(
                    SidebarLink().href("/").content("Overview"),
                    SidebarLink().href("/billing").count(3).content("Billing"),
                )
            )
        )

    def brand(self, value: str) -> Self:
        self._props["brand"] = value
        return self

    def current(self, value: str) -> Self:
        """
        The path of the page you are on. A link whose href matches it is
        marked as the current page.
        """
        self._props["current"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What this navigation is, for a page with more than one. "Main" by
        default, which is what a screen reader reads before the links.
        """
        self._props["label"] = value
        return self

    def footer(self, *values: ComponentType) -> Self:
        self._props["footer"] = values
        return self

    def _render(self, context: HueContext) -> Component:
        current: str | None = self._get_prop("current")
        footer: tuple[ComponentType, ...] = self._get_prop("footer", ())

        for child in self._children:
            if isinstance(child, SidebarGroup):
                child._mark(current)
            elif isinstance(child, SidebarLink):
                child._mark(current)

        return html.nav(
            render_if(self._get_prop("brand"), _brand),
            html.div(
                *self._children,
                class_="flex-1 overflow-y-auto px-2 pt-2 pb-4 [&>*+*]:mt-5",
            ),
            render_when(
                bool(footer),
                html.div(*footer, class_="flex-none border-t border-border p-2"),
            ),
            aria_label=self._get_prop("label", "Main"),
            class_=classnames(
                "flex w-61 flex-none flex-col border-e border-border bg-canvas-subtle",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class SidebarGroup(ChainableComponent):
    """
    A run of links under a heading.
    """

    category = None

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def _mark(self, current: str | None) -> None:
        for child in self._children:
            if isinstance(child, SidebarLink):
                child._mark(current)

    def _render(self, context: HueContext) -> Component:
        return html.div(
            render_if(
                self._get_prop("label"),
                lambda text: html.div(
                    text,
                    class_="px-2 pb-1.5 font-ui text-2xs font-bold uppercase "
                    "tracking-[0.05em] text-fg-subtle",
                ),
            ),
            *self._children,
            class_=self._get_prop("class_"),
            **self._get_base_html_attrs(),
        )


class SidebarLink(ChainableComponent):
    """
    One destination.

    A real link, so middle-click and "open in a new tab" work - a div with a
    router push breaks both.
    """

    category = None

    def href(self, value: str) -> Self:
        self._props["href"] = value
        return self

    def icon(self, value: ComponentType) -> Self:
        self._props["icon"] = value
        return self

    def count(self, value: int) -> Self:
        """
        A number at the end of the row, such as how many are waiting.
        """
        self._props["count"] = value
        return self

    def _mark(self, current: str | None) -> None:
        if current is not None and self._get_prop("href") == current:
            self._props["current"] = True

    def _render(self, context: HueContext) -> Component:
        current: bool = self._get_prop("current", False)

        return html.a(
            render_if(self._get_prop("icon"), lambda icon: icon),
            *self._children,
            render_if(
                self._get_prop("count"),
                lambda count: html.span(
                    str(count),
                    class_="ms-auto text-xs tabular-nums text-fg-subtle",
                ),
            ),
            href=self._get_prop("href", "#"),
            aria_current="page" if current else None,
            class_=classnames(
                _LINK,
                _CURRENT if current else _IDLE,
                FOCUS_RING,
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


def _brand(name: str) -> ComponentType:
    """
    The app's name, with its initial in a tile - the one other place the
    accent is allowed, since it is not navigation.
    """
    return html.div(
        html.span(
            name[:1].upper(),
            aria_hidden="true",
            class_="grid size-6.5 place-content-center rounded-sm bg-accent "
            "font-ui text-sm font-bold text-accent-fg",
        ),
        html.span(
            name,
            class_="font-ui text-md font-bold tracking-[-0.015em]",
        ),
        class_="flex h-14 flex-none items-center gap-2 px-4",
    )
