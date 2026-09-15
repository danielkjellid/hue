from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type TooltipPlacement = Literal["top", "bottom", "start", "end"]

# Where the bubble sits, and which way its arrow points. The arrow is what
# makes the association legible: a bubble floating free of its trigger reads
# as a stray chip.
_PLACEMENTS: dict[TooltipPlacement, str] = {
    "top": "bottom-full left-1/2 -translate-x-1/2 mb-1.5",
    "bottom": "top-full left-1/2 -translate-x-1/2 mt-1.5",
    "start": "right-full top-1/2 -translate-y-1/2 me-1.5",
    "end": "left-full top-1/2 -translate-y-1/2 ms-1.5",
}

_ARROWS: dict[TooltipPlacement, str] = {
    "top": "top-full left-1/2 -ms-[5px] border-t-fg border-b-0",
    "bottom": "bottom-full left-1/2 -ms-[5px] border-b-fg border-t-0",
    "start": "left-full top-1/2 -mt-[5px] border-s-fg border-e-0",
    "end": "right-full top-1/2 -mt-[5px] border-e-fg border-s-0",
}

# ~400ms to open so a pointer crossing the toolbar does not trail bubbles,
# and nothing on the way out.
_OPEN_DELAY_MS = 400


class Tooltip(ChainableComponent):
    """
    A short label for the control it wraps.

    Shown on hover and on focus, because a keyboard never hovers. Never put a
    link or a button inside one: there is no way to reach it, and on a touch
    device the tooltip does not open at all - so what it says can never be the
    only place that information lives.

        Tooltip().content("Rename").trigger(Button().icon_only("Rename"))
    """

    category = "Overlays"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .content("Copy to clipboard")
            .trigger(Button().variant("ghost").size("sm").content("Copy"))
        )

    def trigger(self, value: ChainableComponent) -> Self:
        """
        The control the tooltip is about, which keeps its own accessible name.

        A hue component rather than any markup, because the tooltip has to put
        aria-describedby on the control itself - on a wrapper around it, it
        describes nothing.
        """
        self._props["trigger"] = value
        return self

    def placement(self, value: TooltipPlacement) -> Self:
        self._props["placement"] = value
        return self

    def shortcut(self, value: ComponentType) -> Self:
        """
        A key hint shown after the label, such as a Kbd.
        """
        self._props["shortcut"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        placement: TooltipPlacement = self._get_prop("placement", "top")
        trigger: ChainableComponent | None = self._get_prop("trigger")

        # Alpine mints the id, so two tooltips on a page cannot share one, and
        # the description lands on the control rather than on the wrapper
        # around it - the only element a screen reader will read it from.
        bubble_id = "$id('hue-tooltip')"
        if trigger is not None:
            trigger.x_bind("aria-describedby", bubble_id)

        bubble = html.div(
            *self._children,
            render_if(self._get_prop("shortcut"), lambda hint: hint),
            # The arrow is drawn with borders on a zero-size box, which is the
            # one way to get a triangle without a second colour to keep in
            # step with the bubble.
            html.span(
                aria_hidden="true",
                class_=classnames(
                    "absolute size-0 border-[5px] border-transparent",
                    _ARROWS[placement],
                ),
            ),
            role="tooltip",
            class_=classnames(
                "absolute z-20 inline-flex w-max max-w-60 items-center gap-1.5",
                "rounded-sm bg-fg px-[9px] py-[5px] shadow-raised",
                "font-ui text-xs font-normal leading-[1.45] text-canvas",
                _PLACEMENTS[placement],
            ),
            **{
                ":id": bubble_id,
                "x-show": "open",
                "x-cloak": True,
                "x-transition.opacity": "",
            },
        )

        return html.span(
            render_if(trigger, lambda control: control),
            bubble,
            class_=classnames("relative inline-flex", self._get_prop("class_")),
            **{
                "x-data": "{ open: false }",
                "x-id": "['hue-tooltip']",
                # Focus as well as hover, because a keyboard never hovers, and
                # Escape because a tooltip that cannot be dismissed can sit on
                # top of what the user is trying to read.
                "x-on:mouseenter": f"clearTimeout($el._t); "
                f"$el._t = setTimeout(() => open = true, {_OPEN_DELAY_MS})",
                "x-on:mouseleave": "clearTimeout($el._t); open = false",
                "x-on:focusin": "open = true",
                "x-on:focusout": "open = false",
                "x-on:keydown.escape": "open = false",
                **self._get_base_html_attrs(),
            },
        )
