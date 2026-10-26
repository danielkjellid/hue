from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import NumberInput, Slider, TextInput

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def seats() -> NumberInput:
    return (
        NumberInput()
        .name("seats")
        .label("Seats")
        .min(1)
        .max(50)
        .value("12")
        .hint("Between 1 and 50.")
    )


# Anatomy


def whole_steps() -> NumberInput:
    return NumberInput().name("quantity").label("Quantity").min(0).step(5)


def decimal_steps() -> NumberInput:
    return (
        NumberInput()
        .name("price")
        .label("Price")
        .min(0)
        .step(0.01)
        .prefix("$")
        .value("19.99")
    )


def can_go_negative() -> NumberInput:
    return NumberInput().name("offset").label("Offset").min(-12).max(12).suffix("h")


# Error


def over_the_plan() -> NumberInput:
    return (
        NumberInput()
        .name("plan_seats")
        .label("Seats")
        .min(1)
        .value("80")
        .error("Your plan allows up to 50 seats.")
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `NumberInput` is a ",
            pr.link("TextInput", "/components/text-input/"),
            ' with `type="number"`. It adds `min()`, `max()` and `step()`, which '
            "become the input's own attributes. Label, hint, error, sizes, prefixes "
            "and suffixes work as the `TextInput` page shows. The figures are "
            "set in tabular numerals, so a column of `NumberInput` fields lines up.",
        ),
        pr.code('NumberInput().name("quantity").label("Quantity").min(1).max(100)'),
        pr.p(
            "`value()` takes the starting value as a string, the way the form "
            "submits it."
        ),
        pr.h2("The NumberInput touch keyboard"),
        pr.p(
            "`NumberInput` picks an `inputmode` from `min()` and `step()`. A field "
            "that cannot go negative gets a keypad without a minus sign: "
            '`inputmode="numeric"` when `step()` is a whole number (or not set), '
            'and `inputmode="decimal"` when `step()` is fractional or `"any"`. '
            "Without `min()`, or with a negative `min()`, `NumberInput` sets no "
            '`inputmode` and leaves the keyboard to `type="number"`.'
        ),
        pr.code(
            'NumberInput().name("price").label("Price").min(0).step(0.01)\n'
            "# inputmode=decimal"
        ),
        pr.h2("Validating a NumberInput"),
        pr.p(
            "`min()`, `max()` and `step()` are checked by the browser on submit, "
            "and a request made any other way skips them. Check the number on "
            "the server too and send the message back with `error()` or "
            "`Form.errors()`."
        ),
    )


PAGE = ComponentPage(
    NumberInput,
    lede=(
        "A `TextInput` for a number, with `min()`, `max()` and `step()`. It chooses "
        "the touch keyboard from those limits and lines its figures up in "
        "tabular numerals."
    ),
    usage=_usage,
    panels=[
        panel("Live", seats, layout="stack", hint="Type, or use the arrow keys"),
        panel("Anatomy", whole_steps, decimal_steps, can_go_negative, layout="stack"),
        panel("Error", over_the_plan, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            'The input is a native `type="number"`, so screen readers announce '
            "it as a spin button and the arrow keys step it by `step()`.",
        ),
        Note(
            "note",
            "A prefix or suffix is text beside the input, not part of the "
            'value: a Price field with a `$` prefix submits `"19.99"`.',
        ),
    ],
    related=[TextInput, Slider],
)
