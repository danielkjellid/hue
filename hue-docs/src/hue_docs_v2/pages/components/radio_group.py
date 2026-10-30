from __future__ import annotations

from hue.types.core import ComponentType
from hue.ui import Checkbox, NativeSelect, Radio, RadioGroup, Select

from hue_docs_v2.layout import prose as pr
from hue_docs_v2.model import ComponentPage, Note, panel

# Live


def region() -> RadioGroup:
    return (
        RadioGroup()
        .name("region")
        .legend("Region")
        .value("eu")
        .content(
            Radio().value("eu").label("Europe"),
            Radio().value("us").label("North America"),
            Radio().value("ap").label("Asia Pacific"),
        )
    )


# Anatomy


def legend_and_hint() -> RadioGroup:
    return (
        RadioGroup()
        .name("billing")
        .legend("Billing period")
        .hint("You can switch at the end of any period.")
        .content(
            Radio().value("monthly").label("Monthly"),
            Radio().value("yearly").label("Yearly"),
        )
    )


def with_descriptions() -> RadioGroup:
    return (
        RadioGroup()
        .name("plan")
        .legend("Plan")
        .value("team")
        .content(
            Radio()
            .value("solo")
            .label("Solo")
            .description("One seat, no shared workspaces."),
            Radio()
            .value("team")
            .label("Team")
            .description("Up to 20 seats and shared billing."),
        )
    )


def card() -> RadioGroup:
    return (
        RadioGroup()
        .name("plan_card")
        .legend("Plan")
        .card()
        .value("team")
        .content(
            Radio()
            .value("solo")
            .label("Solo")
            .description("One seat, no shared workspaces."),
            Radio()
            .value("team")
            .label("Team")
            .description("Up to 20 seats and shared billing."),
        )
    )


# States


def nothing_selected() -> RadioGroup:
    return (
        RadioGroup()
        .name("state_none")
        .legend("Delivery")
        .content(
            Radio().value("standard").label("Standard"),
            Radio().value("express").label("Express"),
        )
    )


def required() -> RadioGroup:
    return (
        RadioGroup()
        .name("state_required")
        .legend("Delivery")
        .required()
        .content(
            Radio().value("standard").label("Standard"),
            Radio().value("express").label("Express"),
        )
    )


def one_option_disabled() -> RadioGroup:
    return (
        RadioGroup()
        .name("state_option")
        .legend("Delivery")
        .value("standard")
        .content(
            Radio().value("standard").label("Standard"),
            Radio().value("express").label("Express").disabled(),
        )
    )


def disabled() -> RadioGroup:
    return (
        RadioGroup()
        .name("state_disabled")
        .legend("Delivery")
        .value("standard")
        .disabled()
        .content(
            Radio().value("standard").label("Standard"),
            Radio().value("express").label("Express"),
        )
    )


# Error


def field_error() -> RadioGroup:
    return (
        RadioGroup()
        .name("region_required")
        .legend("Region")
        .required()
        .error("Pick a region to continue.")
        .content(
            Radio().value("eu").label("Europe"),
            Radio().value("us").label("North America"),
        )
    )


def _usage() -> ComponentType:
    return pr.page(
        pr.h2("Usage"),
        pr.p(
            "A `RadioGroup` is a fieldset of native radio inputs. The group owns "
            "the name, the legend and which option is selected; each `Radio` "
            "carries only its value, its label and an optional description. "
            "`value()` on the group picks the option that starts selected."
        ),
        pr.code(
            "(\n"
            "    RadioGroup()\n"
            '    .name("region")\n'
            '    .legend("Region")\n'
            '    .value("eu")\n'
            "    .content(\n"
            '        Radio().value("eu").label("Europe"),\n'
            '        Radio().value("us").label("North America"),\n'
            "    )\n"
            ")"
        ),
        pr.p(
            "`legend()` names the group. `label()` works as well and is used when "
            "there is no legend. A `RadioGroup` with neither renders no legend at "
            "all, so always set one."
        ),
        pr.h3("Ids"),
        pr.p(
            "Each `Radio`'s id is built from the group's id and the option's value, "
            "with the value percent-encoded, so values with spaces or other scripts "
            "still give distinct ids. The group's id is its name unless `id()` is "
            "set, so two `RadioGroup` components that share a name on one page need "
            "an `id()` on one of them."
        ),
        pr.h3("Required, disabled and errors"),
        pr.p(
            "`required()` puts the `required` attribute on every radio, which makes "
            "the browser refuse to submit until one is chosen, and adds the "
            "asterisk to the legend. `disabled()` on the group disables the "
            "fieldset and every radio in it; `disabled()` on a `Radio` disables "
            "that option alone."
        ),
        pr.p(
            "`error()` sets `aria-invalid` on the fieldset and shows the message "
            "under the options, in place of the hint."
        ),
        pr.h3("Cards"),
        pr.p(
            "`card()` on the group gives every option a bordered surface that "
            "fills with the accent when it is selected. It suits options that "
            "carry a description."
        ),
    )


PAGE = ComponentPage(
    RadioGroup,
    lede=(
        "A set of options where exactly one can be selected. It is a fieldset "
        "of native radio inputs, so the arrow keys move the selection and the "
        "legend is read with each option."
    ),
    usage=_usage,
    panels=[
        panel("Live", region, layout="center", hint="Tab in, then use the arrow keys"),
        panel("Anatomy", legend_and_hint, with_descriptions, card, layout="stack"),
        panel(
            "States",
            nothing_selected,
            required,
            one_option_disabled,
            disabled,
        ),
        panel("Error", field_error, layout="stack"),
    ],
    notes=[
        Note(
            "a11y",
            "The options sit in a fieldset with a legend, so a screen reader "
            "announces the question along with each option.",
        ),
        Note(
            "a11y",
            "Each radio is named by its label through `aria-labelledby` and "
            "described by its description through `aria-describedby`, so the "
            "description is not read as part of the name.",
        ),
        Note(
            "a11y",
            "The radios are native inputs sharing one name, so Tab stops once "
            "on the group and the arrow keys move the selection, as the browser "
            "always handles them.",
        ),
        Note(
            "warn",
            "A `RadioGroup` without `legend()` or `label()` renders no legend, and "
            "the options are then announced without their question.",
        ),
    ],
    parts=[Radio],
    related=[Select, NativeSelect, Checkbox],
)
