from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type SkeletonShape = Literal["text", "circle", "rect", "card"]

# Each shape carries the size it usually stands in for, so a skeleton is one
# call. Override either axis with class_() when the real content differs.
# Each axis is kept apart so width() and height() can replace one outright.
# Layering a second width over the shape's own would leave two utilities
# resolved by stylesheet order rather than by what the caller asked for.
_SHAPE_HEIGHTS: dict[SkeletonShape, str] = {
    "text": "h-3.5",
    "circle": "h-9",
    "rect": "h-9",
    "card": "h-32",
}

_SHAPE_WIDTHS: dict[SkeletonShape, str] = {
    "text": "w-full",
    "circle": "w-9",
    "rect": "w-full",
    "card": "w-full",
}

_SHAPE_RADII: dict[SkeletonShape, str] = {
    "text": "rounded-xs",
    "circle": "rounded-full",
    "rect": "rounded-md",
    "card": "rounded-lg",
}

_SHIMMER = (
    "bg-linear-to-r from-surface-active via-border-strong to-surface-active "
    "bg-[length:200%_100%] animate-shimmer"
)

# A paragraph does not end flush with the margin, so the last line stops short.
_LAST_LINE_WIDTH = "w-[62%]"


class Skeleton(ChainableComponent):
    """
    A placeholder in the shape of the content that is still loading.

    Every shape carries the size it usually stands in for, and width() and
    height() replace either one when the real content differs. lines() is the
    one shape-specific control: it stacks text bars into a paragraph, and means
    nothing for the others.

    Rendered aria-hidden, so aria-busy belongs on the region it stands in for.

        Skeleton().shape("text").lines(3)
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        # Deliberately without lines(): the docs render this example under every
        # shape, and a paragraph of circles is exactly what lines() rejects.
        return cls().shape("text")

    def shape(self, value: SkeletonShape) -> Self:
        self._props["shape"] = value
        return self

    def width(self, value: str) -> Self:
        """
        Replace the shape's width with a Tailwind class, e.g. "w-1/2".
        """
        self._props["width"] = value
        return self

    def height(self, value: str) -> Self:
        """
        Replace the shape's height with a Tailwind class, e.g. "h-20".
        """
        self._props["height"] = value
        return self

    def lines(self, value: int) -> Self:
        """
        Stack several text bars, the last one short, so they read as a
        paragraph. Only text has lines; the other shapes are single things.
        """
        self._props["lines"] = value
        return self

    def _box(self, shape: SkeletonShape, *, last_of_many: bool = False) -> str:
        """
        Height, width and radius, each chosen once.
        """
        width = self._get_prop("width") or _SHAPE_WIDTHS[shape]
        if last_of_many:
            width = _LAST_LINE_WIDTH

        return classnames(
            self._get_prop("height") or _SHAPE_HEIGHTS[shape],
            width,
            _SHAPE_RADII[shape],
        )

    def _bar(
        self, shape: SkeletonShape, *, last_of_many: bool = False
    ) -> ComponentType:
        return html.div(
            class_=classnames(_SHIMMER, self._box(shape, last_of_many=last_of_many))
        )

    def _render(self, context: HueContext) -> Component:
        shape: SkeletonShape = self._get_prop("shape", "text")
        lines: int = self._get_prop("lines", 1)

        if lines > 1 and shape != "text":
            raise ValueError(
                f"lines() stacks a paragraph of text bars, so it does not apply "
                f"to a {shape!r} skeleton - three circles on top of each other "
                f"stand in for nothing. Repeat the skeleton itself if you need "
                f"several."
            )

        attrs = {"aria_hidden": "true", **self._get_base_html_attrs()}

        if lines > 1:
            return html.div(
                *(
                    self._bar(shape, last_of_many=index == lines - 1)
                    for index in range(lines)
                ),
                # w-full because the bars inside are too: a percentage width
                # resolves to nothing against a wrapper that is itself sized by
                # its content, so in any flex row the whole stack collapsed.
                class_=classnames(
                    "flex w-full flex-col gap-2", self._get_prop("class_")
                ),
                **attrs,
            )

        return html.div(
            class_=classnames(_SHIMMER, self._box(shape), self._get_prop("class_")),
            **attrs,
        )
