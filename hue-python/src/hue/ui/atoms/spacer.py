from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.spacing import MARGIN, Size
from hue.types.core import Component
from hue.ui.base import ChainableComponent
from hue.utils import classnames


class Spacer(ChainableComponent):
    """
    Fixed empty space between elements.

    Renders an empty div whose bottom margin creates a gap of the chosen
    spacing() size, so elements can be separated without adding margins to them
    directly.

    Note: because it is a real div, the spacer takes up space in the DOM whether
    or not it is visible. Inside a flex container that already defines spacing
    between its children this can cause layout issues.

        Stack().content(Text("Above"), Spacer().spacing("lg"), Text("Below"))
    """

    category = "Layout"

    @classmethod
    def example(cls) -> Self:
        return cls().spacing("md")

    def spacing(self, value: Size) -> Self:
        self._props["spacing"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        spacing: Size = self._get_prop("spacing", "sm")
        return html.div(
            class_=classnames(MARGIN[spacing].bottom, self._get_prop("class_")),
            **self._get_base_html_attrs(),
        )
