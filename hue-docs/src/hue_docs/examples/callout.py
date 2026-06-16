from hue.ui import Callout

from hue_docs.registry import ComponentExample, PlaygroundSpec, axis_grid

COMPONENT = Callout


def _base() -> Callout:
    return Callout().title("Heads up").content("This is a callout message.")


EXAMPLE = ComponentExample(
    showcases=[
        axis_grid(
            "Variants",
            ctor_code='Callout().title("Heads up")',
            content_code='.content("This is a callout message.")',
            build=_base,
            method="variant",
            values=["gray", "primary", "success", "info", "warning", "error"],
            layout="stack",
        ),
    ],
    playground=PlaygroundSpec(
        build=_base,
        ctor_code='Callout().title("Heads up")',
        content_code='.content("This is a callout message.")',
        props=("variant",),
    ),
)
