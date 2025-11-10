from typing import Literal, Type

from htmy import html

from hue.decorators import concatenate_classes
from hue.types.core import ComponentType

__all__ = ["Label", "Text"]

TextTag = (
    Type[html.p]
    | Type[html.span]
    | Type[html.h1]
    | Type[html.h2]
    | Type[html.h3]
    | Type[html.h4]
    | Type[html.h5]
    | Type[html.h6]
    | Type[html.label]
)

TextVariant = Literal[
    "title-1",
    "title-2",
    "title-3",
    "subtitle-1",
    "subtitle-2",
    "body",
]

TextAlign = Literal["text-left", "text-center", "text-right"]


def Text(
    *children: ComponentType,
    muted: bool = False,
    destructive: bool = False,
    tag: TextTag = html.p,
    variant: TextVariant = "body",
    role: str | None = None,
    align: TextAlign = "text-left",
) -> ComponentType:
    """
    The text component is a component provides a common interface for displaying text,
    keeping the text structured.
    """

    classes = _get_text_classes(muted, destructive)

    return BaseText(
        *[str(child) for child in children],
        classes=classes,
        tag=tag,
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
) -> ComponentType:
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


def BaseText(
    *children: ComponentType,
    classes: list[str] | None = None,
    tag: TextTag = html.p,
    variant: TextVariant = "body",
    role: str | None = None,
    html_for: str | None = None,
    align: TextAlign = "text-left",
) -> ComponentType:
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

    return tag(
        *children,
        class_=formatted_classes,
        role=role,
        for_=html_for,
    )


@concatenate_classes
def _get_base_text_classes(
    *,
    variant: TextVariant,
    additional_classes: list[str] | None = None,
    align: TextAlign = "text-left",
) -> list[str]:
    """
    The _get_base_text_classes function is a helper function that returns a list of
    classes for the base text component.
    """
    classes = additional_classes or []
    if variant == "title-1":
        classes.extend(["text-5xl", "font-bold"])
    elif variant == "title-2":
        classes.extend(["text-3xl", "font-bold"])
    elif variant == "title-3":
        classes.extend(["text-2xl"])
    elif variant == "subtitle-1":
        classes.extend(["text-base", "font-medium"])
    elif variant == "subtitle-2":
        classes.extend(["text-sm", "font-medium", "leading-6"])
    elif variant == "body":
        classes.extend(["text-sm", "leading-6"])

    if align == "text-center":
        classes.extend(["text-center"])
    elif align == "text-right":
        classes.extend(["text-right"])
    elif align == "text-left":
        classes.extend(["text-left"])

    return classes
