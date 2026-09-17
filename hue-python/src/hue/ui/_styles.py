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

#: Height, inline padding, type size and the flat leading that keeps a
#: one-line control one line. For the box-shaped controls - inputs,
#: native selects, the select trigger. The heights come from the control-*
#: spacing tokens, which grow on coarse pointers so a touch target stays one.
CONTROL_SIZES: dict[ControlSize, str] = {
    "sm": "h-control-sm px-[9px] text-sm leading-none",
    "md": "h-control-md px-[11px] text-base leading-none",
    "lg": "h-control-lg px-[14px] text-md leading-none",
}

#: Everything a field-shaped control looks like across all of its states.
#:
#: No focus ring here: a control with a border of its own tightens that border
#: to the accent and lays a 3px halo outside it, which moves nothing, where the
#: offset ring on a button would jump the layout of a form row.
FIELD_SHELL = (
    "w-full min-w-0 rounded-md border border-border-input bg-surface text-fg "
    "font-body shadow-field placeholder:text-fg-subtle "
    "transition-[border-color,box-shadow] duration-150 "
    "enabled:hover:border-border-hover "
    "focus:outline-none focus:border-accent focus:ring-3 focus:ring-accent-subtle "
    "aria-invalid:border-danger aria-invalid:focus:ring-danger-subtle "
    "read-only:bg-surface-sunken "
    "disabled:cursor-not-allowed disabled:bg-surface-sunken "
    "disabled:text-fg-disabled disabled:shadow-none"
)

#: The frame around a control that has something attached to it - a prefix, an
#: icon, a button. The border, the fill and the focus halo move up here, so the
#: segments inside can be square without poking past a rounded corner.
#:
#: The halo answers the input rather than focus-within, so it means "you are
#: typing here" and nothing else. An attached button is its own control and
#: says it has focus the way every other button does, with its own ring.
GROUP_SHELL = (
    "flex w-full items-stretch rounded-md border border-border-input bg-surface "
    "shadow-field transition-[border-color,box-shadow] duration-150 "
    "hover:border-border-hover "
    "has-[input:focus]:border-accent has-[input:focus]:ring-3 "
    "has-[input:focus]:ring-accent-subtle "
    "has-[[aria-invalid=true]]:border-danger "
    "has-[:disabled]:bg-surface-sunken has-[:read-only]:bg-surface-sunken"
)

#: A control inside GROUP_SHELL: everything the group now owns, given up.
GROUPED_CONTROL = (
    "min-w-0 flex-1 rounded-none border-none bg-transparent text-fg shadow-none "
    "outline-none placeholder:text-fg-subtle focus:outline-none "
    "disabled:cursor-not-allowed disabled:text-fg-disabled"
)

#: A labelled button attached to the end of a group, flush with its edge.
#:
#: The outer edges belong to the group, so the button gives up its own: no
#: block borders, no end border, square where it meets the input and the
#: group's 7px inner curve where it meets the corner. Selected from the group
#: rather than set on the button, because a compound selector outranks the
#: button's own radius wherever the two land in the stylesheet - and not
#: solved with overflow-hidden on the group, which would clip the focus ring.
#:
#: An icon-only button is not this: it floats inside the field with a little
#: padding, so the selector deliberately reaches only a direct child.
GROUP_ACTION = (
    "[&>button:last-child]:h-auto [&>button:last-child]:self-stretch "
    "[&>button:last-child]:rounded-s-none [&>button:last-child]:rounded-e-[7px] "
    "[&>button:last-child]:border-y-0 [&>button:last-child]:border-e-0"
)

#: A word or a unit attached to the end of a group. The 7px radius is the
#: group's inner curve at a 1px border, so the fill follows its corner.
GROUP_ADDON = (
    "flex items-center gap-[5px] px-[11px] whitespace-nowrap "
    "bg-surface-sunken text-sm text-fg-muted"
)
