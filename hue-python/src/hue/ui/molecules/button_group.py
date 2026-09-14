from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.button import Button
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type ButtonGroupVariant = Literal["attached", "segmented"]
type ButtonGroupSize = Literal["sm", "md", "lg"]

# Buttons glued into one control: square off the inner corners, round the outer
# ones, and pull each button onto its neighbour so the seam is one line rather
# than two. A focused button lifts above its neighbours so its ring is whole.
_ATTACHED_CLASSES = (
    "inline-flex [&>*]:relative [&>*]:rounded-none "
    "[&>*:first-child]:rounded-s-md [&>*:last-child]:rounded-e-md "
    "[&>*+*]:-ms-px [&>*:focus-visible]:z-10"
)

# A track with the selected option raised out of it.
_SEGMENTED_CLASSES = (
    "inline-flex gap-0.5 p-[3px] rounded-md border border-border "
    "bg-surface-sunken [&>*]:rounded-sm [&>*]:shadow-none "
    "[&>[aria-pressed=true]]:bg-surface [&>[aria-pressed=true]]:text-fg "
    "[&>[aria-pressed=true]]:shadow-segment"
)

# The track adds 3px of padding and a 1px border either side, so the child sits
# 8px shorter than the control height the group is named for.
_SEGMENTED_CHILD_HEIGHTS: dict[ButtonGroupSize, str] = {
    "sm": "[&>*]:h-6",
    "md": "[&>*]:h-7",
    "lg": "[&>*]:h-9",
}


class ButtonGroup(ChainableComponent):
    """
    Related buttons joined into one control.

    attached only collapses the seam between the buttons and leaves their sizes
    alone. segmented is a track holding one selected option: it sets its
    children's height from size(), and expects each to carry aria-pressed.

        ButtonGroup().variant("segmented").label("Date range").content(...)
    """

    category = "Actions"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .variant("segmented")
            .label("Date range")
            .content(
                Button().variant("ghost").size("sm").content("Day"),
                Button().variant("ghost").size("sm").content("Week"),
            )
        )

    def variant(self, value: ButtonGroupVariant) -> Self:
        self._props["variant"] = value
        return self

    def size(self, value: ButtonGroupSize) -> Self:
        """
        The control height a segmented group adds up to. Attached groups take
        their height from the buttons themselves.
        """
        self._props["size"] = value
        return self

    def label(self, value: str) -> Self:
        """
        What the group as a whole is choosing, e.g. "Date range".
        """
        self._props["label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: ButtonGroupVariant = self._get_prop("variant", "attached")
        size: ButtonGroupSize = self._get_prop("size", "md")
        label: str | None = self._get_prop("label")

        return html.div(
            *self._children,
            class_=classnames(
                _SEGMENTED_CLASSES if variant == "segmented" else _ATTACHED_CLASSES,
                _SEGMENTED_CHILD_HEIGHTS[size] if variant == "segmented" else "",
                self._get_prop("class_"),
            ),
            **{
                # An unlabelled group role announces a group with no name, so
                # without a label this stays a plain container.
                **({"role": "group", "aria_label": label} if label else {}),
                **self._get_base_html_attrs(),
            },
        )
