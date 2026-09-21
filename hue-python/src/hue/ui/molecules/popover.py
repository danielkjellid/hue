from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import Component
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if, render_when

type PopoverPlacement = Literal["bottom-start", "bottom-end", "top-start", "top-end"]

# 6px off the trigger: far enough that the panel reads as its own surface,
# near enough that the pointer crosses the gap without leaving the pair.
_OFFSET = 6


class Popover(ChainableComponent):
    """
    A panel anchored to a control, for content that can be interacted with.

    Click opens it, Escape and a click outside close it, and Escape puts focus
    back on the trigger. Nothing is trapped and the page behind stays live, so
    a form in a popover is a form on the page. title() and description() open
    it; anything else passed as content follows underneath.
    """

    category = "Overlays"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .title("Share Route planner")
            .description("Anyone with the link can view. Members can edit.")
            .trigger(Button().variant("outline").content("Share project"))
        )

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def description(self, value: str) -> Self:
        self._props["description"] = value
        return self

    def fit(self, value: bool = True) -> Self:
        """
        Size the panel to what is in it, rather than the standard width.

        For the short ones - a handful of links, a line of help - where a
        280px card around two words is mostly card.
        """
        self._props["fit"] = value
        return self

    def placement(self, value: PopoverPlacement) -> Self:
        """
        Which corner of the trigger it hangs off. A preference rather than a
        promise: the panel flips and shifts to stay inside the viewport.
        """
        self._props["placement"] = value
        return self

    def trigger(self, value: ChainableComponent) -> Self:
        """
        The control that opens it.

        A hue component rather than any markup, because the popover wires the
        click, the expanded state and the anchor onto the control itself.
        """
        self._props["trigger"] = value
        return self

    def _render(self, context: Context) -> Component:
        placement: PopoverPlacement = self._get_prop("placement", "bottom-start")
        title: str | None = self._get_prop("title")
        description: str | None = self._get_prop("description")
        trigger: ChainableComponent | None = self._get_prop("trigger")

        panel_id = "$id('hue-popover')"
        title_id = "$id('hue-popover-title')"

        if trigger is not None:
            (
                trigger.x_ref("trigger")
                .x_on("click", unsafe("open = !open"))
                .x_bind("aria-expanded", unsafe("open"))
                .x_bind("aria-controls", unsafe(panel_id))
            )
            trigger._attrs.setdefault("aria_haspopup", "dialog")

        panel = html.div(
            render_if(
                title,
                lambda text: html.div(
                    text,
                    class_="font-ui text-base font-bold leading-[1.35] text-fg",
                    **{":id": title_id},
                ),
            ),
            render_if(
                description,
                lambda text: html.p(
                    text,
                    class_="mt-0.5 text-sm leading-[1.5] text-fg-muted",
                ),
            ),
            # first:mt-0 so the content carries the gap only when there is
            # something above it to be spaced from.
            render_when(
                bool(self._children),
                html.div(
                    *self._children,
                    class_="mt-3.5 flex flex-col gap-3.5 first:mt-0",
                ),
            ),
            role="dialog",
            class_=classnames(
                "z-70 max-w-[calc(100vw-2rem)] rounded-lg border border-border",
                "bg-surface-raised text-base shadow-raised",
                # Picked rather than layered: two width utilities would
                # resolve by stylesheet order.
                "w-auto p-1" if self._get_prop("fit", False) else "w-70 p-4",
            ),
            **{
                ":id": panel_id,
                # Named by its title where it has one; a panel that announces
                # itself as "dialog" and nothing else is a dead end.
                ":aria-labelledby": title_id if title is not None else None,
                "x-show": "open",
                "x-cloak": True,
                "x-transition.opacity": "",
                f"x-anchor.{placement}.offset.{_OFFSET}": "$refs.trigger",
            },
        )

        return html.span(
            render_if(trigger, lambda control: control),
            panel,
            class_=classnames("inline-flex", self._get_prop("class_")),
            **{
                # close() puts focus back where it came from, which a click
                # outside must not do - focus is wherever that click landed.
                "x-data": "{ open: false, "
                "close() { this.open = false; this.$refs.trigger?.focus() } }",
                "x-id": "['hue-popover', 'hue-popover-title']",
                "x-on:keydown.escape.window": "if (open) close()",
                "x-on:click.outside": "open = false",
                **self._get_base_html_attrs(),
            },
        )
