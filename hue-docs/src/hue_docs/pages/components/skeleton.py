from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Empty, Progress, Skeleton, Spinner, Stack

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Shapes


def text() -> Skeleton:
    return Skeleton().shape("text")


def circle() -> Skeleton:
    return Skeleton().shape("circle")


def rect() -> Skeleton:
    return Skeleton().shape("rect")


def card() -> Skeleton:
    return Skeleton().shape("card")


# Sizes


def paragraph() -> Skeleton:
    return Skeleton().shape("text").lines(3)


def larger_circle() -> Skeleton:
    return Skeleton().shape("circle").width("w-16").height("h-16")


def half_width() -> Skeleton:
    return Skeleton().shape("rect").width("w-1/2")


def shorter_card() -> Skeleton:
    return Skeleton().shape("card").height("h-20")


# Loading


def a_list_row() -> ComponentType:
    return (
        Stack()
        .horizontal()
        .spacing("sm")
        .align_items("items-center")
        .aria_busy("true")
        .content(
            Skeleton().shape("circle"),
            Skeleton().shape("text").lines(2).class_("flex-1"),
        )
    )


def a_card() -> ComponentType:
    return (
        Stack()
        .spacing("sm")
        .aria_busy("true")
        .content(
            Skeleton().shape("card").height("h-24"),
            Skeleton().shape("text").lines(2),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Skeleton` is a grey shimmering block in the shape of content "
            "that is still loading. `shape()` picks one of four shapes, each "
            'with the size it usually stands in for. `"text"`, the default, is a '
            'full-width bar 14px tall; `"circle"` is 36px across; `"rect"` is '
            'a full-width 36px block; `"card"` is a full-width block 128px tall.'
        ),
        pr.code('Skeleton().shape("text").lines(3)'),
        pr.h3("Sizing a Skeleton"),
        pr.p(
            "`width()` and `height()` each take one Tailwind class and replace "
            'that axis of the shape outright, such as `width("w-1/2")` or '
            '`height("h-20")`. A class built at runtime, such as an f-string, '
            "is one Tailwind never sees, so write the class out in full."
        ),
        pr.h3("Paragraphs"),
        pr.p(
            "`lines()` stacks text bars into a paragraph whose last line stops "
            'at 62% width. It applies only to the `"text"` shape. `lines()` above `1` '
            "on any other shape raises a `ValueError`. Inside a horizontal "
            '`Stack`, give the paragraph `class_("flex-1")` so it takes the '
            "space left beside its neighbours."
        ),
        pr.h2("Marking the region busy"),
        pr.p(
            "A `Skeleton` renders `aria-hidden`, so a screen reader skips it. "
            'Set `aria_busy("true")` on the container the `Skeleton` stands in '
            "for, and remove it when the content arrives, usually by "
            "replacing the container with the loaded version."
        ),
        pr.code(
            "(\n"
            "    Stack()\n"
            '    .aria_busy("true")\n'
            "    .content(\n"
            '        Skeleton().shape("circle"),\n'
            '        Skeleton().shape("text").lines(2),\n'
            "    )\n"
            ")"
        ),
        pr.p(
            "The shimmer is a CSS animation. With reduced motion turned on, "
            "hue's stylesheet stops it, and the `Skeleton` is a still grey "
            "block."
        ),
    )


PAGE = ComponentPage(
    Skeleton,
    lede=(
        "A `Skeleton` is a placeholder in the shape of content that is still "
        "loading, so the page keeps its layout while it waits. Four shapes "
        "cover lines of text, avatars, controls and cards."
    ),
    usage=_usage,
    panels=[
        panel("Shapes", text, circle, rect, card, layout="stack"),
        panel(
            "Sizes",
            paragraph,
            larger_circle,
            half_width,
            shorter_card,
            layout="stack",
            hint="`width()` and `height()` replace the shape's own size",
        ),
        panel(
            "Loading",
            a_list_row,
            a_card,
            layout="stack",
            hint="Skeletons standing in for real content",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "Every `Skeleton` renders `aria-hidden`, so a screen reader passes over "
            "it.",
        ),
        Note(
            "a11y",
            'Set `aria_busy("true")` on the region the `Skeleton` stands in for, '
            "so assistive technology knows the region is still loading.",
        ),
        Note(
            "warn",
            '`lines()` above `1` on a `"circle"`, `"rect"` or `"card"` shape raises a '
            "`ValueError`. Repeat the `Skeleton` instead.",
        ),
    ],
    related=[Spinner, Progress, Empty],
)
