from functools import partial

from hue.ui import Text

from hue_docs.registry import ComponentExample, PlaygroundSpec, axis_grid

COMPONENT = Text

_SAMPLE = "The quick brown fox"


def _base() -> Text:
    return Text(_SAMPLE)


_grid = partial(
    axis_grid,
    ctor_code=f'Text("{_SAMPLE}")',
    build=_base,
    layout="stack",
)

EXAMPLE = ComponentExample(
    showcases=[
        _grid(
            "Variants",
            method="variant",
            values=[
                "title-1",
                "title-2",
                "title-3",
                "subtitle-1",
                "subtitle-2",
                "body",
            ],
        ),
        _grid(
            "Alignment",
            method="align",
            values=["text-left", "text-center", "text-right"],
        ),
        _grid("Muted", method="muted", values=[False, True]),
        _grid("Destructive", method="destructive", values=[False, True]),
    ],
    playground=PlaygroundSpec(
        build=_base,
        ctor_code=f'Text("{_SAMPLE}")',
        props=("variant", "align", "muted", "destructive"),
    ),
)
