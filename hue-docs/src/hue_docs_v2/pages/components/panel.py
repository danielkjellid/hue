from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Card, Panel, Table, TableBody, TableCell, TableRow

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Anatomy


def label_and_hint() -> Panel:
    return (
        Panel()
        .label("Control heights")
        .hint("36px is the default")
        .content("Every control lines up on a shared baseline.")
    )


def label_only() -> Panel:
    return Panel().label("Variants").content("One per row.")


def hint_only() -> Panel:
    return Panel().hint("Updated hourly").content("The bar shows for a hint alone.")


def no_bar() -> Panel:
    return Panel().content("A plain bordered frame.")


# Padding


def md() -> Panel:
    return Panel().label("md").padding("md").content("The default, 24px.")


def sm() -> Panel:
    return Panel().label("sm").padding("sm").content("16px.")


def none() -> ComponentType:
    return (
        Panel()
        .label("none")
        .padding("none")
        .content(
            Table().content(
                TableBody().content(
                    TableRow().content(
                        TableCell().content("INV-2050"),
                        TableCell().content("$2,190.00"),
                    ),
                    TableRow().content(
                        TableCell().content("INV-2051"),
                        TableCell().content("$740.00"),
                    ),
                )
            )
        )
    )


# States


def plain() -> Panel:
    return Panel().label("Elevation").content(Card().content("A card on the body."))


def sunken() -> Panel:
    return (
        Panel()
        .label("Elevation")
        .sunken()
        .content(Card().variant("raised").content("A raised card on a tinted body."))
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Panel` is a bordered frame with an optional bar along the top. "
            "`label()` fills the start of the bar and `hint()` the end, in quieter "
            "text. The bar renders when either one is set, and a `Panel` with "
            "neither is a plain frame. Children go in the body."
        ),
        pr.code('Panel().label("Variants").hint("Never colour alone").content(...)'),
        pr.h3("Padding a Panel"),
        pr.p(
            '`padding()` sets the body\'s inset: `"md"` (24px, the default), `"sm"` '
            '(16px) or `"none"`. Use `"none"` for content that brings its own edges, '
            "such as a `Table`, so it meets the frame."
        ),
        pr.h3("A Panel with a tinted body"),
        pr.p(
            "`sunken()` fills the body with the page's subtle ground colour, so a "
            "raised `Card` or other surface placed on it stands out. The bar keeps "
            "its own fill either way."
        ),
    )


PAGE = ComponentPage(
    Panel,
    lede=(
        "A panel frames a block of content under a slim bar that holds a "
        "label and a hint. Use it to set a group of examples, settings or "
        "rows apart with a name."
    ),
    usage=_usage,
    panels=[
        panel(
            "Anatomy",
            label_and_hint,
            label_only,
            hint_only,
            no_bar,
            layout="stack",
        ),
        panel("Padding", md, sm, none, layout="stack", captions=False),
        panel("States", plain, sunken, layout="stack"),
    ],
    notes=[
        Note(
            "note",
            "The label and hint are plain text in `span` elements, not a heading, "
            "so they do not appear in a screen reader's list of headings. Put a "
            "heading inside the body when the section needs one.",
        ),
    ],
    related=[Card],
)
