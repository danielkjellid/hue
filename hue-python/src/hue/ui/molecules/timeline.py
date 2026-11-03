from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if, render_when

type TimelineStatus = Literal["complete", "current", "upcoming", "failed"]

# Each map keys None too, for a plain event: not a step, so no status.

# Read before the title, since the marker that shows the status is decoration.
# The current step says so through aria-current instead, and a plain event has
# nothing to say.
_SPOKEN: dict[TimelineStatus | None, str | None] = {
    None: None,
    "complete": "Complete",
    "current": None,
    "upcoming": "Not started",
    "failed": "Failed",
}

_MARKER: dict[TimelineStatus | None, str] = {
    None: "bg-canvas",
    "complete": "border-[1.5px] border-fg bg-fg text-canvas",
    "current": "border-2 border-accent bg-canvas",
    "upcoming": "border-[1.5px] border-border bg-canvas",
    "failed": "border-2 border-fg bg-canvas text-fg",
}

_GLYPH: dict[TimelineStatus | None, str | None] = {
    None: None,
    "complete": "check",
    "current": None,
    "upcoming": None,
    "failed": "x",
}

# The line under a marker belongs to that step, so solid means it finished,
# or was never a step to finish.
_CONNECTOR: dict[TimelineStatus | None, str] = {
    None: "border-solid border-border",
    "complete": "border-solid border-border-strong",
    "current": "border-dashed border-border",
    "upcoming": "border-dashed border-border",
    "failed": "border-dashed border-border-strong",
}

_TIME = "shrink-0 font-mono text-xs font-normal tabular-nums text-fg-muted"

# Wider and taller by its own negative margin, so the hover tint runs past
# the text without moving it. Only into the gap at the start: past the end it
# would overflow the list and scroll a panel sideways. No minimum height,
# which would centre the title lower than the marker beside it, and the
# padding alone clears 24px.
_TOGGLE = (
    "-my-1 -ms-2 flex w-[calc(100%+0.5rem)] cursor-pointer "
    "items-center gap-1.5 rounded-md border-none bg-transparent py-1 ps-2 "
    "text-start hover:bg-surface-hover active:bg-surface-active"
)

_CHEVRON = (
    "size-3.5 flex-none text-fg-muted transition-transform duration-150 "
    "motion-reduce:transition-none [[aria-expanded=true]>&]:rotate-90"
)


class Timeline(ChainableComponent):
    """
    An ordered list of events, each with a marker that shows its status.

    dense() shrinks the markers and type for a log or a side panel, and rail()
    moves each item's time into a column of its own at the start.
    """

    category = "Data"

    def dense(self, value: bool = True) -> Self:
        self._props["dense"] = value
        return self

    def rail(self, value: bool = True) -> Self:
        self._props["rail"] = value
        return self

    def _render(self, context: Context) -> Component:
        dense: bool = self._get_prop("dense", False)
        items = [c for c in self._children if isinstance(c, TimelineItem)]
        # A rail with no times in it would only be an empty column and its gap.
        rail = self._get_prop("rail", False) and any(
            item._get_prop("time") for item in items
        )
        # A toggle's chevron pushes its time inward, so every other row keeps
        # the same gap and the times stay in one column.
        gutter = any(item._get_prop("details") for item in items)
        # The last is told rather than read from :last-child, which a timeline
        # nested in the last item would match too.
        for item in items:
            last = item is items[-1]
            item._props.update(dense=dense, rail=rail, gutter=gutter, last=last)

        # The items are subgrids of this one, so every row shares the columns
        # and a rail is as wide as its longest time.
        return html.ol(
            *self._children,
            class_=classnames(
                "m-0 grid list-none p-0 *:col-span-full",
                "grid-cols-[max-content_auto_minmax(0,1fr)]"
                if rail
                else "grid-cols-[auto_minmax(0,1fr)]",
                "gap-x-2.5" if dense else "gap-x-3",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )


class TimelineItem(ChainableComponent):
    """
    One event: a title, an optional time, and what it says under them.

    details() makes the title a button that shows a list of facts about it.
    The layout comes from the Timeline it sits in, so render it inside one.
    """

    category = None

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def status(self, value: TimelineStatus) -> Self:
        """
        Make the item a step in a process. Without one it is a plain event,
        and a screen reader hears no status before its title.
        """
        self._props["status"] = value
        return self

    def time(self, value: str, datetime: str | None = None) -> Self:
        """
        The time as shown, and as ISO 8601 for the time element's datetime.
        """
        self._props["time"] = (value, datetime)
        return self

    def details(self, value: Mapping[str, ComponentType]) -> Self:
        self._props["details"] = value
        return self

    def _render(self, context: Context) -> Component:
        self._refuse_x_data()
        status: TimelineStatus | None = self._get_prop("status")
        dense: bool = self._get_prop("dense", False)
        rail: bool = self._get_prop("rail", False)
        last: bool = self._get_prop("last", False)
        # An empty mapping has nothing to show, so it gets no button either.
        details: Mapping[str, ComponentType] | None = self._get_prop("details") or None
        title: str = self._get_prop("title", "")
        if details and not title:
            raise ValueError(
                "A TimelineItem with details() needs a title(), which names the "
                "button that shows them."
            )
        when: tuple[str, str | None] | None = self._get_prop("time")

        time = render_if(
            when,
            lambda t: html.time(t[0], datetime=t[1], class_=_TIME),
        )
        spoken = _SPOKEN[status]
        head = html.span(
            html.span(
                render_if(spoken, lambda s: html.span(f"{s}: ", class_="sr-only")),
                title,
                class_=classnames(
                    "min-w-0",
                    "text-sm" if dense else "text-base",
                    "font-medium" if dense or status == "upcoming" else "font-semibold",
                    "text-fg-muted" if status == "upcoming" else "text-fg",
                ),
            ),
            render_when(not rail, time),
            # pe-5 is the chevron's size-3.5 plus the toggle's gap-1.5.
            class_=classnames(
                "flex flex-1 items-baseline justify-between gap-3",
                "pe-5"
                if self._get_prop("gutter", False) and not details and not rail
                else "",
            ),
        )

        body = html.div(
            self._toggle(head) if details else head,
            render_when(
                bool(self._children),
                html.div(*self._children, class_="mt-0.5 text-fg-muted"),
            ),
            render_if(details, self._panel),
            class_=classnames(
                "min-w-0",
                "" if last else "pb-2.5" if dense else "pb-5",
            ),
        )

        # The margins are optical: they set the marker level with the title's
        # first line, and leave a hair of space before the line below it.
        marker = html.span(
            self._glyph(status, dense),
            aria_hidden="true",
            class_=classnames(
                "grid flex-none place-items-center rounded-full",
                "mt-[5px] size-3" if dense else "mt-[3px] size-5",
                _MARKER[status],
            ),
        )
        connector = html.span(
            aria_hidden="true",
            class_=classnames(
                "mt-[3px] w-0 grow border-s",
                "hidden" if last else _CONNECTOR[status],
            ),
        )

        return html.li(
            render_when(
                rail,
                html.span(
                    time,
                    # The title's type size gives this the title's line box, so
                    # the time sits level with it.
                    class_=classnames("text-end", "text-sm" if dense else "text-base"),
                ),
            ),
            html.div(marker, connector, class_="flex flex-col items-center"),
            body,
            class_=classnames("grid grid-cols-subgrid", self._get_prop("class_")),
            aria_current="step" if status == "current" else None,
            **(
                {
                    "x-data": "{ hueDetailsOpen: false }",
                    "x-id": "['hue-timeline-details']",
                }
                if details
                else {}
            ),
            **self._get_base_html_attrs(),
        )

    def _glyph(self, status: TimelineStatus | None, dense: bool) -> ComponentType:
        if status is None or status == "current":
            return html.span(
                class_=classnames(
                    "size-[40%] rounded-full",
                    "bg-fg-muted" if status is None else "bg-accent",
                )
            )
        # A dense complete marker reads as filled without its check, but a
        # failed one keeps its cross, or only a shade would tell it from an
        # upcoming one.
        return render_if(
            None if dense and status == "complete" else _GLYPH[status],
            lambda glyph: HueIcon(glyph).class_("size-2" if dense else "size-3"),
        )

    def _toggle(self, head: ComponentType) -> ComponentType:
        return html.button(
            head,
            HueIcon("chevron-right").class_(_CHEVRON),
            type="button",
            class_=classnames(_TOGGLE, FOCUS_RING),
            **{
                ":aria-expanded": unsafe("hueDetailsOpen"),
                ":aria-controls": "$id('hue-timeline-details')",
                "x-on:click": unsafe("hueDetailsOpen = !hueDetailsOpen"),
            },
        )

    def _panel(self, details: Mapping[str, ComponentType]) -> ComponentType:
        return html.dl(
            *(
                part
                for term, value in details.items()
                for part in (
                    html.dt(term, class_="font-mono text-xs font-normal"),
                    html.dd(value, class_="m-0 text-fg max-sm:mb-1.5"),
                )
            ),
            class_=(
                "m-0 mt-2.5 grid gap-x-4 gap-y-1 rounded-md border border-border "
                "bg-canvas px-3.5 py-3 text-fg-muted sm:grid-cols-[auto_1fr]"
            ),
            **{
                ":id": "$id('hue-timeline-details')",
                "x-show": unsafe("hueDetailsOpen"),
                "x-cloak": True,
            },
        )
