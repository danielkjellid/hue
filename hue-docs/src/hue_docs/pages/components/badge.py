from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Alert, Badge

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Variants


def neutral() -> Badge:
    return Badge().content("Draft")


def accent() -> Badge:
    return Badge().variant("accent").content("Beta")


def success() -> Badge:
    return Badge().variant("success").content("Paid")


def warning() -> Badge:
    return Badge().variant("warning").content("Pending")


def danger() -> Badge:
    return Badge().variant("danger").content("Declined")


def info() -> Badge:
    return Badge().variant("info").content("Scheduled")


def solid() -> Badge:
    return Badge().variant("solid").content("New")


# Sizes


def md() -> Badge:
    return Badge().variant("accent").content("Pro")


def lg() -> Badge:
    return Badge().variant("accent").size("lg").content("Pro")


# Anatomy


def label_only() -> Badge:
    return Badge().variant("success").content("Active")


def with_dot() -> Badge:
    return Badge().variant("success").dot().content("Active")


def pill() -> Badge:
    return Badge().pill().content("12")


def numeric() -> Badge:
    return Badge().numeric().content("1,280")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Badge` is an inline `span` holding a short label. `variant()` sets "
            'the colour and defaults to `"neutral"`. `size()` is `"md"` (20px tall) or '
            '`"lg"` '
            "(24px tall)."
        ),
        pr.code('Badge().variant("success").dot().content("Paid")'),
        pr.h3("Dot, pill and numeric"),
        pr.p(
            "`dot()` puts a small dot before the label in the label's own "
            "colour. `pill()` rounds the ends fully and pads the sides by 9px. "
            '`size("lg")` pads them by 9px already, so a pill only widens at the '
            "default size. "
            "`numeric()` switches the figures to tabular widths, so counts in a "
            "column line up digit for digit."
        ),
        pr.code('Badge().pill().numeric().content("128")'),
    )


PAGE = ComponentPage(
    Badge,
    lede=(
        "A `Badge` is a short status or count label, such as Paid on an invoice "
        "row or 12 next to a tab. Seven variants set its tone, and `dot()`, "
        "`pill()` and `numeric()` adjust it for status and counts."
    ),
    usage=_usage,
    panels=[
        panel(
            "Variants",
            neutral,
            accent,
            success,
            warning,
            danger,
            info,
            solid,
        ),
        panel("Sizes", md, lg),
        panel("Anatomy", label_only, with_dot, pill, numeric),
    ],
    notes=[
        Note(
            "a11y",
            "A `Badge` is a `span` with no role, so a screen reader reads its text "
            "inline with whatever is around it.",
        ),
        Note(
            "a11y",
            "The dot is `aria-hidden` and the colour is not announced, so the "
            "text label is all a screen reader hears.",
        ),
    ],
    related=[Alert],
)
