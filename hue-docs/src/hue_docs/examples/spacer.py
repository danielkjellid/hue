from functools import partial

from hue.spacing import Size
from hue.ui import Spacer, Stack, Text

from hue_docs.registry import ComponentExample, Showcase, Variant

COMPONENT = Spacer


_SIZES: tuple[Size, ...] = ("xs", "sm", "md", "lg", "xl")


def _demo(size: Size) -> Stack:
    return Stack().content(
        Text("Above").variant("subtitle-2"),
        Spacer().spacing(size),
        Text("Below").variant("subtitle-2"),
    )


EXAMPLE = ComponentExample(
    showcases=[
        Showcase(
            title="Spacing",
            layout="stack",
            description="A spacer adds a fixed gap between two elements.",
            variants=[
                Variant(
                    label=size,
                    build=partial(_demo, size),
                    code=f'Spacer().spacing("{size}")',
                )
                for size in _SIZES
            ],
        )
    ]
)
