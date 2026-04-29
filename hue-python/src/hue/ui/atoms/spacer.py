from __future__ import annotations

from htmy import html

from hue.context import HueContext
from hue.spacing import MARGIN, Size
from hue.types.core import Component
from hue.ui.base import ChainableComponent


class Spacer(ChainableComponent):
    """
    A SwiftUI-style chainable spacer component.

    Example::

        Spacer("lg")
        # or
        Spacer().spacing("lg")
    """

    def __init__(self, spacing: Size = "sm") -> None:
        super().__init__()
        self._props["spacing"] = spacing

    def spacing(self, value: Size) -> "Spacer":
        self._props["spacing"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        spacing: Size = self._get_prop("spacing", "sm")
        _top, _right, bottom, _left = MARGIN[spacing]
        return html.div(class_=bottom)
