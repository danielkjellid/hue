from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _overlay
from hue.utils import classnames, render_if, render_when

type PopoverPlacement = Literal["bottom-start", "bottom-end", "top-start", "top-end"]


class Popover(_overlay.WrapsTrigger):
    """
    A panel anchored to a control, for content that can be interacted with.

    Click opens it. Escape, a click outside and focus leaving it close it, and
    Escape puts focus back on the trigger. Nothing is trapped and the page
    behind stays live, so a form in a popover is a form on the page. title()
    and description() open it; anything else passed as content follows
    underneath.
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

    def label(self, value: str) -> Self:
        """
        The panel's accessible name, for a panel with no title to be named by.
        """
        self._props["label"] = value
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

        find_trigger = _overlay.wire_trigger(
            trigger,
            popup="dialog",
            on={"click": "open = !open"},
            bind={"aria-controls": panel_id},
        )

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
                **_overlay.accessible_name(
                    "Popover", title, self._get_prop("label"), title_id=title_id
                ),
                "x-show": "open",
                "x-cloak": True,
                "x-transition.opacity": "",
                **_overlay.anchor(placement, find_trigger),
                **_overlay.HOLDS_FOCUS,
            },
        )

        return html.span(
            render_if(trigger, lambda control: control),
            panel,
            class_=classnames("inline-flex", self._get_prop("class_")),
            **{
                # close() puts focus back where it came from, which a click
                # outside must not do - focus is wherever that click landed.
                **_overlay.overlay_root(_overlay.overlay_state(return_to=find_trigger)),
                "x-id": "['hue-popover', 'hue-popover-title']",
                "x-on:click.outside": "open = false",
                # Tabbing out closes it too, or the panel would sit over
                # whatever took focus next. Focus went somewhere on purpose,
                # so it stays there. A focusout with nowhere to go is one of
                # three things, told apart a tick later. A click on the page
                # leaves the document focused and is the click outside's to
                # handle. Another window or tab taking focus leaves
                # activeElement where it was, so the popover is still open
                # on the way back. Tabbing out of the document leaves
                # neither, and closes it.
                "x-on:focusout": (
                    "if (open && $event.relatedTarget "
                    "&& !$el.contains($event.relatedTarget)) open = false; "
                    "if (open && !$event.relatedTarget) setTimeout(() => { "
                    "if (!document.hasFocus() "
                    "&& !$el.contains(document.activeElement)) open = false })"
                ),
                **self._get_base_html_attrs(),
            },
        )
