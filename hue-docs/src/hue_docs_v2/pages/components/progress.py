from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Progress, ProgressRing, Skeleton, Spinner

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Variants


def accent() -> Progress:
    return Progress().value(64).label("Uploading archive.zip")


def success() -> Progress:
    return Progress().value(100).variant("success").label("Backup complete")


def warning() -> Progress:
    return Progress().value(92).variant("warning").label("Storage used")


def danger() -> Progress:
    return Progress().value(98).variant("danger").label("API quota used")


# Sizes


def sm() -> Progress:
    return Progress().value(40).size("sm").label("Small")


def md() -> Progress:
    return Progress().value(40).size("md").label("Medium")


def lg() -> Progress:
    return Progress().value(40).size("lg").label("Large")


# Anatomy


def labelled() -> Progress:
    return Progress().value(64).label("Uploading archive.zip")


def hidden_label() -> Progress:
    return Progress().value(32).label("Sync progress").hidden_label()


# States


def not_started() -> Progress:
    return Progress().value(0).label("Import")


def partway() -> Progress:
    return Progress().value(37.5).label("Import")


def complete() -> Progress:
    return Progress().value(100).label("Import")


# Loading


def indeterminate() -> Progress:
    return Progress().indeterminate().label("Exporting invoices")


def indeterminate_without_label_text() -> Progress:
    return Progress().indeterminate().label("Loading").hidden_label()


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A Progress is a horizontal bar. value() is the percentage done, "
            "from 0 to 100, and label() names the bar. The label shows above "
            "the bar with the percentage beside it."
        ),
        pr.code('Progress().value(64).label("Uploading archive.zip")'),
        pr.p(
            "label() is required. A Progress without one raises a ValueError "
            "when it renders, because a progressbar with no name is announced "
            "as only a number. hidden_label() keeps the label as the bar's "
            "accessible name and takes it and the percentage off the screen."
        ),
        pr.h3("Values"),
        pr.p(
            "value() is clamped to the range 0 to 100, so 120 renders as 100 "
            "and -5 as 0. NaN raises a ValueError. The percentage prints "
            "without trailing zeros: 37.5 shows as 37.5% and 40.0 as 40%."
        ),
        pr.h3("Unknown length"),
        pr.p(
            "indeterminate() sweeps a short bar along the track and leaves out "
            "aria-valuenow, so a screen reader hears no position rather than "
            "0 percent. It wins over value(). A Progress with neither value() "
            "nor indeterminate() renders as indeterminate too."
        ),
        pr.p(
            "With reduced motion, the sweep stops and the bar fills the whole "
            "track at low opacity, since a still bar at 40% would read as 40% "
            "done."
        ),
        pr.h3("Variant and size"),
        pr.p(
            "variant() colours the fill: accent by default, or success, "
            "warning or danger. size() sets the track height: sm is 4px, md "
            "6px and lg 10px."
        ),
    )


PAGE = ComponentPage(
    Progress,
    lede=(
        "A Progress is a bar that shows how far along a task is, such as an "
        "upload or an import. It reports a percentage, or sweeps when the "
        "length of the work is unknown. For a circle, use ProgressRing."
    ),
    usage=_usage,
    panels=[
        panel("Variants", accent, success, warning, danger, layout="stack"),
        panel("Sizes", sm, md, lg, layout="stack"),
        panel("Anatomy", labelled, hidden_label, layout="stack"),
        panel("States", not_started, partway, complete, layout="stack"),
        panel(
            "Loading",
            indeterminate,
            indeterminate_without_label_text,
            layout="stack",
            hint="indeterminate() for work of unknown length",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The track renders role="progressbar" with aria-valuemin 0, '
            "aria-valuemax 100, aria-valuenow and aria-label from label().",
        ),
        Note(
            "a11y",
            "An indeterminate bar has no aria-valuenow, so a screen reader "
            "announces no position instead of 0 percent.",
        ),
        Note(
            "warn",
            "label() is required: a Progress without one raises a ValueError "
            "on render. Use hidden_label() when the label should not show.",
        ),
        Note(
            "note",
            "Leaving out value() renders the bar as indeterminate, not as 0%.",
        ),
    ],
    related=[ProgressRing, Spinner, Skeleton],
)
