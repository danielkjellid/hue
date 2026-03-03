from __future__ import annotations

import os
from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.ui.atoms.icon import create_icon_base
from hue.ui.atoms.stack import Stack
from hue.ui.v2.base import ChainableComponent
from hue.utils import classes_if, classnames, render_if

# Re-use the same icon setup as the v1 Callout
_icons_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "icons")
_CalloutIcon = create_icon_base(icons_dir=os.path.abspath(_icons_dir))

type CalloutVariant = Literal[
    "gray",
    "primary",
    "success",
    "info",
    "warning",
    "error",
]


class Callout(ChainableComponent):
    """
    A SwiftUI-style chainable callout component.

    Example::

        Callout()
            .variant("error")
            .title("Oops!")
            .content("Something went wrong.")
    """

    def variant(self, value: CalloutVariant) -> Self:
        self._props["variant"] = value
        return self

    def title(self, value: str) -> Self:
        self._props["title"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: CalloutVariant = self._get_prop("variant", "gray")
        title_text: str | None = self._get_prop("title")

        from dataclasses import dataclass, field

        @dataclass(slots=True, frozen=True, kw_only=True)
        class _InfoIcon(_CalloutIcon):  # type: ignore
            name: Literal["circle-info"] = field(default="circle-info", init=False)

        return html.div(
            Stack(
                _InfoIcon(
                    class_=classnames(
                        "size-4 flex-shrink-0 items-start mt-1",
                        classes_if(variant == "gray", ["text-surface-400"]),
                        classes_if(variant == "primary", ["text-primary"]),
                        classes_if(variant == "info", ["text-wg-blue"]),
                        classes_if(variant == "success", ["text-wg-green"]),
                        classes_if(variant == "error", ["text-wg-red"]),
                        classes_if(variant == "warning", ["text-wg-yellow"]),
                    )
                ),
                Stack(
                    render_if(
                        title_text,
                        lambda t: html.p(
                            t,
                            class_=classnames(
                                "font-medium leading-6",
                                classes_if(
                                    variant in ("gray", "primary"),
                                    ["text-surface-900"],
                                ),
                                classes_if(
                                    variant == "info",
                                    ["text-wg-blue-800", "dark:text-wg-blue"],
                                ),
                                classes_if(
                                    variant == "success",
                                    ["text-wg-green-800", "dark:text-wg-green"],
                                ),
                                classes_if(
                                    variant == "error",
                                    ["text-wg-red-800", "dark:text-wg-red"],
                                ),
                                classes_if(
                                    variant == "warning",
                                    ["text-wg-yellow-800", "dark:text-wg-yellow"],
                                ),
                            ),
                        ),
                    ),
                    html.p(*self._children, class_="max-w-prose"),
                    direction="vertical",
                    spacing="xs",
                ),
                direction="horizontal",
                spacing="sm",
                align_items="items-start",
            ),
            class_=classnames(
                "antialiased flex text-sm leading-6 bg-surface dark:bg-surface",
                "dark:text-surface-500 items-start w-full rounded-lg px-2 py-3 border",
                classes_if(
                    variant == "gray",
                    ["border-surface-200", "text-surface-500"],
                ),
                classes_if(
                    variant == "primary",
                    ["border-primary", "text-surface-500"],
                ),
                classes_if(
                    variant == "success",
                    ["border-wg-green", "bg-wg-green-50", "text-wg-green-700"],
                ),
                classes_if(
                    variant == "info",
                    ["border-wg-blue", "bg-wg-blue-50", "text-wg-blue-700"],
                ),
                classes_if(
                    variant == "warning",
                    ["border-wg-yellow", "bg-wg-yellow-50", "text-wg-yellow-800"],
                ),
                classes_if(
                    variant == "error",
                    ["border-wg-red", "bg-wg-red-50", "text-wg-red-700"],
                ),
            ),
            **self._get_base_html_attrs(),
        )
