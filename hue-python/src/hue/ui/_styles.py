"""
Class recipes shared across components.

Only the things the design system defines once and every component is expected
to render identically belong here. Anything a single component owns stays in
that component, where it is visible next to the markup it styles.
"""

from __future__ import annotations

from typing import Literal

#: The system's one flourish, identical on every focusable element: a 2px
#: canvas-coloured gap then 2px of accent. The gap is what keeps the ring
#: legible on tinted surfaces as well as on the canvas.
#:
#: focus-visible rather than focus, so a mouse user does not see a ring on
#: click while a keyboard user always does.
FOCUS_RING = (
    "outline-none focus-visible:ring-2 focus-visible:ring-accent "
    "focus-visible:ring-offset-2 focus-visible:ring-offset-canvas"
)


type ControlSize = Literal["sm", "md", "lg"]

#: Height, inline padding and type size for the box-shaped controls - inputs,
#: native selects, the select trigger. The heights come from the control-*
#: spacing tokens, which grow on coarse pointers so a touch target stays one.
CONTROL_SIZES: dict[ControlSize, str] = {
    "sm": "h-control-sm px-[9px] text-sm",
    "md": "h-control-md px-[11px] text-base",
    "lg": "h-control-lg px-[14px] text-md",
}

#: Everything a field-shaped control looks like across all of its states.
#:
#: No focus ring here: a control with a border of its own tightens that border
#: to the accent and lays a 3px halo outside it, which moves nothing, where the
#: offset ring on a button would jump the layout of a form row.
FIELD_SHELL = (
    "w-full min-w-0 rounded-md border border-border-input bg-surface text-fg "
    "font-body leading-none shadow-field placeholder:text-fg-subtle "
    "transition-[border-color,box-shadow] duration-150 "
    "enabled:hover:border-border-hover "
    "focus:outline-none focus:border-accent focus:ring-3 focus:ring-accent-subtle "
    "aria-invalid:border-danger aria-invalid:focus:ring-danger-subtle "
    "read-only:bg-surface-sunken "
    "disabled:cursor-not-allowed disabled:bg-surface-sunken "
    "disabled:text-fg-disabled disabled:shadow-none"
)
