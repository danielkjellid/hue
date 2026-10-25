from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Kbd, Label, Text

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Variants


def title_1() -> Text:
    return Text("Quarterly report").variant("title-1")


def title_2() -> Text:
    return Text("Quarterly report").variant("title-2")


def title_3() -> Text:
    return Text("Quarterly report").variant("title-3")


def subtitle_1() -> Text:
    return Text("Revenue by region").variant("subtitle-1")


def subtitle_2() -> Text:
    return Text("Revenue by region").variant("subtitle-2")


def body() -> Text:
    return Text("Revenue grew in every region but one.").variant("body")


# Tags


def p() -> Text:
    return Text("A paragraph").tag("p")


def span() -> Text:
    return Text("An inline span").tag("span")


def h1() -> Text:
    return Text("Heading level 1").tag("h1").variant("title-2")


def h2() -> Text:
    return Text("Heading level 2").tag("h2").variant("title-3")


def h3() -> Text:
    return Text("Heading level 3").tag("h3").variant("subtitle-1")


def h4() -> Text:
    return Text("Heading level 4").tag("h4").variant("subtitle-2")


def h5() -> Text:
    return Text("Heading level 5").tag("h5").variant("subtitle-2")


def h6() -> Text:
    return Text("Heading level 6").tag("h6").variant("subtitle-2")


def label() -> Text:
    return Text("A label element").tag("label")


# Alignment


def left() -> Text:
    return Text("Aligned to the start of the line.").align("text-left")


def center() -> Text:
    return Text("Centred on the line.").align("text-center")


def right() -> Text:
    return Text("Aligned to the end of the line.").align("text-right")


# Colour


def default() -> Text:
    return Text("Invoice INV-2048 is paid.")


def muted() -> Text:
    return Text("Last updated 3 minutes ago.").muted()


def destructive() -> Text:
    return Text("The card was declined.").destructive()


def muted_and_destructive() -> Text:
    return Text("Destructive wins over muted.").muted().destructive()


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "Text takes its text as the first argument and renders it in a p "
            "element by default. variant() picks the type style, tag() picks "
            "the element, align() the alignment, and muted() or destructive() "
            "the colour. Children passed to content() follow the text, so a "
            "Text can hold other components inline."
        ),
        pr.code(
            'Text("Quarterly report").variant("title-2").tag("h1")\n'
            'Text("Press ").content(Kbd("mod", "K"), " to search.")'
        ),
        pr.h3("Text variant and tag are separate"),
        pr.p(
            "variant() sets only the size and weight. tag() sets the element: "
            'p, span, h1 to h6 or label. A Text with variant("title-1") is '
            "still a paragraph until tag() makes it a heading, and a heading "
            "can take any variant, so the heading level can follow the "
            "document outline while the size follows the design."
        ),
        pr.h3("Text variants"),
        pr.p(
            "body is the default: 13px on a 24px line. title-1, title-2 and "
            "title-3 are the large sizes, the first two in bold. subtitle-1 "
            "(14px) and subtitle-2 (13px) are medium weight."
        ),
        pr.h3("Text alignment"),
        pr.p(
            "align() takes the Tailwind class itself: text-left (the default), "
            "text-center or text-right."
        ),
        pr.h3("Text colour"),
        pr.p(
            "The default colour is the foreground token. muted() switches to "
            "the muted foreground and destructive() to the danger text colour. "
            "When both are set, destructive wins."
        ),
    )


PAGE = ComponentPage(
    Text,
    lede=(
        "Text renders a run of text in one of hue's type styles, from page "
        "titles down to body copy. Its modifiers also set the element, the "
        "alignment and the colour."
    ),
    usage=_usage,
    panels=[
        panel(
            "Variants",
            title_1,
            title_2,
            title_3,
            subtitle_1,
            subtitle_2,
            body,
            layout="stack",
        ),
        panel(
            "Tags",
            p,
            span,
            h1,
            h2,
            h3,
            h4,
            h5,
            h6,
            label,
            layout="stack",
            hint="tag() sets the element; variant() sets the look",
        ),
        panel("Alignment", left, center, right, layout="stack"),
        panel("Colour", default, muted, destructive, muted_and_destructive),
    ],
    notes=[
        Note(
            "a11y",
            "variant() changes only the look. A screen reader finds headings "
            'by their element, so a heading needs tag("h1") to tag("h6"), '
            "whatever its variant.",
        ),
        Note(
            "note",
            'tag("label") renders a label with no for attribute, and Text has '
            "no html_for(). To name a form control, use Label.",
        ),
    ],
    related=[Label, Kbd],
)
