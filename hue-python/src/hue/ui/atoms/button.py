from __future__ import annotations

from typing import Literal

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component
from hue.types.html import AriaHasPopup
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type ButtonVariant = Literal[
    "primary",
    "secondary",
    "tertiary",
    "quaternary",
    "outline",
    "transparent",
    "primary-destructive",
    "secondary-destructive",
    "tertiary-destructive",
    "outline-destructive",
    "transparent-destructive",
]
type ButtonSize = Literal["xs-icon", "sm", "md", "lg"]
type ButtonShape = Literal["rounded", "pill"]
type ButtonType = Literal["button", "submit", "reset"]

# Keyed by the Literal so mypy keeps the map exhaustive when a variant is added.
_VARIANT_CLASSES: dict[ButtonVariant, str] = {
    "primary": (
        "bg-primary text-white outline-primary hover:bg-primary-600 disabled:opacity-50"
    ),
    "secondary": (
        "bg-secondary text-white outline-secondary hover:bg-secondary-700 "
        "disabled:bg-secondary-200 dark:text-secondary-900 "
        "dark:hover:bg-secondary-800 dark:disabled:text-wg-white-500"
    ),
    "tertiary": (
        "bg-surface text-surface-900 outline-surface hover:bg-surface-100 "
        "disabled:text-surface-300"
    ),
    "quaternary": (
        "bg-surface-200 text-surface-900 outline-surface hover:bg-surface-300 "
        "disabled:text-surface-300"
    ),
    "outline": (
        "border border-surface-200 shadow-xs dark:shadow-none hover:bg-surface "
        "disabled:border-surface-50 dark:border-surface-100 text-surface-900 "
        "outline-primary disabled:text-surface-300"
    ),
    "transparent": (
        "bg-transparent hover:bg-surface text-surface-900 outline-primary "
        "disabled:text-surface-300"
    ),
    "primary-destructive": (
        "bg-destructive text-white outline-destructive hover:bg-destructive-600 "
        "disabled:bg-destructive"
    ),
    "secondary-destructive": (
        "bg-destructive text-white outline-destructive hover:bg-destructive-600 "
        "disabled:bg-destructive disabled:opacity-50 dark:text-white "
        "dark:hover:bg-destructive-600 dark:disabled:text-white"
    ),
    "tertiary-destructive": (
        "bg-destructive-50 hover:bg-destructive-100 disabled:bg-destructive-50 "
        "dark:bg-surface-100 dark:hover:bg-surface-200 text-destructive-700 "
        "outline-destructive disabled:text-destructive-300 "
        "dark:text-destructive-500 dark:disabled:text-destructive/50"
    ),
    "outline-destructive": (
        "border-destructive hover:bg-destructive-50 disabled:border-destructive-100 "
        "dark:border-destructive dark:hover:bg-surface "
        "dark:disabled:border-destructive-900 text-destructive-700 outline "
        "outline-destructive disabled:text-destructive-300 "
        "dark:text-destructive-500 dark:disabled:text-destructive/50"
    ),
    "transparent-destructive": (
        "hover:bg-destructive-50 dark:hover:bg-surface text-destructive-700 "
        "outline-destructive disabled:text-destructive-300 "
        "dark:text-destructive-500 dark:disabled:text-destructive/50"
    ),
}

_SIZE_CLASSES: dict[ButtonSize, str] = {
    "xs-icon": "gap-0 p-1",
    "sm": "gap-0 p-1",
    "md": "gap-1 p-2",
    "lg": "gap-1 p-3",
}

_SHAPE_CLASSES: dict[ButtonShape, str] = {
    "rounded": "rounded-lg",
    "pill": "rounded-full",
}


class Button(ChainableComponent):
    """
    A clickable button styled with the design system.

    The appearance is driven by variant(), size() and shape(). fluid() fills the
    available width, type() sets the button type and disabled() disables it.
    Children become the button's content.

        Button().variant("primary").size("md").content(Text("Save"))
    """

    category = "Actions"

    @classmethod
    def example(cls) -> Self:
        return cls().fluid(False).content("Button")

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

    def type(self, value: ButtonType) -> Self:
        self._props["type"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def aria_haspopup(self, value: AriaHasPopup) -> Self:
        self._attrs["aria_haspopup"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: ButtonVariant = self._get_prop("variant", "primary")
        size: ButtonSize = self._get_prop("size", "md")
        shape: ButtonShape = self._get_prop("shape", "rounded")
        fluid: bool = self._get_prop("fluid", True)
        disabled: bool = self._get_prop("disabled", False)

        classes = classnames(
            "group inline-flex select-none items-center justify-center cursor-pointer",
            "text-sm font-medium leading-6 transition-colors duration-100 antialiased",
            "focus:outline-0 focus-visible:outline focus-visible:outline-2",
            "focus-visible:outline-offset-2 disabled:pointer-events-none",
            _SHAPE_CLASSES[shape],
            _SIZE_CLASSES[size],
            _VARIANT_CLASSES[variant],
            "w-full" if fluid else "w-fit",
            self._get_prop("class_"),
        )

        return html.button(
            *self._children,
            class_=classes,
            type=self._get_prop("type", "button"),
            # Boolean attributes are true by presence, so False must omit it.
            disabled=disabled or None,
            **self._get_base_html_attrs(),
        )
