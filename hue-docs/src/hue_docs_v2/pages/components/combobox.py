from __future__ import annotations

from hue.js import unsafe
from hue.types.core import ComponentType
from hue.ui import (
    Combobox,
    NativeSelect,
    Select,
    SelectGroup,
    SelectOption,
    Stack,
    Text,
)

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def country() -> Combobox:
    return (
        Combobox()
        .name("country")
        .label("Country")
        .placeholder("Search countries")
        .content(
            SelectOption().value("no").label("Norway").meta("NO"),
            SelectOption().value("se").label("Sweden").meta("SE"),
            SelectOption().value("dk").label("Denmark").meta("DK"),
            SelectOption().value("fi").label("Finland").meta("FI"),
            SelectOption().value("is").label("Iceland").meta("IS"),
            SelectOption().value("de").label("Germany").meta("DE"),
        )
    )


# Anatomy


def grouped_with_hint() -> Combobox:
    return (
        Combobox()
        .name("origin")
        .label("Ships from")
        .placeholder("Search countries")
        .value("se")
        .hint("Where the invoice is sent from.")
        .content(
            SelectGroup()
            .label("Nordics")
            .content(
                SelectOption().value("no").label("Norway"),
                SelectOption().value("se").label("Sweden"),
            ),
            SelectGroup()
            .label("Rest of Europe")
            .content(
                SelectOption().value("de").label("Germany"),
                SelectOption().value("nl").label("Netherlands"),
            ),
        )
    )


def descriptions() -> Combobox:
    return (
        Combobox()
        .name("assignee")
        .label("Assignee")
        .placeholder("Search people")
        .content(
            SelectOption().value("ada").label("Ada Lovelace").description("Design"),
            SelectOption().value("grace").label("Grace Hopper").description("Platform"),
            SelectOption()
            .value("alan")
            .label("Alan Turing")
            .description("Research, on leave")
            .disabled(),
        )
    )


# Multiple


def several_values() -> Combobox:
    return (
        Combobox()
        .name("markets")
        .label("Markets")
        .placeholder("Add another")
        .multiple()
        .value("no", "se")
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
            SelectOption().value("dk").label("Denmark"),
            SelectOption().value("fi").label("Finland"),
        )
    )


# Sizes


def sm() -> Combobox:
    return (
        Combobox()
        .name("size_sm")
        .label("Small")
        .size("sm")
        .value("a")
        .content(
            SelectOption().value("a").label("Option A"),
            SelectOption().value("b").label("Option B"),
        )
    )


def md() -> Combobox:
    return (
        Combobox()
        .name("size_md")
        .label("Medium")
        .size("md")
        .value("a")
        .content(
            SelectOption().value("a").label("Option A"),
            SelectOption().value("b").label("Option B"),
        )
    )


def lg() -> Combobox:
    return (
        Combobox()
        .name("size_lg")
        .label("Large")
        .size("lg")
        .value("a")
        .content(
            SelectOption().value("a").label("Option A"),
            SelectOption().value("b").label("Option B"),
        )
    )


# States


def with_value() -> Combobox:
    return (
        Combobox()
        .name("state_value")
        .label("Country")
        .value("no")
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
        )
    )


def required() -> Combobox:
    return (
        Combobox()
        .name("state_required")
        .label("Country")
        .placeholder("Search countries")
        .required()
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
        )
    )


def disabled() -> Combobox:
    return (
        Combobox()
        .name("state_disabled")
        .label("Country")
        .value("no")
        .disabled()
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
        )
    )


def disabled_multiple() -> Combobox:
    return (
        Combobox()
        .name("state_disabled_multiple")
        .label("Markets")
        .multiple()
        .value("no", "se")
        .disabled()
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
        )
    )


# Empty


def own_empty_message() -> Combobox:
    return (
        Combobox()
        .name("ship_to")
        .label("Ship to")
        .placeholder("Try typing Japan")
        .empty_message("We do not ship there yet.")
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
        )
    )


# Error


def field_error() -> Combobox:
    return (
        Combobox()
        .name("billing_country")
        .label("Billing country")
        .placeholder("Search countries")
        .required()
        .error("Pick the country the card is registered in.")
        .content(
            SelectOption().value("no").label("Norway"),
            SelectOption().value("se").label("Sweden"),
        )
    )


# Layout


def horizontal() -> Combobox:
    return (
        Combobox()
        .name("language")
        .label("Language")
        .hint("For emails and the interface.")
        .horizontal()
        .value("en")
        .content(
            SelectOption().value("en").label("English"),
            SelectOption().value("nb").label("Norsk bokmål"),
        )
    )


# Binding


def read_back_as_you_choose() -> ComponentType:
    return (
        Stack()
        .x_data({"markets": ["no"]})
        .content(
            Combobox()
            .name("bound_markets")
            .label("Markets")
            .multiple()
            .x_model(unsafe("markets"))
            .content(
                SelectOption().value("no").label("Norway"),
                SelectOption().value("se").label("Sweden"),
                SelectOption().value("dk").label("Denmark"),
            ),
            Text().x_text(unsafe("'Chosen: ' + markets.join(', ')")),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `Combobox` is a text field with a list of options under it. "
            "Typing filters the list, and the options are the same "
            "`SelectOption` and `SelectGroup` that a `Select` takes, with the same "
            "descriptions, icons and metadata."
        ),
        pr.code(
            "(\n"
            "    Combobox()\n"
            '    .name("country")\n'
            '    .label("Country")\n'
            '    .placeholder("Search countries")\n'
            "    .content(\n"
            '        SelectOption().value("no").label("Norway"),\n'
            '        SelectOption().value("se").label("Sweden"),\n'
            "    )\n"
            ")"
        ),
        pr.h3("Filtering"),
        pr.p(
            "The list opens when the field gets focus. An option stays in the "
            "list while its label contains what was typed, ignoring case, and "
            "a group is hidden once none of its options are left. The first "
            "match becomes active, so a word and Enter picks it. When nothing "
            'matches, the list says `empty_message()`, which defaults to "Nothing '
            'matches."'
        ),
        pr.h3("Keyboard"),
        pr.p("Focus stays in the text field throughout."),
        pr.bullets(
            [
                "Down opens the list on the chosen option, or the first. Up "
                "opens it on the last. Alt+Down opens it with nothing active.",
                "Down and Up move through the options left after filtering "
                "and stop at either end.",
                "Enter chooses the active option. With the list closed, Enter "
                "is left to submit the form.",
                "Escape closes the list. Alt+Up closes it too.",
            ]
        ),
        pr.h3("Several values"),
        pr.p(
            "`multiple()` lets several options be chosen. Each one shows in the "
            "field as a token with a remove button, choosing an option toggles "
            "it, and the list stays open for the next. Backspace in an empty "
            "field removes the last token. `value()` takes several values only "
            "on a multiple `Combobox`. A single one given several raises a "
            "`ValueError` when it renders."
        ),
        pr.h3("What is submitted"),
        pr.p(
            "Each chosen value is a hidden input under `name()`, so a multiple "
            "`Combobox` submits the name once per value. The text field has no "
            "name and is never submitted. Clearing the text of a single "
            "`Combobox` and leaving the field clears its value."
        ),
        pr.p(
            "`x_model()` binds the chosen value, never the typed text. It holds a "
            "string "
            "for a single `Combobox` and a list of values for a multiple one. It "
            "works both ways, so Alpine data can set the choice too."
        ),
        pr.code(
            'Stack().x_data({"markets": ["no"]}).content(\n'
            "    Combobox()\n"
            '    .name("markets")\n'
            '    .label("Markets")\n'
            "    .multiple()\n"
            '    .x_model(unsafe("markets"))\n'
            "    .content(...),\n"
            ")"
        ),
        pr.h3("Errors"),
        pr.p(
            "`error()` sets `aria-invalid` on the text field, which draws the "
            "field's border in red, shows the message in place of the hint and "
            "adds it to the field's `aria-describedby`. A `horizontal()` field "
            "keeps its hint beside the label."
        ),
    )


PAGE = ComponentPage(
    Combobox,
    lede=(
        "A text field that filters a list of options as you type, for a list "
        "too long to scroll through. It follows the ARIA combobox pattern with "
        "list autocomplete, and can hold one value or several."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            country,
            layout="stack",
            min_height=340,
            hint="Focus it and type, or use the arrows",
        ),
        panel(
            "Anatomy",
            grouped_with_hint,
            descriptions,
            min_height=320,
        ),
        panel(
            "Multiple",
            several_values,
            layout="stack",
            min_height=280,
            hint="Backspace removes the last token",
        ),
        panel("Sizes", sm, md, lg, min_height=260),
        panel(
            "States",
            with_value,
            required,
            disabled,
            disabled_multiple,
            layout="stack",
            min_height=220,
        ),
        panel(
            "Empty",
            own_empty_message,
            layout="stack",
            min_height=220,
            hint="Type something that is not in the list",
        ),
        panel("Error", field_error, layout="stack", min_height=220),
        panel(
            "Layout",
            horizontal,
            layout="stack",
            min_height=200,
            min_width=480,
            hint="The label takes a 180px column at every width",
        ),
        panel(
            "Binding",
            read_back_as_you_choose,
            layout="stack",
            min_height=260,
            hint="`x_model()` with a multiple `Combobox`",
        ),
    ],
    notes=[
        Note(
            "a11y",
            'The text field has `role="combobox"` with `aria-autocomplete="list"`, '
            "`aria-expanded` and `aria-activedescendant`, so a screen reader "
            "follows the arrows through options that never take focus.",
        ),
        Note(
            "a11y",
            'The empty message sits in a `role="status"` element that is always on '
            "the page, so it is announced when nothing matches.",
        ),
        Note(
            "a11y",
            "Each token's remove button is named Remove followed by the "
            "option's label. Removing a token moves focus back to the text "
            "field.",
        ),
        Note(
            "a11y",
            "Escape closes only the list and stops there, so a dialog the "
            "`Combobox` sits in stays open.",
        ),
        Note(
            "warn",
            "`required()` sets `aria-required` and the asterisk, but the values "
            "are in hidden inputs, which the browser does not validate. Check "
            "for a missing value on the server.",
        ),
    ],
    related=[Select, NativeSelect],
)
