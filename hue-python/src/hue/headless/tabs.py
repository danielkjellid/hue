"""
A row of tabs as parts: navigation, where each tab is a link to a section.

    TabsRoot().label("Settings").current(request.path).content(
        Tab().href("/settings/account").content("Account"),
        Tab().href("/settings/team").content("Team"),
    )

The root is the nav. It offers the page you are on and the region a tab
swaps, so a tab marks itself and swaps the right region wherever it is built.
"""

from __future__ import annotations

from dataclasses import dataclass

from htmy import Context, html
from typing_extensions import Self

from hue.headless.part import Part
from hue.navigation import CurrentPage, SwapsTarget, swap
from hue.types.core import Component


@dataclass(frozen=True, slots=True)
class TabsState:
    """
    Where a tab in this row lands: the id of the region it swaps, if any.
    """

    target: str | None = None


class TabsRoot(SwapsTarget, Part):
    """
    The nav around a row of tabs, the page you are on, and the region its
    tabs swap.
    """

    def current(self, value: str) -> Self:
        """
        The path of the page you are on, set once rather than per tab.

        A tab is marked by its own href: the one that matches, and the
        one that leads to the section this page is inside. Tab.exact()
        opts a tab out of that.
        """
        self._props["current"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What the row of tabs is for, which is what a screen reader reads
        before the tabs themselves.
        """
        self._attrs["aria_label"] = value
        return self

    def htmy_context(self) -> Context:
        return {
            CurrentPage: CurrentPage(self._get_prop("current")),
            TabsState: TabsState(self._get_prop("target")),
        }

    def _render(self, context: Context) -> Component:
        own_id: str | None = self._attrs.get("id")
        if own_id is not None:
            # A swap replaces every tab, and the id is how focus finds the
            # new one. By position, since an href can be anything.
            for index, child in enumerate(self._children):
                if isinstance(child, Tab):
                    child._attrs.setdefault("id", f"{own_id}-tab-{index}")
        return html.nav(
            *self._content(),
            **self._wired(
                **{
                    # Chrome scrolls a focused tab in only once it is wholly
                    # out of view, so one cut off at the edge stays cut off.
                    "x-on:focusin": "$event.target.scrollIntoView("
                    "{ inline: 'nearest', block: 'nearest' })",
                    **self._sync_attrs(),
                }
            ),
        )


class Tab(Part):
    """
    One tab: a link to one section, marked aria-current when it leads to
    the page you are on.
    """

    def href(self, value: str) -> Self:
        self._props["href"] = value
        return self

    def current(self, value: bool = True) -> Self:
        """
        Mark this as the page you are on, where the row's own current()
        cannot tell - a tab that stands for a path of its own, say.
        """
        self._props["current"] = value
        return self

    def exact(self, value: bool = True) -> Self:
        """
        Mark this only on its own path, not on the pages under it.
        """
        self._props["exact"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        """
        A section there is nothing in yet.

        Rendered as a link with no href, which the Tab key skips. It keeps
        the link role and aria-disabled, so a screen reader still reads it
        as a link that is unavailable. On a span, aria-disabled is never
        read out.
        """
        self._props["disabled"] = value
        return self

    @property
    def unreachable(self) -> bool:
        """
        Whether the tab leads nowhere: disabled, or given no href.
        """
        return self._get_prop("disabled", False) or self._get_prop("href") is None

    def _render(self, context: Context) -> Component:
        state = self._state(context, TabsState)
        if self.unreachable:
            return html.a(
                *self._content(), **self._wired(role="link", aria_disabled="true")
            )
        href: str = self._get_prop("href")
        current: bool = self._get_prop(
            "current",
            CurrentPage.from_context(context).marks(
                href, exact=self._get_prop("exact", False)
            ),
        )
        return html.a(
            *self._content(),
            **self._wired(
                href=href,
                aria_current="page" if current else None,
                **swap(state.target, current=current),
            ),
        )
