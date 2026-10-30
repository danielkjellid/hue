from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from htmy import Context, html
from typing_extensions import Self

from hue.types.core import Component, ComponentType
from hue.ui.base import ChainableComponent
from hue.utils import classes_if_else, classnames, render_when

type TextTag = Literal["p", "span", "h1", "h2", "h3", "h4", "h5", "h6", "label"]

_TAGS: dict[TextTag, Callable[..., Component]] = {
    "p": html.p,
    "span": html.span,
    "h1": html.h1,
    "h2": html.h2,
    "h3": html.h3,
    "h4": html.h4,
    "h5": html.h5,
    "h6": html.h6,
    "label": html.label,
}

type TextVariant = Literal[
    "title-1",
    "title-2",
    "title-3",
    "subtitle-1",
    "subtitle-2",
    "body",
]

# A heading tag says where the text sits in the outline, and the base
# heading rule would also restyle it. These take the type a p would inherit
# instead, at zero specificity so the variant and class_() still win.
_HEADING_RESET = "[:where(&)]:[font:inherit] [:where(&)]:[letter-spacing:inherit]"

# Logical sides, so a right-to-left page starts its lines on the right.
type TextAlign = Literal["start", "center", "end", "justify"]

_ALIGN_CLASSES: dict[TextAlign, str] = {
    "start": "text-start",
    "center": "text-center",
    "end": "text-end",
    "justify": "text-justify",
}

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

        Text("Section title").variant("title-3").tag("h2").align("center")
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

    def tag(self, value: TextTag) -> Self:
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

    def _render(self, context: Context) -> Component:
        variant: TextVariant = self._get_prop("variant", "body")
        align: TextAlign = self._get_prop("align", "start")
        muted: bool = self._get_prop("muted", False)
        destructive: bool = self._get_prop("destructive", False)
        tag: TextTag = self._get_prop("tag", "p")

        classes = classnames(
            {_HEADING_RESET: tag.startswith("h")},
            _VARIANT_CLASSES[variant],
            _ALIGN_CLASSES[align],
            {
                # Destructive wins over muted when both are set.
                "text-danger-text": destructive,
                "text-fg-muted": muted and not destructive,
                "text-fg": not muted and not destructive,
            },
            self._get_prop("class_"),
        )

        return _TAGS[tag](
            self._text,
            *self._children,
            class_=classes,
            **self._get_base_html_attrs(),
        )


def required_marker() -> ComponentType:
    """
    The asterisk beside the label of a required field.

    Hidden from assistive tech: the control's own required attribute announces
    it, and an asterisk read aloud as "star" does not.
    """
    return html.span("*", aria_hidden="true", class_="font-normal text-danger-text")


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

    def _render(self, context: Context) -> Component:
        required: bool = self._get_prop("required", False)
        disabled: bool = self._get_prop("disabled", False)
        hidden_label: bool = self._get_prop("hidden_label", False)

        classes = classnames(
            "inline-flex items-center gap-[5px] text-start",
            "font-ui text-sm font-medium leading-[1.4]",
            classes_if_else(
                disabled,
                ["pointer-events-none", "text-fg-disabled"],
                ["cursor-pointer", "text-fg"],
            ),
            {"sr-only": hidden_label},
            self._get_prop("class_"),
        )

        return html.label(
            html.span(self._text),
            render_when(required, required_marker()),
            class_=classes,
            for_=self._get_prop("html_for"),
            **self._get_base_html_attrs(),
        )
