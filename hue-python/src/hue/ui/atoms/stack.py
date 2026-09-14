from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.spacing import SPACE_BETWEEN, Size
from hue.types.core import Component
from hue.types.css import AlignItems, JustifyContent
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type StackDirection = Literal["horizontal", "vertical"]
type StackPosition = Literal["relative", "absolute", "fixed", "sticky"]


class Stack(ChainableComponent):
    """
    A flex container that lays its children out in a row or column.

    direction() picks the axis, spacing() the gap between items,
    justify_content() and align_items() the alignment along each axis, and
    position() the CSS position.

        Stack().direction("horizontal").spacing("md").align_items("items-center")
    """

    category = "Layout"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .direction("horizontal")
            .content(
                html.div("1", class_="size-10 rounded-md bg-primary p-2 text-white"),
                html.div("2", class_="size-10 rounded-md bg-primary p-2 text-white"),
                html.div("3", class_="size-10 rounded-md bg-primary p-2 text-white"),
            )
        )

    def direction(self, value: StackDirection) -> Self:
        self._props["direction"] = value
        return self

    def spacing(self, value: Size) -> Self:
        self._props["spacing"] = value
        return self

    def justify_content(self, value: JustifyContent) -> Self:
        self._props["justify_content"] = value
        return self

    def align_items(self, value: AlignItems) -> Self:
        self._props["align_items"] = value
        return self

    def position(self, value: StackPosition) -> Self:
        self._props["position"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        direction: StackDirection = self._get_prop("direction", "vertical")
        spacing: Size = self._get_prop("spacing", "sm")
        justify: JustifyContent = self._get_prop("justify_content", "justify-start")
        align: AlignItems = self._get_prop("align_items", "items-start")
        position: StackPosition = self._get_prop("position", "relative")

        vertical = direction == "vertical"
        spacing_x, spacing_y = SPACE_BETWEEN[spacing]

        classes = classnames(
            "flex w-full",
            justify,
            align,
            position,
            "flex-col" if vertical else "flex-row",
            spacing_y if vertical else spacing_x,
            self._get_prop("class_"),
        )

        return html.div(*self._children, class_=classes, **self._get_base_html_attrs())
