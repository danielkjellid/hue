from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Combobox, NativeSelect, RadioGroup, Select

from hue_docs.layout import prose as pr
from hue_docs.model import ComponentPage, Note, panel

# Live


def time_zone() -> NativeSelect:
    return (
        NativeSelect()
        .name("tz")
        .label("Time zone")
        .options([("oslo", "Europe/Oslo"), ("utc", "UTC"), ("ny", "America/New_York")])
        .value("oslo")
        .hint("Affects report boundaries.")
    )


# Anatomy


def label_and_hint() -> NativeSelect:
    return (
        NativeSelect()
        .name("currency")
        .label("Currency")
        .options([("eur", "Euro"), ("nok", "Norwegian krone"), ("usd", "US dollar")])
        .hint("Used on every invoice from now on.")
    )


def placeholder() -> NativeSelect:
    return (
        NativeSelect()
        .name("country")
        .label("Country")
        .placeholder("Select a country")
        .options([("no", "Norway"), ("se", "Sweden"), ("dk", "Denmark")])
    )


def hidden_label() -> NativeSelect:
    return (
        NativeSelect()
        .name("sort")
        .label("Sort by")
        .hidden_label()
        .options([("new", "Newest first"), ("old", "Oldest first")])
    )


# Sizes


def sm() -> NativeSelect:
    return (
        NativeSelect()
        .name("size_sm")
        .label("Small")
        .size("sm")
        .options([("a", "Option A"), ("b", "Option B")])
    )


def md() -> NativeSelect:
    return (
        NativeSelect()
        .name("size_md")
        .label("Medium")
        .size("md")
        .options([("a", "Option A"), ("b", "Option B")])
    )


def lg() -> NativeSelect:
    return (
        NativeSelect()
        .name("size_lg")
        .label("Large")
        .size("lg")
        .options([("a", "Option A"), ("b", "Option B")])
    )


# States


def with_value() -> NativeSelect:
    return (
        NativeSelect()
        .name("state_value")
        .label("Status")
        .options([("open", "Open"), ("paid", "Paid")])
        .value("paid")
    )


def required() -> NativeSelect:
    return (
        NativeSelect()
        .name("state_required")
        .label("Status")
        .placeholder("Choose a status")
        .options([("open", "Open"), ("paid", "Paid")])
        .required()
    )


def disabled() -> NativeSelect:
    return (
        NativeSelect()
        .name("state_disabled")
        .label("Status")
        .options([("open", "Open"), ("paid", "Paid")])
        .value("open")
        .disabled()
    )


# Error


def field_error() -> NativeSelect:
    return (
        NativeSelect()
        .name("tz_required")
        .label("Time zone")
        .required()
        .placeholder("Select a time zone")
        .options([("oslo", "Europe/Oslo"), ("utc", "UTC")])
        .error("Pick a time zone to continue.")
    )


# Layout


def horizontal() -> NativeSelect:
    return (
        NativeSelect()
        .name("language")
        .label("Language")
        .hint("For emails and the interface.")
        .options([("en", "English"), ("nb", "Norsk bokmål")])
        .horizontal()
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `NativeSelect` is the browser's own `select` element with hue's "
            "field styling, its label, hint and error built in. `options()` takes "
            "the choices as `(value, label)` pairs, and `value()` picks the one "
            "that starts selected."
        ),
        pr.code(
            "(\n"
            "    NativeSelect()\n"
            '    .name("tz")\n'
            '    .label("Time zone")\n'
            '    .options([("oslo", "Europe/Oslo"), ("utc", "UTC")])\n'
            '    .value("oslo")\n'
            ")"
        ),
        pr.h3("Placeholder"),
        pr.p(
            "`placeholder()` adds a first option with an empty value, rendered "
            "disabled, so it cannot be chosen again once a real option has "
            "been picked. It is selected whenever `value()` names none of the "
            "options, including an empty string or a value that no longer "
            "exists. Without a placeholder, the browser shows and submits the "
            "first option in that case."
        ),
        pr.p(
            "Together with `required()`, the placeholder makes the browser "
            "refuse to submit until a real option is chosen, since the "
            "placeholder's value is empty."
        ),
        pr.h3("NativeSelect or Select"),
        pr.p(
            "A `NativeSelect` gets the phone's own picker, typeahead and every "
            "assistive technology behaviour from the browser. An option can "
            "only be a line of text. `Select` draws its own list, which can hold "
            "descriptions, icons, metadata and groups. `Combobox` adds a text "
            "field that filters the options."
        ),
        pr.h3("Errors"),
        pr.p(
            "`error()` sets `aria-invalid` on the `select`, shows the message in "
            "place of the hint and adds it to the `select`'s `aria-describedby`."
            " A `horizontal()` field keeps its hint beside the label."
        ),
    )


PAGE = ComponentPage(
    NativeSelect,
    lede=(
        "The browser's own select, styled as a hue field. It suits a short "
        "list of plain choices, and the platform supplies the picker, the "
        "typeahead and the accessibility."
    ),
    usage=_usage,
    panels=[
        panel("Live", time_zone, layout="stack", hint="Open it and choose"),
        panel(
            "Anatomy",
            label_and_hint,
            placeholder,
            hidden_label,
            layout="stack",
        ),
        panel("Sizes", sm, md, lg, layout="stack"),
        panel("States", with_value, required, disabled, layout="stack"),
        panel("Error", field_error, layout="stack"),
        panel(
            "Layout",
            horizontal,
            layout="stack",
            min_width=480,
            hint="The label takes a 180px column at every width",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "The label is a real `label` element pointing at the `select`, and the "
            "hint and error are tied to it through `aria-describedby`.",
        ),
        Note(
            "a11y",
            "The list, the keyboard and the typeahead are the browser's, so "
            "they behave as they do in every other `select` on the platform.",
        ),
        Note(
            "note",
            "`disabled()` sets the native `disabled` attribute, which takes the "
            "select out of the tab order and out of the submitted form.",
        ),
    ],
    related=[Select, Combobox, RadioGroup],
)
