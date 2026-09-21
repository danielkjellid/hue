from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING, SEGMENTED_ITEM, SEGMENTED_TRACK
from hue.ui.base import ChainableComponent
from hue.ui.navigation import CurrentPage
from hue.utils import classnames, render_if

type TabsVariant = Literal["underline", "segmented"]

_ROWS: dict[TabsVariant, str] = {
    # Scrolls rather than wraps on a narrow screen: a row of tabs folded
    # onto a second line stops reading as one row of choices, and every
    # tab stays a real link either way.
    "underline": "flex gap-1 overflow-x-auto border-b border-border",
    "segmented": f"{SEGMENTED_TRACK} overflow-x-auto",
}

# What an underline tab is, laid out. The segmented track says all of
# this for its own items already, so only one of the two is ever applied.
_TAB = "inline-flex items-center gap-1.5 whitespace-nowrap"

# The tab you are on is marked by a rule under it, drawn on the row's own
# border so the two line up rather than stack.
_UNDERLINE_TAB = (
    "relative rounded-t-sm px-[11px] pt-[9px] pb-[11px] "
    "font-ui text-base font-medium hover:bg-surface-hover "
    "aria-[current=page]:text-fg "
    # Tailwind gives any after: utility a content of its own, so the bar is
    # drawn under every tab unless this one says otherwise. Inside the tab
    # rather than a pixel below it: the row scrolls sideways, and a box
    # that scrolls on one axis scrolls on both - one pixel of overflow is
    # a scrollbar down the side of the row.
    "after:absolute after:inset-x-1.5 after:bottom-0 after:h-0.5 "
    "after:rounded-t-sm after:bg-accent "
    "after:content-none aria-[current=page]:after:content-['']"
)

_SEGMENTED_TAB = (
    "h-7 px-2.5 text-sm aria-[current=page]:bg-surface "
    "aria-[current=page]:text-fg aria-[current=page]:shadow-segment"
)

# The colour of a tab at rest, which the segmented track already sets for
# its own items - so it is said once here and once there, never twice on
# the same element.
_IDLE = "text-fg-muted hover:text-fg"

# Not a link, so there is nothing to disable - it is text that says so.
_UNREACHABLE = "cursor-not-allowed text-fg-disabled hover:bg-transparent"


@dataclass(frozen=True, slots=True)
class TabsState:
    """
    How the row is drawn and where a tab lands, offered to every tab in
    it. A tab reads it and draws itself, so it does not have to be a
    child of the row to belong to it.
    """

    variant: TabsVariant = "underline"
    target: str | None = None

    @classmethod
    def from_context(cls, context: Context) -> TabsState:
        found = context.get(cls)
        if isinstance(found, cls):
            return found
        raise ValueError(
            "A Tab only means something inside Tabs, which is what says "
            "how the row is drawn and which of them you are on."
        )


class Tabs(ChainableComponent):
    """
    A row of links to the sections of one thing, and which of them you
    are on.

    Navigation rather than a widget: a tab is a real link to a real URL,
    so it opens in a new tab, sends to somebody and answers the back
    button - and what it shows is whatever the page renders, rather than
    a panel the row has to carry around. current() is the path you are
    on, and the tab that leads there marks itself.

        Tabs().label("Settings").current(request.path).content(
            Tab().href("/settings/account").content("Account"),
        )
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .label("Settings")
            .current("/settings/team")
            .content(
                Tab().href("/settings/account").content("My Account"),
                Tab().href("/settings/team").content("Team Members"),
                Tab().href("/settings/billing").content("Billing"),
            )
        )

    def variant(self, value: TabsVariant) -> Self:
        self._props["variant"] = value
        return self

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
        self._props["label"] = value
        return self

    def target(self, value: str) -> Self:
        """
        The id a tab's section lands in. Given one, the browser fetches
        the section and swaps that element; without one it follows the
        link the long way round.
        """
        self._props["target"] = value
        return self

    def htmy_context(self) -> Context:
        return {
            CurrentPage: CurrentPage(self._get_prop("current")),
            TabsState: TabsState(
                self._get_prop("variant", "underline"), self._get_prop("target")
            ),
        }

    def _render(self, context: Context) -> Component:
        return html.nav(
            *self._children,
            aria_label=self._get_prop("label"),
            class_=classnames(
                _ROWS[self._get_prop("variant", "underline")],
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class Tab(ChainableComponent):
    """
    One tab: a link to one section, and a count or a state after its name.
    """

    category: ClassVar[str | None] = None

    def href(self, value: str) -> Self:
        self._props["href"] = value
        return self

    def badge(self, value: ComponentType) -> Self:
        """
        A count or a state after the name, such as how many rows the
        section holds.
        """
        self._props["badge"] = value
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

        Rendered as text rather than as a link, because a link that goes
        nowhere is one a keyboard still lands on and a screen reader
        still offers.
        """
        self._props["disabled"] = value
        return self

    def _render(self, context: Context) -> Component:
        state = TabsState.from_context(context)
        href: str | None = self._get_prop("href")
        unreachable: bool = self._get_prop("disabled", False) or href is None
        current: bool = self._get_prop(
            "current",
            CurrentPage.from_context(context).marks(
                href, exact=self._get_prop("exact", False)
            ),
        )
        segmented = state.variant == "segmented"
        classes = classnames(
            # A link, and never underlined: the rule under the tab you are
            # on is the mark, and a second one under the words is noise.
            "no-underline",
            SEGMENTED_ITEM if segmented else _TAB,
            _SEGMENTED_TAB if segmented else _UNDERLINE_TAB,
            # Picked rather than layered: the track already colours its own
            # items, and two colours on one element resolve by stylesheet
            # order rather than by intent.
            _UNREACHABLE if unreachable else "" if segmented else _IDLE,
            FOCUS_RING,
        )
        children = (
            *self._children,
            render_if(self._get_prop("badge"), lambda badge: badge),
        )

        if unreachable:
            return html.span(
                *children,
                aria_disabled="true",
                class_=classes,
                **self._get_base_html_attrs(),
            )

        return html.a(
            *children,
            href=href,
            aria_current="page" if current else None,
            class_=classes,
            **{
                # push, so a section is a place: the URL says which one and
                # the back button goes to the last.
                **({"x-target.push": state.target} if state.target else {}),
                **self._get_base_html_attrs(),
            },
        )
