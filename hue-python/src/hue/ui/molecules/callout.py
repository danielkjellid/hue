from __future__ import annotations

from typing import Literal, NamedTuple

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.icon import HueIcon
from hue.ui.atoms.stack import Stack
from hue.ui.base import ChainableComponent
from hue.utils import classnames, render_if

type CalloutVariant = Literal[
    "gray",
    "primary",
    "success",
    "info",
    "warning",
    "error",
]


class _Variant(NamedTuple):
    icon: str
    icon_classes: str
    title_classes: str
    box_classes: str


# Keyed by the Literal so mypy keeps the map exhaustive. Each variant gets its
# own icon so the meaning is not conveyed by colour alone.
_VARIANTS: dict[CalloutVariant, _Variant] = {
    "gray": _Variant(
        icon="circle-info",
        icon_classes="text-surface-400",
        title_classes="text-surface-900",
        box_classes="border-surface-200 bg-surface-50 text-surface-500",
    ),
    "primary": _Variant(
        icon="circle-info",
        icon_classes="text-primary",
        title_classes="text-surface-900",
        box_classes="border-primary bg-surface-50 text-surface-500",
    ),
    "info": _Variant(
        icon="circle-info",
        icon_classes="text-wg-blue",
        title_classes="text-wg-blue-800 dark:text-wg-blue",
        box_classes="border-wg-blue bg-wg-blue-50 text-wg-blue-700",
    ),
    "success": _Variant(
        icon="circle-check",
        icon_classes="text-wg-green",
        title_classes="text-wg-green-800 dark:text-wg-green",
        box_classes="border-wg-green bg-wg-green-50 text-wg-green-700",
    ),
    "warning": _Variant(
        icon="triangle-alert",
        icon_classes="text-wg-yellow",
        title_classes="text-wg-yellow-800 dark:text-wg-yellow",
        box_classes="border-wg-yellow bg-wg-yellow-50 text-wg-yellow-800",
    ),
    "error": _Variant(
        icon="circle-x",
        icon_classes="text-wg-red",
        title_classes="text-wg-red-800 dark:text-wg-red",
        box_classes="border-wg-red bg-wg-red-50 text-wg-red-700",
    ),
}


class Callout(ChainableComponent):
    """
    A boxed, coloured message that draws attention to a piece of content.

    Renders an icon, an optional title() and the body content inside a bordered
    box whose colour and icon are set by variant(). Use it for inline notices,
    hints and errors.

        Callout().variant("error").title("Oops!").content("Something went wrong.")
    """

    category = "Feedback"

    @classmethod
    def example(cls) -> Self:
        return cls().title("Heads up").content("This is a callout message.")

    def variant(self, value: CalloutVariant) -> Self:
        self._props["variant"] = value
        return self

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: CalloutVariant = self._get_prop("variant", "gray")
        title_text: str | None = self._get_prop("title")
        style = _VARIANTS[variant]

        return html.div(
            Stack()
            .direction("horizontal")
            .spacing("sm")
            .align_items("items-start")
            .content(
                HueIcon(style.icon).class_(
                    classnames("size-4 shrink-0 mt-1", style.icon_classes)
                ),
                Stack()
                .direction("vertical")
                .spacing("xs")
                .content(
                    render_if(
                        title_text,
                        lambda t: html.p(
                            t,
                            class_=classnames(
                                "font-medium leading-6", style.title_classes
                            ),
                        ),
                    ),
                    # A div rather than a p, so block children stay valid HTML.
                    html.div(*self._children, class_="max-w-prose"),
                ),
            ),
            class_=classnames(
                "antialiased flex text-sm leading-6 dark:text-surface-500",
                "items-start w-full rounded-lg px-2 py-3 border",
                style.box_classes,
                self._get_prop("class_"),
            ),
            **self._get_base_html_attrs(),
        )
