"""
Private module containing v1 function components used as internal rendering
helpers by the new chainable components.

Not part of the public API — do not import from outside ``hue.ui``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated, Literal, Type, Unpack, cast

from htmy import html
from typing_extensions import Any, Doc

from hue.context import HueContext
from hue.decorators import class_component, function_component
from hue.spacing import SPACE_BETWEEN, Size
from hue.types.core import BaseComponent, BasePropsKwargs, ComponentType, Undefined
from hue.types.css import AlignItems, JustifyContent
from hue.ui.icon import _render_icon
from hue.utils import classnames

# ---------------------------------------------------------------------------
# Stack
# ---------------------------------------------------------------------------


@function_component
def Stack(
    *children: ComponentType,
    direction: Literal["horizontal", "vertical"] = "vertical",
    spacing: Size = "sm",
    justify_content: JustifyContent = "justify-start",
    align_items: AlignItems = "items-start",
    position: Literal["relative", "absolute", "fixed", "sticky"] = "relative",
    **base_props: Unpack[BasePropsKwargs],
) -> html.div:
    """
    The stack component is a flex container that can be used to layout its children in a
    row or column. It provides additional (even) spacing between its children.
    """
    spacing_x, spacing_y = SPACE_BETWEEN[spacing]
    classes = classnames(
        "flex",
        "w-full",
        justify_content,
        align_items,
        position,
        {
            "flex-col": direction == "vertical",
            "flex-row": direction == "horizontal",
        },
        spacing_y if direction == "vertical" else spacing_x,
    )

    return html.div(*children, class_=classes, **base_props)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

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
    align: TextAlign = "text-left",
    **base_props: Unpack[BasePropsKwargs],
) -> T:
    """
    The text component is a component provides a common interface for displaying text,
    keeping the text structured.
    """

    class_ = base_props.pop("class_", None)

    classes = classnames(
        {
            "text-surface-500": muted and not destructive,
            "text-destructive": destructive,
            "text-surface-900": not muted and not destructive,
        },
        class_,
    )

    return BaseText(
        text,
        classes=classes,
        tag=tag or html.p,
        variant=variant,
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

    class_ = base_props.pop("class_", None)

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
        class_,
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
            for_=html_for,
            **base_props,
        ),
    )


# ---------------------------------------------------------------------------
# v1 Icon (dataclass-based) — used by callout
# ---------------------------------------------------------------------------


@class_component(kw_only=True)
class Icon(BaseComponent):
    """v1 dataclass-based icon component used internally by callout."""

    name: Annotated[str, Doc("The file name of the icon.")]

    @property
    def icons_dir(self) -> str:
        raise NotImplementedError("Icons dir must be specified")

    def htmy(self, context: HueContext, **kwargs: Any) -> html.svg | Undefined:
        if not self.name:
            return Undefined

        return _render_icon(
            icon_path=f"{os.path.join(self.icons_dir, self.name)}.svg",
            class_=self.class_,
        )


def create_icon_base(icons_dir: str) -> type[Icon]:
    """v1 factory that returns an Icon subclass with ``icons_dir`` pre-configured."""

    @dataclass(slots=True, frozen=True, kw_only=True)
    class BaseIcon(Icon):
        @property
        def icons_dir(self) -> str:
            return icons_dir

    return BaseIcon
