from hue import html
from hue.ui import Stack

from hue_docs.registry import ComponentExample, PlaygroundSpec, axis_grid

COMPONENT = Stack


def _box(label: str) -> html.Element:
    return html.div(label).class_(
        "flex h-10 w-10 items-center justify-center rounded-md "
        "bg-primary text-sm text-white"
    )


def _base() -> Stack:
    return Stack().content(_box("1"), _box("2"), _box("3"))


def _horizontal() -> Stack:
    return Stack().direction("horizontal").content(_box("1"), _box("2"), _box("3"))


_CONTENT = '.content(box("1"), box("2"), box("3"))'

EXAMPLE = ComponentExample(
    showcases=[
        axis_grid(
            "Direction",
            ctor_code="Stack()",
            content_code=_CONTENT,
            build=_base,
            method="direction",
            values=["vertical", "horizontal"],
            layout="stack",
        ),
        axis_grid(
            "Spacing",
            ctor_code='Stack().direction("horizontal")',
            content_code=_CONTENT,
            build=_horizontal,
            method="spacing",
            values=["xs", "sm", "md", "lg", "xl"],
            layout="stack",
        ),
        axis_grid(
            "Justify content",
            ctor_code='Stack().direction("horizontal")',
            content_code=_CONTENT,
            build=_horizontal,
            method="justify_content",
            values=[
                "justify-start",
                "justify-center",
                "justify-end",
                "justify-between",
            ],
            layout="stack",
        ),
    ],
    playground=PlaygroundSpec(
        build=_horizontal,
        ctor_code="Stack()",
        content_code=_CONTENT,
        props=("direction", "spacing", "justify_content", "align_items"),
    ),
)
