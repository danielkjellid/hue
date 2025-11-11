from typing import Literal, Type, cast

from htmy import html

from hue.types.core import ComponentType
from hue.utils import concatenate_classes

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


def Text[T: TextTag](
    *children: ComponentType,
    muted: bool = False,
    destructive: bool = False,
    tag: Type[T] | None = None,
    variant: TextVariant = "body",
    role: str | None = None,
    align: TextAlign = "text-left",
) -> T:
    """
    The text component is a component provides a common interface for displaying text,
    keeping the text structured.
    """

    classes = _get_text_classes(muted, destructive)

    return BaseText(
        *[str(child) for child in children],
        classes=classes,
        tag=tag or html.p,
        variant=variant,
        role=role,
        align=align,
    )


def _get_text_classes(muted: bool, destructive: bool) -> list[str]:
    """
    The _get_text_classes function is a helper function that returns a list of
    classes for the text component.
    """
    if muted and not destructive:
        return ["text-surface-500"]
    elif destructive:
        return ["text-destructive"]
    else:
        return ["text-surface-900"]


def Label(
    text: str,
    *,
    html_for: str | None = None,
    required: bool = True,
    disabled: bool = False,
    hidden_label: bool = False,
) -> html.label:
    """
    The label component is a component that adds a label to a form field.
    """
    classes = _get_label_classes(disabled=disabled, hidden_label=hidden_label)
    content: list[ComponentType] = [html.span(text)]

    if required:
        content.append(html.span("*", class_="text-destructive"))

    return BaseText(
        *content,
        classes=classes,
        tag=html.label,
        variant="subtitle-2",
        html_for=html_for,
        align="text-left",
    )


def _get_label_classes(disabled: bool, hidden_label: bool) -> list[str]:
    """
    The _get_label_classes function is a helper function that returns a list of
    classes for the label component.
    """
    classes = [
        "inline-flex",
        "items-center",
        "gap-1",
        "text-surface-900",
    ]

    if disabled:
        classes.extend(["pointer-events-none", "text-surface-300"])

    else:
        classes.extend(["cursor-pointer"])

    if hidden_label:
        classes.extend(["sr-only"])

    return classes


def BaseText[T: TextTag](
    *children: ComponentType,
    classes: list[str] | None = None,
    tag: Type[T] | None = None,
    variant: TextVariant = "body",
    role: str | None = None,
    html_for: str | None = None,
    align: TextAlign = "text-left",
) -> T:
    """
    The base text component is a component that provides a common interface for
    displaying text, keeping the text structured, with the flexibility to use
    different tags and variants.
    """

    formatted_classes = _get_base_text_classes(
        variant=variant,
        additional_classes=classes,
        align=align,
    )

    html_tag: Type[T] = tag or cast(Type[T], html.p)

    return cast(
        T,
        html_tag(
            *children,
            class_=formatted_classes,
            role=role,
            for_=html_for,
        ),
    )


def _get_base_text_classes(
    *,
    variant: TextVariant,
    additional_classes: list[str] | None = None,
    align: TextAlign = "text-left",
) -> str:
    """
    The _get_base_text_classes function is a helper function that returns a list of
    classes for the base text component.
    """
    variant_classes: dict[TextVariant, list[str]] = {
        "title-1": ["text-5xl", "font-bold"],
        "title-2": ["text-3xl", "font-bold"],
        "title-3": ["text-2xl"],
        "subtitle-1": ["text-base", "font-medium"],
        "subtitle-2": ["text-sm", "font-medium", "leading-6"],
        "body": ["text-sm", "leading-6"],
    }

    align_classes: dict[TextAlign, list[str]] = {
        "text-center": ["text-center"],
        "text-right": ["text-right"],
        "text-left": ["text-left"],
    }

    classes = (
        variant_classes[variant] + align_classes[align] + (additional_classes or [])
    )
    return concatenate_classes(classes)
