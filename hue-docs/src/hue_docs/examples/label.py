from functools import partial

from hue.ui import Label

from hue_docs.registry import ComponentExample, PlaygroundSpec, axis_grid

COMPONENT = Label


def _base() -> Label:
    return Label("Email")


_grid = partial(axis_grid, ctor_code='Label("Email")', build=_base, layout="stack")

EXAMPLE = ComponentExample(
    showcases=[
        _grid("Required", method="required", values=[False, True]),
        _grid("Disabled", method="disabled", values=[False, True]),
    ],
    playground=PlaygroundSpec(
        build=_base,
        ctor_code='Label("Email")',
        props=("required", "disabled", "hidden_label"),
    ),
)
