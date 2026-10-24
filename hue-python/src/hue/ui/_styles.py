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
#: item, and later a listbox option. Inset, because the offset ring is drawn
#: outside the item, where it lands on the panel's padding and past its edge.
FOCUS_RING_INSET = (
    "outline-none focus-visible:inset-ring-2 focus-visible:inset-ring-accent"
)


#: The small uppercase heading at the top of a panel or over a column of
#: days, which a filter's legend and a calendar's sidebar section are too.
PANEL_LABEL = "font-ui text-2xs font-bold uppercase tracking-[0.05em] text-fg-muted"


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
GROUP_SHELL = (
    "flex w-full items-stretch rounded-md border border-border-input bg-surface "
    "shadow-field transition-[border-color,box-shadow] duration-150 "
    "hover:border-border-hover "
    "has-[input:focus]:border-accent has-[input:focus]:ring-3 "
    "has-[input:focus]:ring-accent-subtle "
    "has-[[aria-invalid=true]]:border-danger "
    "has-[:disabled]:bg-surface-sunken has-[[readonly]]:bg-surface-sunken"
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


#: A chosen value shown as a removable chip, in a Combobox and in a DateInput
#: that holds several days.
TOKEN = (
    "inline-flex h-6 items-center gap-0.5 rounded-sm bg-surface-active ps-[9px] "
    "pe-[3px] text-xs font-medium text-fg"
)

TOKEN_REMOVE = (
    f"{FOCUS_RING} inline-flex size-[18px] flex-none cursor-pointer items-center "
    "justify-center rounded-xs text-fg-muted hover:bg-border-hover hover:text-fg"
)


#: A region Alpine AJAX is about to replace, which it marks aria-busy for as
#: long as the request runs. Dimmed, so a slow query reads as working rather
#: than as a click that did nothing; the attribute itself tells a screen reader.
LOADING = (
    "transition-opacity duration-150 aria-busy:opacity-60 aria-busy:cursor-progress"
)

#: A step through pages, in Pagination and a Calendar's toolbar, minus
#: anything its state decides. Each state names a border colour, a text colour
#: and a cursor, so no two classes compete for the same property.
STEP = (
    "inline-flex h-control-sm min-w-[var(--spacing-control-sm)] items-center "
    "justify-center rounded-md border px-2 font-ui text-sm font-medium "
    "tabular-nums no-underline"
)

STEP_IDLE = (
    "border-transparent text-fg-muted cursor-pointer "
    "hover:bg-surface-hover hover:text-fg"
)

#: A step with nowhere to go stays in the row and stays announced: a control
#: that disappears at the ends teaches nobody where the ends are.
STEP_SPENT = (
    "border-transparent text-fg-disabled cursor-not-allowed pointer-events-none"
)

#: The range separator. An en dash, which is what a range takes.
DASH = "\u2013"
