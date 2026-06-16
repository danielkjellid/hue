from functools import partial

from hue.ui import Button

from hue_docs.registry import ComponentExample, PlaygroundSpec, axis_grid

COMPONENT = Button


def _base() -> Button:
    # fluid(False) so buttons size to their content and sit side by side.
    return Button().fluid(False).content("Button")


_grid = partial(
    axis_grid,
    ctor_code="Button().fluid(False)",
    content_code='.content("Button")',
    build=_base,
    layout="row",
)

EXAMPLE = ComponentExample(
    showcases=[
        _grid(
            "Variants",
            method="variant",
            values=[
                "primary",
                "secondary",
                "tertiary",
                "quaternary",
                "outline",
                "transparent",
            ],
        ),
        _grid(
            "Destructive variants",
            method="variant",
            values=[
                "primary-destructive",
                "secondary-destructive",
                "tertiary-destructive",
                "outline-destructive",
                "transparent-destructive",
            ],
        ),
        _grid("Sizes", method="size", values=["sm", "md", "lg"]),
        _grid("Shapes", method="shape", values=["rounded", "pill"]),
        _grid("Disabled", method="disabled", values=[False, True]),
    ],
    playground=PlaygroundSpec(
        build=_base,
        ctor_code="Button().fluid(False)",
        content_code='.content("Button")',
        props=("variant", "size", "shape", "disabled"),
    ),
)
