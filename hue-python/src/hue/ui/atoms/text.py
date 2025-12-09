from typing import Literal, Type, cast

from htmy import html
from typing_extensions import Unpack

from hue.decorators import function_component
from hue.types.core import BasePropsKwargs, ComponentType
from hue.utils import classnames

__all__ = ["Label", "Text"]

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


@function_component
def Text[T: TextTag](
    text: str,
    *,
    muted: bool = False,
    destructive: bool = False,
    tag: Type[T] | None = None,
    variant: TextVariant = "body",
    role: str | None = None,
    align: TextAlign = "text-left",
    **base_props: Unpack[BasePropsKwargs],
) -> T:
    """
    The text component is a component provides a common interface for displaying text,
    keeping the text structured.
    """

    classes = classnames(
        {
            "text-surface-500": muted and not destructive,
            "text-destructive": destructive,
            "text-surface-900": not muted and not destructive,
        }
    )

    return BaseText(
        text,
        classes=classes,
        tag=tag or html.p,
        variant=variant,
        role=role,
        align=align,
        **base_props,
    )


@function_component
def Label(
    text: str,
    *,
    html_for: str | None = None,
    required: bool = True,
    disabled: bool = False,
    hidden_label: bool = False,
    **base_props: Unpack[BasePropsKwargs],
) -> html.label:
    """
    The label component is a component that adds a label to a form field.
    """
    content: list[html.span] = [html.span(text)]

    if required:
        content.append(html.span("*", class_="text-destructive"))

    classes = classnames(
        {
            "pointer-events-none text-surface-300": disabled,
            "cursor-pointer": not disabled,
            "sr-only": hidden_label,
        },
        "inline-flex items-center gap-1 text-surface-900",
    )

    return BaseText(
        *content,
        classes=classes,
        tag=html.label,
        variant="subtitle-2",
        html_for=html_for,
        align="text-left",
        **base_props,
    )


@function_component
def BaseText[T: TextTag](
    *children: ComponentType,
    classes: str | None = None,
    tag: Type[T] | None = None,
    variant: TextVariant = "body",
    role: str | None = None,
    html_for: str | None = None,
    align: TextAlign = "text-left",
    **base_props: Unpack[BasePropsKwargs],
) -> T:
    """
    The base text component is a component that provides a common interface for
    displaying text, keeping the text structured, with the flexibility to use
    different tags and variants.
    """

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
        classes,
    )

    html_tag: Type[T] = tag or cast(Type[T], html.p)

    return cast(
        T,
        html_tag(
            *children,
            class_=all_classes,
            role=role,
            for_=html_for,
            **base_props,
        ),
    )
