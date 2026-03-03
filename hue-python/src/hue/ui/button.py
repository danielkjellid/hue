from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.types.html import AriaHasPopup
from hue.ui.atoms.button import (
    ButtonSize,
    ButtonShape,
    ButtonVariant,
    _get_base_button_classes,
)
from hue.ui.base import ChainableComponent
from hue.utils import classnames


class Button(ChainableComponent):
    """
    A SwiftUI-style chainable button component.

    Example::

        Button()
            .variant("primary")
            .size("md")
            .disabled(True)
            .content(Text("Click me"))
    """

    def variant(self, value: ButtonVariant) -> Self:
        self._props["variant"] = value
        return self

    def size(self, value: ButtonSize) -> Self:
        self._props["size"] = value
        return self

    def shape(self, value: ButtonShape) -> Self:
        self._props["shape"] = value
        return self

    def fluid(self, value: bool = True) -> Self:
        self._props["fluid"] = value
        return self

    def type(self, value: Literal["button", "submit", "reset"]) -> Self:
        self._props["type"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def aria_haspopup(self, value: AriaHasPopup) -> Self:
        self._props["aria_haspopup"] = value
        return self

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, context: HueContext) -> Component:
        variant: ButtonVariant = self._get_prop("variant", "primary")
        size: ButtonSize = self._get_prop("size", "md")
        shape: ButtonShape = self._get_prop("shape", "rounded")
        fluid: bool = self._get_prop("fluid", True)

        classes = classnames(
            _get_base_button_classes(
                fluid=fluid,
                shape=shape,
                variant=variant,
                size=size,
            ),
            self._get_prop("class_"),
        )

        return html.button(
            *self._children,
            class_=classes,
            tabindex="0",
            type=self._get_prop("type", "button"),
            disabled=self._get_prop("disabled"),
            aria_haspopup=self._get_prop("aria_haspopup"),
            **self._get_base_html_attrs(),
        )
