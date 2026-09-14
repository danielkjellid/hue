from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type SpinnerSize = Literal["xs", "sm", "md", "lg"]

_SIZE_CLASSES: dict[SpinnerSize, str] = {
    "xs": "size-3 border-[1.5px]",
    "sm": "size-4 border-2",
    "md": "size-5 border-2",
    "lg": "size-8 border-[3px]",
}

_LABEL_CLASSES: dict[SpinnerSize, str] = {
    "xs": "text-xs",
    "sm": "text-sm",
    "md": "text-sm",
    "lg": "text-base",
}


class Spinner(ChainableComponent):
    """
    An indeterminate busy indicator.

    size() and muted() set the appearance. label() names what is loading: it
    shows beside the spinner and takes over the live region, so the ring itself
    stops being announced.

        Spinner().label("Loading payments")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().label("Loading payments")

    def size(self, value: SpinnerSize) -> Self:
        self._props["size"] = value
        return self

    def muted(self, value: bool = True) -> Self:
        """
        Drop the accent for somewhere the spinner should not be the loudest
        thing, such as beside body text or inside a toast.
        """
        self._props["muted"] = value
        return self

    def label(self, value: str) -> Self:
        """
        Say what is loading, shown beside the spinner and announced with it.
        """
        self._props["label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        size: SpinnerSize = self._get_prop("size", "md")
        muted: bool = self._get_prop("muted", False)
        label: str | None = self._get_prop("label")

        circle_classes = classnames(
            "inline-block rounded-full border-current/22 border-t-current",
            "animate-spinner",
            _SIZE_CLASSES[size],
            "text-fg-subtle" if muted else "text-accent",
        )

        # role="status" announces politely without stealing focus. It has to be
        # on the element that holds the text, and the ring itself is decoration
        # once a label says what is happening.
        if label is not None:
            return html.span(
                html.span(class_=circle_classes, aria_hidden="true"),
                html.span(
                    label, class_=classnames("text-fg-muted", _LABEL_CLASSES[size])
                ),
                class_=classnames(
                    "inline-flex items-center gap-2.5",
                    self._get_prop("class_"),
                ),
                **{"role": "status", **self._get_base_html_attrs()},
            )

        return html.span(
            class_=classnames(circle_classes, self._get_prop("class_")),
            **{
                "role": "status",
                "aria_label": "Loading",
                **self._get_base_html_attrs(),
            },
        )
