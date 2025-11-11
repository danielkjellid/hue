from typing import Literal

from htmy import html

from hue.spacing import (
    SPACING,
    AlignItems,
    JustifyContent,
    Size,
)

from hue.types.core import ComponentType


def Stack(
    *children: ComponentType,
    direction: Literal["horizontal", "vertical"] = "vertical",
    spacing: Size = "sm",
    justify_content: JustifyContent = "justify-start",
    align_items: AlignItems = "items-start",
    position: Literal["relative", "absolute", "fixed", "sticky"] = "relative",
) -> html.div:
    """
    The stack component is a flex container that can be used to layout its children in a
    row or column. It provides additional (even) spacing between its children.
    """

    classes = _get_stack_component_classes(
        direction=direction,
        spacing=spacing,
        justify_content=justify_content,
        align_items=align_items,
        position=position,
    )

    return html.div(*children, class_=classes)


def _get_stack_component_classes(
    direction: Literal["horizontal", "vertical"] = "vertical",
    spacing: Size = "sm",
    justify_content: JustifyContent = "justify-start",
    align_items: AlignItems = "items-start",
    position: Literal["relative", "absolute", "fixed", "sticky"] = "relative",
) -> list[str]:
    """
    Get the classes for a stack component.
    """

    classes = ["flex", "w-full", justify_content, align_items, position]
    spacing_x, spacing_y = SPACING[spacing]

    if direction == "vertical":
        classes.extend(["flex-col", spacing_y])
    else:
        classes.extend(["flex-row", spacing_x])

    return classes
