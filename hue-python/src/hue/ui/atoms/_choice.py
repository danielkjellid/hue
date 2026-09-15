"""
The row shared by the checkbox, the radio and the switch.

All three are the same shape: a control, a label beside it, and an optional
line of description under that. Only the control differs, so it is passed in.
"""

from __future__ import annotations

from typing import Literal

from htmy import html

from hue.types.core import ComponentType
from hue.ui._styles import FOCUS_RING
from hue.utils import classnames, render_if

type ChoiceVariant = Literal["inline", "card"]

_ROW = "flex items-start gap-3"
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
    variant: ChoiceVariant,
    messages: tuple[ComponentType, ...] = (),
    class_: str | None = None,
) -> ComponentType:
    """
    A control with its label, its description and any error beneath.

    The whole row is a label element, so the text is part of the hit area
    rather than something to aim past on the way to an 18px box.

    Both pieces of text carry ids. Wrapping the control in a label makes every
    word inside it part of the control's name, so a screen reader would read a
    whole sentence of description before getting to "checkbox". The control
    points at the label for its name and at the description for its
    description instead, which is what the two of them are.
    """
    text = render_if(
        label or description,
        lambda _: html.span(
            render_if(
                label,
                lambda text: html.span(
                    text,
                    id=label_id(control_id),
                    class_=classnames(_LABEL, "text-fg-disabled" if disabled else None),
                ),
            ),
            render_if(
                description,
                lambda text: html.span(
                    text, id=description_id(control_id), class_=_DESCRIPTION
                ),
            ),
            class_=_TEXT,
        ),
    )

    return html.div(
        html.label(
            control,
            text,
            for_=control_id,
            class_=classnames(
                _ROW,
                "cursor-not-allowed" if disabled else "cursor-pointer",
                _CARD if variant == "card" else None,
            ),
        ),
        *messages,
        class_=classnames("flex flex-col gap-1.5", class_),
    )
