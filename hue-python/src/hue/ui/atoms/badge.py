from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type BadgeVariant = Literal[
    "neutral",
    "accent",
    "success",
    "warning",
    "danger",
    "info",
    "solid",
]
type BadgeSize = Literal["md", "lg"]
type BadgeShape = Literal["rounded", "pill"]

# Keyed by the Literal so mypy keeps the map exhaustive when a variant is added.
_VARIANT_CLASSES: dict[BadgeVariant, str] = {
    "neutral": "bg-surface-sunken border-border text-fg-muted",
    "accent": "bg-accent-subtle border-accent-border text-accent-text",
    "success": "bg-success-subtle border-success-border text-success-text",
    "warning": "bg-warning-subtle border-warning-border text-warning-text",
    "danger": "bg-danger-subtle border-danger-border text-danger-text",
    "info": "bg-info-subtle border-info-border text-info-text",
    "solid": "bg-fg border-fg text-canvas",
}

_HEIGHT_CLASSES: dict[BadgeSize, str] = {"md": "h-5", "lg": "h-6"}
_FONT_CLASSES: dict[BadgeSize, str] = {"md": "text-xs", "lg": "text-sm"}
_PADDING_CLASSES: dict[BadgeSize, str] = {"md": "px-[7px]", "lg": "px-[9px]"}


class Badge(ChainableComponent):
    """
    A small status label.

    Colour never carries the meaning on its own - every badge has a text label,
    and dot() adds a coloured dot that repeats what the label already says. At
    12px that pairing reads faster than a fully tinted pill, which is why it is
    the usual choice in a table.

    If a badge is coloured because the colour looks nice, it should be neutral:
    a table where every row is tinted has taught the reader to ignore colour.

        Badge().variant("success").dot().content("Active")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().variant("success").dot().content("Active")

    def variant(self, value: BadgeVariant) -> Self:
        self._props["variant"] = value
        return self

    def size(self, value: BadgeSize) -> Self:
        self._props["size"] = value
        return self

    def shape(self, value: BadgeShape) -> Self:
        self._props["shape"] = value
        return self

    def dot(self, value: bool = True) -> Self:
        """
        Prefix a coloured dot, reinforcing the label rather than replacing it.
        """
        self._props["dot"] = value
        return self

    def numeric(self, value: bool = True) -> Self:
        """
        Line the figures up on a shared width, for counts in a column.
        """
        self._props["numeric"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: BadgeVariant = self._get_prop("variant", "neutral")
        size: BadgeSize = self._get_prop("size", "md")
        shape: BadgeShape = self._get_prop("shape", "rounded")
        dot: bool = self._get_prop("dot", False)
        numeric: bool = self._get_prop("numeric", False)

        children: tuple[ComponentType, ...] = self._children
        if dot:
            children = (
                html.span(
                    # currentColor, so the dot needs no per-variant rule.
                    class_="size-1.5 shrink-0 rounded-full bg-current",
                    aria_hidden="true",
                ),
                *children,
            )

        return html.span(
            *children,
            class_=classnames(
                "inline-flex items-center gap-[5px] whitespace-nowrap",
                "border font-ui font-semibold leading-none",
                _HEIGHT_CLASSES[size],
                _FONT_CLASSES[size],
                _VARIANT_CLASSES[variant],
                # A pill's wider padding wins over the size's, so the two are
                # picked here rather than left to fight in the class list.
                "rounded-full px-[9px]" if shape == "pill" else "rounded-sm",
                "" if shape == "pill" else _PADDING_CLASSES[size],
                "tabular-nums" if numeric else "",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
