from __future__ import annotations

from dataclasses import dataclass

from htmy import Context
from typing_extensions import Self

from hue.headless import tabs as headless
from hue.headless.part import Part
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING_INSET, SEGMENTED_ITEM, SEGMENTED_TRACK
from hue.utils import classnames, render_if

# Scrolls rather than wraps on a narrow screen: a row of tabs folded onto
# a second line stops reading as one row of choices, and every tab stays a
# real link either way. Capped at its container's width, or a parent that
# does not stretch it (a Stack, say) lets it grow and scroll nothing.
_SCROLLS = "min-w-0 max-w-full overflow-x-auto"
_ROW = f"flex gap-1 border-b border-border {_SCROLLS}"
_ROW_SEGMENTED = f"{SEGMENTED_TRACK} {_SCROLLS}"

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

# A link with nowhere to go, which says so.
_UNREACHABLE = "cursor-not-allowed text-fg-disabled hover:bg-transparent"


@dataclass(frozen=True, slots=True)
class _Look:
    """
    How the row around a tab is drawn, which is all a tab needs from the
    styled Tabs rather than the headless root.
    """

    segmented: bool


class Tabs(headless.TabsRoot):
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

    def segmented(self, value: bool = True) -> Self:
        """
        Wear the segmented track instead of the rule: a row of places
        that sits inside something rather than heading it.
        """
        self._props["segmented"] = value
        return self

    def htmy_context(self) -> Context:
        return {_Look: _Look(self._get_prop("segmented", False))}

    def _render(self, context: Context) -> Component:
        segmented: bool = self._get_prop("segmented", False)
        return _dressed(
            headless.TabsRoot(), self, _ROW_SEGMENTED if segmented else _ROW
        )


class Tab(headless.Tab):
    """
    One tab: a link to one section, and a count or a state after its name.
    """

    def badge(self, value: ComponentType) -> Self:
        """
        A count or a state after the name, such as how many rows the
        section holds.
        """
        self._props["badge"] = value
        return self

    def _content(self) -> tuple[ComponentType, ...]:
        return (
            *self._children,
            render_if(self._get_prop("badge"), lambda badge: badge),
        )

    def _render(self, context: Context) -> Component:
        look = context.get(_Look)
        if not isinstance(look, _Look):
            raise ValueError(
                "A Tab only means something inside Tabs, which is what says "
                "how the row is drawn and which of them you are on."
            )
        segmented = look.segmented
        return _dressed(
            headless.Tab(),
            self,
            classnames(
                # A link, and never underlined: the rule under the tab you are
                # on is the mark, and a second one under the words is noise.
                "no-underline",
                SEGMENTED_ITEM if segmented else _TAB,
                _SEGMENTED_TAB if segmented else _UNDERLINE_TAB,
                # Picked rather than layered: the track already colours its own
                # items, and two colours on one element resolve by stylesheet
                # order rather than by intent.
                _UNREACHABLE if self.unreachable else "" if segmented else _IDLE,
                # Inset, because the scrolling row clips a ring drawn outside it.
                FOCUS_RING_INSET,
            ),
        )


def _dressed[P: Part](part: P, styled: P, look: str) -> P:
    """
    part, set up as styled is, wearing look before whatever class_() added.
    The look depends on a prop or the row around it, which a class-level
    default_class cannot.
    """
    part._props = {
        **styled._props,
        "class_": classnames(look, styled._get_prop("class_")),
    }
    part._attrs = styled._attrs
    return part.content(*styled._content())
