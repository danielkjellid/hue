from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING, SEGMENTED_ITEM, SEGMENTED_TRACK
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type TabsVariant = Literal["underline", "segmented"]

_LISTS: dict[TabsVariant, str] = {
    "underline": "flex gap-1 border-b border-border",
    "segmented": SEGMENTED_TRACK,
}

# The selected tab is marked by a rule under it, drawn on the list's own
# border so the two line up rather than stack.
_UNDERLINE_TAB = (
    "relative cursor-pointer rounded-t-sm border-none bg-transparent "
    "px-[11px] pt-[9px] pb-[11px] font-ui text-base font-medium text-fg-muted "
    "hover:bg-surface-hover hover:text-fg aria-selected:text-fg "
    # Tailwind gives any after: utility a content of its own, so the bar is
    # drawn under every tab unless this one says otherwise.
    "after:absolute after:inset-x-1.5 after:-bottom-px after:h-0.5 "
    "after:rounded-t-sm after:bg-accent "
    "after:content-none aria-selected:after:content-['']"
)

_SEGMENTED_TAB = (
    "h-7 px-2.5 text-sm aria-selected:bg-surface aria-selected:text-fg "
    "aria-selected:shadow-segment"
)

_DISABLED = (
    "disabled:cursor-not-allowed disabled:text-fg-disabled "
    "disabled:hover:bg-transparent disabled:hover:text-fg-disabled"
)


class Tabs(ChainableComponent):
    """
    One panel at a time, with a row of tabs to pick it.

    value() is the tab that starts selected. The arrow keys move along the
    row and the panel follows, which is what the tab role promises; Tab
    itself carries its label and its panel.

        Tabs().value("overview").content(Tab().value("overview").label("Overview"))
    """

    category = "Navigation"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .value("overview")
            .content(
                Tab().value("overview").label("Overview").content("What happened."),
                Tab().value("activity").label("Activity").content("Who did what."),
            )
        )

    def variant(self, value: TabsVariant) -> Self:
        self._props["variant"] = value
        return self

    def value(self, value: str) -> Self:
        """
        Which tab starts selected. The first one, unset.
        """
        self._props["value"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What the row of tabs is for, which is what a screen reader reads
        before the tabs themselves.
        """
        self._props["label"] = value
        return self

    def _render(self, context: Context) -> Component:
        variant: TabsVariant = self._get_prop("variant", "underline")
        tabs = [child for child in self._children if isinstance(child, Tab)]
        selected: str = self._get_prop("value") or (
            tabs[0]._get_prop("value", "") if tabs else ""
        )

        for tab in tabs:
            tab._props["variant"] = variant

        return html.div(
            html.div(
                *(tab._trigger() for tab in tabs),
                role="tablist",
                aria_label=self._get_prop("label"),
                class_=_LISTS[variant],
                **{
                    # Arrows walk the row and the panel follows the focus,
                    # which is the automatic activation the role implies.
                    "x-on:keydown.right.prevent": "$focus.wrap().next()",
                    "x-on:keydown.left.prevent": "$focus.wrap().previous()",
                    "x-on:keydown.home.prevent": "$focus.first()",
                    "x-on:keydown.end.prevent": "$focus.last()",
                },
            ),
            *(tab._panel() for tab in tabs),
            # w-full, or the rule under the row is as wide as the widest
            # panel and moves every time the panel does.
            class_=classnames("w-full", self._get_prop("class_")),
            **{
                "x-data": f"{{ selected: {selected!r} }}",
                "x-id": "['hue-tab', 'hue-tabpanel']",
                **self._get_base_html_attrs(),
            },
        )


class Tab(ChainableComponent):
    """
    One tab and the panel it shows. Children are the panel.
    """

    category = None

    def value(self, value: str) -> Self:
        self._props["value"] = value
        return self

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def badge(self, value: ComponentType) -> Self:
        """
        A count or a state after the label, such as how many rows the panel
        holds.
        """
        self._props["badge"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def _trigger(self) -> ComponentType:
        value: str = self._get_prop("value", "")
        variant: TabsVariant = self._get_prop("variant", "underline")
        chosen = unsafe(f"selected === {value!r}")

        return html.button(
            render_if(self._get_prop("label"), lambda text: text),
            render_if(self._get_prop("badge"), lambda badge: badge),
            type="button",
            role="tab",
            disabled=self._get_prop("disabled", False) or None,
            class_=classnames(
                SEGMENTED_ITEM if variant == "segmented" else "",
                _SEGMENTED_TAB if variant == "segmented" else _UNDERLINE_TAB,
                _DISABLED,
                FOCUS_RING,
            ),
            **{
                ":id": f"$id('hue-tab', {value!r})",
                ":aria-controls": f"$id('hue-tabpanel', {value!r})",
                ":aria-selected": chosen,
                # Roving: only the selected tab is a tab stop, so Tab moves
                # past the row rather than through it.
                ":tabindex": f"{chosen} ? 0 : -1",
                "x-on:click": unsafe(f"selected = {value!r}"),
                # Selection follows focus, so the arrows show as they go.
                "x-on:focus": unsafe(f"selected = {value!r}"),
            },
        )

    def _panel(self) -> ComponentType:
        value: str = self._get_prop("value", "")
        return html.div(
            *self._children,
            role="tabpanel",
            # Focusable, because a panel of text has nothing else to land on.
            tabindex="0",
            class_="pt-5",
            **{
                ":id": f"$id('hue-tabpanel', {value!r})",
                ":aria-labelledby": f"$id('hue-tab', {value!r})",
                "x-show": unsafe(f"selected === {value!r}"),
                "x-cloak": True,
            },
        )

    def _render(self, context: Context) -> Component:
        # Tabs takes a Tab apart and renders the trigger and the panel in
        # their own places. One on its own has no row to belong to and no
        # scope to ask whether it is selected, so it is just its content.
        return html.div(*self._children, class_=self._get_prop("class_"))
