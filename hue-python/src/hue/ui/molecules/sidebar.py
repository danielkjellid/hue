from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.base import ChainableComponent, Clickable
from hue.utils import classnames, render_if, render_when

_ITEM = (
    "relative flex w-full items-center gap-3 rounded-lg px-2 py-2.5 "
    "text-start font-ui text-base font-medium no-underline cursor-pointer "
    "[&_svg]:size-4 [&_svg]:flex-none"
)

_IDLE = (
    "text-fg-muted [&_svg]:text-fg-subtle "
    "hover:bg-surface-hover hover:text-fg [&:hover_svg]:text-fg-muted"
)

# The page you are on, marked twice: a tint for the eye and a bar in the
# gutter for the glance. The accent is spent here and nowhere else in the
# sidebar, so "where am I" survives a squint.
_CURRENT = "bg-accent-subtle text-accent-text [&_svg]:text-accent-text"


class Sidebar(ChainableComponent):
    """
    The app's navigation, down the side, in three parts.

    A header that stays, a body that scrolls, a footer that stays - built
    from SidebarSection, SidebarHeading, SidebarDivider and SidebarSpacer,
    which is what lets a section sit at the bottom without being pinned
    there. current() marks the link whose href matches the page you are on.
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .current("/events")
            .content(
                SidebarBody().content(
                    SidebarSection().content(
                        SidebarItem().href("/").content("Home"),
                        SidebarItem().href("/events").content("Events"),
                    )
                )
            )
        )

    def current(self, value: str) -> Self:
        """
        The path of the page you are on. The item whose href matches it is
        marked, so a consumer sets this once rather than per item.
        """
        self._props["current"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What this navigation is, for a page with more than one. "Main" by
        default, which a screen reader reads before the links.
        """
        self._props["label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        current: str | None = self._get_prop("current")
        for child in self._children:
            if isinstance(child, ChainableComponent):
                _mark(child, current)

        return html.div(
            *self._children,
            class_=classnames(
                "flex h-full min-h-0 w-64 flex-none flex-col",
                "border-e border-border bg-canvas-subtle",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class SidebarHeader(ChainableComponent):
    """
    What sits above the navigation and stays there: the workspace, a search.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "flex flex-none flex-col gap-2 border-b border-border p-4",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class SidebarBody(ChainableComponent):
    """
    The navigation itself, and the only part that scrolls.
    """

    category = None

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        return html.nav(
            *self._children,
            aria_label=self._get_prop("label", "Main"),
            class_=classnames(
                "flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-4",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class SidebarFooter(ChainableComponent):
    """
    What sits below the navigation and stays there, usually the account.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "flex flex-none flex-col border-t border-border p-4",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class SidebarSection(ChainableComponent):
    """
    A run of items that belong together.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames("flex flex-col gap-0.5", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


class SidebarHeading(ChainableComponent):
    """
    What a section is called.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.div(
            *self._children,
            class_=classnames(
                "mb-1 px-2 font-ui text-2xs font-bold uppercase "
                "tracking-[0.05em] text-fg-subtle",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class SidebarDivider(ChainableComponent):
    """
    A rule between two runs of navigation.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.hr(
            class_=classnames("my-4 h-px border-0 bg-border", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


class SidebarSpacer(ChainableComponent):
    """
    Everything after this goes to the bottom.

    Which is how a section sits down there without being pinned: it is still
    in the scroll, just pushed as far as the room allows.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.div(
            class_=classnames("mt-8 flex-1", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


class SidebarItem(Clickable):
    """
    One destination, or one action.

    With href it is a real link, so middle-click and "open in a new tab"
    work - a div with a router push breaks both. Without one it is a button,
    for the rows that open something instead of going somewhere.
    """

    category = None

    def href(self, value: str) -> Self:
        self._props["href"] = value
        return self

    def icon(self, value: ComponentType) -> Self:
        self._props["icon"] = value
        return self

    def current(self, value: bool = True) -> Self:
        """
        Mark this as the page you are on, where the sidebar's own current()
        cannot tell - a row that stands for several paths, say.
        """
        self._props["current"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        current: bool = self._get_prop("current", False)
        href: str | None = self._get_prop("href")

        children = (
            render_when(current, _indicator()),
            render_if(self._get_prop("icon"), lambda icon: icon),
            *self._children,
        )
        classes = classnames(
            _ITEM,
            _CURRENT if current else _IDLE,
            FOCUS_RING,
            self._get_prop("class_"),
        )
        attrs = {
            "aria_current": "page" if current and href is not None else None,
            **self._get_base_html_attrs(),
        }

        if href is None:
            return html.button(*children, type="button", class_=classes, **attrs)
        return html.a(*children, href=href, class_=classes, **attrs)


class SidebarLabel(ChainableComponent):
    """
    An item's text, where something else has to sit beside it - a count, a
    chevron - and needs the row's spare width to push against.
    """

    category = None

    def _render(self, context: HueContext) -> Component:
        return html.span(
            *self._children,
            class_=classnames("truncate", self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )


def _indicator() -> ComponentType:
    """
    The bar in the gutter beside the current item. A real element rather than
    a pseudo, so nothing depends on a content quirk to be visible.
    """
    return html.span(
        aria_hidden="true",
        class_="absolute inset-y-2 -start-2 w-0.5 rounded-full bg-accent",
    )


def _mark(component: ChainableComponent, current: str | None) -> None:
    """
    Walk the tree marking the item whose href is the page you are on.
    """
    if current is None:
        return
    if isinstance(component, SidebarItem):
        if component._get_prop("href") == current:
            component._props["current"] = True
        return
    for child in component._children:
        if isinstance(child, ChainableComponent):
            _mark(child, current)
