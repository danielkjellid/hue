from __future__ import annotations

from datetime import date

from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import DateInput, DatePicker, DateTimeInput, Stack, Text, TimeInput

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def due_date() -> DateInput:
    return DateInput().name("due").label("Due date").value(date(2026, 10, 30))


# Modes


def one_day() -> DateInput:
    return (
        DateInput()
        .name("mode_single")
        .label("Due date")
        .mode("single")
        .value(date(2026, 10, 14))
    )


def day_range() -> DateInput:
    return (
        DateInput()
        .name("mode_range")
        .label("Stay")
        .mode("range")
        .value(date(2026, 10, 12), date(2026, 10, 16))
    )


def several_days() -> DateInput:
    return (
        DateInput()
        .name("mode_multiple")
        .label("Blackout dates")
        .mode("multiple")
        .value(date(2026, 10, 23), date(2026, 10, 30))
    )


# Anatomy


def hint() -> DateInput:
    return (
        DateInput()
        .name("starts")
        .label("Start date")
        .hint("The first day the contract runs.")
    )


def presets() -> DateInput:
    return (
        DateInput()
        .name("period")
        .label("Reporting period")
        .mode("range", presets=True)
        .value(date(2026, 10, 14), date(2026, 10, 20))
    )


def hidden_label() -> DateInput:
    return DateInput().name("jump_to").label("Jump to day").hidden_label()


# Sizes


def sm() -> DateInput:
    return DateInput().name("size_sm").label("Small").size("sm")


def md() -> DateInput:
    return DateInput().name("size_md").label("Medium").size("md")


def lg() -> DateInput:
    return DateInput().name("size_lg").label("Large").size("lg")


# States


def weekdays_in_a_window() -> DateInput:
    return (
        DateInput()
        .name("visit")
        .label("Visit date")
        .hint("A weekday from 20 October to 18 December.")
        .min(date(2026, 10, 20))
        .max(date(2026, 12, 18))
        .unavailable("saturday", "sunday")
        .value(date(2026, 10, 21))
    )


def required() -> DateInput:
    return DateInput().name("state_required").label("Due date").required()


def readonly() -> DateInput:
    return (
        DateInput()
        .name("state_readonly")
        .label("Signed on")
        .value(date(2026, 10, 2))
        .readonly()
    )


def disabled() -> DateInput:
    return (
        DateInput()
        .name("state_disabled")
        .label("Due date")
        .value(date(2026, 10, 20))
        .disabled()
    )


# Error


def field_error() -> DateInput:
    return (
        DateInput()
        .name("expires")
        .label("Expires")
        .value(date(2026, 10, 1))
        .error("Choose a date on or after 2026-10-20.")
    )


# Layout


def horizontal() -> DateInput:
    return (
        DateInput()
        .name("renews")
        .label("Renews on")
        .hint("The plan renews on this day.")
        .horizontal()
    )


# Binding


def read_back_as_you_pick() -> ComponentType:
    return (
        Stack()
        .x_data({"days": []})
        .content(
            DateInput()
            .name("days_off")
            .label("Days off")
            .mode("multiple")
            .x_model(unsafe("days")),
            Text().x_text(unsafe("'Picked: ' + days.join(', ')")),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `DateInput` is a text field with a button that opens a month "
            "grid in a popover. `value()` takes `date` objects and refuses a "
            "`datetime`. A `DateInput` without `label()` uses its name as the "
            "label, which also names the popover."
        ),
        pr.code(
            "from datetime import date\n\n"
            'DateInput().name("due").label("Due date").value(date(2026, 10, 30))'
        ),
        pr.p(
            "The button opens the popover, and so does the down arrow in the "
            "field. Focus moves to a day in the grid, which takes the same "
            "keys as a `DatePicker`. Escape closes the popover and puts focus "
            "back in the field. A click outside the `DateInput`, or focus "
            "moving out of it, closes the popover too."
        ),
        pr.h2("DateInput modes"),
        pr.p("`mode()` takes the same values as on `DatePicker`."),
        pr.bullets(
            [
                '`"single"`, the default, holds one day. Picking a day sets it '
                "and closes the popover.",
                '`"range"` holds a start and an end, over two months. The pick '
                "takes effect only on Apply, which waits for both ends, and Cancel "
                "or Escape drops it. "
                "`value()` takes both ends or none.",
                '`"multiple"` holds any number of days, each shown under the '
                "field as a chip with a remove button. A pick adds a day or "
                "removes it, and Done closes the popover.",
            ]
        ),
        pr.p(
            '`mode("range", presets=True)` adds a column of ranges around '
            "today, such as Last 7 days and This month. A preset is disabled "
            "when its start or end falls outside `min()` and `max()` or on a "
            "day `unavailable()` names. Presets on any other mode raise a "
            "`ValueError`."
        ),
        pr.h2("Typing into a DateInput"),
        pr.p(
            "Typed text is read on Enter and when the field loses focus. A "
            "`DateInput` reads 2026-10-20, 20.10.2026, 20/10/26, 20 Oct 2026, "
            "Oct 20, 2026, today, tomorrow and yesterday, with an optional "
            "weekday in front. A range is two days with a spaced hyphen, an en "
            "or em dash, or the word to between them. In the multiple mode a typed "
            "day is added to the rest."
        ),
        pr.p(
            "Text that does not read, or a day that `min()`, `max()` or "
            "`unavailable()` refuses, leaves the value as it was and shows "
            "why under the field. The field also reports itself invalid to "
            "the browser, so the form does not submit until the text is "
            "fixed or put back. Enter on text that has not changed submits "
            "the form as usual."
        ),
        pr.h2("Formats of a DateInput"),
        pr.p(
            "The text is written with the date format in the context's "
            "`Formats`, ISO 8601 by default, and the placeholder is that "
            "format with nothing filled in, such as `YYYY-MM-DD`. "
            "`placeholder()` replaces it. A `DateInput` raises a `ValueError` "
            "on a format whose text it cannot read back, and names one that "
            "reads. `Formats` in `hue.formats` lists which do."
        ),
        pr.h2("What a DateInput submits"),
        pr.p(
            "The text is never submitted. Each day is a hidden input under "
            "`name()`, holding `YYYY-MM-DD`, so a range submits two and "
            "the multiple mode one per day. `x_model()` binds the same list "
            "of ISO dates, whether the days were picked or typed."
        ),
        pr.code(
            "from hue.ui import Button, DateInput, Form\n\n"
            'Form().action("/trips/").content(\n'
            '    DateInput().name("trip").label("Trip").mode("range"),\n'
            '    Button().type("submit").content("Book"),\n'
            ")"
        ),
        pr.p(
            "`required()` sets `required` on the text field in the single and "
            "range modes, so the browser checks it. The multiple mode empties "
            "its text once a day is added, so it sets `aria-required` instead."
        ),
        pr.h3("Readonly and disabled"),
        pr.p(
            "`readonly()` shows the value and submits it, but the field takes "
            "no edits and has no popover. `disabled()` also leaves the days out "
            "of what the form submits."
        ),
        pr.h3("Errors"),
        pr.p(
            "`error()` sets `aria-invalid` on the text field and shows the "
            "message under it in place of the hint. A message for typed text "
            "that did not read appears in the same place."
        ),
    )


PAGE = ComponentPage(
    DateInput,
    lede=(
        "A text field for a day, a range or several days, with a button that "
        "opens a month grid to pick from. Typed text is read back as a day, "
        "and the value is submitted as ISO dates."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            due_date,
            layout="stack",
            min_height=420,
            hint="Type a day, or press the down arrow in the field",
        ),
        panel(
            "Modes",
            one_day,
            day_range,
            several_days,
            layout="stack",
            min_height=560,
        ),
        panel(
            "Anatomy",
            hint,
            presets,
            hidden_label,
            layout="stack",
            min_height=560,
        ),
        panel("Sizes", sm, md, lg, layout="stack", min_height=460),
        panel(
            "States",
            weekdays_in_a_window,
            required,
            readonly,
            disabled,
            layout="stack",
            min_height=560,
        ),
        panel("Error", field_error, layout="stack", min_height=420),
        panel(
            "Layout",
            horizontal,
            layout="stack",
            min_height=420,
            min_width=480,
            hint="`horizontal()` puts the label beside the field",
        ),
        panel(
            "Binding",
            read_back_as_you_pick,
            layout="stack",
            min_height=460,
            hint="`x_model()` with the multiple mode",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "The button is an icon button named Choose date, with "
            '`aria-haspopup="dialog"`, `aria-expanded` and `aria-controls`. The '
            'popover has `role="dialog"` and the field\'s label as its name.',
        ),
        Note(
            "a11y",
            "The error element is always on the page and in the field's "
            "`aria-describedby`, so a message for typed text is read with the "
            "field.",
        ),
        Note(
            "a11y",
            "Each chip's remove button is named Remove followed by the full "
            "date. Removing a day moves focus back to the text field.",
        ),
        Note(
            "a11y",
            "Escape closes only the popover and stops there, so a dialog the "
            "`DateInput` sits in stays open. On the month or year grid, "
            "Escape first goes back to the days.",
        ),
        Note(
            "note",
            "The range summary beside Apply, with the picked days and their "
            "count, is a polite live region.",
        ),
        Note(
            "warn",
            "A multiple `DateInput` with `required()` sets only `aria-required`, "
            "since its days are in hidden inputs that the browser does not "
            "validate. Check for a missing value on the server.",
        ),
        Note(
            "warn",
            "A `DateInput` raises a `ValueError` when `value()` holds more than "
            "one day in the single mode, or one day in the range mode.",
        ),
    ],
    related=[DatePicker, DateTimeInput, TimeInput],
)
