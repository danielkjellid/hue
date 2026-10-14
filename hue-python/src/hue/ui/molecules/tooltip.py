from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type TooltipPlacement = Literal["top", "bottom", "start", "end"]

# Where the bubble sits, and which way its arrow points. The arrow is what
# makes the association legible: a bubble floating free of its trigger reads
# as a stray chip. The before element spans the gap on the trigger side, so a
# pointer on its way into the bubble never leaves the wrapper and closes it.
_PLACEMENTS: dict[TooltipPlacement, str] = {
    "top": "bottom-full left-1/2 -translate-x-1/2 mb-1.5 "
    "before:top-full before:inset-x-0 before:h-1.5",
    "bottom": "top-full left-1/2 -translate-x-1/2 mt-1.5 "
    "before:bottom-full before:inset-x-0 before:h-1.5",
    "start": "right-full top-1/2 -translate-y-1/2 me-1.5 "
    "before:left-full before:inset-y-0 before:w-1.5",
    "end": "left-full top-1/2 -translate-y-1/2 ms-1.5 "
    "before:right-full before:inset-y-0 before:w-1.5",
}

_ARROWS: dict[TooltipPlacement, str] = {
    "top": "top-full left-1/2 -ms-[5px] border-t-surface-inverse border-b-0",
    "bottom": "bottom-full left-1/2 -ms-[5px] border-b-surface-inverse border-t-0",
    "start": "left-full top-1/2 -mt-[5px] border-s-surface-inverse border-e-0",
    "end": "right-full top-1/2 -mt-[5px] border-e-surface-inverse border-s-0",
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

    def _trigger_control(self) -> ChainableComponent | None:
        # The span this draws only holds the bubble; the control it wraps
        # takes the click, the focus and the announcement.
        trigger: ChainableComponent | None = self._get_prop("trigger")
        return trigger._trigger_control() if trigger is not None else None

    def placement(self, value: TooltipPlacement) -> Self:
        self._props["placement"] = value
        return self

    def keys(self, value: ComponentType) -> Self:
        """
        The keys the trigger answers to, shown after the label. Pass a Kbd,
        which renders real kbd elements and gives each modifier a spoken name;
        a glyph on its own is announced by its Unicode name. Only shown: bind
        the keys where the action is, in the app's shortcuts or as a palette's
        hotkey.
        """
        self._props["keys"] = value
        return self

    def _render(self, context: Context) -> Component:
        placement: TooltipPlacement = self._get_prop("placement", "top")
        trigger: ChainableComponent | None = self._get_prop("trigger")

        # Alpine mints the id, so two tooltips on a page cannot share one, and
        # the description lands on the control rather than on the wrapper
        # around it - the only element a screen reader will read it from.
        bubble_id = "$id('hue-tooltip')"
        if trigger is not None:
            trigger.x_bind("aria-describedby", unsafe(bubble_id))

        bubble = html.div(
            *self._children,
            render_if(self._get_prop("keys"), lambda keys: keys),
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
                "rounded-sm bg-surface-inverse px-[9px] py-[5px] shadow-raised",
                "font-ui text-xs font-normal leading-[1.45] text-surface-inverse-fg",
                "before:absolute before:content-['']",
                _PLACEMENTS[placement],
            ),
            **{
                ":id": bubble_id,
                "x-show": "shown",
                "x-cloak": True,
                "x-transition.opacity": "",
            },
        )

        return html.span(
            render_if(trigger, lambda control: control),
            bubble,
            class_=classnames("relative inline-flex", self._get_prop("class_")),
            **{
                # shown rather than open: a menu or dialog the trigger opens
                # names its own state open, and the trigger sits in this
                # scope, where the nearer name would win.
                "x-data": "{ shown: false }",
                "x-id": "['hue-tooltip']",
                # Focus as well as hover, because a keyboard never hovers. The
                # bubble sits inside the wrapper, so the pointer can move onto
                # it and read it without the tooltip closing.
                #
                # Escape is heard on the window, because a tooltip opened by
                # hover has to close while focus is somewhere else entirely. It
                # drops a pending open too, which would otherwise undo it.
                "x-on:mouseenter": f"clearTimeout($el._t); "
                f"$el._t = setTimeout(() => shown = true, {_OPEN_DELAY_MS})",
                "x-on:mouseleave": "clearTimeout($el._t); shown = false",
                "x-on:focusin": "shown = true",
                "x-on:focusout": "shown = false",
                "x-on:keydown.escape.window": "clearTimeout($el._t); shown = false",
                **self._get_base_html_attrs(),
            },
        )
