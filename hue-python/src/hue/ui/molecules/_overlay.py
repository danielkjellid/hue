"""
The parts a dialog and a drawer are made of.

Both are a panel over a scrim with the same header, the same body and the
same strip of actions along the bottom; only the edge they arrive from
differs. These are private to the two of them - a consumer composes overlays
through Dialog and Drawer, not out of these.
"""

from __future__ import annotations

from htmy import html

from hue.types.core import ComponentType
from hue.ui._styles import FOCUS_RING
from hue.ui.atoms.icon import HueIcon
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if, render_when

# Alpine mints the ids, so two overlays on a page cannot share one.
TITLE_ID = "$id('hue-overlay-title')"
DESCRIPTION_ID = "$id('hue-overlay-description')"
OVERLAY_IDS = "['hue-overlay-title', 'hue-overlay-description']"

#: The dimmed, blurred page behind an open overlay.
SCRIM = "fixed inset-0 z-80 flex bg-scrim backdrop-blur-[2px]"


def overlay_state(starts_open: bool) -> str:
    """
    The x-data every overlay carries.

    close() rather than a bare assignment, so the actions inside have a way
    out to call that is not the state's shape.
    """
    return f"{{ open: {str(starts_open).lower()}, close() {{ this.open = false }} }}"


def open_on_click(trigger: ChainableComponent) -> None:
    """
    Wire a control to open the overlay it belongs to.
    """
    trigger.x_on("click", "open = true").x_bind("aria-expanded", "open")
    trigger._attrs.setdefault("aria_haspopup", "dialog")


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
