from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Progress, ProgressRing, Spinner

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Variants


def accent() -> ProgressRing:
    return ProgressRing().value(64).show_value().label("Storage used")


def success() -> ProgressRing:
    return ProgressRing().value(100).variant("success").show_value().label("Backup")


def warning() -> ProgressRing:
    return ProgressRing().value(88).variant("warning").show_value().label("Seats")


def danger() -> ProgressRing:
    return ProgressRing().value(97).variant("danger").show_value().label("Quota")


# Anatomy


def with_value() -> ProgressRing:
    return ProgressRing().value(64).show_value().label("Storage used")


def bare() -> ProgressRing:
    return ProgressRing().value(64).label("Storage used")


# States


def empty() -> ProgressRing:
    return ProgressRing().value(0).show_value().label("Onboarding")


def partway() -> ProgressRing:
    return ProgressRing().value(28).show_value().label("Onboarding")


def complete() -> ProgressRing:
    return ProgressRing().value(100).variant("success").show_value().label("Onboarding")


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A ProgressRing draws a percentage as a circle, 52px across, "
            "filling from twelve o'clock. value() is the percentage "
            "from 0 to 100 and defaults to 0. label() names what the ring "
            "measures."
        ),
        pr.code('ProgressRing().value(64).show_value().label("Storage used")'),
        pr.h3("Showing the number"),
        pr.p(
            "show_value() prints the percentage in the middle of the ring. "
            "Without it the ring shows no text. Either way, a screen reader "
            "hears the label and the percentage from the ring itself."
        ),
        pr.h3("Values"),
        pr.p(
            "value() is clamped to 0 to 100, and NaN raises a ValueError. A "
            "ProgressRing has no indeterminate state: for work of unknown "
            "length, use Spinner or an indeterminate Progress."
        ),
        pr.h3("Variant"),
        pr.p(
            "variant() colours the arc: accent by default, or success, warning "
            "or danger. The track stays grey."
        ),
    )


PAGE = ComponentPage(
    ProgressRing,
    lede=(
        "A ProgressRing shows a percentage as a filling circle, for a card or "
        "a table cell where a bar would not fit. It takes the same values and "
        "variants as Progress."
    ),
    usage=_usage,
    panels=[
        panel("Variants", accent, success, warning, danger),
        panel("Anatomy", with_value, bare),
        panel("States", empty, partway, complete),
    ],
    notes=[
        Note(
            "a11y",
            'The ring is an svg with role="img" and an aria-label such as '
            '"Storage used, 64 percent complete". The number printed by '
            "show_value() is aria-hidden, so it is not read twice.",
        ),
        Note(
            "note",
            'A ProgressRing is not role="progressbar" and has no aria-valuenow. '
            "The percentage reaches a screen reader through the label text.",
        ),
        Note(
            "warn",
            "label() is optional on a ProgressRing, unlike Progress. Without it "
            'the ring is announced only as "64 percent complete".',
        ),
    ],
    related=[Progress, Spinner],
)
