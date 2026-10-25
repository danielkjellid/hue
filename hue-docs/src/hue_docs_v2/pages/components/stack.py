from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import Badge, Button, ScrollArea, Spacer, Stack, Text

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Direction


def vertical() -> Stack:
    return Stack().content(
        Badge().content("One"), Badge().content("Two"), Badge().content("Three")
    )


def horizontal() -> Stack:
    return (
        Stack()
        .horizontal()
        .content(
            Badge().content("One"), Badge().content("Two"), Badge().content("Three")
        )
    )


# Spacing


def xs() -> Stack:
    return (
        Stack()
        .horizontal()
        .spacing("xs")
        .content(
            Badge().content("One"), Badge().content("Two"), Badge().content("Three")
        )
    )


def sm() -> Stack:
    return (
        Stack()
        .horizontal()
        .spacing("sm")
        .content(
            Badge().content("One"), Badge().content("Two"), Badge().content("Three")
        )
    )


def md() -> Stack:
    return (
        Stack()
        .horizontal()
        .spacing("md")
        .content(
            Badge().content("One"), Badge().content("Two"), Badge().content("Three")
        )
    )


def lg() -> Stack:
    return (
        Stack()
        .horizontal()
        .spacing("lg")
        .content(
            Badge().content("One"), Badge().content("Two"), Badge().content("Three")
        )
    )


def xl() -> Stack:
    return (
        Stack()
        .horizontal()
        .spacing("xl")
        .content(
            Badge().content("One"), Badge().content("Two"), Badge().content("Three")
        )
    )


# Justify content


def justify_start() -> Stack:
    return (
        Stack()
        .horizontal()
        .justify_content("justify-start")
        .content(Badge().content("One"), Badge().content("Two"))
    )


def justify_center() -> Stack:
    return (
        Stack()
        .horizontal()
        .justify_content("justify-center")
        .content(Badge().content("One"), Badge().content("Two"))
    )


def justify_end() -> Stack:
    return (
        Stack()
        .horizontal()
        .justify_content("justify-end")
        .content(Badge().content("One"), Badge().content("Two"))
    )


def justify_between() -> Stack:
    return (
        Stack()
        .horizontal()
        .justify_content("justify-between")
        .content(Badge().content("One"), Badge().content("Two"))
    )


def justify_around() -> Stack:
    return (
        Stack()
        .horizontal()
        .justify_content("justify-around")
        .content(Badge().content("One"), Badge().content("Two"))
    )


def justify_evenly() -> Stack:
    return (
        Stack()
        .horizontal()
        .justify_content("justify-evenly")
        .content(Badge().content("One"), Badge().content("Two"))
    )


# Align items


def items_start() -> Stack:
    return (
        Stack()
        .horizontal()
        .align_items("items-start")
        .content(
            Button().size("lg").content("Large"), Button().size("xs").content("Small")
        )
    )


def items_center() -> Stack:
    return (
        Stack()
        .horizontal()
        .align_items("items-center")
        .content(
            Button().size("lg").content("Large"), Button().size("xs").content("Small")
        )
    )


def items_end() -> Stack:
    return (
        Stack()
        .horizontal()
        .align_items("items-end")
        .content(
            Button().size("lg").content("Large"), Button().size("xs").content("Small")
        )
    )


def items_baseline() -> Stack:
    return (
        Stack()
        .horizontal()
        .align_items("items-baseline")
        .content(
            Text().variant("title-3").content("$48,290"), Text().muted().content("USD")
        )
    )


def items_stretch() -> Stack:
    return (
        Stack()
        .horizontal()
        .align_items("items-stretch")
        .content(
            html.div("Short").class_("rounded-md border border-border px-3 py-1"),
            html.div("Tall").class_("rounded-md border border-border px-3 py-6"),
        )
    )


# Position


def sticky() -> ScrollArea:
    return (
        ScrollArea()
        .label("Activity")
        .max_height("max-h-32")
        .class_("rounded-md border border-border px-3")
        .content(
            Stack()
            .position("sticky")
            .class_("top-0 bg-surface py-1 font-semibold")
            .content("Today"),
            html.p("Ada sent INV-2050."),
            html.p("Grace paid INV-2049."),
            html.p("Linus opened INV-2048."),
            html.p("Margaret archived INV-2047."),
            html.p("Alan sent INV-2046."),
            html.p("Barbara paid INV-2045."),
        )
    )


def absolute() -> Stack:
    return (
        Stack()
        .class_("h-24 rounded-md border border-border p-3")
        .content(
            Text().content("Q3 revenue report"),
            Stack()
            .position("absolute")
            .horizontal()
            .justify_content("justify-end")
            .class_("end-3 bottom-3")
            .content(Badge().content("New")),
        )
    )


# Width


def a_row_that_shrinks() -> Stack:
    return (
        Stack()
        .horizontal()
        .spacing("md")
        .content(
            html.p("Usage-based billing on Pro and Scale.").class_(
                "rounded-md border border-border p-3"
            ),
            html.p("Cursor pagination on the transactions endpoint.").class_(
                "rounded-md border border-border p-3"
            ),
            html.p("Idempotency keys on every write endpoint.").class_(
                "rounded-md border border-border p-3"
            ),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A Stack is a flex container that lays its children out in a column, "
            "or in a row with horizontal(). It spans the full width of its "
            "parent. spacing() sets the gap between children, from xs to xl, "
            "and defaults to sm."
        ),
        pr.code(
            'Stack().horizontal().spacing("md").align_items("items-center").content(\n'
            '    Button().content("Save"),\n'
            '    Button().variant("ghost").content("Cancel"),\n'
            ")"
        ),
        pr.h3("Aligning a Stack's children"),
        pr.p(
            "justify_content() places the children along the Stack's direction "
            "and align_items() across it. Both take the Tailwind class name as "
            "their value, such as justify-between or items-center. The defaults "
            "are justify-start and items-start, so children in a vertical Stack "
            "keep their own width rather than stretching. Pass items-stretch to "
            "make them fill it."
        ),
        pr.h3("Positioning a Stack"),
        pr.p(
            "position() sets the CSS position: relative (the default), absolute, "
            "fixed or sticky. Because a Stack is relative by default, it is "
            "already the containing block for an absolute child. Set the offsets "
            "yourself with class_(), such as top-0 for a sticky Stack."
        ),
        pr.h2("A Stack at narrow widths"),
        pr.p(
            "A Stack has no responsive classes and its row never wraps. A "
            "horizontal Stack stays one row at every width, and its children "
            "shrink to fit."
        ),
    )


PAGE = ComponentPage(
    Stack,
    lede=(
        "A stack lays its children out in a column or a row with an even gap "
        "between them, and aligns them along either axis."
    ),
    usage=_usage,
    panels=[
        panel("Direction", vertical, horizontal),
        panel("Spacing", xs, sm, md, lg, xl, layout="stack"),
        panel(
            "Justify content",
            justify_start,
            justify_center,
            justify_end,
            justify_between,
            justify_around,
            justify_evenly,
            layout="stack",
        ),
        panel(
            "Align items",
            items_start,
            items_center,
            items_end,
            items_baseline,
            items_stretch,
        ),
        panel(
            "Position", sticky, absolute, layout="stack", hint="Scroll the first one"
        ),
        panel(
            "Width",
            a_row_that_shrinks,
            layout="stack",
            hint="The row never wraps: at sm its children get narrower",
        ),
    ],
    notes=[
        Note(
            "note",
            "A Stack is a div with no role. It groups children visually and "
            "says nothing to a screen reader, so the reading order is the order "
            "of its children.",
        ),
        Note(
            "note",
            "spacing() is applied with Tailwind's space-x and space-y utilities, "
            "which set margins on the children. A Spacer inside a Stack adds "
            "its own margin on top of that gap.",
        ),
    ],
    related=[Spacer],
)
