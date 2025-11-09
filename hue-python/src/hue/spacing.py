from collections import namedtuple
from typing import Literal, Mapping

Size = Literal["xs", "sm", "md", "lg", "xl"]


XY = namedtuple("XY", ["x", "y"])
SPACING: Mapping[Size, XY] = {
    "xs": XY(x="space-x-1", y="space-y-1"),
    "sm": XY(x="space-x-2", y="space-y-2"),
    "md": XY(x="space-x-5", y="space-y-5"),
    "lg": XY(x="space-x-8", y="space-y-8"),
    "xl": XY(x="space-x-16", y="space-y-16"),
}

JustifyContent = Literal[
    "justify-start",
    "justify-center",
    "justify-end",
    "justify-between",
    "justify-around",
    "justify-evenly",
]
AlignItems = Literal[
    "items-start",
    "items-center",
    "items-end",
    "items-stretch",
    "items-baseline",
]
