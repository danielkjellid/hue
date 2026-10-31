from __future__ import annotations

from datetime import time

from hue.types.core import ComponentType
from hue.ui import DateInput, DateTimeInput, TimeInput

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def reminder() -> TimeInput:
    return TimeInput().name("reminder").label("Reminder").value(time(14, 30))


# Step


def every_five_minutes() -> TimeInput:
    return TimeInput().name("alarm").label("Alarm").step(5)


# Sizes


def sm() -> TimeInput:
    return TimeInput().name("size_sm").label("Small").size("sm")


def md() -> TimeInput:
    return TimeInput().name("size_md").label("Medium").size("md")


def lg() -> TimeInput:
    return TimeInput().name("size_lg").label("Large").size("lg")


# States


def required() -> TimeInput:
    return TimeInput().name("state_required").label("Opens at").required()


def readonly() -> TimeInput:
    return (
        TimeInput()
        .name("state_readonly")
        .label("Opens at")
        .value(time(8, 0))
        .readonly()
    )


def disabled() -> TimeInput:
    return (
        TimeInput()
        .name("state_disabled")
        .label("Opens at")
        .value(time(8, 0))
        .disabled()
    )


# Error


def field_error() -> TimeInput:
    return (
        TimeInput()
        .name("closes")
        .label("Closes at")
        .value(time(7, 0))
        .error("Close after the shop opens.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `TimeInput` is a text field with a button that opens a list of "
            "the day's times. `value()` takes a `time`, and `step()` sets the "
            "minutes between the times in the list, 15 by default, from 1 to "
            "720. A step outside that raises a `ValueError`."
        ),
        pr.code(
            "from datetime import time\n\n"
            'TimeInput().name("reminder").label("Reminder").value(time(14, 30))'
        ),
        pr.p(
            "The list opens on the time set, or on 09:00 when there is none. "
            "Picking a time sets it and closes the list."
        ),
        pr.h2("Typing into a TimeInput"),
        pr.p(
            "Typed text is read on Enter and when the field loses focus. A "
            "`TimeInput` reads 14:30, 14.30, 1430, 2:30 pm and 9a, and writes "
            "the time back with the time format in the context's `Formats`, "
            "which also labels the times in the list. Text that does not read "
            "leaves the value as it was and shows why under the field."
        ),
        pr.h2("What a TimeInput submits"),
        pr.p(
            "One hidden input under `name()`, holding `HH:MM`. The text is "
            "never submitted. `readonly()`, `disabled()`, `required()` and "
            "`error()` work as on a `DateInput`."
        ),
    )


PAGE = ComponentPage(
    TimeInput,
    lede=(
        "A text field for a time of day, with a button that opens a list of "
        "times a step apart. It shares its typing, states and errors with "
        "`DateInput`."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            reminder,
            layout="stack",
            min_height=380,
            hint="Type 9a, or press the down arrow in the field",
        ),
        panel(
            "Step",
            every_five_minutes,
            layout="stack",
            min_height=380,
            hint="`step(5)` lists every five minutes",
        ),
        panel("Sizes", sm, md, lg, layout="stack", min_height=460),
        panel(
            "States",
            required,
            readonly,
            disabled,
            layout="stack",
            min_height=460,
        ),
        panel("Error", field_error, layout="stack", min_height=380),
    ],
    notes=[
        Note(
            "a11y",
            'The list is a `role="listbox"` named by the field\'s label, with '
            "one tab stop. The up and down arrows, Home and End move through "
            "it, and Enter or Space picks a time.",
        ),
        Note(
            "a11y",
            "The button is an icon button named Choose time. Escape closes "
            "the list and puts focus back in the field.",
        ),
        Note(
            "note",
            "A time format the field cannot read back raises a `ValueError`. "
            "One reads with `%H` and `%M`, or with `%I`, `%M` and `%p`.",
        ),
    ],
    related=[DateInput, DateTimeInput],
)
