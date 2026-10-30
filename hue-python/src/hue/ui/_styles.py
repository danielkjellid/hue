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


#: The same ring for a control that sits flush inside a padded panel - a menu
#: item, and later a listbox option - or in a row that scrolls, such as a tab.
#: Inset, because the offset ring is drawn outside the item, where it lands on
#: the panel's padding and past its edge, or is clipped by the scrolling row.
FOCUS_RING_INSET = (
    "outline-none focus-visible:inset-ring-2 focus-visible:inset-ring-accent"
)


type ControlSize = Literal["sm", "md", "lg"]

#: The heights of the box-shaped controls - inputs, native selects, the
#: select trigger - from the control-* spacing tokens, which grow on coarse
#: pointers so a touch target stays one.
CONTROL_HEIGHTS: dict[ControlSize, str] = {
    "sm": "h-control-sm",
    "md": "h-control-md",
    "lg": "h-control-lg",
}

#: Inline padding, type size and the flat leading that keeps a one-line
#: control one line: a control's size without its height. A control inside
#: a group takes only this, since the group carries the height and the
#: control stretches to fill the inside of its border.
CONTROL_TEXT: dict[ControlSize, str] = {
    "sm": "px-[9px] text-sm leading-none",
    "md": "px-[11px] text-base leading-none",
    "lg": "px-[14px] text-md leading-none",
}

#: A group's height: at least a plain field's, so the two line up, and more
#: when the control inside it is given more.
GROUP_HEIGHTS: dict[ControlSize, str] = {
    "sm": "min-h-control-sm",
    "md": "min-h-control-md",
    "lg": "min-h-control-lg",
}

#: Height and text together, for a control that stands on its own.
CONTROL_SIZES: dict[ControlSize, str] = {
    size: f"{CONTROL_HEIGHTS[size]} {CONTROL_TEXT[size]}" for size in CONTROL_TEXT
}

#: Everything a field-shaped control looks like across all of its states.
#:
#: No focus ring here: a control with a border of its own tightens that border
#: to the accent and lays a 3px halo outside it, which moves nothing, where the
#: offset ring on a button would jump the layout of a form row. An invalid one
#: keeps its red border and draws a solid 2px danger ring instead, since a
#: pale red halo is too faint to show focus.
FIELD_SHELL = (
    "w-full min-w-0 rounded-md border border-border-input bg-surface text-fg "
    "font-body shadow-field placeholder:text-fg-subtle "
    "transition-[border-color,box-shadow] duration-150 "
    # Hover leaves an invalid or focused border alone: it sorts after both, so
    # it would otherwise grey out the red or the accent under the pointer.
    "enabled:not-aria-invalid:not-focus:hover:border-border-hover "
    "focus:outline-none not-aria-invalid:focus:border-accent "
    "not-aria-invalid:focus:ring-3 not-aria-invalid:focus:ring-accent-subtle "
    "aria-invalid:border-danger aria-invalid:focus:ring-2 "
    "aria-invalid:focus:ring-danger "
    # The attribute, not :read-only, which every select and button matches.
    "[&[readonly]]:bg-surface-sunken "
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
#: The states of a frame that answers the control inside it, shared by
#: GROUP_SHELL and the combobox. Hover only applies to a valid, enabled,
#: unfocused control and the accent only to a valid one, so an invalid one
#: keeps its danger border and ring the way an ungrouped field does. Left to
#: the order the variants sort in, hover and focus would win.
GROUP_STATES = (
    "transition-[border-color,box-shadow] duration-150 "
    # One token, not split across lines: Tailwind reads the source as text.
    "not-has-[input:is(:focus,:disabled),[aria-invalid=true]]:hover:border-border-hover"
    " not-has-[[aria-invalid=true]]:has-[input:focus]:border-accent "
    "not-has-[[aria-invalid=true]]:has-[input:focus]:ring-3 "
    "not-has-[[aria-invalid=true]]:has-[input:focus]:ring-accent-subtle "
    "has-[[aria-invalid=true]]:border-danger "
    "has-[[aria-invalid=true]:focus]:ring-2 "
    "has-[[aria-invalid=true]:focus]:ring-danger "
    "has-[:disabled]:bg-surface-sunken"
)

GROUP_SHELL = (
    "flex w-full items-stretch rounded-md border border-border-input bg-surface "
    f"shadow-field {GROUP_STATES} has-[[readonly]]:bg-surface-sunken"
)

#: A control inside GROUP_SHELL: everything the group now owns, given up.
#: It sits inside the group's border, and at either end follows the group's
#: 7px inner curve, so a fill the browser paints on it (autofill) leaves the
#: border and the corners alone.
GROUPED_CONTROL = (
    "min-w-0 flex-1 rounded-none first:rounded-s-[7px] last:rounded-e-[7px] "
    "border-none bg-transparent text-fg "
    "shadow-none "
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

#: The sunken track a run of segments sits in, and what one segment looks
#: like before anything is selected.
#:
#: Shared by SegmentedControl and the segmented Tabs, which look identical and
#: mean different things - one is a group of toggles answering to aria-pressed,
#: the other a tablist answering to aria-selected. The three classes that mark
#: the chosen one carry that difference, so they stay at the call sites; only
#: what both wear is here.
SEGMENTED_TRACK = (
    "inline-flex gap-0.5 rounded-md border border-border bg-surface-sunken p-[3px]"
)

SEGMENTED_ITEM = (
    "inline-flex items-center justify-center gap-1.5 rounded-sm cursor-pointer "
    "select-none whitespace-nowrap font-ui font-semibold leading-none "
    "transition-colors text-fg-muted hover:text-fg [&_svg]:size-3.5 "
    "[&_svg]:shrink-0"
)

#: A word or a unit attached to the end of a group. The 7px radius is the
#: group's inner curve at a 1px border, so the fill follows its corner.
GROUP_ADDON = (
    "flex items-center gap-[5px] px-[11px] whitespace-nowrap "
    "bg-surface-sunken text-sm text-fg-muted"
)
