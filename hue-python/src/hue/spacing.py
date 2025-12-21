from collections import namedtuple
from typing import Literal, Mapping

Size = Literal["xs", "sm", "md", "lg", "xl"]


XY = namedtuple("XY", ["x", "y"])
TRBL = namedtuple("TRBL", ["top", "right", "bottom", "left"])

MARGIN: Mapping[Size, TRBL] = {
    "xs": TRBL(top="mt-1", right="mr-1", bottom="mb-1", left="ml-1"),
    "sm": TRBL(top="mt-2", right="mr-2", bottom="mb-2", left="ml-2"),
    "md": TRBL(top="mt-5", right="mr-5", bottom="mb-5", left="ml-5"),
    "lg": TRBL(top="mt-8", right="mr-8", bottom="mb-8", left="ml-8"),
    "xl": TRBL(top="mt-16", right="mr-16", bottom="mb-16", left="ml-16"),
}

SPACE_BETWEEN: Mapping[Size, XY] = {
    "xs": XY(x="space-x-1", y="space-y-1"),
    "sm": XY(x="space-x-2", y="space-y-2"),
    "md": XY(x="space-x-5", y="space-y-5"),
    "lg": XY(x="space-x-8", y="space-y-8"),
    "xl": XY(x="space-x-16", y="space-y-16"),
}
