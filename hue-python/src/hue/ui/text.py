from __future__ import annotations

from typing import Literal, Type, cast

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classnames

type TextTag = (
    html.p
    | html.span
    | html.h1
    | html.h2
    | html.h3
    | html.h4
    | html.h5
    | html.h6
    | html.label
)

type TextVariant = Literal[
    "title-1",
    "title-2",
    "title-3",
    "subtitle-1",
    "subtitle-2",
    "body",
]

type TextAlign = Literal["text-left", "text-center", "text-right"]


class Text(ChainableComponent):
    """
    A SwiftUI-style chainable text component.

    Example::

        Text("Hello world")
            .variant("title-3")
            .tag(html.h1)
            .align("text-center")
            .muted()
    """

    def __init__(self, text: str = "") -> None:
        super().__init__()
        self._text = text

    def variant(self, value: TextVariant) -> Self:
        self._props["variant"] = value
        return self

    def tag(self, value: Type[TextTag]) -> Self:
        self._props["tag"] = value
        return self

    def align(self, value: TextAlign) -> Self:
        self._props["align"] = value
        return self

    def muted(self, value: bool = True) -> Self:
        self._props["muted"] = value
        return self

    def destructive(self, value: bool = True) -> Self:
        self._props["destructive"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        variant: TextVariant = self._get_prop("variant", "body")
        align: TextAlign = self._get_prop("align", "text-left")
        muted: bool = self._get_prop("muted", False)
        destructive: bool = self._get_prop("destructive", False)
        html_tag: Type[TextTag] = self._get_prop("tag", html.p)

        color_classes = classnames(
            {
                "text-surface-500": muted and not destructive,
                "text-destructive": destructive,
                "text-surface-900": not muted and not destructive,
            },
        )

        all_classes = classnames(
            {
                "text-5xl font-bold": variant == "title-1",
                "text-3xl font-bold": variant == "title-2",
                "text-2xl": variant == "title-3",
                "text-base font-medium": variant == "subtitle-1",
                "text-sm font-medium leading-6": variant == "subtitle-2",
                "text-sm leading-6": variant == "body",
            },
            {
                "text-center": align == "text-center",
                "text-right": align == "text-right",
                "text-left": align == "text-left",
            },
            color_classes,
            self._get_prop("class_"),
        )

        return cast(
            Component,
            html_tag(
                self._text,
                *self._children,
                class_=all_classes,
                **self._get_base_html_attrs(),
            ),
        )


class Label(ChainableComponent):
    """
    A SwiftUI-style chainable label component.

    Example::

        Label("Email")
            .html_for("email-input")
            .required()
            .hidden_label()
    """

    def __init__(self, text: str = "") -> None:
        super().__init__()
        self._text = text

    def html_for(self, value: str) -> Self:
        self._props["html_for"] = value
        return self

    def required(self, value: bool = True) -> Self:
        self._props["required"] = value
        return self

    def disabled(self, value: bool = True) -> Self:
        self._props["disabled"] = value
        return self

    def hidden_label(self, value: bool = True) -> Self:
        self._props["hidden_label"] = value
        return self

    def _render(self, context: HueContext) -> Component:
        required: bool = self._get_prop("required", True)
        disabled: bool = self._get_prop("disabled", False)
        hidden_label: bool = self._get_prop("hidden_label", False)

        content: list[ComponentType] = [html.span(self._text)]

        if required:
            content.append(html.span("*", class_="text-destructive"))

        classes = classnames(
            {
                "pointer-events-none text-surface-300": disabled,
                "cursor-pointer": not disabled,
                "sr-only": hidden_label,
            },
            "inline-flex items-center gap-1 text-surface-900",
            # Label variant is always subtitle-2
            "text-sm font-medium leading-6",
            {
                "text-left": True,
            },
            self._get_prop("class_"),
        )

        return html.label(
            *content,
            class_=classes,
            for_=self._get_prop("html_for"),
            **self._get_base_html_attrs(),
        )
