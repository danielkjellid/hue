from __future__ import annotations

from hue import html
from hue.types.core import ComponentType
from hue.ui import Panel, ScrollArea

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def time_zones() -> ScrollArea:
    return (
        ScrollArea()
        .label("Time zones")
        .max_height("max-h-48")
        .class_("rounded-md border border-border p-2")
        .content(
            html.p("Europe/Oslo, UTC+2").class_("px-2 py-1.5"),
            html.p("Europe/London, UTC+1").class_("px-2 py-1.5"),
            html.p("America/New_York, UTC-4").class_("px-2 py-1.5"),
            html.p("America/Chicago, UTC-5").class_("px-2 py-1.5"),
            html.p("America/Los_Angeles, UTC-7").class_("px-2 py-1.5"),
            html.p("Asia/Tokyo, UTC+9").class_("px-2 py-1.5"),
            html.p("Asia/Singapore, UTC+8").class_("px-2 py-1.5"),
            html.p("Australia/Sydney, UTC+10").class_("px-2 py-1.5"),
        )
    )


# Anatomy


def hard_edges() -> ScrollArea:
    return (
        ScrollArea()
        .label("Release notes, hard edges")
        .max_height("max-h-32")
        .content(
            html.p("4.2.0: Usage-based billing on Pro and Scale."),
            html.p("4.1.3: Fixed a rounding error in multi-currency invoices."),
            html.p("4.1.0: Cursor pagination on the transactions endpoint."),
            html.p("4.0.1: Webhook retries now back off exponentially."),
            html.p("4.0.0: Bearer tokens replace the key-and-secret pair."),
            html.p("3.9.2: Rate limits are reported in the response headers."),
            html.p("3.9.0: Idempotency keys on every write endpoint."),
        )
    )


def faded_edges() -> ScrollArea:
    return (
        ScrollArea()
        .label("Release notes, faded edges")
        .max_height("max-h-32")
        .fade()
        .content(
            html.p("4.2.0: Usage-based billing on Pro and Scale."),
            html.p("4.1.3: Fixed a rounding error in multi-currency invoices."),
            html.p("4.1.0: Cursor pagination on the transactions endpoint."),
            html.p("4.0.1: Webhook retries now back off exponentially."),
            html.p("4.0.0: Bearer tokens replace the key-and-secret pair."),
            html.p("3.9.2: Rate limits are reported in the response headers."),
            html.p("3.9.0: Idempotency keys on every write endpoint."),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `ScrollArea` is a box whose content scrolls once it is taller than "
            "the box. The scrolling is the browser's own; `ScrollArea` only themes "
            "the scrollbar and makes the box reachable from the keyboard. "
            "`label()` is required, and rendering a `ScrollArea` without one raises "
            "a `ValueError`."
        ),
        pr.code(
            'ScrollArea().label("Release notes").max_height("max-h-64").content(...)'
        ),
        pr.h3("How tall a ScrollArea grows"),
        pr.p(
            "`max_height()` takes a Tailwind class, such as `max-h-64`, and the box "
            "grows with its content up to that height before it scrolls. Leave "
            "it out when the parent already gives the `ScrollArea` a height."
        ),
        pr.h3("A ScrollArea with faded edges"),
        pr.p(
            "`fade()` softens the top edge while there is content above and the "
            "bottom edge while there is content below, in place of a hard cut. "
            "It watches the scroll position and the content's size with Alpine, "
            "so the fade updates when rows are added or the box is resized."
        ),
        pr.h3("Scrolling past the end"),
        pr.p(
            "`ScrollArea` sets `overscroll-contain`, so a wheel or swipe that reaches "
            "the end of the box stops there instead of scrolling the page behind "
            "it."
        ),
    )


PAGE = ComponentPage(
    ScrollArea,
    lede=(
        "A scroll area caps the height of a list or a run of text and scrolls "
        "what does not fit, with a scrollbar themed to match the page. It is "
        "focusable and named, so a keyboard can reach and scroll it."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            time_zones,
            layout="stack",
            hint="Tab to it, then scroll with the arrow keys",
        ),
        panel("Anatomy", hard_edges, faded_edges),
    ],
    notes=[
        Note(
            "a11y",
            'A `ScrollArea` has `tabindex="0"`, so a keyboard user can focus it and '
            "scroll it with the arrow keys, Page Up and Page Down. The focus "
            "ring shows on keyboard focus.",
        ),
        Note(
            "a11y",
            'A `ScrollArea` renders with `role="region"` and `aria-label` from '
            "`label()`, so a screen reader announces its name when focus lands on it.",
        ),
        Note(
            "warn",
            "`label()` is required. A `ScrollArea` without one raises a `ValueError` "
            "when it renders, because an unnamed tab stop tells a screen reader "
            "nothing.",
        ),
    ],
    related=[Panel],
)
