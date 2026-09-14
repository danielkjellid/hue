from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type PanelPadding = Literal["md", "sm", "none"]

_PADDING_CLASSES: dict[PanelPadding, str] = {
    "md": "p-6",
    "sm": "p-4",
    # For content that brings its own edges, such as a table.
    "none": "p-0",
}


class Panel(ChainableComponent):
    """
    A bordered frame with a labelled bar along the top.

    label() and hint() fill the two ends of that bar, and the bar only appears
    when one of them is set. padding() sizes the body and sunken() tints it.

        Panel().label("Variants").hint("Never colour alone").content(...)
    """

    category = "Layout"

    @classmethod
    def example(cls) -> Self:
        return (
            cls()
            .label("Interaction ladder")
            .hint("Tab through these")
            .content("Panel content")
        )

    def label(self, value: str) -> Self:
        self._props["label"] = value
        return self

    def hint(self, value: str) -> Self:
        """
        A quieter note at the far end of the bar, opposite the label.
        """
        self._props["hint"] = value
        return self

    def padding(self, value: PanelPadding) -> Self:
        self._props["padding"] = value
        return self

    def sunken(self, value: bool = True) -> Self:
        """
        Tint the body, so that whatever sits on it reads as raised.
        """
        self._props["sunken"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        label: str | None = self._get_prop("label")
        hint: str | None = self._get_prop("hint")
        padding: PanelPadding = self._get_prop("padding", "md")
        sunken: bool = self._get_prop("sunken", False)

        children: list[ComponentType] = []

        if label is not None or hint is not None:
            children.append(
                html.div(
                    html.span(
                        label or "",
                        class_="font-ui text-xs font-semibold text-fg-muted",
                    ),
                    html.span(hint or "", class_="text-2xs text-fg-subtle"),
                    class_=classnames(
                        "flex items-center justify-between gap-3",
                        "border-b border-border bg-surface-sunken px-4 py-[7px]",
                    ),
                )
            )

        children.append(
            html.div(
                *self._children,
                class_=classnames(
                    _PADDING_CLASSES[padding],
                    # The page ground rather than surface-sunken, which the
                    # name suggests: the body has to recede past the frame it
                    # sits in, and the bar above already owns surface-sunken.
                    "bg-canvas-subtle" if sunken else "",
                ),
            )
        )

        return html.div(
            *children,
            class_=classnames(
                "overflow-hidden rounded-lg border border-border bg-surface",
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
