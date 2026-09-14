from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type SkeletonShape = Literal["line", "text", "circle", "rect", "card"]

# Each shape carries the size it usually stands in for, so a skeleton is one
# call. Override either axis with class_() when the real content differs.
_SHAPE_CLASSES: dict[SkeletonShape, str] = {
    "line": "h-3 rounded-sm",
    "text": "h-3.5 rounded-xs",
    "circle": "size-9 rounded-full",
    "rect": "h-9 rounded-md",
    "card": "h-32 rounded-lg",
}

# Kept apart from the shape so the short last line replaces the width rather
# than being layered on top of it: two width utilities on one element resolve by
# stylesheet order, not by the order they are written. A circle has none,
# because size-9 already sets both axes.
_SHAPE_WIDTHS: dict[SkeletonShape, str] = {
    "line": "w-full",
    "text": "w-full",
    "circle": "",
    "rect": "w-full",
    "card": "w-full",
}

_SHIMMER = (
    "bg-linear-to-r from-surface-sunken via-surface-active to-surface-sunken "
    "bg-[length:200%_100%] animate-shimmer"
)

# A paragraph does not end flush with the margin, so the last line stops short.
_LAST_LINE_WIDTH = "w-[62%]"


class Skeleton(ChainableComponent):
    """
    A placeholder in the shape of the content that is still loading.

    Each shape carries a default size, which class_() overrides. lines() stacks
    several bars as a paragraph.

    Rendered aria-hidden, so aria-busy belongs on the region it stands in for.

        Skeleton().shape("text").lines(3)
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().shape("text").lines(3)

    def shape(self, value: SkeletonShape) -> Self:
        self._props["shape"] = value
        return self

    def lines(self, value: int) -> Self:
        """
        Stack several bars, the last one short, so they read as a paragraph.
        """
        self._props["lines"] = value
        return self

    def _bar(
        self, shape: SkeletonShape, *, last_of_many: bool = False
    ) -> ComponentType:
        width = _SHAPE_WIDTHS[shape]
        if last_of_many and width:
            width = _LAST_LINE_WIDTH

        return html.div(class_=classnames(_SHIMMER, _SHAPE_CLASSES[shape], width))

    def _render(self, context: HueContext) -> Component:
        shape: SkeletonShape = self._get_prop("shape", "line")
        lines: int = self._get_prop("lines", 1)

        attrs = {"aria_hidden": "true", **self._get_base_html_attrs()}

        if lines > 1:
            return html.div(
                *(
                    self._bar(shape, last_of_many=index == lines - 1)
                    for index in range(lines)
                ),
                class_=classnames("flex flex-col gap-2", self._get_prop("class_")),
                **attrs,
            )

        return html.div(
            class_=classnames(
                _SHIMMER,
                _SHAPE_CLASSES[shape],
                _SHAPE_WIDTHS[shape],
                self._get_prop("class_"),
            ),
            **attrs,
        )
