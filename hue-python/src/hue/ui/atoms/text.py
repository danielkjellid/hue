from __future__ import annotations

from typing import Literal, cast

from htmy import html
from typing_extensions import Self

from hue.context import HueContext
from hue.types.core import UNDEFINED, Component
from hue.ui.base import ChainableComponent
from hue.utils import classes_if_else, classnames

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

# The values double as the Tailwind classes they apply.
type TextAlign = Literal["text-left", "text-center", "text-right"]

_VARIANT_CLASSES: dict[TextVariant, str] = {
    "title-1": "text-5xl font-bold",
    "title-2": "text-3xl font-bold",
    "title-3": "text-2xl",
    "subtitle-1": "text-base font-medium",
    "subtitle-2": "text-sm font-medium leading-6",
    "body": "text-sm leading-6",
}


class Text(ChainableComponent):
    """
    A run of text rendered with a typographic style.

    Renders inside a configurable tag (p by default; also span, h1 to h6 and
    label) using one of the design system's type scales via variant(). align()
    controls alignment and muted() / destructive() set the colour.

        Text("Section title").variant("title-3").tag(html.h2).align("text-center")
    """

    category = "Typography"

    def __init__(self, text: str = "") -> None:
        super().__init__()
        self._text = text

    @classmethod
    def example(cls) -> Self:
        return cls("The quick brown fox")

    def variant(self, value: TextVariant) -> Self:
        self._props["variant"] = value
        return self

    def tag(self, value: type[TextTag]) -> Self:
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
        html_tag: type[TextTag] = self._get_prop("tag", html.p)

        classes = classnames(
            _VARIANT_CLASSES[variant],
            align,
            {
                # Destructive wins over muted when both are set.
                "text-destructive": destructive,
                "text-surface-500": muted and not destructive,
                "text-surface-900": not muted and not destructive,
            },
            self._get_prop("class_"),
        )

        return cast(
            Component,
            html_tag(
                self._text,
                *self._children,
                class_=classes,
                **self._get_base_html_attrs(),
            ),
        )


class Label(ChainableComponent):
    """
    A label for a form control.

    Renders the label text, optionally followed by a required-field asterisk.
    Use html_for() to link it to a control's id, disabled() to style it as
    disabled, and hidden_label() to keep it visually hidden but available to
    screen readers.

        Label("Email").html_for("email-input").required()
    """

    category = "Typography"

    def __init__(self, text: str = "") -> None:
        super().__init__()
        self._text = text

    @classmethod
    def example(cls) -> Self:
        return cls("Email")

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
        required: bool = self._get_prop("required", False)
        disabled: bool = self._get_prop("disabled", False)
        hidden_label: bool = self._get_prop("hidden_label", False)

        classes = classnames(
            # Labels always use the subtitle-2 scale.
            "inline-flex items-center gap-1 text-left text-sm font-medium leading-6",
            classes_if_else(
                disabled,
                ["pointer-events-none", "text-surface-300"],
                ["cursor-pointer", "text-surface-900"],
            ),
            {"sr-only": hidden_label},
            self._get_prop("class_"),
        )

        return html.label(
            html.span(self._text),
            html.span("*", class_="text-destructive") if required else UNDEFINED,
            class_=classes,
            for_=self._get_prop("html_for"),
            **self._get_base_html_attrs(),
        )
