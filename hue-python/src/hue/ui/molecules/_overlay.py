"""
The parts a dialog and a drawer are made of.

Both are a panel over a scrim with the same header, the same body and the
same strip of actions along the bottom; only the edge they arrive from
differs. Every other overlay shares the Escape handling. All of it is
private: a consumer builds overlays from the components, never from these.
"""

from __future__ import annotations

from htmy import html

from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.ui.molecules.tooltip import Tooltip
from hue.utils import classnames, render_if, render_when

# Alpine mints the ids, so two overlays on a page cannot share one.
TITLE_ID = "$id('hue-overlay-title')"
DESCRIPTION_ID = "$id('hue-overlay-description')"
OVERLAY_IDS = "['hue-overlay-title', 'hue-overlay-description']"

#: The dimmed, blurred page behind an open overlay.
#:
#: group, so the panel inside can answer the one class Alpine puts here while
#: the overlay is leaving. One x-show and one timer for the pair: the panel
#: had its own once, and two animations deciding separately when they were
#: done is what a closing overlay flickering looks like.
SCRIM = "group fixed inset-0 z-80 flex bg-scrim backdrop-blur-[2px]"

#: What Alpine applies for the length of the leave, and the mirror of the
#: 180ms the exit animations run for.
LEAVING = "leaving transition-opacity duration-[180ms]"

#: How every overlay, the popover and the menu included, closes on Escape.
#: The listener sits on the overlay and not on the window: window listeners
#: run outermost first, so an inner overlay could never stop an outer one. It
#: stops the key, so one press closes only the innermost open overlay and a
#: page-wide Escape behind it (the one that clears a table's selection, say)
#: never fires.
CLOSE_ON_ESCAPE = {
    "x-on:keydown.escape": "if (open) { $event.stopPropagation(); close() }"
}

#: The listener above only hears keys pressed inside the overlay. A click on
#: anything that cannot take focus leaves focus on the body, where the
#: listener cannot hear it. A popover or a menu puts this on its panel. A
#: modal puts it on the scrim, which takes the focus from a click on the
#: panel's text or beside the panel; the focus trap then moves it back in.
HOLDS_FOCUS = {"tabindex": "-1"}


#: Close on a click on the scrim itself, but only one that also began there.
#: A click lands on the element that holds both ends of the press, so a drag
#: that selects text in the panel and lets go over the scrim is a click on
#: the scrim too, and closing would throw away whatever was being selected.
#: The press is kept on the element rather than in an x-data of its own,
#: which would become the scope the panel's x-refs register on.
DISMISS_ON_SCRIM = {
    "x-on:pointerdown": "$el.huePressed = $event.target === $el",
    "x-on:click.self": "if ($el.huePressed) close()",
}


def overlay_state(starts_open: bool) -> str:
    """
    The x-data every overlay carries.

    close() rather than a bare assignment, so the actions inside have a way
    out to call that is not the state's shape.
    """
    return f"{{ open: {str(starts_open).lower()}, close() {{ this.open = false }} }}"


#: What wire_trigger hands back for a control it has marked.
TRIGGER = "$root.querySelector('[data-hue-trigger]')"


def wire_trigger(
    trigger: ChainableComponent | None,
    *,
    popup: str,
    on: dict[str, str],
    bind: dict[str, str] | None = None,
) -> str:
    """
    Put an overlay's listeners and state on the control that opens it, and
    return the expression that finds that control again from inside.

    Listeners go on as x-on rather than @, so a handler the control already
    has through on_click runs alongside them instead of being overwritten
    under the same key. A Tooltip is looked through to the control it labels,
    because the control gets the click, the focus and the announcement, and
    the span the tooltip wraps it in gets none of them.

    The way back is a query rather than x-ref, because a ref registers on the
    nearest x-data, and a control wrapped in a Tooltip sits inside the
    tooltip's. The control renders before the panel, so the first mark under
    the overlay's root is its own. With no control there is no mark of its
    own, and the first one would belong to an overlay nested in the content,
    so the expression is null instead.
    """
    control = trigger
    while isinstance(control, Tooltip):
        control = control._get_prop("trigger")
    if control is None:
        return "null"

    for event, expression in on.items():
        control._attrs[f"x-on:{event}"] = expression
    for attr, expression in {"aria-expanded": "open", **(bind or {})}.items():
        control.x_bind(attr, unsafe(expression))
    control._attrs.setdefault("aria_haspopup", popup)
    control._attrs["data-hue-trigger"] = ""
    return TRIGGER


def grabber(hidden_class: str = "") -> ComponentType:
    """
    The handle that says "sheet" before anything has moved. Pass the class
    that hides it at the width where the panel stops being one.
    """
    return html.div(
        aria_hidden="true",
        class_=classnames(
            "mx-auto mt-3 mb-1 h-1 w-9 flex-none rounded-full bg-border-strong",
            hidden_class,
        ),
    )


def header(
    title: str | None,
    description: str | None,
    *,
    dismissible: bool,
) -> ComponentType:
    """
    Title, description and the close button, when there is any of them.
    """
    return render_when(
        bool(title or description or dismissible),
        html.div(
            html.div(
                render_if(
                    title,
                    lambda text: html.h2(
                        text,
                        class_="font-ui text-lg font-bold leading-[1.3] "
                        "tracking-[-0.015em] text-fg",
                        **{":id": TITLE_ID},
                    ),
                ),
                render_if(
                    description,
                    lambda text: html.p(
                        text,
                        class_="mt-1 text-sm leading-[1.55] text-fg-muted",
                        **{":id": DESCRIPTION_ID},
                    ),
                ),
                class_="min-w-0 flex-1",
            ),
            render_when(
                dismissible,
                html.button(
                    HueIcon("x").class_("size-4"),
                    type="button",
                    aria_label="Close",
                    class_=classnames(
                        "grid size-7 flex-none place-content-center rounded-sm",
                        "cursor-pointer text-fg-subtle hover:bg-surface-hover "
                        "hover:text-fg",
                        FOCUS_RING,
                    ),
                    **{"x-on:click": "close()"},
                ),
            ),
            class_="flex items-start gap-4 px-5 pt-5 pb-3",
        ),
    )


def body(children: tuple[ComponentType, ...]) -> ComponentType:
    """
    The scrolling middle. min-h-0 is what lets it scroll rather than pushing
    the footer out of the clipped panel.
    """
    return render_when(
        bool(children),
        html.div(
            *children,
            class_="min-h-0 flex-1 overflow-y-auto px-5 pb-5 text-base",
        ),
    )


def footer(items: tuple[ComponentType, ...]) -> ComponentType:
    """
    The strip of actions along the bottom.

    Where the panel is docked to the bottom edge of a phone, that strip is
    the edge of the screen, so its buttons clear the home indicator. The
    max() is py-4 everywhere the inset is zero.
    """
    return render_when(
        bool(items),
        html.div(
            *items,
            # mt-auto, because the strip belongs to the bottom edge of the
            # panel rather than to whatever is above it - a drawer with no
            # body at all still has its actions where the thumb expects them.
            class_="mt-auto flex items-center justify-end gap-2 border-t "
            "border-border bg-surface-sunken px-5 pt-4 "
            "pb-[max(1rem,env(safe-area-inset-bottom))]",
        ),
    )
