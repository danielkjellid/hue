from typing import Literal, Unpack

from htmy import html

from hue.decorators import function_component
from hue.spacing import SPACE_BETWEEN, Size
from hue.types.core import BasePropsKwargs, ComponentType
from hue.types.css import AlignItems, JustifyContent
from hue.utils import classnames


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
