from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert, Button, Empty, Skeleton, Spinner

from hue_docs.icons import Icon
from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Variants


def neutral() -> Empty:
    return (
        Empty()
        .title("No invoices yet")
        .description("Invoices appear here once your first order is paid.")
    )


def danger() -> Empty:
    return (
        Empty()
        .variant("danger")
        .title("Could not load invoices")
        .description("The billing service did not respond.")
    )


# Anatomy


def title_only() -> Empty:
    return Empty().title("No comments")


def with_description() -> Empty:
    return (
        Empty()
        .title("No comments")
        .description("Comments on this invoice show up here.")
    )


def with_actions() -> Empty:
    return (
        Empty()
        .title("No team members")
        .description("Invite people to share invoices with them.")
        .actions(Button().content(Icon("plus"), "Invite people"))
    )


def own_icon() -> Empty:
    return (
        Empty()
        .icon(Icon("credit-card"))
        .title("No saved cards")
        .description("Cards you pay with are saved here.")
    )


def no_icon() -> Empty:
    return Empty().icon(None).compact().title("Nothing scheduled")


def as_a_heading() -> Empty:
    return (
        Empty()
        .title("No projects yet", heading="h2")
        .description("A project groups invoices for one client.")
    )


# Layout


def default_padding() -> Empty:
    return Empty().title("No files").description("Uploads appear here.")


def compact() -> Empty:
    return Empty().compact().title("No files").description("Uploads appear here.")


# Empty


def first_use() -> Empty:
    return (
        Empty()
        .icon(Icon("inbox"))
        .title("No invoices yet")
        .description("Invoices appear here once your first order is paid.")
        .actions(Button().content("Create invoice"))
    )


def no_results() -> Empty:
    return (
        Empty()
        .icon(Icon("search"))
        .compact()
        .title('No results for "refund q3"')
        .description("Try clearing the Declined filter.")
        .actions(Button().variant("outline").size("sm").content("Clear filters"))
    )


# Error


def could_not_load() -> Empty:
    return (
        Empty()
        .variant("danger")
        .icon(Icon("triangle-alert"))
        .compact()
        .title("Could not load invoices")
        .description("The billing service did not respond. Last tried 12s ago.")
        .actions(
            Button().variant("outline").size("sm").content("Try again"),
            Button().variant("ghost").size("sm").content("Contact support"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "An `Empty` takes the place of content that is not there: a table "
            "with no rows, a search with no matches, a list that failed to "
            "load. Every part is optional. `title()` is the bold line, "
            "`description()` the sentence under it, and `actions()` a row of "
            "buttons below both."
        ),
        pr.code(
            "(\n"
            "    Empty()\n"
            '    .title("No invoices yet")\n'
            '    .description("Invoices appear here once your first order is paid.")\n'
            '    .actions(Button().content("Create invoice"))\n'
            ")"
        ),
        pr.h3("Variant and icon"),
        pr.p(
            '`variant()` is `"neutral"` or `"danger"`, and only changes the icon chip: '
            '`"neutral"` shows an inbox on a grey chip, `"danger"` a cross on a red '
            "one. `icon()` replaces the variant's icon and keeps the chip's "
            "colour. `icon(None)` removes the chip, and with it the only visible "
            "difference between the two variants."
        ),
        pr.h3("Headings"),
        pr.p(
            "`title()` renders a `div` by default. Pass `heading`, as in "
            '`title("No projects yet", heading="h2")`, to render a real heading '
            "element instead, so an `Empty` that stands in for a page or a "
            "section shows up in the document outline. The heading looks the "
            "same as the `div`."
        ),
        pr.h3("Inside a card or a table"),
        pr.p(
            "`compact()` reduces the padding and the icon chip, for an `Empty` "
            "inside a card, a table body or a panel."
        ),
        pr.h2("Swapping an Empty in"),
        pr.p(
            "An `Empty` is a plain `div` with no role and no live region. When one "
            "replaces a list after a search or a filter, a screen reader is "
            "not told. Put the announcement on the region that changes, for "
            "example with `aria_live()` on its container."
        ),
    )


PAGE = ComponentPage(
    Empty,
    lede=(
        "An `Empty` fills the space where content would be: nothing created "
        "yet, nothing matched, or nothing could be loaded. It holds an icon, a "
        "title, a description and actions, every one of them optional."
    ),
    usage=_usage,
    panels=[
        panel("Variants", neutral, danger),
        panel(
            "Anatomy",
            title_only,
            with_description,
            with_actions,
            own_icon,
            no_icon,
            as_a_heading,
        ),
        panel(
            "Layout",
            default_padding,
            compact,
            hint="`compact()` for an `Empty` inside a card or a table",
        ),
        panel("Empty", first_use, no_results),
        panel("Error", could_not_load, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "The icon is `aria-hidden`, so the title and description are what a "
            "screen reader reads.",
        ),
        Note(
            "a11y",
            '`title(..., heading="h2")` renders a heading element, which puts '
            "the `Empty` in the document outline.",
        ),
        Note(
            "warn",
            "An `Empty` has no role and no live region, so swapping one in by "
            "AJAX is silent to a screen reader unless its container announces "
            "the change.",
        ),
    ],
    related=[Alert, Skeleton, Spinner],
)
