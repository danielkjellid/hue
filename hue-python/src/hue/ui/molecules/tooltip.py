from __future__ import annotations

import json
from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.js import unsafe
from hue.types.core import Component, ComponentType
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.ui.molecules import _overlay
from hue.utils import classnames, render_if

type TooltipPlacement = Literal["top", "bottom", "start", "end"]

# Where the bubble sits, and which way its arrow points. The arrow is what
# makes the association legible: a bubble floating free of its trigger reads
# as a stray chip. The before element spans the gap on the trigger side, so a
# pointer on its way into the bubble never leaves the wrapper and closes it.
# The anchor only knows physical sides, so start and end name one for each
# direction; the classes are logical and follow the direction on their own.
_PLACEMENTS: dict[TooltipPlacement, tuple[str, str, str]] = {
    "top": ("top", "top", "before:top-full before:inset-x-0 before:h-1.5"),
    "bottom": ("bottom", "bottom", "before:bottom-full before:inset-x-0 before:h-1.5"),
    "start": ("left", "right", "before:start-full before:inset-y-0 before:w-1.5"),
    "end": ("right", "left", "before:end-full before:inset-y-0 before:w-1.5"),
}

_ARROWS: dict[TooltipPlacement, str] = {
    "top": "top-full start-1/2 -ms-[5px] border-t-surface-inverse border-b-0",
    "bottom": "bottom-full start-1/2 -ms-[5px] border-b-surface-inverse border-t-0",
    "start": "start-full top-1/2 -mt-[5px] border-s-surface-inverse border-e-0",
    "end": "end-full top-1/2 -mt-[5px] border-e-surface-inverse border-s-0",
}


def _anchored(side: str) -> str:
    # The arrow points one way, so the bubble keeps its side.
    return json.dumps(_overlay.anchor(side, "$el.parentElement", flip=False))


# ~400ms to open so a pointer crossing the toolbar does not trail bubbles,
# and nothing on the way out.
_OPEN_DELAY_MS = 400


class Tooltip(_overlay.WrapsTrigger):
    """
    A short label for the control it wraps.

    Shown on hover and on keyboard focus, because a keyboard never hovers. Never put a
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
        ltr, rtl, bridge = _PLACEMENTS[placement]
        trigger: ChainableComponent | None = self._get_prop("trigger")

        # Alpine mints the id, so two tooltips on a page cannot share one, and
        # the description lands on the control rather than on the wrapper
        # around it - the only element a screen reader will read it from.
        bubble_id = "$id('hue-tooltip')"
        control = self._trigger_control()
        if control is not None:
            control.x_bind("aria-describedby", unsafe(bubble_id))

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
                "z-20 inline-flex w-max max-w-60 items-center gap-1.5",
                "rounded-sm bg-surface-inverse px-[9px] py-[5px] shadow-raised",
                "font-ui text-xs font-normal leading-[1.45] text-surface-inverse-fg",
                "before:absolute before:content-['']",
                bridge,
            ),
            **{
                ":id": bubble_id,
                "x-show": "shown",
                "x-cloak": True,
                "x-transition.opacity": "",
                # Bound as an object, the one way to pick a directive by the
                # direction the bubble ends up in.
                "x-bind": "getComputedStyle($el).direction === 'rtl' ? "
                f"{_anchored(rtl)} : {_anchored(ltr)}",
            },
        )

        # The control's own mark, which renders before anything it opens.
        popup_open = f"({_overlay.TRIGGER}?.getAttribute('aria-expanded') === 'true')"

        return html.span(
            render_if(trigger, lambda control: control),
            bubble,
            class_=classnames("inline-flex", self._get_prop("class_")),
            **{
                # shown rather than open: a menu or dialog the trigger opens
                # names its own state open, and the trigger sits in this
                # scope, where the nearer name would win.
                "x-data": "{ shown: false }",
                "x-id": "['hue-tooltip']",
                # Keyboard focus as well as hover, because a keyboard never
                # hovers; a press focuses too, and the pointer is already
                # covered. The bubble sits inside the wrapper, so the pointer
                # can move onto it and read it without the tooltip closing.
                #
                # Never over the popup the control opened, which is what the
                # control is now about. A pointer click drops a pending open,
                # which a quick click would otherwise leave to fire over the
                # popup. Enter and Space click too, with detail 0, and keep a
                # label the keyboard is reading, unless that click opened a
                # popup; its state lands a tick after the click.
                #
                # Escape is heard on the window, because a tooltip opened by
                # hover has to close while focus is somewhere else entirely. It
                # drops a pending open too, which would otherwise undo it. In
                # the capture phase, before a dialog around it hears the key
                # and stops it: an open tooltip takes the first Escape, and
                # only one that was open, so the next press reaches the dialog.
                # An open popup is the exception, focus on its control or
                # inside it: it opened last, so it closes first.
                "x-on:mouseenter": f"clearTimeout($el._t); "
                f"$el._t = setTimeout(() => shown = !{popup_open}, "
                f"{_OPEN_DELAY_MS})",
                "x-on:mouseleave": "clearTimeout($el._t); shown = false",
                "x-on:click": "clearTimeout($el._t); if ($event.detail) "
                "shown = false; "
                f"else $nextTick(() => shown = shown && !{popup_open})",
                "x-on:focusin": "shown = "
                f"$event.target.matches(':focus-visible') && !{popup_open}",
                "x-on:focusout": "shown = false",
                "x-on:keydown.escape.window.capture": "clearTimeout($el._t); "
                f"if (shown && !{popup_open} && "
                "$event.target.getAttribute?.('aria-expanded') !== 'true') "
                "{ $event.stopPropagation(); shown = false }",
                **self._get_base_html_attrs(),
            },
        )
