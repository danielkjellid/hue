from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import Spacer, Stack, Text

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Sizes


def xs() -> ComponentType:
    return html.div(
        Text().content("Above"), Spacer().spacing("xs"), Text().content("Below")
    )


def sm() -> ComponentType:
    return html.div(
        Text().content("Above"), Spacer().spacing("sm"), Text().content("Below")
    )


def md() -> ComponentType:
    return html.div(
        Text().content("Above"), Spacer().spacing("md"), Text().content("Below")
    )


def lg() -> ComponentType:
    return html.div(
        Text().content("Above"), Spacer().spacing("lg"), Text().content("Below")
    )


def xl() -> ComponentType:
    return html.div(
        Text().content("Above"), Spacer().spacing("xl"), Text().content("Below")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Spacer` is an empty `div` with a bottom margin. Put it between two "
            "elements to push them apart without giving either one a margin of its "
            "own. `spacing()` sets the size, from `xs` to `xl`, and defaults to `sm`."
        ),
        pr.code(
            'html.div(Text().content("Above"), Spacer().spacing("lg"), '
            'Text().content("Below"))'
        ),
        pr.h3("Spacer sizes"),
        pr.p(
            "The sizes are the same steps `Stack` uses for its gaps: `xs` is 4px, `sm` "
            "8px, `md` 20px, `lg` 32px and `xl` 64px."
        ),
        pr.h2("A Spacer inside a Stack"),
        pr.p(
            "A `Stack` sets its gap with margins on its children, and a `Spacer` is "
            "one of its children, so inside a `Stack` the two add up: a `Spacer` of "
            "`lg` in a `Stack` of `sm` leaves a 40px gap, the `Stack`'s 8px plus the "
            "`Spacer`'s 32px. Set the `Stack`'s `spacing()` instead when every gap "
            "should be the same."
        ),
    )


PAGE = ComponentPage(
    Spacer,
    lede=(
        "A spacer is a fixed gap between two elements, in one of the five "
        "spacing steps. It is for layouts that have no `Stack` to set the gap."
    ),
    usage=_usage,
    panels=[panel("Sizes", xs, sm, md, lg, xl)],
    notes=[
        Note(
            "note",
            "A `Spacer` renders an empty `div`, so it is a real element in the DOM. "
            "It has no content and no role, and a screen reader skips it.",
        ),
    ],
    related=[Stack],
)
