from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Combobox, NativeSelect, RadioGroup, Select, SelectGroup, SelectOption

from hue_docs_v2.icons import Icon
from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def plan() -> Select:
    return (
        Select()
        .name("plan")
        .label("Plan")
        .placeholder("Choose a plan")
        .content(
            SelectOption().value("free").label("Free").meta("$0"),
            SelectOption().value("pro").label("Pro").meta("$49"),
            SelectOption().value("scale").label("Scale").meta("$199"),
        )
    )


# Anatomy


def descriptions() -> Select:
    return (
        Select()
        .name("role")
        .label("Role")
        .value("editor")
        .content(
            SelectOption()
            .value("viewer")
            .label("Viewer")
            .description("Can read everything, change nothing."),
            SelectOption()
            .value("editor")
            .label("Editor")
            .description("Can edit content but not settings."),
            SelectOption()
            .value("admin")
            .label("Admin")
            .description("Full access, including billing."),
        )
    )


def icons_and_meta() -> Select:
    return (
        Select()
        .name("channel")
        .label("Notify by")
        .value("email")
        .content(
            SelectOption()
            .value("email")
            .label("Email")
            .icon(Icon("bell"))
            .meta("Instant"),
            SelectOption()
            .value("digest")
            .label("Daily digest")
            .icon(Icon("calendar"))
            .meta("09:00"),
            SelectOption()
            .value("card")
            .label("Invoice only")
            .icon(Icon("credit-card"))
            .meta("Monthly"),
        )
    )


def groups() -> Select:
    return (
        Select()
        .name("tz")
        .label("Time zone")
        .placeholder("Choose a time zone")
        .content(
            SelectGroup()
            .label("Europe")
            .content(
                SelectOption().value("oslo").label("Oslo").meta("UTC+1"),
                SelectOption().value("london").label("London").meta("UTC+0"),
            ),
            SelectGroup()
            .label("Americas")
            .content(
                SelectOption().value("ny").label("New York").meta("UTC-5"),
                SelectOption().value("la").label("Los Angeles").meta("UTC-8"),
            ),
        )
    )


# Sizes


def sm() -> Select:
    return (
        Select()
        .name("size_sm")
        .label("Small")
        .size("sm")
        .value("a")
        .content(
            SelectOption().value("a").label("Option A"),
            SelectOption().value("b").label("Option B"),
        )
    )


def md() -> Select:
    return (
        Select()
        .name("size_md")
        .label("Medium")
        .size("md")
        .value("a")
        .content(
            SelectOption().value("a").label("Option A"),
            SelectOption().value("b").label("Option B"),
        )
    )


def lg() -> Select:
    return (
        Select()
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


def placeholder() -> Select:
    return (
        Select()
        .name("state_placeholder")
        .label("Status")
        .placeholder("Choose a status")
        .content(
            SelectOption().value("open").label("Open"),
            SelectOption().value("paid").label("Paid"),
        )
    )


def required() -> Select:
    return (
        Select()
        .name("state_required")
        .label("Status")
        .placeholder("Choose a status")
        .required()
        .content(
            SelectOption().value("open").label("Open"),
            SelectOption().value("paid").label("Paid"),
        )
    )


def disabled_option() -> Select:
    return (
        Select()
        .name("state_option")
        .label("Status")
        .value("open")
        .content(
            SelectOption().value("open").label("Open"),
            SelectOption().value("paid").label("Paid"),
            SelectOption().value("void").label("Void").disabled(),
        )
    )


def disabled() -> Select:
    return (
        Select()
        .name("state_disabled")
        .label("Status")
        .value("open")
        .disabled()
        .content(
            SelectOption().value("open").label("Open"),
            SelectOption().value("paid").label("Paid"),
        )
    )


# Error


def field_error() -> Select:
    return (
        Select()
        .name("plan_required")
        .label("Plan")
        .placeholder("Choose a plan")
        .required()
        .hint("You can change plans at any time.")
        .error("Pick a plan to continue.")
        .content(
            SelectOption().value("free").label("Free"),
            SelectOption().value("pro").label("Pro"),
        )
    )


# Layout


def horizontal() -> Select:
    return (
        Select()
        .name("language")
        .label("Language")
        .hint("For emails and the interface.")
        .value("en")
        .horizontal()
        .content(
            SelectOption().value("en").label("English"),
            SelectOption().value("nb").label("Norsk bokmål"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A Select is a button that opens a list of SelectOption children. "
            "Each option has a value() and a label(); the label is what the "
            "list and the trigger show, and falls back to the value. value() "
            "on the Select picks the option that starts selected, and "
            "placeholder() is what the trigger says while nothing is."
        ),
        pr.code(
            "(\n"
            "    Select()\n"
            '    .name("plan")\n'
            '    .label("Plan")\n'
            '    .placeholder("Choose a plan")\n'
            "    .content(\n"
            '        SelectOption().value("free").label("Free").meta("$0"),\n'
            '        SelectOption().value("pro").label("Pro").meta("$49"),\n'
            "    )\n"
            ")"
        ),
        pr.h3("What an option can hold"),
        pr.p(
            "description() adds a muted line under the label, icon() puts a "
            "component before it, and meta() puts a short note at the end of "
            "the row, such as a price or a code. SelectGroup().label() heads a "
            "run of options. disabled() on an option keeps it in the list but "
            "out of reach of the keys and the pointer."
        ),
        pr.h3("Keyboard"),
        pr.p(
            "Focus stays on the trigger the whole time. The option the keys are "
            "on is named by aria-activedescendant."
        ),
        pr.bullets(
            [
                "Enter, Space, Down or Up opens the list on the selected "
                "option; Home and End open it on the first or last.",
                "Down and Up move one option and stop at either end. Home, "
                "End, Page Up and Page Down jump.",
                "Typing a letter moves to the next option whose label starts "
                "with it. Letters typed within half a second build a word.",
                "Enter or Space chooses the active option and closes the list.",
                "Escape closes the list without choosing. Tab chooses the "
                "active option and moves on.",
            ]
        ),
        pr.h3("What is submitted"),
        pr.p(
            "The value travels in a hidden input under name(). The trigger is "
            "as wide as its longest label, the way a native select is, so "
            "choosing an option does not resize it. disabled() disables both "
            "the trigger and the hidden input, so a disabled Select submits "
            "nothing."
        ),
        pr.p(
            "x_model() goes on the hidden input, so Alpine data bound to a "
            "Select reads the chosen value. The Select sends input and change "
            "events from the hidden input whenever the value changes."
        ),
        pr.h3("Errors"),
        pr.p(
            "error() sets aria-invalid on the trigger, shows the message in "
            "place of the hint and adds it to the trigger's aria-describedby."
        ),
    )


PAGE = ComponentPage(
    Select,
    lede=(
        "A select that draws its own list, so an option can carry a "
        "description, an icon, trailing metadata or a group heading. It "
        "follows the ARIA select-only combobox pattern. For a plain list of "
        "words, NativeSelect is the lighter choice."
    ),
    usage=_usage,
    panels=[
        panel(
            "Live",
            plan,
            layout="stack",
            min_height=260,
            hint="Open it with the keys or a click",
        ),
        panel(
            "Anatomy",
            descriptions,
            icons_and_meta,
            groups,
            min_height=420,
        ),
        panel("Sizes", sm, md, lg, min_height=260),
        panel(
            "States",
            placeholder,
            required,
            disabled_option,
            disabled,
            min_height=240,
        ),
        panel("Error", field_error, layout="stack", min_height=240),
        panel(
            "Layout",
            horizontal,
            layout="stack",
            min_height=200,
            hint="The label takes a 180px column at every width",
        ),
    ],
    notes=[
        Note(
            "a11y",
            "The trigger is a button with role=combobox, aria-haspopup=listbox "
            "and aria-expanded; the list is a listbox named after the label, "
            "and each option has role=option with aria-selected.",
        ),
        Note(
            "a11y",
            "Escape closes only the list and stops there, so a dialog the "
            "Select sits in stays open.",
        ),
        Note(
            "a11y",
            "Option ids are built from the Select's id and a hash of the "
            "value, so values that differ only in spacing or punctuation never "
            "share an id.",
        ),
        Note(
            "warn",
            "required() sets aria-required and the asterisk, but the value is "
            "in a hidden input, which the browser does not validate. Check "
            "for an empty value on the server.",
        ),
    ],
    parts=[SelectOption, SelectGroup],
    related=[NativeSelect, Combobox, RadioGroup],
)
