from __future__ import annotations

from typing import Literal

from htmy import Context, html
from typing_extensions import Self

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

    size() and muted() set the appearance. label() names what is loading and
    shows beside the spinner.

        Spinner().label("Loading payments")
    """

    category = "Feedback"

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

    def label(self, value: str, *, visible: bool = True) -> Self:
        """
        Say what is loading, shown beside the spinner and announced with it.
        visible=False keeps it for screen readers only, for a spinner with no
        room for words. Without a label it announces "Loading".
        """
        self._props["label"] = value
        self._props["label_visible"] = visible
        return self

    def _render(self, context: Context) -> Component:
        size: SpinnerSize = self._get_prop("size", "md")
        muted: bool = self._get_prop("muted", False)
        label: str | None = self._get_prop("label")
        visible: bool = label is not None and self._get_prop("label_visible", True)

        # role="status" announces politely without stealing focus. A live
        # region reads the text inside it and ignores its aria-label, so the
        # text is always there, hidden when nothing on screen says it, and the
        # ring is decoration.
        return html.span(
            html.span(
                aria_hidden="true",
                class_=classnames(
                    # flex-none, or a label that wraps squashes it to an oval.
                    "inline-block flex-none rounded-full",
                    "border-current/22 border-t-current",
                    "animate-spinner",
                    _SIZE_CLASSES[size],
                    "text-fg-subtle" if muted else "text-accent",
                ),
            ),
            html.span(
                label or "Loading",
                class_=classnames("text-fg-muted", _LABEL_CLASSES[size])
                if visible
                else "sr-only",
            ),
            class_=classnames(
                "inline-flex items-center gap-2.5", self._get_prop("class_")
            ),
            **{"role": "status", **self._get_base_html_attrs()},
        )
