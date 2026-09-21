"""
The row shared by the checkbox, the radio and the switch.

All three are the same shape: a control, a label beside it, and an optional
line of description under that. Only the control differs, so it is passed in.
"""

from __future__ import annotations

from htmy import html

from hue.types.core import UNDEFINED, ComponentType
from hue.ui._styles import FOCUS_RING
from hue.utils import classnames, render_if

#: Which side the control sits on. Leading with it is what a checkbox in a
#: form does; horizontal puts the text first and pushes the control to the
#: far end, which is the scanning order a settings list wants - what can I
#: change, then the thing that changes it.
# Top-aligned, because a two-line label would otherwise push the control
# down to the middle of its own text.
_ROW = "flex items-start gap-3"
# Centred, because the control is opposite the whole block rather than
# beside its first line.
_ROW_HORIZONTAL = "flex items-center justify-between gap-6"
_TEXT = "flex min-w-0 flex-col gap-px"
_LABEL = "font-ui text-base font-medium leading-[1.35]"
_DESCRIPTION = "text-sm leading-[1.45] text-fg-muted"

# A card is the same row inside a pressable surface. The fill follows the
# control's own state through :has, so nothing has to be mirrored in Alpine.
_CARD = (
    "rounded-md border border-border bg-surface p-4 "
    "transition-[border-color,background-color] duration-150 "
    "hover:border-border-hover "
    "has-[:checked]:border-accent has-[:checked]:bg-accent-subtle"
)

#: The 18px box a checkbox and a radio share. The native control is styled
#: rather than hidden behind a lookalike, so every keyboard, form and
#: assistive-tech behaviour stays the browser's to provide.
CHOICE_BOX = classnames(
    "mt-px grid size-[18px] flex-none cursor-pointer appearance-none",
    "place-content-center border-[1.5px] border-border-input bg-surface",
    "transition-[background-color,border-color,box-shadow] duration-150",
    "enabled:hover:border-accent",
    "checked:border-accent checked:bg-accent",
    "disabled:cursor-not-allowed disabled:border-border disabled:bg-surface-sunken",
    "disabled:checked:border-fg-disabled disabled:checked:bg-fg-disabled",
    "aria-invalid:border-danger",
    FOCUS_RING,
)


def label_id(control_id: str) -> str:
    """
    The id of the label belonging to the control with this id.
    """
    return f"{control_id}-label"


def description_id(control_id: str) -> str:
    """
    The id of the description belonging to the control with this id.
    """
    return f"{control_id}-description"


def choice_row(
    control: ComponentType,
    *,
    control_id: str,
    label: str | None,
    description: str | None,
    disabled: bool,
    card: bool,
    horizontal: bool = False,
    status: ComponentType = UNDEFINED,
    messages: tuple[ComponentType, ...] = (),
    class_: str | None = None,
) -> ComponentType:
    """
    A control with its label, its description and any error beneath.

    The whole row is a label element, so the text is part of the hit area
    rather than something to aim past on the way to an 18px box. status sits
    on the label's own line, which is the one thing in the row guaranteed to
    be there.

    Both pieces of text carry ids. Wrapping the control in a label makes every
    word inside it part of the control's name, so a screen reader would read a
    whole sentence of description before getting to "checkbox". The control
    points at the label for its name and at the description for its
    description instead, which is what the two of them are.
    """
    head = render_if(
        label,
        lambda text: html.span(
            text,
            id=label_id(control_id),
            class_=classnames(_LABEL, "text-fg-disabled" if disabled else None),
        ),
    )

    text: ComponentType = UNDEFINED
    if label is not None or description is not None or status is not UNDEFINED:
        text = html.span(
            # The label and the status share a line, so the status does not
            # move depending on whether there is a description under it.
            html.span(head, status, class_="inline-flex items-center gap-2"),
            render_if(
                description,
                lambda text: html.span(
                    text, id=description_id(control_id), class_=_DESCRIPTION
                ),
            ),
            class_=classnames(_TEXT, "flex-1" if horizontal else None),
        )

    return html.div(
        html.label(
            *((text, control) if horizontal else (control, text)),
            for_=control_id,
            class_=classnames(
                _ROW_HORIZONTAL if horizontal else _ROW,
                "cursor-not-allowed" if disabled else "cursor-pointer",
                _CARD if card else None,
            ),
        ),
        *messages,
        class_=classnames("flex flex-col gap-1.5", class_),
    )
