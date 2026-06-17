from __future__ import annotations

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.spacing import MARGIN, Size
from hue.types.core import Component
from hue.ui.base import ChainableComponent


class Spacer(ChainableComponent):
    """
    Fixed empty space between elements.

    Renders an empty ``<div>`` whose bottom margin creates a gap of the chosen
    ``.spacing()`` size — a way to separate elements without adding margins to
    them directly.

    Note: because it is a real ``<div>``, the spacer takes up space in the DOM
    whether or not it is visible. Inside a flex container that already defines
    spacing between its children this can cause layout issues.

    Example::

        Stack().content(
            Text("Above"),
            Spacer().spacing("lg"),
            Text("Below"),
        )
    """

    @classmethod
    def example(cls) -> Self:
        """A representative instance, used by the docs site for previews."""
        return cls().spacing("md")

    def spacing(self, value: Size) -> Self:
        self._props["spacing"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        spacing: Size = self._get_prop("spacing", "sm")
        _top, _right, bottom, _left = MARGIN[spacing]
        return html.div(class_=bottom, **self._get_base_html_attrs())
