from __future__ import annotations

from datetime import date

from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import DatePicker, Stack, Text

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def due_date() -> DatePicker:
    return DatePicker().name("due").label("Due date").value(date(2026, 10, 30))


# Modes


def single_day() -> DatePicker:
    return (
        DatePicker()
        .name("mode_single")
        .label("Due date")
        .mode("single")
        .value(date(2026, 10, 14))
    )


def day_range() -> DatePicker:
    return (
        DatePicker()
        .name("mode_range")
        .label("Stay")
        .mode("range")
        .value(date(2026, 10, 12), date(2026, 10, 16))
    )


def several_days() -> DatePicker:
    return (
        DatePicker()
        .name("mode_multiple")
        .label("Shifts")
        .mode("multiple")
        .value(date(2026, 10, 6), date(2026, 10, 8), date(2026, 10, 13))
    )


# Sizes


def sm() -> DatePicker:
    return (
        DatePicker().name("size_sm").label("Small").size("sm").value(date(2026, 10, 14))
    )


def md() -> DatePicker:
    return (
        DatePicker()
        .name("size_md")
        .label("Medium")
        .size("md")
        .value(date(2026, 10, 14))
    )


# Anatomy


def two_months() -> DatePicker:
    return (
        DatePicker()
        .name("stay")
        .label("Stay")
        .mode("range")
        .months(2)
        .value(date(2026, 10, 27), date(2026, 11, 3))
    )


def markers() -> DatePicker:
    return (
        DatePicker()
        .name("agenda")
        .label("Agenda")
        .markers(date(2026, 10, 2), date(2026, 10, 14), date(2026, 10, 19))
        .value(date(2026, 10, 19))
    )


def hint() -> DatePicker:
    return (
        DatePicker()
        .name("start")
        .label("Start date")
        .hint("The first day the contract runs.")
        .value(date(2026, 11, 2))
    )


def hidden_label() -> DatePicker:
    return (
        DatePicker()
        .name("jump_to")
        .label("Jump to day")
        .hidden_label()
        .value(date(2026, 10, 21))
    )


# Week start


def monday() -> DatePicker:
    return (
        DatePicker()
        .name("week_monday")
        .label("Monday first")
        .size("sm")
        .week_start("monday")
        .value(date(2026, 10, 14))
    )


def saturday() -> DatePicker:
    return (
        DatePicker()
        .name("week_saturday")
        .label("Saturday first")
        .size("sm")
        .week_start("saturday")
        .value(date(2026, 10, 14))
    )


def sunday() -> DatePicker:
    return (
        DatePicker()
        .name("week_sunday")
        .label("Sunday first")
        .size("sm")
        .week_start("sunday")
        .value(date(2026, 10, 14))
    )


# States


def limits_and_unavailable() -> DatePicker:
    return (
        DatePicker()
        .name("delivery")
        .label("Delivery day")
        .min(date(2026, 12, 1))
        .max(date(2026, 12, 31))
        .unavailable("saturday", "sunday", date(2026, 12, 25))
        .value(date(2026, 12, 3))
    )


def required() -> DatePicker:
    return DatePicker().name("state_required").label("Due date").required()


def disabled() -> DatePicker:
    return (
        DatePicker()
        .name("state_disabled")
        .label("Due date")
        .value(date(2026, 10, 14))
        .disabled()
    )


# Error


def field_error() -> DatePicker:
    return (
        DatePicker()
        .name("checkout")
        .label("Check-out")
        .mode("range")
        .value(date(2026, 10, 20))
        .required()
        .error("Pick the day you leave.")
    )


# Binding


def read_back_as_you_pick() -> ComponentType:
    return (
        Stack()
        .x_data({"days": []})
        .content(
            DatePicker()
            .name("trip")
            .label("Trip")
            .mode("range")
            .x_model(unsafe("days")),
            Text().x_text(unsafe("'Picked: ' + days.join(' to ')")),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A DatePicker is a month grid on the page, not a field with a "
            "popover. label() is required: it becomes the legend over the "
            "months, and a DatePicker without one raises a ValueError. value() "
            "takes date objects; a datetime raises a ValueError too, since it "
            "would match none of the days."
        ),
        pr.code(
            "from datetime import date\n\n"
            'DatePicker().name("due").label("Due date").value(date(2026, 10, 30))'
        ),
        pr.p(
            "Without a value, the DatePicker opens on today's month, or on the "
            "nearest day min() and max() allow. Today is bold, ringed while it "
            'is not selected, and has aria-current="date".'
        ),
        pr.h2("DatePicker modes"),
        pr.p("mode() decides what a click does to the selection."),
        pr.bullets(
            [
                '"single", the default, holds one day. A click replaces it.',
                '"range" holds a start and an end. The first click starts a '
                "range and the second ends it, in either order; until then the "
                "band follows the pointer or the keys.",
                '"multiple" holds any number of days. A click adds a day or '
                "takes it away.",
            ]
        ),
        pr.p(
            "months() shows several months side by side. Only the first has "
            "Previous and only the last has Next."
        ),
        pr.h2("Days that refuse a pick"),
        pr.p(
            "min() and max() bound the days that can be picked. unavailable() "
            'takes dates and weekday names, as in unavailable("saturday", '
            '"sunday", date(2026, 12, 25)). A refused day is struck through '
            "and has aria-disabled; the keys still move onto it, but Enter "
            "and a click do nothing."
        ),
        pr.p(
            "markers() puts a dot under days with something on them. Its label "
            'argument, "has events" by default, is added to each marked '
            "day's accessible name, since a dot says nothing to a screen reader."
        ),
        pr.h2("DatePicker keyboard"),
        pr.p("One day in the grid is a tab stop. From there:"),
        pr.bullets(
            [
                "The arrow keys move a day or a week.",
                "Home and End go to the start and end of the week, by week_start().",
                "Page Up and Page Down move a month, and with Shift a year.",
                "Enter or Space picks the focused day.",
                "The title button in the caption switches to a grid of months, "
                "and from there to a grid of years. Escape goes back to the "
                "days and puts focus on the focused day.",
            ]
        ),
        pr.h2("What a DatePicker submits"),
        pr.p(
            "Each picked day is a hidden input under name(), holding an ISO "
            "date. A range submits its start and its end, and a range picked "
            "on one day submits that day twice. x_model() binds the same list "
            "of ISO dates in every mode."
        ),
        pr.p(
            "Hidden inputs are never validated, so required() adds an empty, "
            "visually hidden text input that the browser does check. It stays "
            "required until the pick is complete: one day, or both ends of a "
            "range. When the browser points at it, focus goes on to the grid."
        ),
        pr.h3("Errors"),
        pr.p(
            "error() sets aria-invalid on the fieldset and shows the message "
            "under the months. A DatePicker shows its hint and its error "
            "together."
        ),
    )


PAGE = ComponentPage(
    DatePicker,
    lede=(
        "A month grid to pick a day, a range or several days from, inline on "
        "the page. It follows the WAI-ARIA date grid pattern, and min(), max() "
        "and unavailable() say which days refuse a pick."
    ),
    usage=_usage,
    panels=[
        panel("Live", due_date, layout="center", hint="Tab in and use the arrows"),
        panel("Modes", single_day, day_range, several_days, layout="stack"),
        panel("Sizes", sm, md, layout="stack"),
        panel("Anatomy", two_months, markers, hint, hidden_label, layout="stack"),
        panel(
            "Week start",
            monday,
            saturday,
            sunday,
            layout="stack",
            hint="week_start() sets the first column",
        ),
        panel("States", limits_and_unavailable, required, disabled, layout="stack"),
        panel("Error", field_error, layout="stack"),
        panel(
            "Binding",
            read_back_as_you_pick,
            layout="stack",
            hint="x_model() with a range",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "Each month is a table with role=grid, labelled with its month and "
            "year, and with aria-multiselectable in the range and multiple "
            "modes. Each day carries its full date as aria-label and its "
            "selection as aria-selected.",
        ),
        Note(
            "a11y",
            "The column headers carry the full weekday name in abbr, which a "
            "screen reader announces in place of the short name.",
        ),
        Note(
            "a11y",
            "The days are a single tab stop with a roving tabindex, so Tab "
            "moves past the grid in one press.",
        ),
        Note(
            "a11y",
            "Escape on the month or year grid goes back to the days and stops "
            "there, so a dialog the DatePicker sits in stays open.",
        ),
        Note(
            "note",
            "Day and month names come from Formats, so a framework's "
            "translations reach the grid.",
        ),
        Note(
            "warn",
            "A DatePicker raises a ValueError without label(), and when value() "
            "is given more days than the mode holds.",
        ),
    ],
)
