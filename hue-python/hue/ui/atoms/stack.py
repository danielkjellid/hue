from typing import Literal

from htmy import html

from hue.spacing import (
    SPACING,
    Size,
)
from hue.types.core import ComponentType
from hue.types.css import AlignItems, JustifyContent
from hue.utils import classnames


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
    spacing_x, spacing_y = SPACING[spacing]
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

    return html.div(*children, class_=classes)
