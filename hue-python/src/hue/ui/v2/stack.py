from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.spacing import SPACE_BETWEEN, Size
from hue.types.core import Component
from hue.types.css import AlignItems, JustifyContent
from hue.ui.v2.base import ChainableComponent
from hue.utils import classnames


class Stack(ChainableComponent):
    """
    A SwiftUI-style chainable flex-container component.

    Example::

        Stack()
            .direction("horizontal")
            .spacing("md")
            .align_items("items-center")
            .content(
                Text("Hello").variant("title-3"),
                Text("World").variant("body"),
            )
    """

    def direction(self, value: Literal["horizontal", "vertical"]) -> Self:
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

    def position(
        self, value: Literal["relative", "absolute", "fixed", "sticky"]
    ) -> Self:
        self._props["position"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        direction: Literal["horizontal", "vertical"] = self._get_prop(
            "direction", "vertical"
        )
        spacing_size: Size = self._get_prop("spacing", "sm")
        justify: JustifyContent = self._get_prop("justify_content", "justify-start")
        align: AlignItems = self._get_prop("align_items", "items-start")
        pos = self._get_prop("position", "relative")

        spacing_x, spacing_y = SPACE_BETWEEN[spacing_size]

        classes = classnames(
            "flex",
            "w-full",
            justify,
            align,
            pos,
            {
                "flex-col": direction == "vertical",
                "flex-row": direction == "horizontal",
            },
            spacing_y if direction == "vertical" else spacing_x,
            self._get_prop("class_"),
        )

        return html.div(
            *self._children,
            class_=classes,
            **self._get_base_html_attrs(),
        )
