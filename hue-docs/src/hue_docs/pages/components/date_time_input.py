from __future__ import annotations

from datetime import date, datetime

from hue.types.core import ComponentType
from hue.ui import DateInput, DateTimeInput, TimeInput

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def publish_at() -> DateTimeInput:
    return (
        DateTimeInput()
        .name("publish_at")
        .label("Publish at")
        .value(datetime(2026, 10, 21, 9, 30))
    )


# Step


def half_hours() -> DateTimeInput:
    return (
        DateTimeInput()
        .name("call_at")
        .label("Call at")
        .step(30)
        .min(date(2026, 10, 20))
    )


# States


def required() -> DateTimeInput:
    return DateTimeInput().name("state_required").label("Starts").required()


def readonly() -> DateTimeInput:
    return (
        DateTimeInput()
        .name("state_readonly")
        .label("Sent at")
        .value(datetime(2026, 10, 2, 16, 45))
        .readonly()
    )


def disabled() -> DateTimeInput:
    return (
        DateTimeInput()
        .name("state_disabled")
        .label("Starts")
        .value(datetime(2026, 10, 20, 10, 0))
        .disabled()
    )


# Error


def field_error() -> DateTimeInput:
    return (
        DateTimeInput()
        .name("deadline")
        .label("Deadline")
        .value(datetime(2026, 10, 1, 17, 0))
        .error("Choose a date on or after 2026-10-20.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `DateTimeInput` holds one day and a time of day. Its "
            "button opens a month beside a list of times. `value()` takes a "
            "`datetime`, and `min()`, `max()`, `unavailable()` and `week_start()` "
            "work on the days as on a `DateInput`."
        ),
        pr.code(
            "from datetime import datetime\n\n"
            'DateTimeInput().name("publish_at").label("Publish at")'
            ".value(datetime(2026, 10, 21, 9, 30))"
        ),
        pr.h2("Picking in a DateTimeInput"),
        pr.p(
            "`step()` sets the minutes between the times in the list, 15 by "
            "default, from 1 to 720. A step outside that raises a `ValueError`."
        ),
        pr.bullets(
            [
                "Picking a day keeps the time already set, or uses 09:00 "
                "when there is none.",
                "Picking a time keeps the day already set, or uses today.",
                "Now picks the current time, rounded up to the next step of the list.",
                "The popover stays open while you pick. Done closes it.",
            ]
        ),
        pr.p(
            "Typed text is a day as a `DateInput` reads it, followed by a time "
            "if it has one, as in 2026-10-20 14:30 or 20 Oct 2026, 2:30 pm. "
            "Text with no time keeps the time already set, or uses 09:00."
        ),
        pr.h2("What a DateTimeInput submits"),
        pr.p(
            "One hidden input under `name()`, holding `YYYY-MM-DDTHH:MM` with "
            "no offset. An aware `datetime` is first converted with the "
            "`localize` of the context's `Formats`, when it has one, so the "
            "field shows and submits the reader's time."
        ),
    )


PAGE = ComponentPage(
    DateTimeInput,
    lede=(
        "A text field for a day and a time, with a button that opens a month "
        "beside a list of times. It shares its typing, refusals and states "
        "with `DateInput`."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            publish_at,
            layout="stack",
            min_height=460,
            hint="Open it and press Now",
        ),
        panel(
            "Step",
            half_hours,
            layout="stack",
            min_height=460,
            hint="`step(30)` lists every half hour",
        ),
        panel(
            "States",
            required,
            readonly,
            disabled,
            layout="stack",
            min_height=520,
        ),
        panel("Error", field_error, layout="stack", min_height=460),
    ],
    notes=[
        Note(
            "a11y",
            'The times are a `role="listbox"` of options with one tab stop. '
            "The up and down arrows, Home and End move through them, and "
            "Enter or Space picks one.",
        ),
        Note(
            "a11y",
            "Escape closes only the popover and puts focus back in the field, "
            "so a dialog the `DateTimeInput` sits in stays open.",
        ),
        Note(
            "note",
            "The text is written with the datetime format in the context's "
            "`Formats`, and a format the field cannot read back raises a "
            "`ValueError`.",
        ),
    ],
    related=[DateInput, TimeInput],
)
